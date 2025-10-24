"""
Processador de Campanhas Automáticas - 3A Frios
==============================================

Sistema inteligente para processar e enviar campanhas automáticas 
baseadas nos insights do Bruno Analista Invisível e contexto conversacional.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import json
import re

from .supabase_store import get_supabase_client
from .evolution import send_text

logger = logging.getLogger("3afrios.campaign_processor")

class CampaignAutomation:
    """
    Processador principal de campanhas automáticas
    """
    
    def __init__(self):
        self.supabase = get_supabase_client()
        
    async def process_campaign_action(
        self, 
        acao_especial: str,
        cliente_data: Dict[str, Any],
        bruno_insights: Dict[str, Any] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Processa uma ação especial de campanha gerada pelos agentes
        """
        try:
            logger.info(f"[Campaign Processor] Processando ação: {acao_especial}")
            
            # Extrai tipo de campanha da ação especial
            tipo_campanha = self._extract_campaign_type(acao_especial)
            if not tipo_campanha:
                return {"ok": False, "error": "Tipo de campanha não reconhecido", "acao": acao_especial}
            
            # Verifica se automação está ativa
            config = await self._get_campaign_config()
            if not config.get("automacao_ativa", False):
                logger.info(f"[Campaign Processor] Automação desativada - ignorando {tipo_campanha}")
                return {"ok": True, "ignored": "automacao_desativada", "tipo": tipo_campanha}
            
            # Verifica configuração específica do tipo
            campanhas_config = config.get("campanhas_automaticas", {})
            tipo_config = campanhas_config.get(tipo_campanha, {})
            
            if not tipo_config.get("ativo", False):
                logger.info(f"[Campaign Processor] Tipo {tipo_campanha} desativado")
                return {"ok": True, "ignored": "tipo_desativado", "tipo": tipo_campanha}
            
            # Verifica elegibilidade do cliente
            elegibilidade = await self._check_campaign_eligibility(
                cliente_data.get("telefone", ""),
                tipo_campanha,
                bruno_insights or {}
            )
            
            if not elegibilidade["elegivel"]:
                logger.info(f"[Campaign Processor] Cliente não elegível: {elegibilidade['motivo']}")
                return {"ok": True, "ignored": "nao_elegivel", "motivo": elegibilidade["motivo"]}
            
            # Busca template adequado
            template = await self._get_template_for_campaign(tipo_campanha, tipo_config)
            if not template:
                logger.error(f"[Campaign Processor] Template não encontrado para {tipo_campanha}")
                return {"ok": False, "error": "Template não encontrado", "tipo": tipo_campanha}
            
            # Prepara variáveis do template
            variaveis = await self._prepare_template_variables(
                cliente_data, bruno_insights or {}, context or {}, tipo_campanha
            )
            
            # Programa envio baseado no delay configurado
            delay_minutos = tipo_config.get("delay_minutos", 30)
            envio_programado = datetime.now() + timedelta(minutes=delay_minutos)
            
            # Processa conteúdo do template
            conteudo_processado = await self._process_template(template, variaveis)
            
            # Executa envio (imediato se delay = 0, programado se delay > 0)
            if delay_minutos <= 0:
                resultado_envio = await self._send_campaign_now(
                    cliente_data, conteudo_processado, tipo_campanha, template, variaveis, bruno_insights, context
                )
            else:
                resultado_envio = await self._schedule_campaign_send(
                    cliente_data, conteudo_processado, tipo_campanha, template, variaveis, 
                    envio_programado, bruno_insights, context
                )
            
            logger.info(f"[Campaign Processor] Campanha processada: {tipo_campanha} -> {cliente_data.get('telefone')}")
            
            return {
                "ok": True,
                "tipo_campanha": tipo_campanha,
                "delay_minutos": delay_minutos,
                "envio_programado": envio_programado.isoformat() if delay_minutos > 0 else None,
                "template_usado": template["nome"],
                "variaveis_aplicadas": variaveis,
                "resultado_envio": resultado_envio,
                "acoes_executadas": [f"campanha_{tipo_campanha}_processada"]
            }
            
        except Exception as e:
            logger.error(f"[Campaign Processor] Erro ao processar campanha: {e}", exc_info=True)
            return {"ok": False, "error": str(e)}
    
    async def test_campaign_send(
        self,
        tipo_campanha: str,
        template: Dict[str, Any],
        cliente_data: Dict[str, Any],
        variaveis: Dict[str, str] = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Testa envio de campanha (para usar na API de teste)
        """
        try:
            # Prepara variáveis padrão se não fornecidas
            if not variaveis:
                variaveis = {
                    "nome_cliente": cliente_data.get("nome", "Cliente"),
                    "produto_interesse": "Produtos 3A Frios",
                    "valor_oferta": "Consulte condições especiais",
                    "prazo_entrega": "24-48h"
                }
            
            # Processa template
            conteudo_processado = await self._process_template(template, variaveis)
            
            resultado = {
                "ok": True,
                "dry_run": dry_run,
                "tipo_campanha": tipo_campanha,
                "template_usado": template["nome"],
                "cliente_telefone": cliente_data.get("telefone"),
                "conteudo_final": conteudo_processado,
                "variaveis_aplicadas": variaveis
            }
            
            if not dry_run:
                # Executa envio real
                envio_result = await self._send_campaign_now(
                    cliente_data, conteudo_processado, tipo_campanha, template, variaveis, {}, {"origem": "teste_api"}
                )
                resultado["envio_resultado"] = envio_result
            
            return resultado
            
        except Exception as e:
            logger.error(f"[Campaign Processor] Erro no teste: {e}")
            return {"ok": False, "error": str(e)}
    
    # ===================================
    # MÉTODOS PRIVADOS
    # ===================================
    
    def _extract_campaign_type(self, acao_especial: str) -> Optional[str]:
        """
        Extrai o tipo de campanha da ação especial
        """
        # Mapeamento de ações especiais para tipos de campanha
        mapping = {
            "[CAMPANHA:LEAD_QUALIFICADO]": "lead_qualificado",
            "[CAMPANHA:PROMOCAO_PRODUTOS]": "promocao_produtos", 
            "[CAMPANHA:FOLLOW_UP_PEDIDO]": "follow_up_pedido",
            "[CAMPANHA:REATIVACAO_CLIENTE]": "reativacao_cliente",
            "[CAMPANHA:CROSS_SELL]": "cross_sell",
            "[CAMPANHA:FEEDBACK_POS_VENDA]": "feedback_pos_venda",
            "[CAMPANHA:OFERTA_PERSONALIZADA]": "oferta_personalizada",
            "[CAMPANHA:EVENTO_ESPECIAL]": "evento_especial",
            # Compatibilidade com ações antigas da Camila
            "[ACAO:CAMPANHA_B2B]": "oferta_personalizada",
            "[ACAO:EVENTO_EXPRESS]": "evento_especial",
            "[ACAO:CLIENTE_PREMIUM]": "oferta_personalizada",
            "[ACAO:BEM_VINDO]": "lead_qualificado"
        }
        
        return mapping.get(acao_especial)
    
    async def _get_campaign_config(self) -> Dict[str, Any]:
        """
        Busca configurações de campanha do banco
        """
        try:
            result = self.supabase.table("configuracoes_campanhas").select("*").execute()
            if result.data:
                return result.data[0]
            return {"automacao_ativa": False, "campanhas_automaticas": {}}
        except Exception as e:
            logger.error(f"Erro ao buscar config de campanhas: {e}")
            return {"automacao_ativa": False, "campanhas_automaticas": {}}
    
    async def _check_campaign_eligibility(
        self, 
        telefone: str, 
        tipo_campanha: str, 
        bruno_insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verifica se cliente é elegível para receber a campanha
        """
        try:
            # Verifica se cliente já recebeu campanha similar recentemente
            limite_horas = 24  # Não enviar mesmo tipo em 24h
            
            result = self.supabase.table("historico_campanhas").select("enviado_em").eq(
                "cliente_telefone", telefone
            ).eq("tipo_campanha", tipo_campanha).gte(
                "enviado_em", (datetime.now() - timedelta(hours=limite_horas)).isoformat()
            ).execute()
            
            if result.data:
                return {
                    "elegivel": False,
                    "motivo": f"Campanha {tipo_campanha} já enviada nas últimas {limite_horas}h"
                }
            
            # Verifica limite diário de campanhas
            hoje = datetime.now().date().isoformat()
            result_hoje = self.supabase.table("historico_campanhas").select("id").eq(
                "cliente_telefone", telefone
            ).gte("enviado_em", f"{hoje}T00:00:00").execute()
            
            if len(result_hoje.data or []) >= 3:  # Max 3 campanhas por dia
                return {
                    "elegivel": False,
                    "motivo": "Limite diário de campanhas atingido (3/dia)"
                }
            
            # Validações específicas baseadas nos insights do Bruno
            lead_score = bruno_insights.get("lead_score", 0)
            
            # Validações por tipo de campanha
            if tipo_campanha == "lead_qualificado" and lead_score < 5:
                return {
                    "elegivel": False,
                    "motivo": f"Lead score muito baixo ({lead_score}) para campanha de lead qualificado"
                }
            
            if tipo_campanha == "oferta_personalizada" and lead_score < 7:
                return {
                    "elegivel": False,
                    "motivo": f"Lead score insuficiente ({lead_score}) para oferta personalizada"
                }
            
            return {"elegivel": True, "motivo": "Cliente elegível"}
            
        except Exception as e:
            logger.error(f"Erro ao verificar elegibilidade: {e}")
            return {"elegivel": False, "motivo": f"Erro na verificação: {str(e)}"}
    
    async def _get_template_for_campaign(self, tipo_campanha: str, tipo_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Busca template adequado para o tipo de campanha
        """
        try:
            # Primeiro tenta template específico configurado
            template_id = tipo_config.get("template_id")
            if template_id:
                result = self.supabase.table("templates_campanhas").select("*").eq("id", template_id).eq("ativo", True).execute()
                if result.data:
                    return result.data[0]
            
            # Senão busca template padrão para o tipo
            result = self.supabase.table("templates_campanhas").select("*").eq(
                "tipo", tipo_campanha
            ).eq("template_padrao", True).eq("ativo", True).execute()
            
            if result.data:
                return result.data[0]
            
            # Por último, qualquer template ativo do tipo
            result = self.supabase.table("templates_campanhas").select("*").eq(
                "tipo", tipo_campanha
            ).eq("ativo", True).limit(1).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Erro ao buscar template: {e}")
            return None
    
    async def _prepare_template_variables(
        self,
        cliente_data: Dict[str, Any],
        bruno_insights: Dict[str, Any],
        context: Dict[str, Any],
        tipo_campanha: str
    ) -> Dict[str, str]:
        """
        Prepara variáveis para substituição no template
        """
        variaveis = {}
        
        # Variáveis do cliente
        variaveis["nome_cliente"] = cliente_data.get("nome", "Cliente")
        variaveis["telefone_cliente"] = cliente_data.get("telefone", "")
        
        # Variáveis baseadas no contexto conversacional
        mensagem_cliente = context.get("mensagem_cliente", "")
        
        # Detecta produtos mencionados
        produtos_detectados = self._extract_products_from_message(mensagem_cliente)
        variaveis["produto_interesse"] = produtos_detectados or "nossos produtos de qualidade"
        
        # Variáveis baseadas nos insights do Bruno
        lead_score = bruno_insights.get("lead_score", 0)
        segmento = bruno_insights.get("segmento", "pessoa_fisica")
        urgencia = bruno_insights.get("urgencia", "baixa")
        
        # Personaliza oferta baseada no perfil
        if lead_score >= 8:
            variaveis["valor_oferta"] = "15% de desconto especial + frete grátis"
        elif lead_score >= 6:
            variaveis["valor_oferta"] = "10% de desconto + condições facilitadas"
        elif lead_score >= 4:
            variaveis["valor_oferta"] = "5% de desconto na primeira compra"
        else:
            variaveis["valor_oferta"] = "Condições especiais de pagamento"
        
        # Personaliza prazo baseado na urgência
        if urgencia == "alta":
            variaveis["prazo_entrega"] = "entrega expressa em até 4 horas"
        elif urgencia == "media":
            variaveis["prazo_entrega"] = "entrega em 24h"
        else:
            variaveis["prazo_entrega"] = "entrega em 24-48h"
        
        # Variáveis específicas por tipo de campanha
        if tipo_campanha == "evento_especial":
            pessoas = bruno_insights.get("pessoas")
            if pessoas and pessoas > 20:
                variaveis["produto_interesse"] = "kits para eventos grandes (20+ pessoas)"
                variaveis["valor_oferta"] = "Desconto especial para grandes volumes"
            else:
                variaveis["produto_interesse"] = "produtos selecionados para seu evento"
        
        # Variáveis da empresa
        variaveis["nome_empresa"] = "3A Frios"
        variaveis["horario_funcionamento"] = "Segunda a Sexta: 7h às 18h, Sábado: 7h às 12h"
        
        return variaveis
    
    def _extract_products_from_message(self, message: str) -> Optional[str]:
        """
        Extrai produtos mencionados na mensagem
        """
        if not message:
            return None
        
        message_lower = message.lower()
        
        # Mapeamento de produtos
        produtos = {
            "carne": "carnes nobres",
            "frango": "frango de qualidade",
            "peixe": "peixes frescos",
            "queijo": "queijos artesanais",
            "presunto": "presunto premium",
            "mortadela": "mortadela especial",
            "salame": "salames selecionados",
            "linguiça": "linguiças artesanais",
            "picanha": "picanha premium",
            "file": "filé nobre"
        }
        
        produtos_encontrados = []
        for palavra, produto in produtos.items():
            if palavra in message_lower:
                produtos_encontrados.append(produto)
        
        if produtos_encontrados:
            if len(produtos_encontrados) == 1:
                return produtos_encontrados[0]
            elif len(produtos_encontrados) == 2:
                return f"{produtos_encontrados[0]} e {produtos_encontrados[1]}"
            else:
                return f"{', '.join(produtos_encontrados[:-1])} e {produtos_encontrados[-1]}"
        
        return None
    
    async def _process_template(self, template: Dict[str, Any], variaveis: Dict[str, str]) -> Dict[str, str]:
        """
        Processa template substituindo variáveis
        """
        titulo = template["template_titulo"]
        conteudo = template["template_conteudo"]
        
        # Substitui variáveis no formato {variavel}
        for var, valor in variaveis.items():
            titulo = titulo.replace(f"{{{var}}}", valor)
            conteudo = conteudo.replace(f"{{{var}}}", valor)
        
        return {
            "titulo": titulo,
            "conteudo": conteudo,
            "texto_completo": f"{titulo}\n\n{conteudo}"
        }
    
    async def _send_campaign_now(
        self,
        cliente_data: Dict[str, Any],
        conteudo_processado: Dict[str, str],
        tipo_campanha: str,
        template: Dict[str, Any],
        variaveis: Dict[str, str],
        bruno_insights: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Envia campanha imediatamente
        """
        try:
            telefone = cliente_data.get("telefone", "")
            texto_envio = conteudo_processado["texto_completo"]
            
            # Envia via Evolution API
            envio_result = await send_text(telefone, texto_envio)
            
            # Registra no histórico
            historico_data = {
                "tipo_campanha": tipo_campanha,
                "template_usado_id": template["id"],
                "cliente_telefone": telefone,
                "cliente_nome": cliente_data.get("nome"),
                "titulo_enviado": conteudo_processado["titulo"],
                "conteudo_enviado": texto_envio,
                "variaveis_usadas": variaveis,
                "gatilho_origem": "automatico",
                "agente_responsavel": context.get("agente_responsavel", "system"),
                "bruno_insights": bruno_insights,
                "contexto_conversa": context,
                "status": "enviado" if envio_result.get("sent") else "falhado",
                "resultado": envio_result,
                "enviado_em": datetime.now().isoformat()
            }
            
            self.supabase.table("historico_campanhas").insert(historico_data).execute()
            
            logger.info(f"[Campaign Processor] Campanha enviada: {tipo_campanha} -> {telefone}")
            
            return {
                "enviado": envio_result.get("sent", False),
                "resultado_evolution": envio_result,
                "historico_salvo": True
            }
            
        except Exception as e:
            logger.error(f"Erro ao enviar campanha: {e}")
            return {"enviado": False, "erro": str(e)}
    
    async def _schedule_campaign_send(
        self,
        cliente_data: Dict[str, Any],
        conteudo_processado: Dict[str, str],
        tipo_campanha: str,
        template: Dict[str, Any],
        variaveis: Dict[str, str],
        envio_programado: datetime,
        bruno_insights: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Programa envio de campanha para momento futuro
        """
        try:
            telefone = cliente_data.get("telefone", "")
            
            # Registra no histórico como pendente
            historico_data = {
                "tipo_campanha": tipo_campanha,
                "template_usado_id": template["id"],
                "cliente_telefone": telefone,
                "cliente_nome": cliente_data.get("nome"),
                "titulo_enviado": conteudo_processado["titulo"],
                "conteudo_enviado": conteudo_processado["texto_completo"],
                "variaveis_usadas": variaveis,
                "gatilho_origem": "automatico",
                "agente_responsavel": context.get("agente_responsavel", "system"),
                "bruno_insights": bruno_insights,
                "contexto_conversa": context,
                "status": "pendente",
                "programado_para": envio_programado.isoformat(),
                "enviado_em": datetime.now().isoformat()
            }
            
            result = self.supabase.table("historico_campanhas").insert(historico_data).execute()
            
            logger.info(f"[Campaign Processor] Campanha programada: {tipo_campanha} -> {telefone} em {envio_programado}")
            
            return {
                "programado": True,
                "envio_em": envio_programado.isoformat(),
                "historico_id": result.data[0]["id"] if result.data else None
            }
            
        except Exception as e:
            logger.error(f"Erro ao programar campanha: {e}")
            return {"programado": False, "erro": str(e)}


# ===================================
# FUNÇÕES DE CONVENIÊNCIA
# ===================================

# Instância global para uso no orquestrador
_campaign_automation = None

def get_campaign_automation() -> CampaignAutomation:
    """Retorna instância global do processador de campanhas"""
    global _campaign_automation
    if _campaign_automation is None:
        _campaign_automation = CampaignAutomation()
    return _campaign_automation

# Função principal para uso no orquestrador (compatibilidade)
async def process_campaign_action(
    acao_especial: str,
    cliente_data: Dict[str, Any],
    bruno_insights: Dict[str, Any] = None,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Função de conveniência para processar ação de campanha
    """
    automation = get_campaign_automation()
    return await automation.process_campaign_action(
        acao_especial, cliente_data, bruno_insights, context
    )