'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getSupabase, ClienteDelivery } from '@/lib/supabase'

export function useLeads() {
  return useQuery<ClienteDelivery[]>({
    queryKey: ['leads'],
    queryFn: async () => {
      const supabase = getSupabase()
      const { data, error } = await supabase
        .from('clientes_delivery')
        .select('*')
        .order('updated_at', { ascending: false })

      if (error) {
        console.error('Erro ao buscar leads:', error)
        return []
      }
      return (data ?? []) as ClienteDelivery[]
    },
  })
}

export function useLeadsByScore(minScore: number) {
  return useQuery<ClienteDelivery[]>({
    queryKey: ['leads', 'by-score', minScore],
    queryFn: async () => {
      const supabase = getSupabase()
      const { data, error } = await supabase
        .from('clientes_delivery')
        .select('*')
        .gte('lead_score', minScore)
        .order('lead_score', { ascending: false })

      if (error) {
        console.error('Erro ao buscar leads por score:', error)
        return []
      }

      return (data ?? []) as ClienteDelivery[]
    },
  })
}

type UpdateLeadInput = { id: string; updates: Partial<ClienteDelivery> }

export function useUpdateLead() {
  const queryClient = useQueryClient()

  return useMutation<ClienteDelivery, unknown, UpdateLeadInput>({
    mutationFn: async ({ id, updates }) => {
      const supabase = getSupabase()
      const table: any = supabase.from('clientes_delivery') // evita Update<never>
      const { data, error } = await table
        .update(updates)
        .eq('id', id)
        .select()
        .single()

      if (error) throw error
      if (!data) throw new Error('Atualização não retornou dados')
      return data as ClienteDelivery
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
    },
  })
}