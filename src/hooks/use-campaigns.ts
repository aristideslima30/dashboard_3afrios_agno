'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { supabase, CampanhaMarketing } from '@/lib/supabase'

// Campanhas mockadas para testes
const MOCK_CAMPAIGNS: CampanhaMarketing[] = [
  {
    id: 'camp-1',
    nome: 'Promoção Queijos Artesanais',
    produtos: ['Queijo Minas', 'Queijo Coalho', 'Queijo Prato'],
    oferta: '20% de desconto na compra de 2kg ou mais',
    data_inicio: new Date().toISOString(),
    data_fim: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 dias
    segmento: { "lead_score": ">5", "interesse": "contains queijo" },
    created_at: new Date().toISOString()
  },
  {
    id: 'camp-2',
    nome: 'Kit Churrasco Premium',
    produtos: ['Picanha', 'Maminha', 'Linguiça', 'Pão de Alho'],
    oferta: 'Kit completo por R$ 399 (economia de R$ 50)',
    data_inicio: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 dias atrás
    data_fim: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(), // 5 dias
    segmento: { "lead_score": ">7", "interesse": "contains carne" },
    created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString()
  },
  {
    id: 'camp-3',
    nome: 'Frios para Festas',
    produtos: ['Presunto', 'Mortadela', 'Salame', 'Queijos Variados'],
    oferta: 'Monte sua tábua de frios - 15% off',
    data_inicio: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(), // 5 dias atrás
    data_fim: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), // 1 dia atrás (expirada)
    segmento: { "lead_score": ">3", "interesse": "contains festa" },
    created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString()
  }
]

export function useCampaigns() {
  return useQuery({
    queryKey: ['campaigns'],
    queryFn: async () => {
      try {
        const { data, error } = await supabase
          .from('campanhas_marketing')
          .select('*')
          .order('created_at', { ascending: false })

        if (error) {
          console.error('Erro ao buscar campanhas:', error)
          return MOCK_CAMPAIGNS
        }

        // Se não há dados reais, retorna os dados mockados
        if (!data || data.length === 0) {
          return MOCK_CAMPAIGNS
        }

        return data as CampanhaMarketing[]
      } catch (error) {
        console.error('Erro na query de campanhas:', error)
        return MOCK_CAMPAIGNS
      }
    }
  })
}

export function useActiveCampaigns() {
  return useQuery({
    queryKey: ['active-campaigns'],
    queryFn: async () => {
      try {
        const now = new Date().toISOString()
        const { data, error } = await supabase
          .from('campanhas_marketing')
          .select('*')
          .lte('data_inicio', now)
          .gte('data_fim', now)
          .order('created_at', { ascending: false })

        if (error) {
          console.error('Erro ao buscar campanhas ativas:', error)
          // Retorna campanhas mockadas ativas
          return MOCK_CAMPAIGNS.filter(campaign => {
            const now = new Date()
            const inicio = new Date(campaign.data_inicio)
            const fim = new Date(campaign.data_fim)
            return now >= inicio && now <= fim
          })
        }

        // Se não há dados reais, retorna as campanhas mockadas ativas
        if (!data || data.length === 0) {
          return MOCK_CAMPAIGNS.filter(campaign => {
            const now = new Date()
            const inicio = new Date(campaign.data_inicio)
            const fim = new Date(campaign.data_fim)
            return now >= inicio && now <= fim
          })
        }

        return data as CampanhaMarketing[]
      } catch (error) {
        console.error('Erro na query de campanhas ativas:', error)
        return MOCK_CAMPAIGNS.filter(campaign => {
          const now = new Date()
          const inicio = new Date(campaign.data_inicio)
          const fim = new Date(campaign.data_fim)
          return now >= inicio && now <= fim
        })
      }
    }
  })
}

export function useCreateCampaign() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (newCampaign: Omit<CampanhaMarketing, 'id' | 'created_at'>) => {
      const { data, error } = await supabase
        .from('campanhas_marketing')
        .insert([newCampaign])
        .select()
        .single()

      if (error) {
        throw error
      }

      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] })
      queryClient.invalidateQueries({ queryKey: ['active-campaigns'] })
    }
  })
}