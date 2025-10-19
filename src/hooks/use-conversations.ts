'use client'

import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getSupabase } from '@/lib/supabase'
import { useEffect } from 'react'

interface TempMessage {
  id: string
  cliente_id: string
  mensagem_cliente: string
  resposta_bot?: string
  tipo_mensagem: 'texto' | 'audio'
  agente_responsavel?: string
  acao_especial?: string
  timestamp: string
}

// função: useConversations(clienteId: string)
export function useConversations(clienteId: string | number) {
  const cid = typeof clienteId === 'string' && /^\d+$/.test(clienteId) ? Number(clienteId) : clienteId

  const query = useQuery({
    queryKey: ['conversations', String(clienteId)],
    queryFn: async () => {
      const supabase = getSupabase()
      const { data, error } = await supabase
        .from('temp_messages')
        .select('*')
        .eq('cliente_id', cid)
        .order('timestamp', { ascending: true })

      if (error) {
        console.error('Erro ao buscar conversas:', error)
        return []
      }
      const rows = (data || []) as any[]
      return rows.map((r) => ({
        id: String(r.id),
        cliente_id: r.cliente_id,
        mensagem_cliente: (r.mensagem_cliente ?? r.mensagem ?? '') as string,
        resposta_bot: (r.resposta_bot ?? '') as string,
        tipo_mensagem: (r.tipo_mensagem ?? r.tipo ?? 'texto') as 'texto' | 'audio',
        agente_responsavel: r.agente_responsavel,
        acao_especial: r.acao_especial,
        timestamp: (r.timestamp ?? r.created_at ?? new Date().toISOString()) as string,
      }))
    },
    enabled: !!clienteId,
    refetchInterval: 2000,  // Reduzido para 2 segundos
    staleTime: 1000,       // Reduzido para 1 segundo
  })

  const queryClient = useQueryClient()

  useEffect(() => {
    if (!clienteId) return
    const supabase = getSupabase()
    const filtro = typeof cid === 'number' ? cid : clienteId
    
    // Canal para mensagens específicas do cliente
    const clientChannel = supabase
      .channel(`realtime_messages_${filtro}`)
      .on(
        'postgres_changes',
        { 
          event: '*', // Captura INSERT, UPDATE e DELETE
          schema: 'public', 
          table: 'temp_messages', 
          filter: `cliente_id=eq.${filtro}` 
        },
        (payload) => {
          // Atualiza imediatamente
          query.refetch()
          
          // Invalida o cache de conversas recentes também
          queryClient.invalidateQueries({ queryKey: ['conversations', 'recent'] })
        }
      )
      .subscribe()

    // Canal para todas as mensagens (útil para atualizações gerais)
    const globalChannel = supabase
      .channel('realtime_messages_global')
      .on(
        'postgres_changes',
        { 
          event: 'INSERT', 
          schema: 'public', 
          table: 'temp_messages'
        },
        () => {
          queryClient.invalidateQueries({ queryKey: ['conversations', 'recent'] })
        }
      )
      .subscribe()

    return () => { 
      supabase.removeChannel(clientChannel)
      supabase.removeChannel(globalChannel)
    }
  }, [clienteId, query, queryClient])

  return query
}

// função: useRecentConversations()
export function useRecentConversations() {
  return useQuery({
    queryKey: ['conversations', 'recent'],
    queryFn: async () => {
      const supabase = getSupabase()
      const { data, error } = await supabase
        .from('temp_messages')
        .select('*')
        .order('timestamp', { ascending: false })

      if (error) {
        console.error('Erro ao buscar conversas recentes:', error)
        return []
      }
      const rows = (data || []) as any[]
      const mapped = rows.map((r) => {
        const ts = (r.timestamp ?? r.created_at ?? new Date().toISOString()) as string
        return {
          id: String(r.id),
          cliente_id: r.cliente_id,
          mensagem_cliente: (r.mensagem_cliente ?? r.mensagem ?? '') as string,
          resposta_bot: (r.resposta_bot ?? '') as string,
          tipo_mensagem: (r.tipo_mensagem ?? r.tipo ?? 'texto') as 'texto' | 'audio',
          agente_responsavel: r.agente_responsavel,
          acao_especial: r.acao_especial,
          timestamp: ts,
        }
      })
      // Filtra últimas 24h com base no timestamp efetivo
      const cutoff = Date.now() - 24 * 60 * 60 * 1000
      return mapped.filter((m) => new Date(m.timestamp).getTime() >= cutoff)
    },
  })
}