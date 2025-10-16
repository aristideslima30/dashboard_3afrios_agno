'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { supabase, ClienteDelivery } from '@/lib/supabase'

// Dados mockados para testes
const MOCK_LEADS: ClienteDelivery[] = [
  {
    id: 'mock-1',
    nome: 'João Silva',
    telefone: '11987654321',
    endereco: 'Rua das Flores, 123 - São Paulo, SP',
    lead_score: 8,
    lead_status: 'interessado',
    interesse_declarado: 'Queijos artesanais e frios especiais',
    frequencia_compra: 'Semanal',
    valor_potencial: 250.00,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'mock-2',
    nome: 'Maria Santos',
    telefone: '11976543210',
    endereco: 'Av. Paulista, 456 - São Paulo, SP',
    lead_score: 9,
    lead_status: 'pronto_para_comprar',
    interesse_declarado: 'Carnes premium para churrasco',
    frequencia_compra: 'Quinzenal',
    valor_potencial: 450.00,
    created_at: new Date(Date.now() - 86400000).toISOString(), // 1 dia atrás
    updated_at: new Date(Date.now() - 3600000).toISOString() // 1 hora atrás
  },
  {
    id: 'mock-3',
    nome: 'Pedro Oliveira',
    telefone: '11965432109',
    endereco: 'Rua Augusta, 789 - São Paulo, SP',
    lead_score: 6,
    lead_status: 'interessado',
    interesse_declarado: 'Produtos para festa de aniversário',
    frequencia_compra: 'Mensal',
    valor_potencial: 180.00,
    created_at: new Date(Date.now() - 172800000).toISOString(), // 2 dias atrás
    updated_at: new Date(Date.now() - 7200000).toISOString() // 2 horas atrás
  },
  {
    id: 'mock-4',
    nome: 'Ana Costa',
    telefone: '11954321098',
    endereco: 'Rua Oscar Freire, 321 - São Paulo, SP',
    lead_score: 4,
    lead_status: 'novo',
    interesse_declarado: undefined,
    frequencia_compra: undefined,
    valor_potencial: undefined,
    created_at: new Date(Date.now() - 259200000).toISOString(), // 3 dias atrás
    updated_at: new Date(Date.now() - 10800000).toISOString() // 3 horas atrás
  },
  {
    id: 'mock-5',
    nome: 'Carlos Ferreira',
    telefone: '11943210987',
    endereco: 'Rua Consolação, 654 - São Paulo, SP',
    lead_score: 10,
    lead_status: 'pronto_para_comprar',
    interesse_declarado: 'Kit completo para restaurante',
    frequencia_compra: 'Semanal',
    valor_potencial: 800.00,
    created_at: new Date(Date.now() - 345600000).toISOString(), // 4 dias atrás
    updated_at: new Date(Date.now() - 1800000).toISOString() // 30 min atrás
  },
  {
    id: 'mock-6',
    nome: 'Lucia Rodrigues',
    telefone: '11932109876',
    endereco: 'Av. Faria Lima, 987 - São Paulo, SP',
    lead_score: 7,
    lead_status: 'interessado',
    interesse_declarado: 'Frios para lanchonete',
    frequencia_compra: 'Quinzenal',
    valor_potencial: 320.00,
    created_at: new Date(Date.now() - 432000000).toISOString(), // 5 dias atrás
    updated_at: new Date(Date.now() - 14400000).toISOString() // 4 horas atrás
  },
  {
    id: 'mock-7',
    nome: 'Roberto Lima',
    telefone: '11921098765',
    endereco: 'Rua Haddock Lobo, 147 - São Paulo, SP',
    lead_score: 3,
    lead_status: 'novo',
    interesse_declarado: undefined,
    frequencia_compra: undefined,
    valor_potencial: undefined,
    created_at: new Date(Date.now() - 518400000).toISOString(), // 6 dias atrás
    updated_at: new Date(Date.now() - 21600000).toISOString() // 6 horas atrás
  },
  {
    id: 'mock-8',
    nome: 'Fernanda Alves',
    telefone: '11910987654',
    endereco: 'Rua Bela Cintra, 258 - São Paulo, SP',
    lead_score: 5,
    lead_status: 'interessado',
    interesse_declarado: 'Queijos especiais para evento',
    frequencia_compra: 'Esporádica',
    valor_potencial: 150.00,
    created_at: new Date(Date.now() - 604800000).toISOString(), // 7 dias atrás
    updated_at: new Date(Date.now() - 28800000).toISOString() // 8 horas atrás
  }
]

export function useLeads() {
    return useQuery({
        queryKey: ['leads'],
        queryFn: async () => {
            const { data, error } = await supabase
                .from('clientes_delivery')
                .select('*')
                .order('updated_at', { ascending: false })

            if (error) {
                console.error('Erro ao buscar leads:', error)
                return [] // sem fallback para MOCK_LEADS
            }

            // Retorna somente dados reais, sem mesclar com mockados
            return data || []
        },
    })
}

export function useLeadsByScore(minScore: number) {
    return useQuery({
        queryKey: ['leads', 'by-score', minScore],
        queryFn: async () => {
            const { data, error } = await supabase
                .from('clientes_delivery')
                .select('*')
                .gte('lead_score', minScore)
                .order('lead_score', { ascending: false })

            if (error) {
                console.error('Erro ao buscar leads por score:', error)
                return [] // sem fallback para MOCK_LEADS
            }

            return data || []
        },
    })
}

export function useUpdateLead() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, updates }: { id: string; updates: Partial<ClienteDelivery> }) => {
      // Se for um ID mockado, simula a atualização
      if (id.startsWith('mock-')) {
        console.log('Simulando atualização de lead mockado:', id, updates)
        return { id, ...updates }
      }

      const { data, error } = await supabase
        .from('clientes_delivery')
        .update(updates)
        .eq('id', id)
        .select()
        .single()

      if (error) throw error
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
    },
  })
}