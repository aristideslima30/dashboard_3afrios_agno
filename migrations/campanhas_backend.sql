-- ========================================
-- 3A FRIOS - ESTRUTURA BACKEND CAMPANHAS
-- ========================================
-- Script para criação das tabelas necessárias para o sistema de campanhas automáticas
-- Execute este script no Supabase SQL Editor

-- 1. CONFIGURAÇÕES DE CAMPANHAS AUTOMÁTICAS
-- ==========================================
CREATE TABLE IF NOT EXISTS configuracoes_campanhas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Controle geral de automação
    automacao_ativa BOOLEAN DEFAULT false,
    
    -- Configurações por tipo de campanha
    campanhas_automaticas JSONB DEFAULT '{
        "lead_qualificado": {
            "ativo": false,
            "delay_minutos": 30,
            "template_id": null,
            "condicoes": {
                "lead_score_minimo": 7,
                "segmentos": ["pessoa_fisica", "pessoa_juridica"]
            }
        },
        "promocao_produtos": {
            "ativo": false,
            "delay_minutos": 60,
            "template_id": null,
            "condicoes": {
                "interesse_declarado": true,
                "dias_sem_compra": 7
            }
        },
        "follow_up_pedido": {
            "ativo": false,
            "delay_minutos": 15,
            "template_id": null,
            "condicoes": {
                "carrinho_abandonado": true,
                "valor_minimo": 50.00
            }
        },
        "reativacao_cliente": {
            "ativo": false,
            "delay_minutos": 1440,
            "template_id": null,
            "condicoes": {
                "dias_inativo": 30,
                "historico_compras": true
            }
        },
        "cross_sell": {
            "ativo": false,
            "delay_minutos": 45,
            "template_id": null,
            "condicoes": {
                "compra_recente": true,
                "categoria_complementar": true
            }
        },
        "feedback_pos_venda": {
            "ativo": false,
            "delay_minutos": 2880,
            "template_id": null,
            "condicoes": {
                "pedido_entregue": true,
                "dias_apos_entrega": 2
            }
        },
        "oferta_personalizada": {
            "ativo": false,
            "delay_minutos": 120,
            "template_id": null,
            "condicoes": {
                "perfil_alto_valor": true,
                "interesse_especifico": true
            }
        },
        "evento_especial": {
            "ativo": false,
            "delay_minutos": 15,
            "template_id": null,
            "condicoes": {
                "mencao_evento": true,
                "volume_estimado": ">20"
            }
        }
    }'::jsonb,
    
    -- Configurações globais do sistema
    configuracoes_globais JSONB DEFAULT '{
        "horario_envio": {
            "inicio": "08:00",
            "fim": "18:00"
        },
        "dias_semana": [1, 2, 3, 4, 5, 6],
        "max_campanhas_por_cliente_dia": 2,
        "intervalo_minimo_entre_envios": 30,
        "blacklist_telefones": [],
        "teste_mode": false
    }'::jsonb,
    
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- 2. TEMPLATES DE CAMPANHAS
-- =========================
CREATE TABLE IF NOT EXISTS templates_campanhas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identificação do template
    tipo TEXT NOT NULL, -- 'lead_qualificado', 'promocao_produtos', etc.
    nome TEXT NOT NULL,
    descricao TEXT,
    
    -- Conteúdo do template
    template_titulo TEXT NOT NULL,
    template_conteudo TEXT NOT NULL,
    variaveis_disponiveis TEXT[] DEFAULT ARRAY['nome_cliente', 'produto_interesse', 'valor_oferta', 'prazo_entrega'],
    
    -- Configurações do template
    ativo BOOLEAN DEFAULT true,
    template_padrao BOOLEAN DEFAULT false,
    
    -- Metadados
    categoria TEXT DEFAULT 'marketing',
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    
    -- Constraint para garantir apenas um template padrão por tipo
    UNIQUE(tipo, template_padrao) DEFERRABLE INITIALLY DEFERRED
);

-- 3. HISTÓRICO DE CAMPANHAS ENVIADAS
-- ===================================
CREATE TABLE IF NOT EXISTS historico_campanhas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identificação da campanha
    campanha_id TEXT, -- ID da campanha original ou auto-gerado
    tipo_campanha TEXT NOT NULL,
    template_usado_id UUID REFERENCES templates_campanhas(id),
    
    -- Dados do cliente
    cliente_telefone TEXT NOT NULL,
    cliente_nome TEXT,
    cliente_id TEXT, -- Referência ao sistema de CRM se existir
    
    -- Conteúdo enviado
    titulo_enviado TEXT,
    conteudo_enviado TEXT NOT NULL,
    variaveis_usadas JSONB DEFAULT '{}',
    
    -- Contexto do envio
    gatilho_origem TEXT, -- 'automatico', 'manual', 'campanha_programada'
    agente_responsavel TEXT, -- qual agente detectou a oportunidade
    bruno_insights JSONB, -- insights que geraram o envio
    contexto_conversa JSONB, -- contexto da conversa no momento
    
    -- Status e resultado
    status TEXT DEFAULT 'enviado' CHECK (status IN ('enviado', 'falhado', 'pendente')),
    resultado JSONB DEFAULT '{}', -- resposta da API de envio
    
    -- Métricas
    aberto BOOLEAN DEFAULT false,
    respondido BOOLEAN DEFAULT false,
    converteu BOOLEAN DEFAULT false,
    valor_conversao DECIMAL(10,2),
    
    -- Timestamps
    enviado_em TIMESTAMP DEFAULT now(),
    programado_para TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT now()
);

-- 4. GATILHOS E AUTOMAÇÕES
-- =========================
CREATE TABLE IF NOT EXISTS gatilhos_campanhas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Configuração do gatilho
    nome TEXT NOT NULL,
    descricao TEXT,
    tipo_campanha TEXT NOT NULL,
    
    -- Condições para ativação
    condicoes JSONB NOT NULL,
    prioridade INTEGER DEFAULT 5,
    
    -- Controle de execução
    ativo BOOLEAN DEFAULT true,
    max_execucoes_dia INTEGER DEFAULT 10,
    intervalo_cooldown_minutos INTEGER DEFAULT 60,
    
    -- Metadados
    created_by TEXT DEFAULT 'system',
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- 5. ÍNDICES PARA PERFORMANCE
-- ============================

-- Índices para configurações
CREATE INDEX IF NOT EXISTS idx_configuracoes_campanhas_updated_at 
ON configuracoes_campanhas(updated_at);

-- Índices para templates
CREATE INDEX IF NOT EXISTS idx_templates_campanhas_tipo 
ON templates_campanhas(tipo);

CREATE INDEX IF NOT EXISTS idx_templates_campanhas_ativo 
ON templates_campanhas(ativo);

CREATE INDEX IF NOT EXISTS idx_templates_campanhas_padrao 
ON templates_campanhas(tipo, template_padrao);

-- Índices para histórico
CREATE INDEX IF NOT EXISTS idx_historico_campanhas_telefone 
ON historico_campanhas(cliente_telefone);

CREATE INDEX IF NOT EXISTS idx_historico_campanhas_tipo 
ON historico_campanhas(tipo_campanha);

CREATE INDEX IF NOT EXISTS idx_historico_campanhas_enviado_em 
ON historico_campanhas(enviado_em);

CREATE INDEX IF NOT EXISTS idx_historico_campanhas_status 
ON historico_campanhas(status);

-- Índice composto para verificar campanhas por cliente/tipo/data
CREATE INDEX IF NOT EXISTS idx_historico_campanhas_dedup 
ON historico_campanhas(cliente_telefone, tipo_campanha, enviado_em);

-- Índices para gatilhos
CREATE INDEX IF NOT EXISTS idx_gatilhos_campanhas_tipo 
ON gatilhos_campanhas(tipo_campanha);

CREATE INDEX IF NOT EXISTS idx_gatilhos_campanhas_ativo 
ON gatilhos_campanhas(ativo);

-- 6. TRIGGERS PARA UPDATED_AT
-- ============================

-- Função para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para as tabelas
DROP TRIGGER IF EXISTS update_configuracoes_campanhas_updated_at ON configuracoes_campanhas;
CREATE TRIGGER update_configuracoes_campanhas_updated_at
    BEFORE UPDATE ON configuracoes_campanhas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_templates_campanhas_updated_at ON templates_campanhas;
CREATE TRIGGER update_templates_campanhas_updated_at
    BEFORE UPDATE ON templates_campanhas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_gatilhos_campanhas_updated_at ON gatilhos_campanhas;
CREATE TRIGGER update_gatilhos_campanhas_updated_at
    BEFORE UPDATE ON gatilhos_campanhas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 7. DADOS INICIAIS
-- =================

-- Inserir configuração inicial (se não existir)
INSERT INTO configuracoes_campanhas (automacao_ativa, campanhas_automaticas, configuracoes_globais)
SELECT false, 
       '{
        "lead_qualificado": {"ativo": false, "delay_minutos": 30, "template_id": null, "condicoes": {"lead_score_minimo": 7}},
        "promocao_produtos": {"ativo": false, "delay_minutos": 60, "template_id": null, "condicoes": {"interesse_declarado": true}},
        "follow_up_pedido": {"ativo": false, "delay_minutos": 15, "template_id": null, "condicoes": {"carrinho_abandonado": true}},
        "reativacao_cliente": {"ativo": false, "delay_minutos": 1440, "template_id": null, "condicoes": {"dias_inativo": 30}},
        "cross_sell": {"ativo": false, "delay_minutos": 45, "template_id": null, "condicoes": {"compra_recente": true}},
        "feedback_pos_venda": {"ativo": false, "delay_minutos": 2880, "template_id": null, "condicoes": {"pedido_entregue": true}},
        "oferta_personalizada": {"ativo": false, "delay_minutos": 120, "template_id": null, "condicoes": {"perfil_alto_valor": true}},
        "evento_especial": {"ativo": false, "delay_minutos": 15, "template_id": null, "condicoes": {"mencao_evento": true}}
       }'::jsonb,
       '{"horario_envio": {"inicio": "08:00", "fim": "18:00"}, "dias_semana": [1,2,3,4,5,6], "max_campanhas_por_cliente_dia": 2}'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM configuracoes_campanhas);

-- Templates padrão para cada tipo de campanha
INSERT INTO templates_campanhas (tipo, nome, template_titulo, template_conteudo, template_padrao, ativo) VALUES
('lead_qualificado', 'Lead Qualificado - Padrão', '🎯 Oferta Especial 3A Frios', 
 'Olá {nome_cliente}! 😊\n\nNotei seu interesse em nossos produtos de qualidade. Como você demonstrou um perfil de cliente especial, preparei uma oferta exclusiva:\n\n🥩 {produto_interesse}\n💰 {valor_oferta}\n🚚 Entrega: {prazo_entrega}\n\nEssa condição é válida apenas hoje! Posso preparar seu pedido agora?', 
 true, true),

('promocao_produtos', 'Promoção de Produtos', '🔥 Promoção Imperdível!', 
 'Oi {nome_cliente}! 🔥\n\nTemos uma promoção especial nos produtos que você tem interesse:\n\n{produto_interesse}\n{valor_oferta}\n\nPromoção válida apenas hoje! Quer garantir o seu?', 
 true, true),

('follow_up_pedido', 'Follow-up de Pedido', '🛒 Finalize seu pedido!', 
 'Olá {nome_cliente}! 😊\n\nVi que você estava interessado em finalizar um pedido conosco. Posso ajudar a completar sua compra?\n\nSeus itens ainda estão disponíveis e posso garantir a {prazo_entrega}!', 
 true, true),

('reativacao_cliente', 'Reativação de Cliente', '😊 Sentimos sua falta!', 
 'Oi {nome_cliente}! 😊\n\nFaz um tempo que não fazemos suas compras juntos! Como você é um cliente especial, preparei uma oferta exclusiva para seu retorno:\n\n{valor_oferta}\n\nQue tal voltarmos a trabalhar juntos?', 
 true, true),

('cross_sell', 'Cross-sell', '🥩 Que tal complementar?', 
 'Oi {nome_cliente}! 😊\n\nVi que você gostou do {produto_interesse}. Para completar sua compra, que tal adicionar:\n\n{valor_oferta}\n\nFica um combo perfeito! Posso incluir no seu pedido?', 
 true, true),

('feedback_pos_venda', 'Feedback Pós-venda', '📝 Como foi sua experiência?', 
 'Oi {nome_cliente}! 😊\n\nEspero que tenha gostado dos produtos que entregamos! Sua opinião é muito importante para nós.\n\nComo foi sua experiência? Ficou satisfeito com a qualidade e entrega?', 
 true, true),

('oferta_personalizada', 'Oferta Personalizada', '🎁 Oferta Exclusiva para Você', 
 'Olá {nome_cliente}! 🎁\n\nComo você é um cliente VIP, preparei uma oferta exclusiva baseada no seu perfil:\n\n{produto_interesse}\n{valor_oferta}\n\nEssa condição especial é só para você! Interessado?', 
 true, true),

('evento_especial', 'Evento Especial', '🎉 Produtos para seu Evento', 
 'Oi {nome_cliente}! 🎉\n\nVi que você está organizando um evento especial! Temos produtos perfeitos para a ocasião:\n\n{produto_interesse}\n{valor_oferta}\n{prazo_entrega}\n\nPosso ajudar a tornar seu evento ainda mais especial?', 
 true, true)

ON CONFLICT (tipo, template_padrao) DO NOTHING;

-- =========================================
-- SCRIPT FINALIZADO
-- =========================================
-- Para executar este script:
-- 1. Acesse o Supabase Dashboard
-- 2. Vá em SQL Editor
-- 3. Cole este script completo
-- 4. Execute
-- 
-- O script criará toda a estrutura necessária para o sistema de campanhas automáticas.
-- =========================================