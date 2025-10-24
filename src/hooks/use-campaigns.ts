'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getSupabase, CampanhaMarketing } from '@/lib/supabase'

// ===================================
// CONFIGURAÇÕES DA API
// ===================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ===================================
// FUNÇÕES DA API
// ===================================

async function fetchCampaignConfigs() {
  const response = await fetch(`${API_BASE_URL}/api/campanhas/configuracoes`)
  if (!response.ok) {
    throw new Error('Erro ao buscar configurações de campanhas')
  }
  return response.json()
}

async function saveCampaignConfigs(config: any) {
  const response = await fetch(`${API_BASE_URL}/api/campanhas/configuracoes`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config),
  })
  if (!response.ok) {
    throw new Error('Erro ao salvar configurações de campanhas')
  }
  return response.json()
}

async function fetchCampaignTemplates(tipo?: string) {
  const params = new URLSearchParams()
  if (tipo) params.append('tipo', tipo)
  
  const response = await fetch(`${API_BASE_URL}/api/campanhas/templates?${params}`)
  if (!response.ok) {
    throw new Error('Erro ao buscar templates de campanhas')
  }
  return response.json()
}

async function createCampaignTemplate(template: any) {
  const response = await fetch(`${API_BASE_URL}/api/campanhas/templates`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(template),
  })
  if (!response.ok) {
    throw new Error('Erro ao criar template de campanha')
  }
  return response.json()
}

async function testCampaign(testData: any) {
  const response = await fetch(`${API_BASE_URL}/api/campanhas/testar`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(testData),
  })
  if (!response.ok) {
    throw new Error('Erro ao testar campanha')
  }
  return response.json()
}

async function fetchCampaignHistory(filters: any = {}) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.append(key, String(value))
  })
  
  const response = await fetch(`${API_BASE_URL}/api/campanhas/historico?${params}`)
  if (!response.ok) {
    throw new Error('Erro ao buscar histórico de campanhas')
  }
  return response.json()
}

async function fetchCampaignStatistics(dataInicio?: string, dataFim?: string) {
  const params = new URLSearchParams()
  if (dataInicio) params.append('data_inicio', dataInicio)
  if (dataFim) params.append('data_fim', dataFim)
  
  const response = await fetch(`${API_BASE_URL}/api/campanhas/historico/estatisticas?${params}`)
  if (!response.ok) {
    throw new Error('Erro ao buscar estatísticas de campanhas')
  }
  return response.json()
}

async function fetchCampaignTypes() {
  const response = await fetch(`${API_BASE_URL}/api/campanhas/tipos`)
  if (!response.ok) {
    throw new Error('Erro ao buscar tipos de campanhas')
  }
  return response.json()
}

// ===================================
// HOOKS PRINCIPAIS
// ===================================

export function useCampaigns() {
  return useQuery({
    queryKey: ['campaigns'],
    queryFn: async () => {
      try {
        const supabase = getSupabase()
        const { data, error } = await supabase
          .from('campanhas_marketing')
          .select('*')
          .order('created_at', { ascending: false })

        if (error) {
          console.error('Erro ao buscar campanhas:', error)
          // Fallback para dados mockados se Supabase falhar
          return getMockCampaigns()
        }

        // Se não há dados reais, retorna os dados mockados
        if (!data || data.length === 0) {
          return getMockCampaigns()
        }

        return data as CampanhaMarketing[]
      } catch (error) {
        console.error('Erro na query de campanhas:', error)
        return getMockCampaigns()
      }
    }
  })
}

export function useActiveCampaigns() {
  return useQuery({
    queryKey: ['active-campaigns'],
    queryFn: async () => {
      try {
        const supabase = getSupabase()
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
          return getActiveMockCampaigns()
        }

        // Se não há dados reais, retorna as campanhas mockadas ativas
        if (!data || data.length === 0) {
          return getActiveMockCampaigns()
        }

        return data as CampanhaMarketing[]
      } catch (error) {
        console.error('Erro na query de campanhas ativas:', error)
        return getActiveMockCampaigns()
      }
    }
  })
}

export function useCreateCampaign() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (newCampaign: Omit<CampanhaMarketing, 'id' | 'created_at'>) => {
      const supabase = getSupabase()
      const table: any = supabase.from('campanhas_marketing')
      const { data, error } = await table
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

// ===================================
// HOOKS PARA CONFIGURAÇÕES
// ===================================

export function useCampaignConfigs() {
  return useQuery({
    queryKey: ['campaign-configs'],
    queryFn: fetchCampaignConfigs,
    staleTime: 5 * 60 * 1000, // 5 minutos
  })
}

export function useSaveCampaignConfigs() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: saveCampaignConfigs,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaign-configs'] })
    }
  })
}

// ===================================
// HOOKS PARA TEMPLATES
// ===================================

export function useCampaignTemplates(tipo?: string) {
  return useQuery({
    queryKey: ['campaign-templates', tipo],
    queryFn: () => fetchCampaignTemplates(tipo),
    staleTime: 10 * 60 * 1000, // 10 minutos
  })
}

export function useCreateCampaignTemplate() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: createCampaignTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaign-templates'] })
    }
  })
}

// ===================================
// HOOKS PARA TESTES
// ===================================

export function useTestCampaign() {
  return useMutation({
    mutationFn: testCampaign,
  })
}

// ===================================
// HOOKS PARA HISTÓRICO
// ===================================

export function useCampaignHistory(filters: any = {}) {
  return useQuery({
    queryKey: ['campaign-history', filters],
    queryFn: () => fetchCampaignHistory(filters),
    staleTime: 2 * 60 * 1000, // 2 minutos
  })
}

export function useCampaignStatistics(dataInicio?: string, dataFim?: string) {
  return useQuery({
    queryKey: ['campaign-statistics', dataInicio, dataFim],
    queryFn: () => fetchCampaignStatistics(dataInicio, dataFim),
    staleTime: 5 * 60 * 1000, // 5 minutos
  })
}

// ===================================
// HOOKS PARA UTILITÁRIOS
// ===================================

export function useCampaignTypes() {
  return useQuery({
    queryKey: ['campaign-types'],
    queryFn: fetchCampaignTypes,
    staleTime: 60 * 60 * 1000, // 1 hora (dados raramente mudam)
  })
}

// ===================================
// DADOS MOCKADOS (FALLBACK)
// ===================================

function getMockCampaigns(): CampanhaMarketing[] {
  return [
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
}

function getActiveMockCampaigns(): CampanhaMarketing[] {
  return getMockCampaigns().filter(campaign => {
    const now = new Date()
    const inicio = new Date(campaign.data_inicio)
    const fim = new Date(campaign.data_fim)
    return now >= inicio && now <= fim
  })
}