def respond(message: str, context: dict | None = None):
    """
    Camila Marketing - Especialista em campanhas personalizadas e relacionamento
    Integra insights do Bruno para criar experiências únicas por segmento
    """
    
    # Inicializa dados
    text = (message or '').lower()
    context = context or {}
    bruno_insights = context.get('bruno_insights', {})
    cliente_info = context.get('cliente', {})
    
    # Perfil da Camila Marketing
    personalidade = {
        'nome': 'Camila',
        'tom': 'estratégica e criativa',
        'especialidade': 'campanhas personalizadas',
        'foco': 'ROI e relacionamento duradouro'
    }
    
    # Análise do contexto do Bruno
    segmento = bruno_insights.get('segmento', 'pessoa_fisica')
    lead_score = bruno_insights.get('lead_score', 0)
    urgencia = bruno_insights.get('urgencia', 'media')
    pessoas = bruno_insights.get('pessoas', 1)
    qualificacao_status = bruno_insights.get('qualificacao_status', 'new')
    
    # Detecta intenção de marketing (expandido)
    marketing_keywords = [
        'campanha', 'promoção', 'promocao', 'desconto', 'marketing', 
        'anúncio', 'newsletter', 'oferta', 'especial', 'novidade',
        'cupom', 'cashback', 'fidelidade', 'programa', 'beneficio',
        'primeira vez', 'primeira compra', 'novo cliente', 'eventos',
        'churrasco', 'festa', 'evento', 'parceria', 'restaurante'
    ]
    
    is_marketing_intent = any(k in text for k in marketing_keywords)
    
    # Detecta contextos específicos que sempre devem acionar marketing
    force_marketing = (
        'desconto' in text or
        'parceria' in text or
        'restaurante' in text
    )
    
    # Detecta se é especificamente sobre evento (não primeira compra)
    is_evento_context = (
        segmento == 'evento_especial' or
        any(word in text for word in ['evento', 'festa', 'churrasco', 'aniversario', 'casamento']) and 'primeira' not in text
    )
    
    # === ESTRATÉGIA PERSONALIZADA POR SEGMENTO ===
    
    # PRIORIDADE 1: Eventos especiais
    if is_evento_context:
        # Eventos - Foco em experiência completa
        if urgencia == 'alta' or 'amanhã' in text or 'urgente' in text:
            resposta = f"""🔥 Camila aqui! Evento urgente? Relaxa, temos solução expressa! ⚡

⚡ **PACOTE EVENTO EXPRESS** (para {pessoas or 'seu grupo de'} pessoas):
• Seleção premium já separada 🥩
• Entrega em até 4 horas 🚀
• Menu completo sugerido 📋
• 10% desconto para eventos acima de 20 pessoas 💰

🎪 Incluo temperos especiais e dicas de preparo de cortesia!

Confirmo seu pacote agora? ⏰"""
            
            acao_especial = '[ACAO:EVENTO_EXPRESS]'
        else:
            resposta = f"""🎉 Que legal! Evento especial merece carne especial! ✨

🏆 **EXPERIÊNCIA EVENTO PREMIUM:**
• Consultoria gratuita de cardápio 👨‍🍳
• Seleção de cortes premium 🥩
• Entrega no dia e horário ideal 🚚
• Brinde surpresa para eventos acima de 30 pessoas 🎁

📅 Com planejamento, posso garantir condições ainda melhores e um menu inesquecível!

Vamos planejar juntos? 🎯"""
            
            acao_especial = '[ACAO:PLANEJAMENTO_EVENTO]'
    
    # PRIORIDADE 2: B2B
    elif segmento == 'pessoa_juridica':
        # Cliente B2B - Foco em parcerias e volumes
        if is_marketing_intent or force_marketing:
            resposta = f"""🎯 Oi! Sou a Camila, especialista em marketing da 3A Frios! ✨

Para {_determinar_tipo_negocio(text)}, temos condições especiais:

💼 **PROGRAMA PARCEIRO EMPRESARIAL:**
• Descontos progressivos por volume 📈
• Entrega programada sem taxa extra 🚚
• Cardápio personalizado para seu negócio 🍖
• Suporte comercial dedicado 🤝

📊 Baseado no seu perfil, posso estruturar uma proposta com até 15% de desconto para volumes acima de R$ 500,00.

Quer que eu prepare uma apresentação comercial personalizada? �"""
            
            acao_especial = '[ACAO:CAMPANHA_B2B]'
        else:
            resposta = f"""👋 Camila aqui, marketing da 3A Frios! 🎯

Vejo que representa uma empresa. Temos soluções especiais para o segmento corporativo:

🏢 **SOLUÇÕES EMPRESARIAIS:**
• Fornecimento regular com preços especiais 💰
• Consultoria em cardápios 👨‍🍳
• Entrega programada 📅
• Condições diferenciadas 🌟

Posso apresentar nossas campanhas corporativas? 📊"""
            
            acao_especial = '[ACAO:APRESENTAR_B2B]'
    
    # PRIORIDADE 3: Pessoa física/família
    else:  # pessoa_fisica
        # Clientes família - Foco em relacionamento e valor
        if qualificacao_status == 'hot' and lead_score >= 7:
            # Cliente quente - Oferta premium
            resposta = f"""✨ Oi! Camila da 3A Frios! 🎯

Percebi seu interesse pelos nossos produtos! Para clientes especiais como você:

🏆 **EXPERIÊNCIA PREMIUM:**
• 1ª compra com 12% de desconto 💰
• Delivery gratuito na sua região 🚚
• Kit degustação de temperos exclusivos 🧂
• Acesso ao programa fidelidade VIP 👑

💝 Ainda incluímos consultoria personalizada para você escolher os melhores cortes!

Ativamos sua experiência premium agora? 🌟"""
            
            acao_especial = '[ACAO:CLIENTE_PREMIUM]'
            
        elif qualificacao_status in ['warm', 'cold'] or lead_score <= 4 or 'primeira' in text:
            # Cliente morno/frio - Estratégia de conversão
            resposta = f"""👋 Camila aqui, marketing da 3A Frios! 🎯

Primeira vez aqui? Preparei algo especial para você:

🎁 **PACOTE BEM-VINDO:**
• 10% desconto na primeira compra 💰
• Frete grátis acima de R$ 80 🚚
• Guia de cortes gratuito 📖
• WhatsApp direto para dúvidas 💬

🔥 Válido por 7 dias! Perfeito para você experimentar nossa qualidade sem compromisso.

Garanto sua oferta de boas-vindas? 🎯"""
            
            acao_especial = '[ACAO:BEM_VINDO]'
        else:
            # Cliente regular - Manutenção e fidelização
            resposta = f"""💫 Oi! Camila da equipe de marketing! 🎯

Que bom ter você aqui! Para nossos clientes especiais:

🎪 **NOVIDADES DA SEMANA:**
• Promoção relâmpago: Picanha 15% off 🥩
• Combo família: 3kg variados com desconto 👨‍👩‍👧‍👦
• Programa pontos: Ganhe desconto nas próximas 🎁

📱 Quer receber essas ofertas exclusivas direto no WhatsApp? ✨"""
            
            acao_especial = '[ACAO:NEWSLETTER_OFERTAS]'
    
    # Caso não seja intenção de marketing mas chegou aqui
    if not (is_marketing_intent or force_marketing or is_evento_context):
        resposta = f"""👋 Oi! Sou a Camila, especialista em relacionamento da 3A Frios! 🎯

Mesmo que não tenha perguntado sobre promoções, sempre tenho algo especial para nossos clientes:

{_gerar_oferta_contextual(segmento, lead_score)}

Posso apresentar nossas campanhas atuais? ✨"""
        acao_especial = '[ACAO:OFERTAS_CONTEXTUAIS]'
    
    return {
        'resposta': resposta,
        'acao_especial': acao_especial,
        'camila_strategy': {
            'segmento_identificado': segmento,
            'estrategia_aplicada': _obter_estrategia(segmento, qualificacao_status),
            'urgencia_detectada': urgencia,
            'lead_score': lead_score
        }
    }

def _determinar_tipo_negocio(text: str) -> str:
    """Identifica o tipo de negócio com base no texto"""
    if any(k in text for k in ['restaurante', 'lanchonete', 'bar']):
        return 'restaurantes'
    elif any(k in text for k in ['hotel', 'pousada', 'resort']):
        return 'hotelaria' 
    elif any(k in text for k in ['empresa', 'escritorio', 'corporativo']):
        return 'corporativo'
    elif any(k in text for k in ['evento', 'festa', 'casamento']):
        return 'eventos'
    else:
        return 'seu negócio'

def _gerar_oferta_contextual(segmento: str, lead_score: int) -> str:
    """Gera oferta baseada no contexto do cliente"""
    if segmento == 'pessoa_juridica':
        return "🏢 **CONDIÇÕES ESPECIAIS B2B:** Descontos progressivos e entrega programada"
    elif segmento == 'evento_especial':
        return "🎉 **PACOTE EVENTO:** Consultoria + cortes premium + entrega pontual"
    elif lead_score >= 7:
        return "🌟 **OFERTA VIP:** 12% desconto + frete grátis + kit degustação"
    else:
        return "🎁 **BEM-VINDO:** 10% off primeira compra + guia de cortes grátis"

def _obter_estrategia(segmento: str, status: str) -> str:
    """Retorna a estratégia aplicada para analytics"""
    estrategias = {
        'pessoa_juridica': 'Parceria B2B',
        'evento_especial': 'Experiência Premium Evento',
        'pessoa_fisica': {
            'hot': 'Conversão Premium',
            'warm': 'Ativação Interesse', 
            'cold': 'Primeira Impressão'
        }
    }
    
    if segmento == 'pessoa_fisica':
        return estrategias[segmento].get(status, 'Relacionamento')
    return estrategias.get(segmento, 'Marketing Geral')