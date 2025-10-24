"""
API de Campanhas Automáticas - 3A Frios
========================================

Endpoints para gerenciar configurações, templates e histórico 
das campanhas automáticas de marketing.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date
import logging
import json

# Importações locais
try:
    from ..integrations.supabase_store import get_supabase_client
except ImportError:
    # Fallback se não conseguir importar
    def get_supabase_client():
        class MockClient:
            def table(self, name):
                return type('MockTable', (), {
                    'select': lambda *a: type('MockQuery', (), {
                        'execute': lambda: type('MockResult', (), {'data': [], 'count': 0})(),
                        'eq': lambda *a: type('MockQuery', (), {'execute': lambda: type('MockResult', (), {'data': []})()})(),
                        'order': lambda *a, **k: type('MockQuery', (), {'execute': lambda: type('MockResult', (), {'data': []})()})(),
                        'limit': lambda *a: type('MockQuery', (), {'execute': lambda: type('MockResult', (), {'data': []})()})(),
                    })(),
                    'insert': lambda *a: type('MockQuery', (), {'execute': lambda: type('MockResult', (), {'data': []})()})(),
                    'update': lambda *a: type('MockQuery', (), {'execute': lambda: type('MockResult', (), {'data': []})()})(),
                    'delete': lambda *a: type('MockQuery', (), {'execute': lambda: type('MockResult', (), {'data': []})()})(),
                })()
        return MockClient()

from ..integrations.campaign_processor import CampaignAutomation

logger = logging.getLogger("3afrios.api.campaigns")
router = APIRouter()

# ===================================
# MODELOS PYDANTIC
# ===================================

class CampaignConfig(BaseModel):
    """Configuração de automação de campanhas"""
    automacao_ativa: bool = False
    campanhas_automaticas: Dict[str, Any] = {}
    configuracoes_globais: Dict[str, Any] = {}

class CampaignTemplate(BaseModel):
    """Template de campanha"""
    tipo: str
    nome: str
    descricao: Optional[str] = None
    template_titulo: str
    template_conteudo: str
    variaveis_disponiveis: List[str] = []
    ativo: bool = True
    template_padrao: bool = False
    categoria: str = "marketing"
    tags: List[str] = []

class CampaignTemplateUpdate(BaseModel):
    """Atualização de template de campanha"""
    nome: Optional[str] = None
    descricao: Optional[str] = None
    template_titulo: Optional[str] = None
    template_conteudo: Optional[str] = None
    variaveis_disponiveis: Optional[List[str]] = None
    ativo: Optional[bool] = None
    template_padrao: Optional[bool] = None
    categoria: Optional[str] = None
    tags: Optional[List[str]] = None

class CampaignTest(BaseModel):
    """Teste de envio de campanha"""
    tipo_campanha: str
    template_id: Optional[str] = None
    cliente_telefone: str
    variaveis: Dict[str, str] = {}
    dry_run: bool = True

class CampaignHistoryFilter(BaseModel):
    """Filtros para histórico de campanhas"""
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    tipo_campanha: Optional[str] = None
    cliente_telefone: Optional[str] = None
    status: Optional[str] = None
    limit: int = 50
    offset: int = 0

# ===================================
# DEPENDENCY INJECTION
# ===================================

async def get_campaign_automation() -> CampaignAutomation:
    """Dependency para obter instância do processador de campanhas"""
    return CampaignAutomation()

# ===================================
# ENDPOINTS - CONFIGURAÇÕES
# ===================================

@router.get("/configuracoes", response_model=Dict[str, Any])
async def get_campaign_configs():
    """
    Busca as configurações atuais de automação de campanhas
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table("configuracoes_campanhas").select("*").execute()
        
        if not result.data:
            # Retorna configuração padrão se não existir
            return {
                "automacao_ativa": False,
                "campanhas_automaticas": {},
                "configuracoes_globais": {
                    "horario_envio": {"inicio": "08:00", "fim": "18:00"},
                    "dias_semana": [1, 2, 3, 4, 5, 6],
                    "max_campanhas_por_cliente_dia": 2
                }
            }
        
        config = result.data[0]
        return {
            "id": config["id"],
            "automacao_ativa": config["automacao_ativa"],
            "campanhas_automaticas": config["campanhas_automaticas"],
            "configuracoes_globais": config["configuracoes_globais"],
            "updated_at": config["updated_at"]
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar configurações: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/configuracoes", response_model=Dict[str, Any])
async def save_campaign_configs(config: CampaignConfig):
    """
    Salva as configurações de automação de campanhas
    """
    try:
        supabase = get_supabase_client()
        
        # Verifica se já existe configuração
        existing = supabase.table("configuracoes_campanhas").select("id").execute()
        
        config_data = {
            "automacao_ativa": config.automacao_ativa,
            "campanhas_automaticas": config.campanhas_automaticas,
            "configuracoes_globais": config.configuracoes_globais,
            "updated_at": datetime.now().isoformat()
        }
        
        if existing.data:
            # Atualiza configuração existente
            result = supabase.table("configuracoes_campanhas").update(config_data).eq("id", existing.data[0]["id"]).execute()
        else:
            # Cria nova configuração
            result = supabase.table("configuracoes_campanhas").insert(config_data).execute()
        
        if result.data:
            logger.info(f"Configurações salvas: automacao_ativa={config.automacao_ativa}")
            return {"ok": True, "message": "Configurações salvas com sucesso", "data": result.data[0]}
        else:
            raise HTTPException(status_code=400, detail="Erro ao salvar configurações")
            
    except Exception as e:
        logger.error(f"Erro ao salvar configurações: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# ===================================
# ENDPOINTS - TEMPLATES
# ===================================

@router.get("/templates", response_model=List[Dict[str, Any]])
async def get_campaign_templates(
    tipo: Optional[str] = Query(None, description="Filtrar por tipo de campanha"),
    ativo: Optional[bool] = Query(None, description="Filtrar por status ativo")
):
    """
    Lista todos os templates de campanha disponíveis
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.table("templates_campanhas").select("*")
        
        if tipo:
            query = query.eq("tipo", tipo)
        if ativo is not None:
            query = query.eq("ativo", ativo)
            
        result = query.order("tipo", "nome").execute()
        
        return result.data or []
        
    except Exception as e:
        logger.error(f"Erro ao buscar templates: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/templates", response_model=Dict[str, Any])
async def create_campaign_template(template: CampaignTemplate):
    """
    Cria um novo template de campanha
    """
    try:
        supabase = get_supabase_client()
        
        # Se está marcando como padrão, remove o padrão anterior do mesmo tipo
        if template.template_padrao:
            supabase.table("templates_campanhas").update({"template_padrao": False}).eq("tipo", template.tipo).eq("template_padrao", True).execute()
        
        template_data = template.dict()
        template_data["created_at"] = datetime.now().isoformat()
        template_data["updated_at"] = datetime.now().isoformat()
        
        result = supabase.table("templates_campanhas").insert(template_data).execute()
        
        if result.data:
            logger.info(f"Template criado: {template.nome} ({template.tipo})")
            return {"ok": True, "message": "Template criado com sucesso", "data": result.data[0]}
        else:
            raise HTTPException(status_code=400, detail="Erro ao criar template")
            
    except Exception as e:
        logger.error(f"Erro ao criar template: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.put("/templates/{template_id}", response_model=Dict[str, Any])
async def update_campaign_template(template_id: str, template_update: CampaignTemplateUpdate):
    """
    Atualiza um template de campanha existente
    """
    try:
        supabase = get_supabase_client()
        
        # Busca template atual para validações
        current = supabase.table("templates_campanhas").select("*").eq("id", template_id).execute()
        if not current.data:
            raise HTTPException(status_code=404, detail="Template não encontrado")
        
        current_template = current.data[0]
        
        # Prepara dados para atualização (apenas campos não-None)
        update_data = {k: v for k, v in template_update.dict().items() if v is not None}
        update_data["updated_at"] = datetime.now().isoformat()
        
        # Se está marcando como padrão, remove o padrão anterior do mesmo tipo
        if template_update.template_padrao:
            supabase.table("templates_campanhas").update({"template_padrao": False}).eq("tipo", current_template["tipo"]).eq("template_padrao", True).execute()
        
        result = supabase.table("templates_campanhas").update(update_data).eq("id", template_id).execute()
        
        if result.data:
            logger.info(f"Template atualizado: {template_id}")
            return {"ok": True, "message": "Template atualizado com sucesso", "data": result.data[0]}
        else:
            raise HTTPException(status_code=400, detail="Erro ao atualizar template")
            
    except Exception as e:
        logger.error(f"Erro ao atualizar template: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.delete("/templates/{template_id}", response_model=Dict[str, Any])
async def delete_campaign_template(template_id: str):
    """
    Remove um template de campanha
    """
    try:
        supabase = get_supabase_client()
        
        # Verifica se template existe
        existing = supabase.table("templates_campanhas").select("nome, tipo").eq("id", template_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Template não encontrado")
        
        template_info = existing.data[0]
        
        # Remove template
        result = supabase.table("templates_campanhas").delete().eq("id", template_id).execute()
        
        logger.info(f"Template removido: {template_info['nome']} ({template_info['tipo']})")
        return {"ok": True, "message": "Template removido com sucesso"}
        
    except Exception as e:
        logger.error(f"Erro ao remover template: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# ===================================
# ENDPOINTS - TESTE DE CAMPANHAS
# ===================================

@router.post("/testar", response_model=Dict[str, Any])
async def test_campaign(
    test_data: CampaignTest,
    campaign_automation: CampaignAutomation = Depends(get_campaign_automation)
):
    """
    Testa o envio de uma campanha para um cliente específico
    """
    try:
        supabase = get_supabase_client()
        
        # Busca template se especificado
        template = None
        if test_data.template_id:
            template_result = supabase.table("templates_campanhas").select("*").eq("id", test_data.template_id).execute()
            if template_result.data:
                template = template_result.data[0]
        else:
            # Busca template padrão para o tipo
            template_result = supabase.table("templates_campanhas").select("*").eq("tipo", test_data.tipo_campanha).eq("template_padrao", True).execute()
            if template_result.data:
                template = template_result.data[0]
        
        if not template:
            raise HTTPException(status_code=404, detail=f"Template não encontrado para tipo: {test_data.tipo_campanha}")
        
        # Prepara contexto do teste
        cliente_data = {
            "telefone": test_data.cliente_telefone,
            "nome": test_data.variaveis.get("nome_cliente", "Cliente")
        }
        
        # Executa teste de envio
        result = await campaign_automation.test_campaign_send(
            tipo_campanha=test_data.tipo_campanha,
            template=template,
            cliente_data=cliente_data,
            variaveis=test_data.variaveis,
            dry_run=test_data.dry_run
        )
        
        logger.info(f"Teste de campanha executado: {test_data.tipo_campanha} -> {test_data.cliente_telefone}")
        return result
        
    except Exception as e:
        logger.error(f"Erro no teste de campanha: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# ===================================
# ENDPOINTS - HISTÓRICO
# ===================================

@router.get("/historico", response_model=Dict[str, Any])
async def get_campaign_history(
    data_inicio: Optional[str] = Query(None, description="Data início (YYYY-MM-DD)"),
    data_fim: Optional[str] = Query(None, description="Data fim (YYYY-MM-DD)"),
    tipo_campanha: Optional[str] = Query(None, description="Tipo de campanha"),
    cliente_telefone: Optional[str] = Query(None, description="Telefone do cliente"),
    status: Optional[str] = Query(None, description="Status da campanha"),
    limit: int = Query(50, description="Limite de resultados"),
    offset: int = Query(0, description="Offset para paginação")
):
    """
    Busca histórico de campanhas enviadas com filtros
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.table("historico_campanhas").select("*")
        
        # Aplica filtros
        if data_inicio:
            query = query.gte("enviado_em", f"{data_inicio}T00:00:00")
        if data_fim:
            query = query.lte("enviado_em", f"{data_fim}T23:59:59")
        if tipo_campanha:
            query = query.eq("tipo_campanha", tipo_campanha)
        if cliente_telefone:
            query = query.eq("cliente_telefone", cliente_telefone)
        if status:
            query = query.eq("status", status)
        
        # Aplica paginação e ordenação
        result = query.order("enviado_em", desc=True).limit(limit).offset(offset).execute()
        
        # Busca total de registros para paginação
        count_query = supabase.table("historico_campanhas").select("id", count="exact")
        if data_inicio:
            count_query = count_query.gte("enviado_em", f"{data_inicio}T00:00:00")
        if data_fim:
            count_query = count_query.lte("enviado_em", f"{data_fim}T23:59:59")
        if tipo_campanha:
            count_query = count_query.eq("tipo_campanha", tipo_campanha)
        if cliente_telefone:
            count_query = count_query.eq("cliente_telefone", cliente_telefone)
        if status:
            count_query = count_query.eq("status", status)
            
        count_result = count_query.execute()
        total_count = count_result.count if hasattr(count_result, 'count') else len(result.data)
        
        return {
            "data": result.data or [],
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar histórico: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/historico/estatisticas", response_model=Dict[str, Any])
async def get_campaign_statistics(
    data_inicio: Optional[str] = Query(None, description="Data início (YYYY-MM-DD)"),
    data_fim: Optional[str] = Query(None, description="Data fim (YYYY-MM-DD)")
):
    """
    Busca estatísticas das campanhas enviadas
    """
    try:
        supabase = get_supabase_client()
        
        # Constrói filtros de data
        date_filter = ""
        if data_inicio and data_fim:
            date_filter = f"AND enviado_em BETWEEN '{data_inicio}T00:00:00' AND '{data_fim}T23:59:59'"
        elif data_inicio:
            date_filter = f"AND enviado_em >= '{data_inicio}T00:00:00'"
        elif data_fim:
            date_filter = f"AND enviado_em <= '{data_fim}T23:59:59'"
        
        # Query para estatísticas gerais
        stats_query = f"""
        SELECT 
            COUNT(*) as total_enviadas,
            COUNT(CASE WHEN status = 'enviado' THEN 1 END) as enviadas_sucesso,
            COUNT(CASE WHEN status = 'falhado' THEN 1 END) as falhadas,
            COUNT(CASE WHEN aberto = true THEN 1 END) as abertas,
            COUNT(CASE WHEN respondido = true THEN 1 END) as respondidas,
            COUNT(CASE WHEN converteu = true THEN 1 END) as convertidas,
            SUM(CASE WHEN valor_conversao IS NOT NULL THEN valor_conversao ELSE 0 END) as valor_total_conversoes
        FROM historico_campanhas 
        WHERE 1=1 {date_filter}
        """
        
        # Query para estatísticas por tipo
        tipos_query = f"""
        SELECT 
            tipo_campanha,
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'enviado' THEN 1 END) as enviadas,
            COUNT(CASE WHEN converteu = true THEN 1 END) as convertidas
        FROM historico_campanhas 
        WHERE 1=1 {date_filter}
        GROUP BY tipo_campanha
        ORDER BY total DESC
        """
        
        # Executa queries (usando rpc se disponível, senão busca dados e processa)
        try:
            # Tenta usar função SQL personalizada
            stats_result = supabase.rpc('get_campaign_stats', {'start_date': data_inicio, 'end_date': data_fim}).execute()
            tipos_result = supabase.rpc('get_campaign_stats_by_type', {'start_date': data_inicio, 'end_date': data_fim}).execute()
            
            return {
                "estatisticas_gerais": stats_result.data[0] if stats_result.data else {},
                "estatisticas_por_tipo": tipos_result.data or []
            }
        except:
            # Fallback: busca todos os dados e processa localmente
            query = supabase.table("historico_campanhas").select("*")
            if data_inicio:
                query = query.gte("enviado_em", f"{data_inicio}T00:00:00")
            if data_fim:
                query = query.lte("enviado_em", f"{data_fim}T23:59:59")
                
            result = query.execute()
            data = result.data or []
            
            # Processa estatísticas gerais
            total_enviadas = len(data)
            enviadas_sucesso = len([r for r in data if r["status"] == "enviado"])
            falhadas = len([r for r in data if r["status"] == "falhado"])
            abertas = len([r for r in data if r.get("aberto")])
            respondidas = len([r for r in data if r.get("respondido")])
            convertidas = len([r for r in data if r.get("converteu")])
            valor_total = sum([r.get("valor_conversao", 0) or 0 for r in data])
            
            # Processa estatísticas por tipo
            tipos_stats = {}
            for record in data:
                tipo = record["tipo_campanha"]
                if tipo not in tipos_stats:
                    tipos_stats[tipo] = {"total": 0, "enviadas": 0, "convertidas": 0}
                tipos_stats[tipo]["total"] += 1
                if record["status"] == "enviado":
                    tipos_stats[tipo]["enviadas"] += 1
                if record.get("converteu"):
                    tipos_stats[tipo]["convertidas"] += 1
            
            return {
                "estatisticas_gerais": {
                    "total_enviadas": total_enviadas,
                    "enviadas_sucesso": enviadas_sucesso,
                    "falhadas": falhadas,
                    "abertas": abertas,
                    "respondidas": respondidas,
                    "convertidas": convertidas,
                    "valor_total_conversoes": valor_total,
                    "taxa_sucesso": (enviadas_sucesso / total_enviadas * 100) if total_enviadas > 0 else 0,
                    "taxa_conversao": (convertidas / enviadas_sucesso * 100) if enviadas_sucesso > 0 else 0
                },
                "estatisticas_por_tipo": [
                    {"tipo_campanha": tipo, **stats} 
                    for tipo, stats in tipos_stats.items()
                ]
            }
        
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# ===================================
# ENDPOINTS - UTILITÁRIOS
# ===================================

@router.get("/tipos", response_model=List[Dict[str, str]])
async def get_campaign_types():
    """
    Lista todos os tipos de campanha disponíveis
    """
    tipos = [
        {"value": "lead_qualificado", "label": "Lead Qualificado", "description": "Cliente demonstrou interesse e está qualificado"},
        {"value": "promocao_produtos", "label": "Promoção de Produtos", "description": "Ofertas e promoções de produtos específicos"},
        {"value": "follow_up_pedido", "label": "Follow-up de Pedido", "description": "Acompanhamento de carrinho abandonado ou pedido pendente"},
        {"value": "reativacao_cliente", "label": "Reativação de Cliente", "description": "Reconquista de clientes inativos"},
        {"value": "cross_sell", "label": "Cross-sell", "description": "Venda de produtos complementares"},
        {"value": "feedback_pos_venda", "label": "Feedback Pós-venda", "description": "Coleta de feedback após entrega"},
        {"value": "oferta_personalizada", "label": "Oferta Personalizada", "description": "Ofertas baseadas no perfil do cliente"},
        {"value": "evento_especial", "label": "Evento Especial", "description": "Produtos para eventos e comemorações"}
    ]
    return tipos

@router.get("/variaveis", response_model=Dict[str, List[str]])
async def get_template_variables():
    """
    Lista todas as variáveis disponíveis para templates
    """
    variaveis = {
        "cliente": [
            "nome_cliente", "telefone_cliente", "email_cliente", 
            "endereco_cliente", "cidade_cliente"
        ],
        "produto": [
            "produto_interesse", "categoria_produto", "preco_produto",
            "descricao_produto", "disponibilidade_produto"
        ],
        "oferta": [
            "valor_oferta", "percentual_desconto", "valor_desconto",
            "condicoes_oferta", "validade_oferta"
        ],
        "entrega": [
            "prazo_entrega", "data_entrega", "taxa_entrega",
            "endereco_entrega", "horario_entrega"
        ],
        "empresa": [
            "nome_empresa", "telefone_empresa", "endereco_empresa",
            "horario_funcionamento", "site_empresa"
        ]
    }
    return variaveis

# ===================================
# HEALTH CHECK
# ===================================

@router.get("/health", response_model=Dict[str, str])
async def campaigns_health():
    """
    Health check para API de campanhas
    """
    try:
        # Testa conexão com Supabase
        supabase = get_supabase_client()
        supabase.table("configuracoes_campanhas").select("id").limit(1).execute()
        
        return {"status": "ok", "service": "campaigns_api", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Health check falhou: {e}")
        return {"status": "error", "service": "campaigns_api", "error": str(e)}