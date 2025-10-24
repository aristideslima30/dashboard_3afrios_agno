'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Plus, Calendar, Target, Users, Edit, Trash2, AlertCircle, Settings, Zap, Info } from 'lucide-react'
import { useCampaigns, useActiveCampaigns, useCreateCampaign } from '@/hooks/use-campaigns'
import { CampanhaMarketing } from '@/lib/supabase'

interface FormData {
  nome: string
  produtos: string
  oferta: string
  data_inicio: string
  data_fim: string
  segmento: string
  tipo_campanha: string
  publico_alvo: string
  objetivo: string
  canal_preferido: string
  // Campos de segmentação simplificada
  segmentacao_score: string
  segmentacao_tipo: string
  segmentacao_frequencia: string
  segmentacao_interesse: string
}

// 🎯 Opções de segmentação simplificadas
const SEGMENTATION_OPTIONS = {
  lead_score: [
    { value: 'todos', label: '📊 Todos os leads', description: 'Sem filtro de pontuação' },
    { value: '>3', label: '🔥 Leads interessados (Score > 3)', description: 'Clientes que demonstraram interesse' },
    { value: '>5', label: '⭐ Leads quentes (Score > 5)', description: 'Clientes muito interessados' },
    { value: '>7', label: '� Leads premium (Score > 7)', description: 'Clientes prontos para comprar' }
  ],
  tipo_cliente: [
    { value: 'todos', label: '👥 Todos os clientes', description: 'Pessoa física e jurídica' },
    { value: 'pessoa_fisica', label: '👤 Pessoa Física', description: 'Clientes individuais' },
    { value: 'pessoa_juridica', label: '🏢 Pessoa Jurídica', description: 'Empresas e negócios' },
    { value: 'evento_especial', label: '🎉 Eventos Especiais', description: 'Clientes organizando eventos' }
  ],
  frequencia: [
    { value: 'todos', label: '🌐 Todos os clientes', description: 'Novos e antigos' },
    { value: 'novos', label: '🆕 Clientes novos', description: 'Primeira compra ou contato' },
    { value: 'recorrentes', label: '🔄 Clientes recorrentes', description: 'Já compraram antes' },
    { value: 'inativos', label: '😴 Clientes inativos', description: 'Sem compra há 30+ dias' }
  ],
  interesse: [
    { value: 'geral', label: '🛒 Interesse geral', description: 'Qualquer produto' },
    { value: 'queijos', label: '🧀 Interessados em queijos', description: 'Mencionaram queijos' },
    { value: 'embutidos', label: '🥓 Interessados em embutidos', description: 'Mencionaram presunto/salame' },
    { value: 'premium', label: '⭐ Produtos premium', description: 'Interessados em produtos especiais' }
  ]
}
const CAMPAIGN_TEMPLATES = [
  {
    id: 'promocional',
    nome: '🎯 Campanha Promocional',
    icon: '🏷️',
    campos: {
      nome: 'Promoção [PRODUTO] - [DESCONTO]%',
      oferta: '[DESCONTO]% de desconto em [PRODUTO] por tempo limitado!',
      objetivo: 'Aumentar vendas de produtos específicos',
      publico_alvo: 'Clientes interessados no produto',
      canal_preferido: 'WhatsApp'
    }
  },
  {
    id: 'lancamento',
    nome: '🚀 Lançamento de Produto',
    icon: '✨',
    campos: {
      nome: 'Lançamento: [PRODUTO]',
      oferta: 'Conheça nosso novo [PRODUTO]! Primeira semana com desconto especial.',
      objetivo: 'Apresentar novo produto ao mercado',
      publico_alvo: 'Base de clientes ativos',
      canal_preferido: 'WhatsApp + Newsletter'
    }
  },
  {
    id: 'reativacao',
    nome: '🔄 Reativação de Clientes',
    icon: '💌',
    campos: {
      nome: 'Volta que eu te perdoo',
      oferta: 'Sentimos sua falta! Volta com desconto especial de 15%.',
      objetivo: 'Reativar clientes inativos',
      publico_alvo: 'Clientes sem compra há 30+ dias',
      canal_preferido: 'WhatsApp'
    }
  },
  {
    id: 'fidelizacao',
    nome: '⭐ Fidelização',
    icon: '🎖️',
    campos: {
      nome: 'Programa Cliente VIP',
      oferta: 'Descontos exclusivos para nossos clientes mais fiéis!',
      objetivo: 'Fortalecer relacionamento com clientes frequentes',
      publico_alvo: 'Clientes com múltiplas compras',
      canal_preferido: 'WhatsApp'
    }
  },
  {
    id: 'sazonal',
    nome: '🎄 Campanha Sazonal',
    icon: '📅',
    campos: {
      nome: 'Especial [OCASIÃO]',
      oferta: 'Produtos especiais para [OCASIÃO] com preços imperdíveis!',
      objetivo: 'Aproveitar datas comemorativas',
      publico_alvo: 'Todos os clientes',
      canal_preferido: 'WhatsApp + Redes Sociais'
    }
  }
]

// 🎯 Tipos de campanhas automáticas disponíveis pela Camila
const CAMPAIGN_TYPES = [
  {
    id: 'CAMPANHA_B2B',
    title: '🏢 Campanha B2B',
    description: 'Gera propostas comerciais, cupons B2B e agendamento de follow-up para empresas',
    actions: ['Proposta comercial', 'Cupom desconto', 'Follow-up telefônico']
  },
  {
    id: 'APRESENTAR_B2B',
    title: '📋 Apresentação B2B',
    description: 'Envia catálogo empresarial e agenda apresentação comercial',
    actions: ['Catálogo B2B', 'Agendamento apresentação']
  },
  {
    id: 'EVENTO_EXPRESS',
    title: '⚡ Evento Express',
    description: 'Orçamento rápido e checklist para eventos pequenos',
    actions: ['Orçamento automático', 'Checklist evento', 'Confirmação']
  },
  {
    id: 'PLANEJAMENTO_EVENTO',
    title: '🎉 Planejamento de Evento',
    description: 'Proposta detalhada, cronograma e acompanhamento para eventos grandes',
    actions: ['Proposta evento', 'Cronograma', 'Acompanhamento', 'Lembretes']
  },
  {
    id: 'CLIENTE_PREMIUM',
    title: '⭐ Cliente Premium',
    description: 'Cupom VIP, programa de pontos e atendimento exclusivo',
    actions: ['Cupom VIP', 'Programa pontos', 'Atendimento exclusivo']
  },
  {
    id: 'BEM_VINDO',
    title: '👋 Boas-vindas',
    description: 'Cupom primeira compra, guia de produtos e newsletter',
    actions: ['Cupom boas-vindas', 'Guia produtos', 'Newsletter']
  },
  {
    id: 'NEWSLETTER_OFERTAS',
    title: '📧 Newsletter',
    description: 'Cadastro automático em ofertas e promoções semanais',
    actions: ['Newsletter automática', 'Ofertas personalizadas']
  },
  {
    id: 'OFERTAS_CONTEXTUAIS',
    title: '🎯 Ofertas Contextuais',
    description: 'Ofertas baseadas no contexto da conversa e interesses do cliente',
    actions: ['Ofertas personalizadas', 'Cupons contextuais']
  }
]

interface AutomationSettings {
  enabled: boolean
  selectedCampaigns: string[]
  globalSettings: {
    processAllMessages: boolean
    onlyHighScore: boolean
    scoreThreshold: number
  }
}

export function CampaignsManager() {
  const { data: campaigns, isLoading } = useCampaigns()
  const { data: activeCampaigns } = useActiveCampaigns()
  const createCampaign = useCreateCampaign()
  
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingCampaign, setEditingCampaign] = useState<CampanhaMarketing | null>(null)
  const [formData, setFormData] = useState<FormData>({
    nome: '',
    produtos: '',
    oferta: '',
    data_inicio: '',
    data_fim: '',
    segmento: '',
    tipo_campanha: '',
    publico_alvo: '',
    objetivo: '',
    canal_preferido: 'WhatsApp',
    segmentacao_score: 'todos',
    segmentacao_tipo: 'todos',
    segmentacao_frequencia: 'todos',
    segmentacao_interesse: 'geral'
  })
  const [jsonError, setJsonError] = useState<string>('')
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [showPreview, setShowPreview] = useState<boolean>(false)
  
  // 🤖 Estados para automação de campanhas
  const [automationSettings, setAutomationSettings] = useState<AutomationSettings>({
    enabled: true,
    selectedCampaigns: ['CAMPANHA_B2B', 'BEM_VINDO', 'CLIENTE_PREMIUM'],
    globalSettings: {
      processAllMessages: true,
      onlyHighScore: false,
      scoreThreshold: 5
    }
  })
  
  const [activeTab, setActiveTab] = useState('campaigns')
  const [selectedCampaignType, setSelectedCampaignType] = useState('')

  // 🔧 Funções para automação
  const handleAutomationToggle = (enabled: boolean) => {
    setAutomationSettings(prev => ({
      ...prev,
      enabled
    }))
    console.log('🤖 Automação de campanhas:', enabled ? 'ATIVADA' : 'DESATIVADA')
  }

  const handleCampaignTypeToggle = (campaignId: string, enabled: boolean) => {
    setAutomationSettings(prev => ({
      ...prev,
      selectedCampaigns: enabled 
        ? [...prev.selectedCampaigns, campaignId]
        : prev.selectedCampaigns.filter(id => id !== campaignId)
    }))
    console.log(`🎯 Campanha ${campaignId}:`, enabled ? 'ATIVADA' : 'DESATIVADA')
  }

  const handleCampaignTypeSelect = (typeId: string) => {
    const selectedType = CAMPAIGN_TYPES.find(type => type.id === typeId)
    if (selectedType) {
      setSelectedCampaignType(typeId)
      setFormData(prev => ({
        ...prev,
        nome: selectedType.title,
        tipo_campanha: typeId,
        segmento: JSON.stringify({
          "tipo_campanha": typeId,
          "automatica": true
        }, null, 2)
      }))
    }
  }

  // 📝 Função para aplicar template
  const handleTemplateSelect = (templateId: string) => {
    const template = CAMPAIGN_TEMPLATES.find(t => t.id === templateId)
    if (template) {
      setSelectedTemplate(templateId)
      setFormData(prev => ({
        ...prev,
        nome: template.campos.nome,
        oferta: template.campos.oferta,
        objetivo: template.campos.objetivo,
        publico_alvo: template.campos.publico_alvo,
        canal_preferido: template.campos.canal_preferido,
        tipo_campanha: templateId
      }))
    }
  }

  // � Função para gerar JSON automaticamente a partir das opções simples
  const generateSegmentationJson = () => {
    const segmentacao: any = {}
    
    if (formData.segmentacao_score !== 'todos') {
      segmentacao.lead_score = formData.segmentacao_score
    }
    
    if (formData.segmentacao_tipo !== 'todos') {
      segmentacao.tipo_cliente = formData.segmentacao_tipo
    }
    
    if (formData.segmentacao_frequencia !== 'todos') {
      segmentacao.frequencia = formData.segmentacao_frequencia
    }
    
    if (formData.segmentacao_interesse !== 'geral') {
      segmentacao.interesse = formData.segmentacao_interesse
    }
    
    // Adiciona campos extras se preenchidos
    if (formData.tipo_campanha) {
      segmentacao.tipo_campanha = formData.tipo_campanha
    }
    
    if (formData.publico_alvo) {
      segmentacao.publico_alvo = formData.publico_alvo
    }
    
    if (formData.objetivo) {
      segmentacao.objetivo = formData.objetivo
    }
    
    if (formData.canal_preferido) {
      segmentacao.canal_preferido = formData.canal_preferido
    }
    
    return JSON.stringify(segmentacao, null, 2)
  }

  // �👁️ Função para toggle do preview
  const togglePreview = () => {
    setShowPreview(!showPreview)
  }

  const resetForm = () => {
    setFormData({
      nome: '',
      produtos: '',
      oferta: '',
      data_inicio: '',
      data_fim: '',
      segmento: '',
      tipo_campanha: '',
      publico_alvo: '',
      objetivo: '',
      canal_preferido: 'WhatsApp',
      segmentacao_score: 'todos',
      segmentacao_tipo: 'todos',
      segmentacao_frequencia: 'todos',
      segmentacao_interesse: 'geral'
    })
    setJsonError('')
    setEditingCampaign(null)
    setSelectedCampaignType('')
    setSelectedTemplate('')
    setShowPreview(false)
  }

  const validateJson = (jsonString: string): boolean => {
    if (!jsonString.trim()) return true // JSON vazio é válido
    
    try {
      JSON.parse(jsonString)
      setJsonError('')
      return true
    } catch (error) {
      setJsonError('JSON inválido. Verifique a sintaxe.')
      return false
    }
  }

  const handleSegmentoChange = (value: string) => {
    setFormData({...formData, segmento: value})
    if (value.trim()) {
      validateJson(value)
    } else {
      setJsonError('')
    }
  }

  const formatDateForInput = (dateString: string): string => {
    const date = new Date(dateString)
    return date.toISOString().slice(0, 16)
  }

  const handleEdit = (campaign: CampanhaMarketing) => {
    setEditingCampaign(campaign)
    setFormData({
      nome: campaign.nome,
      produtos: campaign.produtos.join(', '),
      oferta: campaign.oferta,
      data_inicio: formatDateForInput(campaign.data_inicio),
      data_fim: formatDateForInput(campaign.data_fim),
      segmento: typeof campaign.segmento === 'object' ? JSON.stringify(campaign.segmento, null, 2) : campaign.segmento || '',
      tipo_campanha: (campaign.segmento as any)?.tipo_campanha || '',
      publico_alvo: (campaign.segmento as any)?.publico_alvo || '',
      objetivo: (campaign.segmento as any)?.objetivo || '',
      canal_preferido: (campaign.segmento as any)?.canal_preferido || 'WhatsApp',
      segmentacao_score: (campaign.segmento as any)?.lead_score || 'todos',
      segmentacao_tipo: (campaign.segmento as any)?.tipo_cliente || 'todos',
      segmentacao_frequencia: (campaign.segmento as any)?.frequencia || 'todos',
      segmentacao_interesse: (campaign.segmento as any)?.interesse || 'geral'
    })
    setIsDialogOpen(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validações
    if (!formData.nome.trim()) {
      alert('Nome da campanha é obrigatório')
      return
    }
    
    if (!formData.produtos.trim()) {
      alert('Produtos são obrigatórios')
      return
    }
    
    if (!formData.oferta.trim()) {
      alert('Oferta é obrigatória')
      return
    }
    
    if (new Date(formData.data_inicio) >= new Date(formData.data_fim)) {
      alert('Data de início deve ser anterior à data de fim')
      return
    }
    
    if (formData.segmento.trim() && !validateJson(formData.segmento)) {
      return
    }
    
    try {
      // Gera JSON automaticamente se não foi preenchido manualmente
      const segmentoFinal = formData.segmento.trim() || generateSegmentationJson()
      const segmentoJson = segmentoFinal ? JSON.parse(segmentoFinal) : {}
      
      await createCampaign.mutateAsync({
        nome: formData.nome.trim(),
        produtos: formData.produtos.split(',').map(p => p.trim()).filter(p => p),
        oferta: formData.oferta.trim(),
        data_inicio: formData.data_inicio,
        data_fim: formData.data_fim,
        segmento: segmentoJson
      })
      
      setIsDialogOpen(false)
      resetForm()
    } catch (error) {
      console.error('Erro ao criar campanha:', error)
      alert('Erro ao criar campanha. Tente novamente.')
    }
  }

  const handleDelete = async (campaignId: string) => {
    // Por enquanto apenas um console.log, pois não temos o hook de delete ainda
    console.log('Deletar campanha:', campaignId)
    alert('Funcionalidade de exclusão será implementada em breve')
  }

  const isActive = (campaign: CampanhaMarketing) => {
    const now = new Date()
    const inicio = new Date(campaign.data_inicio)
    const fim = new Date(campaign.data_fim)
    return now >= inicio && now <= fim
  }

  const formatDateRange = (inicio: string, fim: string) => {
    const startDate = new Date(inicio)
    const endDate = new Date(fim)
    
    const options: Intl.DateTimeFormatOptions = {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }
    
    return `${startDate.toLocaleDateString('pt-BR', options)} - ${endDate.toLocaleDateString('pt-BR', options)}`
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 animate-spin" />
            Carregando campanhas...
          </CardTitle>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Campanhas de Marketing
          </CardTitle>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Zap className={`h-4 w-4 ${automationSettings.enabled ? 'text-green-500' : 'text-gray-400'}`} />
              <span className="text-sm">Automação</span>
              <Switch 
                checked={automationSettings.enabled}
                onCheckedChange={handleAutomationToggle}
              />
            </div>
            
            <Dialog open={isDialogOpen} onOpenChange={(open) => {
              setIsDialogOpen(open)
              if (!open) resetForm()
            }}>
              <DialogTrigger asChild>
                <Button className="bg-orange-500 hover:bg-orange-600">
                  <Plus className="h-4 w-4 mr-2" />
                  Nova Campanha
                </Button>
              </DialogTrigger>
            
            <DialogContent className="w-[95vw] max-w-[1600px] h-[92vh] max-h-[92vh] overflow-hidden p-0 m-0">
              <div className="h-full flex flex-col">
                <DialogHeader className="px-6 py-4 border-b bg-white flex-shrink-0">
                  <DialogTitle className="flex items-center gap-2 text-xl font-semibold">
                    {editingCampaign ? (
                      <>
                        <Edit className="h-5 w-5 text-orange-500" />
                        Editar Campanha
                      </>
                    ) : (
                      <>
                        <Plus className="h-5 w-5 text-orange-500" />
                        Criar Nova Campanha
                      </>
                    )}
                  </DialogTitle>
                </DialogHeader>
                
                <div className="flex-1 flex overflow-hidden">
                  {/* Coluna Principal - Formulário */}
                  <div className="flex-1 overflow-y-auto px-6 py-4">
                    <div className="space-y-8">
                      {!editingCampaign && (
                        <div className="space-y-4">
                          <Label className="text-lg font-semibold text-gray-800">🎯 Escolha um Template (Opcional)</Label>
                          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                            {CAMPAIGN_TEMPLATES.map((template) => (
                              <div
                                key={template.id}
                                onClick={() => handleTemplateSelect(template.id)}
                                className={`p-4 border-2 rounded-xl cursor-pointer transition-all hover:shadow-lg hover:scale-105 ${
                                  selectedTemplate === template.id 
                                    ? 'border-orange-500 bg-orange-50 shadow-md' 
                                    : 'border-gray-200 hover:border-orange-300 bg-white'
                                }`}
                              >
                                <div className="flex flex-col items-center gap-3 text-center">
                                  <span className="text-3xl">{template.icon}</span>
                                  <span className="font-semibold text-sm text-gray-700 leading-tight">{template.nome}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <form onSubmit={handleSubmit} className="space-y-8">
                        {/* Informações Básicas */}
                        <div className="space-y-6 p-6 border border-gray-200 rounded-xl bg-gradient-to-br from-blue-50 to-indigo-50 shadow-sm">
                          <h3 className="font-semibold flex items-center gap-3 text-xl text-gray-800 border-b border-blue-200 pb-3">
                            📝 Informações Básicas
                          </h3>
                          
                          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                            <div className="space-y-3">
                              <Label htmlFor="nome" className="text-sm font-semibold text-gray-700">Nome da Campanha *</Label>
                              <Input
                                id="nome"
                                value={formData.nome}
                                onChange={(e) => setFormData({...formData, nome: e.target.value})}
                                placeholder="Ex: Promoção Queijos Premium"
                                required
                                className="h-11 border-gray-300 focus:border-orange-500 focus:ring-orange-500"
                              />
                            </div>
                            
                            <div className="space-y-3">
                              <Label htmlFor="tipo_campanha" className="text-sm font-semibold text-gray-700">Tipo de Campanha</Label>
                              <Select value={formData.tipo_campanha} onValueChange={(value) => setFormData({...formData, tipo_campanha: value})}>
                                <SelectTrigger className="h-11 border-gray-300 focus:border-orange-500">
                                  <SelectValue placeholder="Selecione o tipo" />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="promocional">🏷️ Promocional</SelectItem>
                                  <SelectItem value="lancamento">🚀 Lançamento</SelectItem>
                                  <SelectItem value="reativacao">🔄 Reativação</SelectItem>
                                  <SelectItem value="fidelizacao">⭐ Fidelização</SelectItem>
                                  <SelectItem value="sazonal">🎄 Sazonal</SelectItem>
                                  <SelectItem value="personalizada">🎨 Personalizada</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                            
                            <div className="space-y-3 lg:col-span-2 xl:col-span-1">
                              <Label htmlFor="produtos" className="text-sm font-semibold text-gray-700">Produtos (separados por vírgula) *</Label>
                              <Input
                                id="produtos"
                                value={formData.produtos}
                                onChange={(e) => setFormData({...formData, produtos: e.target.value})}
                                placeholder="Ex: queijo, presunto, salame"
                                required
                                className="h-11 border-gray-300 focus:border-orange-500 focus:ring-orange-500"
                              />
                            </div>
                          </div>
                        </div>

                        {/* Oferta e Objetivo */}
                        <div className="space-y-6 p-6 border border-gray-200 rounded-xl bg-gradient-to-br from-green-50 to-emerald-50 shadow-sm">
                          <h3 className="font-semibold flex items-center gap-3 text-xl text-gray-800 border-b border-green-200 pb-3">
                            🎯 Oferta e Objetivo
                          </h3>
                          
                          <div className="space-y-6">
                            <div className="space-y-3">
                              <Label htmlFor="oferta" className="text-sm font-semibold text-gray-700">Oferta *</Label>
                              <Textarea
                                id="oferta"
                                value={formData.oferta}
                                onChange={(e) => setFormData({...formData, oferta: e.target.value})}
                                placeholder="Ex: 20% de desconto em todos os queijos premium"
                                required
                                rows={4}
                                className="resize-none border-gray-300 focus:border-green-500 focus:ring-green-500 text-sm"
                              />
                            </div>
                            
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                              <div className="space-y-3">
                                <Label htmlFor="objetivo" className="text-sm font-semibold text-gray-700">Objetivo da Campanha</Label>
                                <Input
                                  id="objetivo"
                                  value={formData.objetivo}
                                  onChange={(e) => setFormData({...formData, objetivo: e.target.value})}
                                  placeholder="Ex: Aumentar vendas de queijos"
                                  className="h-11 border-gray-300 focus:border-green-500 focus:ring-green-500"
                                />
                              </div>
                              
                              <div className="space-y-3">
                                <Label htmlFor="canal_preferido" className="text-sm font-semibold text-gray-700">Canal Preferido</Label>
                                <Select value={formData.canal_preferido} onValueChange={(value) => setFormData({...formData, canal_preferido: value})}>
                                  <SelectTrigger className="h-11 border-gray-300 focus:border-green-500">
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="WhatsApp">📱 WhatsApp</SelectItem>
                                    <SelectItem value="Newsletter">📧 Newsletter</SelectItem>
                                    <SelectItem value="WhatsApp + Newsletter">📱📧 WhatsApp + Newsletter</SelectItem>
                                    <SelectItem value="Redes Sociais">📱 Redes Sociais</SelectItem>
                                    <SelectItem value="Todos">🌐 Todos os Canais</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Período e Público */}
                        <div className="space-y-6 p-6 border border-gray-200 rounded-xl bg-gradient-to-br from-purple-50 to-pink-50 shadow-sm">
                          <h3 className="font-semibold flex items-center gap-3 text-xl text-gray-800 border-b border-purple-200 pb-3">
                            🗓️ Período e Público
                          </h3>
                          
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <div className="space-y-3">
                              <Label htmlFor="data_inicio" className="text-sm font-semibold text-gray-700">Data de Início *</Label>
                              <Input
                                id="data_inicio"
                                type="datetime-local"
                                value={formData.data_inicio}
                                onChange={(e) => setFormData({...formData, data_inicio: e.target.value})}
                                required
                                className="h-11 border-gray-300 focus:border-purple-500 focus:ring-purple-500"
                              />
                            </div>
                            
                            <div className="space-y-3">
                              <Label htmlFor="data_fim" className="text-sm font-semibold text-gray-700">Data de Fim *</Label>
                              <Input
                                id="data_fim"
                                type="datetime-local"
                                value={formData.data_fim}
                                onChange={(e) => setFormData({...formData, data_fim: e.target.value})}
                                required
                                className="h-11 border-gray-300 focus:border-purple-500 focus:ring-purple-500"
                              />
                            </div>
                          </div>
                          
                          <div className="space-y-3">
                            <Label htmlFor="publico_alvo" className="text-sm font-semibold text-gray-700">Público Alvo</Label>
                            <Input
                              id="publico_alvo"
                              value={formData.publico_alvo}
                              onChange={(e) => setFormData({...formData, publico_alvo: e.target.value})}
                              placeholder="Ex: Clientes interessados em queijos premium"
                              className="h-11 border-gray-300 focus:border-purple-500 focus:ring-purple-500"
                            />
                          </div>
                        </div>

                        {/* Segmentação Simplificada */}
                        <div className="space-y-6 p-6 border border-gray-200 rounded-xl bg-gradient-to-br from-yellow-50 to-orange-50 shadow-sm">
                          <h3 className="font-semibold flex items-center gap-3 text-xl text-gray-800 border-b border-yellow-200 pb-3">
                            🎯 Quem Receberá a Campanha (Simples e Fácil)
                          </h3>
                          
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                            {/* Score dos Leads */}
                            <div className="space-y-4">
                              <Label className="font-semibold text-gray-700 text-base flex items-center gap-2">
                                📊 Nível de Interesse
                              </Label>
                              <div className="space-y-3 bg-white p-4 rounded-lg border border-yellow-200">
                                {SEGMENTATION_OPTIONS.lead_score.map((option) => (
                                  <div key={option.value} className="flex items-start gap-3 p-2 hover:bg-gray-50 rounded transition-colors">
                                    <input
                                      type="radio"
                                      id={`score_${option.value}`}
                                      name="segmentacao_score"
                                      value={option.value}
                                      checked={formData.segmentacao_score === option.value}
                                      onChange={(e) => setFormData({...formData, segmentacao_score: e.target.value})}
                                      className="mt-1 w-4 h-4 text-orange-600 focus:ring-orange-500"
                                    />
                                    <label htmlFor={`score_${option.value}`} className="flex-1 cursor-pointer">
                                      <div className="font-medium text-sm text-gray-900">{option.label}</div>
                                      <div className="text-xs text-gray-600 mt-1">{option.description}</div>
                                    </label>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {/* Tipo de Cliente */}
                            <div className="space-y-4">
                              <Label className="font-semibold text-gray-700 text-base flex items-center gap-2">
                                👥 Tipo de Cliente
                              </Label>
                              <div className="space-y-3 bg-white p-4 rounded-lg border border-yellow-200">
                                {SEGMENTATION_OPTIONS.tipo_cliente.map((option) => (
                                  <div key={option.value} className="flex items-start gap-3 p-2 hover:bg-gray-50 rounded transition-colors">
                                    <input
                                      type="radio"
                                      id={`tipo_${option.value}`}
                                      name="segmentacao_tipo"
                                      value={option.value}
                                      checked={formData.segmentacao_tipo === option.value}
                                      onChange={(e) => setFormData({...formData, segmentacao_tipo: e.target.value})}
                                      className="mt-1 w-4 h-4 text-orange-600 focus:ring-orange-500"
                                    />
                                    <label htmlFor={`tipo_${option.value}`} className="flex-1 cursor-pointer">
                                      <div className="font-medium text-sm text-gray-900">{option.label}</div>
                                      <div className="text-xs text-gray-600 mt-1">{option.description}</div>
                                    </label>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {/* Frequência */}
                            <div className="space-y-4">
                              <Label className="font-semibold text-gray-700 text-base flex items-center gap-2">
                                🔄 Frequência de Compra
                              </Label>
                              <div className="space-y-3 bg-white p-4 rounded-lg border border-yellow-200">
                                {SEGMENTATION_OPTIONS.frequencia.map((option) => (
                                  <div key={option.value} className="flex items-start gap-3 p-2 hover:bg-gray-50 rounded transition-colors">
                                    <input
                                      type="radio"
                                      id={`freq_${option.value}`}
                                      name="segmentacao_frequencia"
                                      value={option.value}
                                      checked={formData.segmentacao_frequencia === option.value}
                                      onChange={(e) => setFormData({...formData, segmentacao_frequencia: e.target.value})}
                                      className="mt-1 w-4 h-4 text-orange-600 focus:ring-orange-500"
                                    />
                                    <label htmlFor={`freq_${option.value}`} className="flex-1 cursor-pointer">
                                      <div className="font-medium text-sm text-gray-900">{option.label}</div>
                                      <div className="text-xs text-gray-600 mt-1">{option.description}</div>
                                    </label>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {/* Interesse */}
                            <div className="space-y-4">
                              <Label className="font-semibold text-gray-700 text-base flex items-center gap-2">
                                🛒 Interesse em Produtos
                              </Label>
                              <div className="space-y-3 bg-white p-4 rounded-lg border border-yellow-200">
                                {SEGMENTATION_OPTIONS.interesse.map((option) => (
                                  <div key={option.value} className="flex items-start gap-3 p-2 hover:bg-gray-50 rounded transition-colors">
                                    <input
                                      type="radio"
                                      id={`int_${option.value}`}
                                      name="segmentacao_interesse"
                                      value={option.value}
                                      checked={formData.segmentacao_interesse === option.value}
                                      onChange={(e) => setFormData({...formData, segmentacao_interesse: e.target.value})}
                                      className="mt-1 w-4 h-4 text-orange-600 focus:ring-orange-500"
                                    />
                                    <label htmlFor={`int_${option.value}`} className="flex-1 cursor-pointer">
                                      <div className="font-medium text-sm text-gray-900">{option.label}</div>
                                      <div className="text-xs text-gray-600 mt-1">{option.description}</div>
                                    </label>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>

                          {/* Configuração Manual (Avançado) */}
                          <details className="mt-6">
                            <summary className="cursor-pointer text-sm font-semibold text-gray-700 hover:text-orange-600 transition-colors p-3 bg-white rounded-lg border border-yellow-200">
                              ⚙️ Configuração Manual (Avançado - JSON)
                            </summary>
                            <div className="mt-4 space-y-3 p-4 bg-white rounded-lg border border-gray-200">
                              <Label htmlFor="segmento" className="text-sm font-semibold text-gray-700">Configuração de Segmento (JSON)</Label>
                              <Textarea
                                id="segmento"
                                value={formData.segmento}
                                onChange={(e) => handleSegmentoChange(e.target.value)}
                                placeholder='Deixe vazio para usar as seleções acima automaticamente'
                                className="font-mono text-sm resize-none border-gray-300 focus:border-orange-500 focus:ring-orange-500"
                                rows={4}
                              />
                              {jsonError && (
                                <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                                  {jsonError}
                                </div>
                              )}
                              <p className="text-xs text-gray-500 bg-gray-50 p-3 rounded-lg border">
                                💡 Se deixar em branco, será gerado automaticamente com base nas suas seleções acima
                              </p>
                            </div>
                          </details>
                        </div>
                        
                        {/* Botões de Ação */}
                        <div className="flex flex-col sm:flex-row justify-end gap-4 pt-6 border-t border-gray-200">
                          <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)} className="h-11 px-6 font-medium">
                            Cancelar
                          </Button>
                          {!showPreview && (
                            <Button type="button" variant="outline" onClick={togglePreview} className="h-11 px-6 font-medium">
                              👁️ Preview
                            </Button>
                          )}
                          <Button 
                            type="submit" 
                            disabled={createCampaign.isPending || !!jsonError}
                            className="bg-orange-500 hover:bg-orange-600 h-11 px-8 font-semibold shadow-lg hover:shadow-xl transition-all"
                          >
                            {createCampaign.isPending ? 'Salvando...' : editingCampaign ? 'Atualizar' : 'Criar Campanha'}
                          </Button>
                        </div>
                      </form>
                    </div>
                  </div>

                  {/* Coluna Direita - Preview */}
                  <div className="w-80 xl:w-96 flex-shrink-0 border-l border-gray-200 bg-gray-50">
                    <div className="sticky top-0 h-full overflow-y-auto p-6">
                      <div className="space-y-6">
                        <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm">
                          <h3 className="font-semibold mb-6 flex items-center gap-3 text-xl text-gray-800 border-b border-gray-200 pb-4">
                            👁️ Preview da Campanha
                          </h3>
                          
                          <div className="space-y-5">
                            <div className="space-y-2">
                              <span className="font-semibold text-gray-600 text-sm uppercase tracking-wide">Nome:</span>
                              <p className="text-gray-900 font-medium break-words bg-gray-50 p-3 rounded-lg border">
                                {formData.nome || 'Não definido'}
                              </p>
                            </div>
                            
                            <div className="space-y-2">
                              <span className="font-semibold text-gray-600 text-sm uppercase tracking-wide">Tipo:</span>
                              <p className="text-gray-900 bg-gray-50 p-3 rounded-lg border">
                                {formData.tipo_campanha || 'Não definido'}
                              </p>
                            </div>
                            
                            <div className="space-y-2">
                              <span className="font-semibold text-gray-600 text-sm uppercase tracking-wide">Produtos:</span>
                              <p className="text-gray-900 break-words bg-gray-50 p-3 rounded-lg border">
                                {formData.produtos || 'Não definido'}
                              </p>
                            </div>
                            
                            <div className="space-y-2">
                              <span className="font-semibold text-gray-600 text-sm uppercase tracking-wide">Oferta:</span>
                              <p className="text-gray-900 break-words bg-gray-50 p-3 rounded-lg border leading-relaxed">
                                {formData.oferta || 'Não definida'}
                              </p>
                            </div>
                            
                            <div className="space-y-2">
                              <span className="font-semibold text-gray-600 text-sm uppercase tracking-wide">Público:</span>
                              <p className="text-gray-900 break-words bg-gray-50 p-3 rounded-lg border">
                                {formData.publico_alvo || 'Não definido'}
                              </p>
                            </div>
                            
                            <div className="space-y-2">
                              <span className="font-semibold text-gray-600 text-sm uppercase tracking-wide">Canal:</span>
                              <p className="text-gray-900 bg-gray-50 p-3 rounded-lg border">
                                {formData.canal_preferido}
                              </p>
                            </div>
                            
                            {/* Resumo da Segmentação */}
                            <div className="pt-4 border-t border-gray-200">
                              <span className="font-semibold text-gray-600 text-sm uppercase tracking-wide">🎯 Vai para:</span>
                              <div className="text-sm space-y-2 mt-3 bg-orange-50 p-4 rounded-lg border border-orange-200">
                                <p className="flex items-center gap-2">
                                  <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
                                  📊 {SEGMENTATION_OPTIONS.lead_score.find(opt => opt.value === formData.segmentacao_score)?.label}
                                </p>
                                <p className="flex items-center gap-2">
                                  <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
                                  👥 {SEGMENTATION_OPTIONS.tipo_cliente.find(opt => opt.value === formData.segmentacao_tipo)?.label}
                                </p>
                                <p className="flex items-center gap-2">
                                  <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
                                  🔄 {SEGMENTATION_OPTIONS.frequencia.find(opt => opt.value === formData.segmentacao_frequencia)?.label}
                                </p>
                                <p className="flex items-center gap-2">
                                  <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
                                  🛒 {SEGMENTATION_OPTIONS.interesse.find(opt => opt.value === formData.segmentacao_interesse)?.label}
                                </p>
                              </div>
                            </div>
                            
                            {formData.data_inicio && formData.data_fim && (
                              <div className="space-y-2">
                                <span className="font-semibold text-gray-600 text-sm uppercase tracking-wide">Período:</span>
                                <p className="text-gray-900 text-sm bg-gray-50 p-3 rounded-lg border">
                                  {new Date(formData.data_inicio).toLocaleDateString('pt-BR')} até {new Date(formData.data_fim).toLocaleDateString('pt-BR')}
                                </p>
                              </div>
                            )}
                          </div>
                          
                          {formData.nome && formData.oferta && (
                            <div className="mt-6 p-4 bg-gradient-to-r from-orange-50 to-orange-100 border border-orange-200 rounded-xl shadow-sm">
                              <p className="text-sm font-semibold text-orange-800 mb-3 flex items-center gap-2">
                                💬 Mensagem de exemplo:
                              </p>
                              <div className="bg-white p-4 rounded-lg border-l-4 border-l-orange-500 shadow-sm">
                                <p className="text-sm leading-relaxed">
                                  🎯 <strong className="text-gray-900">{formData.nome}</strong><br/>
                                  <span className="text-gray-700">{formData.oferta}</span><br/>
                                  <span className="text-orange-600 font-medium">📱 Responda para saber mais!</span>
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </DialogContent>
          </Dialog>
          </div>
        </div>
        
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span>{activeCampaigns?.length || 0} Ativas</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
            <span>{campaigns?.length || 0} Total</span>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${automationSettings.enabled ? 'bg-orange-500' : 'bg-red-500'}`}></div>
            <span>{automationSettings.selectedCampaigns.length} Automações Ativas</span>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="campaigns">📋 Campanhas</TabsTrigger>
            <TabsTrigger value="automation" className="relative">
              <Settings className="h-4 w-4 mr-2" />
              🤖 Automação
              {automationSettings.enabled && (
                <div className="absolute -top-1 -right-1 w-2 h-2 bg-orange-500 rounded-full"></div>
              )}
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="automation" className="space-y-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg bg-gradient-to-r from-blue-50 to-indigo-50">
                <div>
                  <h3 className="font-medium">🤖 Automação de Campanhas da Camila</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Permite que a Camila execute automaticamente campanhas baseadas nas conversas dos clientes
                  </p>
                </div>
                <Switch 
                  checked={automationSettings.enabled}
                  onCheckedChange={handleAutomationToggle}
                />
              </div>
              
              {automationSettings.enabled && (
                <>
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-medium mb-3">⚙️ Configurações Globais</h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <Label>Processar todas as mensagens</Label>
                        <Switch 
                          checked={automationSettings.globalSettings.processAllMessages}
                          onCheckedChange={(checked) => 
                            setAutomationSettings(prev => ({
                              ...prev,
                              globalSettings: { ...prev.globalSettings, processAllMessages: checked }
                            }))
                          }
                        />
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <Label>Apenas leads com score alto</Label>
                        <Switch 
                          checked={automationSettings.globalSettings.onlyHighScore}
                          onCheckedChange={(checked) => 
                            setAutomationSettings(prev => ({
                              ...prev,
                              globalSettings: { ...prev.globalSettings, onlyHighScore: checked }
                            }))
                          }
                        />
                      </div>
                      
                      {automationSettings.globalSettings.onlyHighScore && (
                        <div className="flex items-center gap-4">
                          <Label>Score mínimo:</Label>
                          <Input
                            type="number"
                            min="1"
                            max="10"
                            value={automationSettings.globalSettings.scoreThreshold}
                            onChange={(e) => 
                              setAutomationSettings(prev => ({
                                ...prev,
                                globalSettings: { ...prev.globalSettings, scoreThreshold: parseInt(e.target.value) }
                              }))
                            }
                            className="w-20"
                          />
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-medium mb-3">🎯 Tipos de Campanha Automática</h4>
                    <div className="space-y-3">
                      {CAMPAIGN_TYPES.map((campaignType) => (
                        <div key={campaignType.id} className="flex items-start gap-3 p-3 border rounded hover:bg-gray-50 transition-colors">
                          <Switch 
                            checked={automationSettings.selectedCampaigns.includes(campaignType.id)}
                            onCheckedChange={(checked) => handleCampaignTypeToggle(campaignType.id, checked)}
                          />
                          <div className="flex-1">
                            <h5 className="font-medium text-sm">{campaignType.title}</h5>
                            <p className="text-xs text-gray-600 mt-1">{campaignType.description}</p>
                            <div className="flex flex-wrap gap-1 mt-2">
                              {campaignType.actions.map((action, index) => (
                                <Badge key={index} variant="outline" className="text-xs">
                                  {action}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          </TabsContent>
          
          <TabsContent value="campaigns">
        <div className="space-y-4">
          {campaigns && campaigns.length > 0 ? (
            campaigns.map((campaign) => (
              <div
                key={campaign.id}
                className={`p-4 border rounded-lg transition-all hover:shadow-md ${
                  isActive(campaign) 
                    ? 'border-green-300 bg-green-50' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg">{campaign.nome}</h3>
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      {isActive(campaign) ? (
                        <Badge className="bg-green-500 text-white">Ativa</Badge>
                      ) : (
                        <Badge variant="secondary">Inativa</Badge>
                      )}
                      {(campaign.segmento as any)?.automatica && (
                        <Badge className="bg-orange-500 text-white">
                          <Zap className="h-3 w-3 mr-1" />
                          🤖 Automática
                        </Badge>
                      )}
                      <span className="text-sm text-gray-600">
                        {campaign.produtos.join(', ')}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleEdit(campaign)}
                      className="hover:bg-blue-50"
                    >
                      <Edit className="h-3 w-3" />
                    </Button>
                    
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="outline" size="sm" className="text-red-600 hover:bg-red-50">
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Excluir Campanha</AlertDialogTitle>
                          <AlertDialogDescription>
                            Tem certeza que deseja excluir a campanha &quot;{campaign.nome}&quot;?
                            Esta ação não pode ser desfeita.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancelar</AlertDialogCancel>
                          <AlertDialogAction 
                            onClick={() => handleDelete(campaign.id)}
                            className="bg-red-600 hover:bg-red-700"
                          >
                            Excluir
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </div>
                
                <p className="text-sm text-gray-700 mb-3 leading-relaxed">{campaign.oferta}</p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-gray-600">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3 w-3 flex-shrink-0" />
                    <span className="truncate">
                      {formatDateRange(campaign.data_inicio, campaign.data_fim)}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-1">
                    <Users className="h-3 w-3 flex-shrink-0" />
                    <span className="truncate">
                      Segmento: {Object.keys(campaign.segmento).length > 0 
                        ? JSON.stringify(campaign.segmento) 
                        : 'Todos os leads'}
                    </span>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-12 text-gray-500">
              <Target className="h-16 w-16 mx-auto mb-4 opacity-30" />
              <h3 className="text-lg font-medium mb-2">Nenhuma campanha criada</h3>
              <p className="text-sm mb-4">Crie sua primeira campanha de marketing para começar</p>
              <Button 
                onClick={() => setIsDialogOpen(true)}
                className="bg-orange-500 hover:bg-orange-600"
              >
                <Plus className="h-4 w-4 mr-2" />
                Criar Primeira Campanha
              </Button>
            </div>
          )}
        </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}