"""
Campaign Processor - 3A Frios
Processa automaticamente as ações especiais geradas pela Camila Marketing
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger("3afrios.campaign_processor")

async def process_campaign_action(
    acao_especial: str, 
    cliente_data: Dict[str, Any], 
    bruno_insights: Dict[str, Any],
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Processa ação especial da Camila Marketing e executa automações
    
    Args:
        acao_especial: Ação retornada pela Camila (ex: [ACAO:CAMPANHA_B2B])
        cliente_data: Dados do cliente (telefone, id, nome, etc.)
        bruno_insights: Insights do Bruno (score, segmento, urgência, etc.)
        context: Contexto adicional da conversa
    
    Returns:
        Dict com resultado das ações executadas
    """
    if not acao_especial or not cliente_data:
        return {"ok": False, "reason": "missing_required_data"}
    
    logger.info(f"[Campaign Processor] Processando {acao_especial} para cliente {cliente_data.get('telefone')}")
    
    result = {
        "ok": True,
        "acao_processada": acao_especial,
        "cliente_id": cliente_data.get("id"),
        "acoes_executadas": [],
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Rota para processadores específicos
        if acao_especial in ["[ACAO:CAMPANHA_B2B]", "[ACAO:APRESENTAR_B2B]"]:
            b2b_result = await _process_b2b_campaign(acao_especial, cliente_data, bruno_insights, context)
            result["acoes_executadas"].extend(b2b_result.get("acoes", []))
            
        elif acao_especial in ["[ACAO:EVENTO_EXPRESS]", "[ACAO:PLANEJAMENTO_EVENTO]"]:
            event_result = await _process_event_campaign(acao_especial, cliente_data, bruno_insights, context)
            result["acoes_executadas"].extend(event_result.get("acoes", []))
            
        elif acao_especial in ["[ACAO:CLIENTE_PREMIUM]", "[ACAO:BEM_VINDO]", "[ACAO:NEWSLETTER_OFERTAS]"]:
            family_result = await _process_family_campaign(acao_especial, cliente_data, bruno_insights, context)
            result["acoes_executadas"].extend(family_result.get("acoes", []))
            
        elif acao_especial == "[ACAO:OFERTAS_CONTEXTUAIS]":
            contextual_result = await _process_contextual_offers(cliente_data, bruno_insights, context)
            result["acoes_executadas"].extend(contextual_result.get("acoes", []))
            
        else:
            logger.warning(f"[Campaign Processor] Ação não reconhecida: {acao_especial}")
            result["acoes_executadas"].append({
                "tipo": "log",
                "acao": "acao_nao_reconhecida",
                "detalhes": f"Ação {acao_especial} não possui processamento definido"
            })
        
        # Salva métricas da campanha
        await _track_campaign_metrics(acao_especial, cliente_data, bruno_insights, result)
        
        logger.info(f"[Campaign Processor] Processamento concluído: {len(result['acoes_executadas'])} ações executadas")
        
    except Exception as e:
        logger.error(f"[Campaign Processor] Erro ao processar {acao_especial}: {e}")
        result["ok"] = False
        result["error"] = str(e)
    
    return result


async def _process_b2b_campaign(
    acao: str, 
    cliente: Dict[str, Any], 
    bruno_insights: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Processa campanhas B2B"""
    
    acoes = []
    segmento = bruno_insights.get("segmento", "pessoa_juridica")
    lead_score = bruno_insights.get("lead_score", 0)
    urgencia = bruno_insights.get("urgencia", "media")
    
    # Determina tipo de negócio
    mensagem = context.get("mensagem_cliente", "").lower() if context else ""
    tipo_negocio = _detectar_tipo_negocio(mensagem)
    
    if acao == "[ACAO:CAMPANHA_B2B]":
        # Campanha ativa para B2B interessado
        acoes.extend([
            {
                "tipo": "gerar_proposta",
                "acao": "criar_proposta_comercial",
                "detalhes": {
                    "tipo_negocio": tipo_negocio,
                    "desconto_sugerido": min(15, 5 + (lead_score * 1.5)),
                    "validade_dias": 7 if urgencia == "alta" else 15
                }
            },
            {
                "tipo": "cupom",
                "acao": "gerar_cupom_b2b",
                "detalhes": {
                    "codigo": f"B2B{cliente.get('id', '')[:6]}{datetime.now().strftime('%m%d')}",
                    "desconto_percentual": 10 if lead_score >= 7 else 5,
                    "minimo_compra": 500.00,
                    "validade": (datetime.now() + timedelta(days=30)).isoformat()
                }
            },
            {
                "tipo": "follow_up",
                "acao": "agendar_contato_comercial",
                "detalhes": {
                    "quando": (datetime.now() + timedelta(hours=24)).isoformat(),
                    "tipo": "ligacao_comercial",
                    "objetivo": "apresentar_proposta_detalhada"
                }
            }
        ])
        
    elif acao == "[ACAO:APRESENTAR_B2B]":
        # Apresentação inicial B2B
        acoes.extend([
            {
                "tipo": "material",
                "acao": "enviar_catalogo_empresarial",
                "detalhes": {
                    "tipo": "catalogo_b2b",
                    "formato": "pdf",
                    "personalizado_para": tipo_negocio
                }
            },
            {
                "tipo": "follow_up",
                "acao": "agendar_apresentacao",
                "detalhes": {
                    "quando": (datetime.now() + timedelta(hours=48)).isoformat(),
                    "tipo": "apresentacao_comercial",
                    "duracao_minutos": 30
                }
            }
        ])
    
    return {"acoes": acoes}


async def _process_event_campaign(
    acao: str,
    cliente: Dict[str, Any], 
    bruno_insights: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Processa campanhas de eventos"""
    
    acoes = []
    pessoas = bruno_insights.get("pessoas", 20)
    urgencia = bruno_insights.get("urgencia", "media")
    lead_score = bruno_insights.get("lead_score", 0)
    
    if acao == "[ACAO:EVENTO_EXPRESS]":
        # Evento urgente
        acoes.extend([
            {
                "tipo": "orcamento",
                "acao": "gerar_orcamento_express",
                "detalhes": {
                    "pessoas": pessoas,
                    "prazo_entrega": "4_horas",
                    "valor_estimado": pessoas * 35,  # R$ 35 por pessoa
                    "inclui_temperos": True,
                    "desconto_urgencia": 5 if pessoas >= 30 else 0
                }
            },
            {
                "tipo": "checklist",
                "acao": "enviar_checklist_evento",
                "detalhes": {
                    "tipo": "evento_express",
                    "quantidade_pessoas": pessoas,
                    "sugestoes_cortes": ["picanha", "maminha", "fraldinha"],
                    "tempo_preparo": "3-4 horas"
                }
            },
            {
                "tipo": "follow_up",
                "acao": "ligar_confirmacao",
                "detalhes": {
                    "quando": (datetime.now() + timedelta(minutes=30)).isoformat(),
                    "tipo": "confirmacao_urgente",
                    "objetivo": "confirmar_pedido_e_endereco"
                }
            }
        ])
        
    elif acao == "[ACAO:PLANEJAMENTO_EVENTO]":
        # Evento com planejamento
        acoes.extend([
            {
                "tipo": "consultoria",
                "acao": "agendar_consultoria_evento",
                "detalhes": {
                    "tipo": "consultoria_gratuita",
                    "duracao": "45_minutos",
                    "quando": (datetime.now() + timedelta(days=1)).isoformat(),
                    "inclui": ["cardapio_personalizado", "calculo_quantidades", "sugestoes_preparo"]
                }
            },
            {
                "tipo": "material",
                "acao": "enviar_guia_evento_premium",
                "detalhes": {
                    "guias": ["quantidades_por_pessoa", "cortes_recomendados", "dicas_preparo", "acompanhamentos"],
                    "personalizado_para": pessoas
                }
            }
        ])
    
    return {"acoes": acoes}


async def _process_family_campaign(
    acao: str,
    cliente: Dict[str, Any], 
    bruno_insights: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Processa campanhas para pessoa física/família"""
    
    acoes = []
    lead_score = bruno_insights.get("lead_score", 0)
    qualificacao_status = bruno_insights.get("qualificacao_status", "new")
    
    if acao == "[ACAO:CLIENTE_PREMIUM]":
        # Cliente quente VIP
        acoes.extend([
            {
                "tipo": "cupom",
                "acao": "gerar_cupom_premium",
                "detalhes": {
                    "codigo": f"VIP{cliente.get('id', '')[:6]}",
                    "desconto_percentual": 12,
                    "frete_gratis": True,
                    "validade": (datetime.now() + timedelta(days=7)).isoformat(),
                    "beneficios_extras": ["kit_temperos", "consultoria_cortes"]
                }
            },
            {
                "tipo": "vip",
                "acao": "ativar_programa_vip",
                "detalhes": {
                    "beneficios": ["desconto_progressivo", "frete_gratis_sempre", "atendimento_prioritario"],
                    "pontos_iniciais": 100
                }
            }
        ])
        
    elif acao == "[ACAO:BEM_VINDO]":
        # Cliente novo
        acoes.extend([
            {
                "tipo": "cupom",
                "acao": "gerar_cupom_boas_vindas",
                "detalhes": {
                    "codigo": f"BV{cliente.get('id', '')[:6]}",
                    "desconto_percentual": 10,
                    "minimo_compra": 80.00,
                    "validade": (datetime.now() + timedelta(days=7)).isoformat(),
                    "primeira_compra": True
                }
            },
            {
                "tipo": "material",
                "acao": "enviar_guia_cortes",
                "detalhes": {
                    "tipo": "guia_iniciante",
                    "inclui": ["tipos_cortes", "como_escolher", "dicas_preparo", "receitas_simples"]
                }
            },
            {
                "tipo": "email_marketing",
                "acao": "cadastrar_newsletter",
                "detalhes": {
                    "lista": "novos_clientes",
                    "sequencia": "boas_vindas_7_dias",
                    "frequencia": "semanal"
                }
            }
        ])
        
    elif acao == "[ACAO:NEWSLETTER_OFERTAS]":
        # Cliente interessado em promoções
        acoes.extend([
            {
                "tipo": "email_marketing",
                "acao": "enviar_ofertas_semanais",
                "detalhes": {
                    "ofertas_personalizadas": True,
                    "baseado_em_historico": True,
                    "cupom_exclusivo": f"PROMO{datetime.now().strftime('%W%y')}"
                }
            }
        ])
    
    return {"acoes": acoes}


async def _process_contextual_offers(
    cliente: Dict[str, Any], 
    bruno_insights: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Processa ofertas contextuais genéricas"""
    
    acoes = []
    segmento = bruno_insights.get("segmento", "pessoa_fisica")
    lead_score = bruno_insights.get("lead_score", 0)
    
    # Oferta baseada no segmento e score
    if segmento == "pessoa_juridica":
        acoes.append({
            "tipo": "follow_up",
            "acao": "contato_comercial_b2b",
            "detalhes": {
                "quando": (datetime.now() + timedelta(hours=4)).isoformat(),
                "objetivo": "identificar_necessidades_empresariais"
            }
        })
    elif lead_score >= 6:
        acoes.append({
            "tipo": "cupom",
            "acao": "cupom_contextual",
            "detalhes": {
                "desconto_percentual": 8,
                "validade": (datetime.now() + timedelta(days=3)).isoformat()
            }
        })
    
    return {"acoes": acoes}


async def _track_campaign_metrics(
    acao_especial: str,
    cliente_data: Dict[str, Any],
    bruno_insights: Dict[str, Any],
    result: Dict[str, Any]
) -> None:
    """Salva métricas da campanha para análise"""
    
    try:
        # Aqui você pode integrar com seu sistema de métricas
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "acao_especial": acao_especial,
            "cliente_id": cliente_data.get("id"),
            "cliente_telefone": cliente_data.get("telefone"),
            "segmento": bruno_insights.get("segmento"),
            "lead_score": bruno_insights.get("lead_score"),
            "acoes_executadas": len(result.get("acoes_executadas", [])),
            "sucesso": result.get("ok", False)
        }
        
        logger.info(f"[Campaign Metrics] {json.dumps(metrics, ensure_ascii=False)}")
        
        # TODO: Implementar salvamento em banco de dados de métricas
        # await save_campaign_metrics(metrics)
        
    except Exception as e:
        logger.error(f"[Campaign Metrics] Erro ao salvar métricas: {e}")


def _detectar_tipo_negocio(mensagem: str) -> str:
    """Detecta tipo de negócio baseado na mensagem"""
    
    if any(palavra in mensagem for palavra in ["restaurante", "bar", "lanchonete"]):
        return "restaurante"
    elif any(palavra in mensagem for palavra in ["hotel", "pousada", "resort"]):
        return "hotelaria"
    elif any(palavra in mensagem for palavra in ["empresa", "escritorio", "corporativo"]):
        return "corporativo"
    elif any(palavra in mensagem for palavra in ["evento", "festa", "casamento"]):
        return "eventos"
    else:
        return "comercio_geral"


# Funções utilitárias para integração futura
async def generate_coupon(discount_type: str, value: float, cliente_id: str) -> Dict[str, Any]:
    """Gera cupom de desconto"""
    # TODO: Implementar geração real de cupons
    return {
        "codigo": f"CUP{cliente_id[:6]}{datetime.now().strftime('%m%d')}",
        "tipo": discount_type,
        "valor": value,
        "gerado_em": datetime.now().isoformat()
    }


async def send_email_campaign(template: str, cliente_data: Dict[str, Any]) -> Dict[str, Any]:
    """Envia campanha por email"""
    # TODO: Implementar integração com serviço de email
    return {
        "enviado": False,
        "motivo": "integracao_email_nao_implementada",
        "template": template,
        "destinatario": cliente_data.get("email", "nao_informado")
    }


async def schedule_followup(delay_hours: int, message: str, cliente_id: str) -> Dict[str, Any]:
    """Agenda follow-up automático"""
    # TODO: Implementar sistema de agendamento
    return {
        "agendado": True,
        "quando": (datetime.now() + timedelta(hours=delay_hours)).isoformat(),
        "cliente_id": cliente_id,
        "mensagem": message
    }