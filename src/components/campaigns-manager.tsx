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
            
            <DialogContent className="w-[95vw] max-w-[1400px] h-[90vh] max-h-[90vh] overflow-y-auto p-4 lg:p-6">
              <DialogHeader className="pb-4 lg:pb-6">
                <DialogTitle className="flex items-center gap-2 text-xl lg:text-2xl">
                  {editingCampaign ? (
                    <>
                      <Edit className="h-6 w-6" />
                      Editar Campanha
                    </>
                  ) : (
                    <>
                      <Plus className="h-6 w-6" />
                      Criar Nova Campanha
                    </>
                  )}
                </DialogTitle>
              </DialogHeader>
              
              <div className="flex flex-col lg:flex-row gap-6 lg:gap-8 h-full">
                {/* Coluna Principal - Formulário */}
                <div className="flex-1 min-w-0 space-y-6 overflow-y-auto">
                  {!editingCampaign && (
                    <div className="space-y-4">
                      <Label className="text-lg font-medium">🎯 Escolha um Template (Opcional)</Label>
                      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
                        {CAMPAIGN_TEMPLATES.map((template) => (
                          <div
                            key={template.id}
                            onClick={() => handleTemplateSelect(template.id)}
                            className={`p-3 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                              selectedTemplate === template.id 
                                ? 'border-orange-500 bg-orange-50' 
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                          >
                            <div className="flex flex-col items-center gap-2 text-center">
                              <span className="text-2xl">{template.icon}</span>
                              <span className="font-medium text-xs leading-tight">{template.nome}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Informações Básicas */}
                    <div className="space-y-4 p-4 lg:p-6 border rounded-lg bg-gradient-to-r from-blue-50 to-indigo-50">
                      <h3 className="font-medium flex items-center gap-2 text-lg">
                        📝 Informações Básicas
                      </h3>
                      
                      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="nome">Nome da Campanha *</Label>
                          <Input
                            id="nome"
                            value={formData.nome}
                            onChange={(e) => setFormData({...formData, nome: e.target.value})}
                            placeholder="Ex: Promoção Queijos Premium"
                            required
                            className="h-10"
                          />
                        </div>
                        
                        <div className="space-y-2">
                          <Label htmlFor="tipo_campanha">Tipo de Campanha</Label>
                          <Select value={formData.tipo_campanha} onValueChange={(value) => setFormData({...formData, tipo_campanha: value})}>
                            <SelectTrigger className="h-10">
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
                        
                        <div className="space-y-2 lg:col-span-2 xl:col-span-1">
                          <Label htmlFor="produtos">Produtos (separados por vírgula) *</Label>
                          <Input
                            id="produtos"
                            value={formData.produtos}
                            onChange={(e) => setFormData({...formData, produtos: e.target.value})}
                            placeholder="Ex: queijo, presunto, salame"
                            required
                            className="h-10"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Oferta e Objetivo */}
                    <div className="space-y-4 p-4 lg:p-6 border rounded-lg bg-gradient-to-r from-green-50 to-emerald-50">
                      <h3 className="font-medium flex items-center gap-2 text-lg">
                        🎯 Oferta e Objetivo
                      </h3>
                      
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="oferta">Oferta *</Label>
                          <Textarea
                            id="oferta"
                            value={formData.oferta}
                            onChange={(e) => setFormData({...formData, oferta: e.target.value})}
                            placeholder="Ex: 20% de desconto em todos os queijos premium"
                            required
                            rows={3}
                            className="resize-none"
                          />
                        </div>
                        
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="objetivo">Objetivo da Campanha</Label>
                            <Input
                              id="objetivo"
                              value={formData.objetivo}
                              onChange={(e) => setFormData({...formData, objetivo: e.target.value})}
                              placeholder="Ex: Aumentar vendas de queijos"
                              className="h-10"
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <Label htmlFor="canal_preferido">Canal Preferido</Label>
                            <Select value={formData.canal_preferido} onValueChange={(value) => setFormData({...formData, canal_preferido: value})}>
                              <SelectTrigger className="h-10">
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
                    <div className="space-y-4 p-4 lg:p-6 border rounded-lg bg-gradient-to-r from-purple-50 to-pink-50">
                      <h3 className="font-medium flex items-center gap-2 text-lg">
                        🗓️ Período e Público
                      </h3>
                      
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="data_inicio">Data de Início *</Label>
                          <Input
                            id="data_inicio"
                            type="datetime-local"
                            value={formData.data_inicio}
                            onChange={(e) => setFormData({...formData, data_inicio: e.target.value})}
                            required
                            className="h-10"
                          />
                        </div>
                        
                        <div className="space-y-2">
                          <Label htmlFor="data_fim">Data de Fim *</Label>
                          <Input
                            id="data_fim"
                            type="datetime-local"
                            value={formData.data_fim}
                            onChange={(e) => setFormData({...formData, data_fim: e.target.value})}
                            required
                            className="h-10"
                          />
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <Label htmlFor="publico_alvo">Público Alvo</Label>
                        <Input
                          id="publico_alvo"
                          value={formData.publico_alvo}
                          onChange={(e) => setFormData({...formData, publico_alvo: e.target.value})}
                          placeholder="Ex: Clientes interessados em queijos premium"
                          className="h-10"
                        />
                      </div>
                    </div>

                    {/* Segmentação Simplificada */}
                    <div className="space-y-4 p-4 lg:p-6 border rounded-lg bg-gradient-to-r from-yellow-50 to-orange-50">
                      <h3 className="font-medium flex items-center gap-2 text-lg">
                        🎯 Quem Receberá a Campanha (Simples e Fácil)
                      </h3>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                        {/* Score dos Leads */}
                        <div className="space-y-3">
                          <Label className="font-medium">📊 Nível de Interesse</Label>
                          <div className="space-y-2">
                            {SEGMENTATION_OPTIONS.lead_score.map((option) => (
                              <div key={option.value} className="flex items-start gap-3">
                                <input
                                  type="radio"
                                  id={`score_${option.value}`}
                                  name="segmentacao_score"
                                  value={option.value}
                                  checked={formData.segmentacao_score === option.value}
                                  onChange={(e) => setFormData({...formData, segmentacao_score: e.target.value})}
                                  className="mt-1 w-4 h-4"
                                />
                                <label htmlFor={`score_${option.value}`} className="flex-1 cursor-pointer">
                                  <div className="font-medium text-sm">{option.label}</div>
                                  <div className="text-xs text-gray-600">{option.description}</div>
                                </label>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Tipo de Cliente */}
                        <div className="space-y-3">
                          <Label className="font-medium">👥 Tipo de Cliente</Label>
                          <div className="space-y-2">
                            {SEGMENTATION_OPTIONS.tipo_cliente.map((option) => (
                              <div key={option.value} className="flex items-start gap-3">
                                <input
                                  type="radio"
                                  id={`tipo_${option.value}`}
                                  name="segmentacao_tipo"
                                  value={option.value}
                                  checked={formData.segmentacao_tipo === option.value}
                                  onChange={(e) => setFormData({...formData, segmentacao_tipo: e.target.value})}
                                  className="mt-1 w-4 h-4"
                                />
                                <label htmlFor={`tipo_${option.value}`} className="flex-1 cursor-pointer">
                                  <div className="font-medium text-sm">{option.label}</div>
                                  <div className="text-xs text-gray-600">{option.description}</div>
                                </label>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Frequência */}
                        <div className="space-y-3">
                          <Label className="font-medium">🔄 Frequência de Compra</Label>
                          <div className="space-y-2">
                            {SEGMENTATION_OPTIONS.frequencia.map((option) => (
                              <div key={option.value} className="flex items-start gap-3">
                                <input
                                  type="radio"
                                  id={`freq_${option.value}`}
                                  name="segmentacao_frequencia"
                                  value={option.value}
                                  checked={formData.segmentacao_frequencia === option.value}
                                  onChange={(e) => setFormData({...formData, segmentacao_frequencia: e.target.value})}
                                  className="mt-1 w-4 h-4"
                                />
                                <label htmlFor={`freq_${option.value}`} className="flex-1 cursor-pointer">
                                  <div className="font-medium text-sm">{option.label}</div>
                                  <div className="text-xs text-gray-600">{option.description}</div>
                                </label>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Interesse */}
                        <div className="space-y-3">
                          <Label className="font-medium">🛒 Interesse em Produtos</Label>
                          <div className="space-y-2">
                            {SEGMENTATION_OPTIONS.interesse.map((option) => (
                              <div key={option.value} className="flex items-start gap-3">
                                <input
                                  type="radio"
                                  id={`int_${option.value}`}
                                  name="segmentacao_interesse"
                                  value={option.value}
                                  checked={formData.segmentacao_interesse === option.value}
                                  onChange={(e) => setFormData({...formData, segmentacao_interesse: e.target.value})}
                                  className="mt-1 w-4 h-4"
                                />
                                <label htmlFor={`int_${option.value}`} className="flex-1 cursor-pointer">
                                  <div className="font-medium text-sm">{option.label}</div>
                                  <div className="text-xs text-gray-600">{option.description}</div>
                                </label>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>

                      {/* Configuração Manual (Avançado) */}
                      <details className="mt-6">
                        <summary className="cursor-pointer text-sm font-medium text-gray-600 hover:text-gray-800">
                          ⚙️ Configuração Manual (Avançado - JSON)
                        </summary>
                        <div className="mt-3 space-y-2">
                          <Label htmlFor="segmento">Configuração de Segmento (JSON)</Label>
                          <Textarea
                            id="segmento"
                            value={formData.segmento}
                            onChange={(e) => handleSegmentoChange(e.target.value)}
                            placeholder='Deixe vazio para usar as seleções acima automaticamente'
                            className="font-mono text-sm resize-none"
                            rows={3}
                          />
                          {jsonError && (
                            <div className="flex items-center gap-2 mt-1 text-red-600 text-xs">
                              <AlertCircle className="h-3 w-3" />
                              {jsonError}
                            </div>
                          )}
                          <p className="text-xs text-gray-500">
                            💡 Se deixar em branco, será gerado automaticamente com base nas suas seleções acima
                          </p>
                        </div>
                      </details>
                    </div>
                    
                    <div className="flex flex-col sm:flex-row justify-end gap-3 pt-6">
                      <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                        Cancelar
                      </Button>
                      {!showPreview && (
                        <Button type="button" variant="outline" onClick={togglePreview}>
                          👁️ Preview
                        </Button>
                      )}
                      <Button 
                        type="submit" 
                        disabled={createCampaign.isPending || !!jsonError}
                        className="bg-orange-500 hover:bg-orange-600"
                      >
                        {createCampaign.isPending ? 'Salvando...' : editingCampaign ? 'Atualizar' : 'Criar Campanha'}
                      </Button>
                    </div>
                  </form>
                </div>

                {/* Coluna Direita - Preview */}
                <div className="lg:w-80 xl:w-96 flex-shrink-0">
                  <div className="sticky top-4">
                    <div className="p-4 lg:p-6 border rounded-lg bg-gradient-to-br from-gray-50 to-gray-100">
                      <h3 className="font-medium mb-4 flex items-center gap-2 text-lg">
                        👁️ Preview da Campanha
                      </h3>
                      
                      <div className="space-y-3 text-sm">
                        <div>
                          <span className="font-medium text-gray-600">Nome:</span>
                          <p className="text-gray-900 break-words mt-1">{formData.nome || 'Não definido'}</p>
                        </div>
                        
                        <div>
                          <span className="font-medium text-gray-600">Tipo:</span>
                          <p className="text-gray-900 mt-1">{formData.tipo_campanha || 'Não definido'}</p>
                        </div>
                        
                        <div>
                          <span className="font-medium text-gray-600">Produtos:</span>
                          <p className="text-gray-900 break-words mt-1">{formData.produtos || 'Não definido'}</p>
                        </div>
                        
                        <div>
                          <span className="font-medium text-gray-600">Oferta:</span>
                          <p className="text-gray-900 break-words mt-1">{formData.oferta || 'Não definida'}</p>
                        </div>
                        
                        <div>
                          <span className="font-medium text-gray-600">Público:</span>
                          <p className="text-gray-900 break-words mt-1">{formData.publico_alvo || 'Não definido'}</p>
                        </div>
                        
                        <div>
                          <span className="font-medium text-gray-600">Canal:</span>
                          <p className="text-gray-900 mt-1">{formData.canal_preferido}</p>
                        </div>
                        
                        {/* Resumo da Segmentação */}
                        <div className="pt-3 border-t">
                          <span className="font-medium text-gray-600">🎯 Vai para:</span>
                          <div className="text-xs space-y-1 mt-2">
                            <p>📊 {SEGMENTATION_OPTIONS.lead_score.find(opt => opt.value === formData.segmentacao_score)?.label}</p>
                            <p>👥 {SEGMENTATION_OPTIONS.tipo_cliente.find(opt => opt.value === formData.segmentacao_tipo)?.label}</p>
                            <p>🔄 {SEGMENTATION_OPTIONS.frequencia.find(opt => opt.value === formData.segmentacao_frequencia)?.label}</p>
                            <p>🛒 {SEGMENTATION_OPTIONS.interesse.find(opt => opt.value === formData.segmentacao_interesse)?.label}</p>
                          </div>
                        </div>
                        
                        {formData.data_inicio && formData.data_fim && (
                          <div>
                            <span className="font-medium text-gray-600">Período:</span>
                            <p className="text-gray-900 text-xs mt-1">
                              {new Date(formData.data_inicio).toLocaleDateString('pt-BR')} até {new Date(formData.data_fim).toLocaleDateString('pt-BR')}
                            </p>
                          </div>
                        )}
                      </div>
                      
                      {formData.nome && formData.oferta && (
                        <div className="mt-4 p-3 bg-white border rounded border-l-4 border-l-orange-500">
                          <p className="text-xs text-gray-600 mb-2">💬 Mensagem de exemplo:</p>
                          <p className="text-sm break-words">
                            🎯 <strong>{formData.nome}</strong><br/>
                            {formData.oferta}<br/>
                            📱 Responda para saber mais!
                          </p>
                        </div>
                      )}
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