import { createClient } from '@supabase/supabase-js'

let _supabase: ReturnType<typeof createClient> | null = null

export function getSupabase() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error('Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY')
  }
  if (!_supabase) {
    _supabase = createClient(supabaseUrl, supabaseAnonKey)
  }
  return _supabase
}

// Tipos para as tabelas do banco
export interface ClienteDelivery {
  id: string
  nome: string
  telefone: string
  endereco?: string
  lead_score: number
  lead_status: 'novo' | 'interessado' | 'pronto_para_comprar'
  interesse_declarado?: string
  frequencia_compra?: string
  valor_potencial?: number
  created_at: string
  updated_at: string
}

export interface PedidoDelivery {
  id: string
  cliente_id: string
  itens: unknown[]
  valor_total: number
  forma_pagamento: string
  status: string
  data_pedido: string
  created_at: string
}

export interface CampanhaMarketing {
  id: string
  nome: string
  produtos: string[]
  oferta: string
  data_inicio: string
  data_fim: string
  segmento: Record<string, unknown>
  created_at: string
  updated_at?: string
}

export interface TempMessage {
  id: string
  cliente_id: string
  cliente_telefone?: string
  mensagem_cliente: string
  resposta_bot?: string
  tipo_mensagem: 'texto' | 'audio'
  agente_responsavel?: string
  acao_especial?: string
  timestamp: string
}