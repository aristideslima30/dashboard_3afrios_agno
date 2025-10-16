-- Padronização de schema no Supabase (public)
-- Clientes: unifica telefone_cliente -> telefone e normaliza colunas

-- Cria colunas padronizadas se não existirem
ALTER TABLE public.clientes_delivery
  ADD COLUMN IF NOT EXISTS nome text,
  ADD COLUMN IF NOT EXISTS telefone text,
  ADD COLUMN IF NOT EXISTS endereco text,
  ADD COLUMN IF NOT EXISTS lead_score integer DEFAULT 0 NOT NULL,
  ADD COLUMN IF NOT EXISTS lead_status text DEFAULT 'novo' NOT NULL,
  ADD COLUMN IF NOT EXISTS interesse_declarado text,
  ADD COLUMN IF NOT EXISTS frequencia_compra text,
  ADD COLUMN IF NOT EXISTS valor_potencial numeric,
  ADD COLUMN IF NOT EXISTS created_at timestamptz DEFAULT now() NOT NULL,
  ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now() NOT NULL;

-- Migra dados de telefone_cliente para telefone
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'clientes_delivery' AND column_name = 'telefone_cliente'
  ) THEN
    UPDATE public.clientes_delivery SET telefone = telefone_cliente
    WHERE telefone IS NULL AND telefone_cliente IS NOT NULL;
    -- Remove coluna antiga
    ALTER TABLE public.clientes_delivery DROP COLUMN IF EXISTS telefone_cliente;
  END IF;
END $$;

-- Índices úteis
CREATE UNIQUE INDEX IF NOT EXISTS clientes_delivery_telefone_unique ON public.clientes_delivery(telefone);
CREATE INDEX IF NOT EXISTS clientes_delivery_updated_at_idx ON public.clientes_delivery(updated_at DESC);

-- Conversas: padroniza temp_messages para schema do backend/frontend
-- Cria tabela se não existir
CREATE TABLE IF NOT EXISTS public.temp_messages (
  id bigserial PRIMARY KEY,
  cliente_id bigint NOT NULL REFERENCES public.clientes_delivery(id) ON DELETE CASCADE,
  mensagem_cliente text DEFAULT '' NOT NULL,
  resposta_bot text DEFAULT '' NOT NULL,
  tipo_mensagem text DEFAULT 'texto' NOT NULL,
  agente_responsavel text,
  acao_especial text,
  timestamp timestamptz DEFAULT now() NOT NULL
);

-- Garante colunas padronizadas mesmo se a tabela já existia com schema alternativo
ALTER TABLE public.temp_messages ADD COLUMN IF NOT EXISTS cliente_id bigint;
ALTER TABLE public.temp_messages ADD COLUMN IF NOT EXISTS mensagem_cliente text DEFAULT '' NOT NULL;
ALTER TABLE public.temp_messages ADD COLUMN IF NOT EXISTS resposta_bot text DEFAULT '' NOT NULL;
ALTER TABLE public.temp_messages ADD COLUMN IF NOT EXISTS tipo_mensagem text DEFAULT 'texto' NOT NULL;
ALTER TABLE public.temp_messages ADD COLUMN IF NOT EXISTS agente_responsavel text;
ALTER TABLE public.temp_messages ADD COLUMN IF NOT EXISTS acao_especial text;
ALTER TABLE public.temp_messages ADD COLUMN IF NOT EXISTS timestamp timestamptz DEFAULT now() NOT NULL;

-- Adiciona FK cliente_id -> clientes_delivery(id) se ainda não existir
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'temp_messages_cliente_id_fkey'
  ) THEN
    ALTER TABLE public.temp_messages
      ADD CONSTRAINT temp_messages_cliente_id_fkey
      FOREIGN KEY (cliente_id) REFERENCES public.clientes_delivery(id) ON DELETE CASCADE;
  END IF;
END $$;

-- Se existir tabela/colunas com schema alternativo, migra dados
-- cliente_telefone -> cliente_id, mensagem -> mensagem_cliente, tipo -> tipo_mensagem, created_at -> timestamp
DO $$
DECLARE
  has_cliente_telefone boolean;
  has_mensagem boolean;
  has_tipo boolean;
  has_created_at boolean;
BEGIN
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'temp_messages' AND column_name = 'cliente_telefone'
  ) INTO has_cliente_telefone;
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'temp_messages' AND column_name = 'mensagem'
  ) INTO has_mensagem;
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'temp_messages' AND column_name = 'tipo'
  ) INTO has_tipo;
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'temp_messages' AND column_name = 'created_at'
  ) INTO has_created_at;

  IF has_cliente_telefone THEN
    -- Adiciona coluna cliente_id se não existir
    ALTER TABLE public.temp_messages ADD COLUMN IF NOT EXISTS cliente_id bigint;
    -- Preenche cliente_id baseado em telefone
    UPDATE public.temp_messages tm
    SET cliente_id = cd.id
    FROM public.clientes_delivery cd
    WHERE tm.cliente_id IS NULL AND tm.cliente_telefone = cd.telefone;

    -- Remove coluna antiga
    ALTER TABLE public.temp_messages DROP COLUMN IF EXISTS cliente_telefone;
  END IF;

  IF has_mensagem THEN
    -- Adiciona coluna mensagem_cliente se não existir e migra
    ALTER TABLE public.temp_messages ADD COLUMN IF NOT EXISTS mensagem_cliente text DEFAULT '';
    UPDATE public.temp_messages SET mensagem_cliente = mensagem
    WHERE mensagem_cliente = '' AND mensagem IS NOT NULL;
    -- Remove coluna antiga
    ALTER TABLE public.temp_messages DROP COLUMN IF EXISTS mensagem;
  END IF;

  IF has_tipo THEN
    ALTER TABLE public.temp_messages ADD COLUMN IF NOT EXISTS tipo_mensagem text DEFAULT 'texto';
    UPDATE public.temp_messages SET tipo_mensagem = tipo WHERE tipo IS NOT NULL;
    ALTER TABLE public.temp_messages DROP COLUMN IF EXISTS tipo;
  END IF;

  IF has_created_at THEN
    ALTER TABLE public.temp_messages ADD COLUMN IF NOT EXISTS timestamp timestamptz DEFAULT now();
    UPDATE public.temp_messages SET timestamp = created_at WHERE timestamp IS NULL AND created_at IS NOT NULL;
    ALTER TABLE public.temp_messages DROP COLUMN IF EXISTS created_at;
  END IF;
END $$;

-- Índices úteis em conversas
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'temp_messages' AND column_name = 'cliente_id'
  ) THEN
    CREATE INDEX IF NOT EXISTS temp_messages_cliente_id_idx ON public.temp_messages(cliente_id);
  END IF;
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'temp_messages' AND column_name = 'timestamp'
  ) THEN
    CREATE INDEX IF NOT EXISTS temp_messages_timestamp_idx ON public.temp_messages(timestamp DESC);
  END IF;
END $$;

-- Campanhas (exemplo de padronização básica)
CREATE TABLE IF NOT EXISTS public.campanhas_marketing (
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

-- Pedidos (stub, ajustar conforme necessidade)
CREATE TABLE IF NOT EXISTS public.pedidos_delivery (
  id bigserial PRIMARY KEY,
  cliente_id bigint NOT NULL REFERENCES public.clientes_delivery(id) ON DELETE CASCADE,
  itens jsonb NOT NULL,
  valor_total numeric NOT NULL,
  forma_pagamento text NOT NULL,
  status text NOT NULL,
  data_pedido timestamptz NOT NULL,
  created_at timestamptz DEFAULT now() NOT NULL
);