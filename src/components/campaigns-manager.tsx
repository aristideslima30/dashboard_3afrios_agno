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
}

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
    segmento: ''
  })
  const [jsonError, setJsonError] = useState<string>('')
  
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
        segmento: JSON.stringify({
          "tipo_campanha": typeId,
          "automatica": true
        }, null, 2)
      }))
    }
  }

  const resetForm = () => {
    setFormData({
      nome: '',
      produtos: '',
      oferta: '',
      data_inicio: '',
      data_fim: '',
      segmento: ''
    })
    setJsonError('')
    setEditingCampaign(null)
    setSelectedCampaignType('')
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
      segmento: JSON.stringify(campaign.segmento, null, 2)
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
      const segmentoJson = formData.segmento.trim() ? JSON.parse(formData.segmento) : {}
      
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
            
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>
                  {editingCampaign ? 'Editar Campanha' : 'Criar Nova Campanha'}
                </DialogTitle>
              </DialogHeader>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="nome">Nome da Campanha *</Label>
                    <Input
                      id="nome"
                      value={formData.nome}
                      onChange={(e) => setFormData({...formData, nome: e.target.value})}
                      placeholder="Ex: Promoção Queijos Premium"
                      required
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="produtos">Produtos (separados por vírgula) *</Label>
                    <Input
                      id="produtos"
                      value={formData.produtos}
                      onChange={(e) => setFormData({...formData, produtos: e.target.value})}
                      placeholder="Ex: queijo, presunto, salame"
                      required
                    />
                  </div>
                </div>
                
                <div>
                  <Label htmlFor="oferta">Oferta *</Label>
                  <Textarea
                    id="oferta"
                    value={formData.oferta}
                    onChange={(e) => setFormData({...formData, oferta: e.target.value})}
                    placeholder="Ex: 20% de desconto em todos os queijos premium"
                    required
                    rows={3}
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="data_inicio">Data de Início *</Label>
                    <Input
                      id="data_inicio"
                      type="datetime-local"
                      value={formData.data_inicio}
                      onChange={(e) => setFormData({...formData, data_inicio: e.target.value})}
                      required
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="data_fim">Data de Fim *</Label>
                    <Input
                      id="data_fim"
                      type="datetime-local"
                      value={formData.data_fim}
                      onChange={(e) => setFormData({...formData, data_fim: e.target.value})}
                      required
                    />
                  </div>
                </div>
                
                <div>
                  <Label htmlFor="segmento">Segmento (JSON)</Label>
                  <Textarea
                    id="segmento"
                    value={formData.segmento}
                    onChange={(e) => handleSegmentoChange(e.target.value)}
                    placeholder='{"lead_score": ">5", "interesseProduto": "contains queijo"}'
                    className="font-mono text-sm"
                    rows={4}
                  />
                  {jsonError && (
                    <div className="flex items-center gap-2 mt-1 text-red-600 text-xs">
                      <AlertCircle className="h-3 w-3" />
                      {jsonError}
                    </div>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    Exemplo: {`{"lead_score": ">5", "interesseProduto": "contains queijo"}`}
                  </p>
                </div>
                
                <div className="flex justify-end gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                    Cancelar
                  </Button>
                  <Button 
                    type="submit" 
                    disabled={createCampaign.isPending || !!jsonError}
                    className="bg-orange-500 hover:bg-orange-600"
                  >
                    {createCampaign.isPending ? 'Salvando...' : editingCampaign ? 'Atualizar' : 'Criar Campanha'}
                  </Button>
                </div>
              </form>
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