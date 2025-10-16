-- Recriação do schema do zero (DROPs + CREATEs)
-- ATENÇÃO: isto apaga dados existentes. Faça backup se necessário.

BEGIN;

-- Remove tabelas na ordem segura (por FK)
DROP TABLE IF EXISTS public.temp_messages CASCADE;
DROP TABLE IF EXISTS public.pedidos_delivery CASCADE;
DROP TABLE IF EXISTS public.campanhas_marketing CASCADE;
DROP TABLE IF EXISTS public.clientes_delivery CASCADE;

-- Tabela de clientes (usada pelo frontend e backend)
CREATE TABLE public.clientes_delivery (
  id bigserial PRIMARY KEY,
  nome text,
  telefone text NOT NULL,
  endereco text,
  lead_score integer DEFAULT 0 NOT NULL,
  lead_status text DEFAULT 'novo' NOT NULL,
  interesse_declarado text,
  frequencia_compra text,
  valor_potencial numeric,
  created_at timestamptz DEFAULT now() NOT NULL,
  updated_at timestamptz DEFAULT now() NOT NULL
);

-- Índices de clientes
CREATE UNIQUE INDEX clientes_delivery_telefone_unique ON public.clientes_delivery(telefone);
CREATE INDEX clientes_delivery_updated_at_idx ON public.clientes_delivery(updated_at DESC);

-- Tabela de mensagens temporárias (compatível com use-conversations.ts)
CREATE TABLE public.temp_messages (
  id bigserial PRIMARY KEY,
  cliente_id bigint NOT NULL REFERENCES public.clientes_delivery(id) ON DELETE CASCADE,
  cliente_telefone text,
  mensagem_cliente text DEFAULT '' NOT NULL,
  resposta_bot text DEFAULT '' NOT NULL,
  tipo_mensagem text DEFAULT 'texto' NOT NULL,
  agente_responsavel text,
  acao_especial text,
  timestamp timestamptz DEFAULT now() NOT NULL
);
-- Índices de conversas
CREATE INDEX temp_messages_cliente_id_idx ON public.temp_messages(cliente_id);
CREATE INDEX temp_messages_cliente_telefone_idx ON public.temp_messages(cliente_telefone);
CREATE INDEX temp_messages_timestamp_idx ON public.temp_messages(timestamp DESC);

-- Campanhas de marketing (compatível com use-campaigns.ts)
CREATE TABLE public.campanhas_marketing (
  id bigserial PRIMARY KEY,
  nome text NOT NULL,
  produtos jsonb NOT NULL,
  oferta text NOT NULL,
  data_inicio timestamptz NOT NULL,
  data_fim timestamptz NOT NULL,
  segmento jsonb NOT NULL,
  created_at timestamptz DEFAULT now() NOT NULL,
  updated_at timestamptz
);

-- Pedidos (stub compatível com backend)
CREATE TABLE public.pedidos_delivery (
  id bigserial PRIMARY KEY,
  cliente_id bigint NOT NULL REFERENCES public.clientes_delivery(id) ON DELETE CASCADE,
  itens jsonb NOT NULL,
  valor_total numeric NOT NULL,
  forma_pagamento text NOT NULL,
  status text NOT NULL,
  data_pedido timestamptz NOT NULL,
  created_at timestamptz DEFAULT now() NOT NULL
);

COMMIT;