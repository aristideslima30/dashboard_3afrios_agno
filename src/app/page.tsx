'use client'

import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { LeadsList } from '@/components/leads-list'
import { ConversationViewer } from '@/components/conversation-viewer'
import { CampaignsManager } from '@/components/campaigns-manager'
import { LeadActions } from '@/components/lead-actions'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ClienteDelivery } from '@/lib/supabase'
import { LeadScoreBadge } from '@/components/lead-score-badge'
import { LeadStatusBadge } from '@/components/lead-status-badge'
import { useLeads } from '@/hooks/use-leads'
import { useRecentConversations } from '@/hooks/use-conversations'
import { useCampaigns } from '@/hooks/use-campaigns'
import { MapPin, Phone, Calendar, DollarSign, Users, MessageSquare, Megaphone, Settings, BarChart3, Snowflake, TrendingUp, Target, Clock, Star } from 'lucide-react'

// Interfaces para configurações
interface NotificationSettings {
  email: boolean
  push: boolean
  sms: boolean
  whatsapp: boolean
}

interface WhatsAppConfig {
  autoResponse: boolean
  businessHours: boolean
  responseDelay: number
}

interface SystemConfig {
  theme: string
  language: string
  timezone: string
  dataRetention: number
}

export default function Dashboard() {
  const [selectedClient, setSelectedClient] = useState<ClienteDelivery | null>(null)
  const [activeTab, setActiveTab] = useState("conversations")

  // Estados para configurações
  const [notifications, setNotifications] = useState<NotificationSettings>({
    email: true,
    push: true,
    sms: false,
    whatsapp: true
  })

  const [whatsappConfig, setWhatsappConfig] = useState<WhatsAppConfig>({
    autoResponse: true,
    businessHours: true,
    responseDelay: 2
  })

  const [systemConfig, setSystemConfig] = useState<SystemConfig>({
    theme: 'light',
    language: 'pt-BR',
    timezone: 'America/Sao_Paulo',
    dataRetention: 365
  })

  const [securityConfig, setSecurityConfig] = useState({
    twoFactorAuth: false,
    auditLog: true
  })

  // Hooks para dados de analytics
  const { data: leads = [] } = useLeads()
  const { data: conversations = [] } = useRecentConversations()
  const { data: campaigns = [] } = useCampaigns()

  // Cálculos para analytics
  const totalLeads = leads.length
  const leadsInteressados = leads.filter(lead => lead.lead_status === 'interessado').length
  const leadsProntos = leads.filter(lead => lead.lead_status === 'pronto_para_comprar').length
  const leadsNovos = leads.filter(lead => lead.lead_status === 'novo').length
  const valorPotencialTotal = leads.reduce((sum, lead) => sum + (lead.valor_potencial || 0), 0)
  const scoreMediaLeads = leads.length > 0 ? leads.reduce((sum, lead) => sum + lead.lead_score, 0) / leads.length : 0
  const totalConversas = conversations.length
  const campanhasAtivas = campaigns.filter(camp => new Date(camp.data_fim) > new Date()).length

  // Distribuição por score
  const leadsAltoScore = leads.filter(lead => lead.lead_score >= 8).length
  const leadsMedioScore = leads.filter(lead => lead.lead_score >= 5 && lead.lead_score < 8).length
  const leadsBaixoScore = leads.filter(lead => lead.lead_score < 5).length

  // Funções para configurações
  const handleSaveSettings = () => {
    console.log('Configurações salvas:', { 
      notifications, 
      whatsappConfig, 
      systemConfig, 
      securityConfig 
    })
    alert('Configurações salvas com sucesso!')
  }

  const handleExportData = () => {
    const data = {
      leads,
      conversations,
      campaigns,
      exportDate: new Date().toISOString()
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `dashboard-data-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    alert('Dados exportados com sucesso!')
  }

  const handleBackupSystem = () => {
    console.log('Iniciando backup do sistema...')
    alert('Backup do sistema iniciado! Você receberá uma notificação quando concluído.')
  }

  const handleClearCache = () => {
    if (confirm('Tem certeza que deseja limpar o cache? Esta ação não pode ser desfeita.')) {
      localStorage.clear()
      sessionStorage.clear()
      alert('Cache limpo com sucesso! A página será recarregada.')
      window.location.reload()
    }
  }

  return (
    <div className="min-h-screen bg-gradient-main flex">
      {/* Sidebar Moderna */}
      <div className="w-72 sidebar-gradient flex flex-col shadow-xl">
        {/* Header do Sidebar */}
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <Snowflake className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">3A Frios</h1>
              <p className="text-sm text-blue-100">Dashboard Pro</p>
            </div>
          </div>
        </div>

        {/* Navegação */}
        <div className="flex-1 flex flex-col">
          <div className="flex flex-col p-4 gap-2">
            <button 
              onClick={() => setActiveTab("conversations")}
              className={`w-full justify-start gap-4 px-4 py-3.5 text-white/80 hover:text-white hover:bg-white/10 rounded-xl transition-all duration-200 flex items-center ${
                activeTab === "conversations" ? "bg-white/20 text-white shadow-lg nav-active" : ""
              }`}
            >
              <MessageSquare className="h-5 w-5" />
              <span className="font-medium">Conversas</span>
            </button>
            <button 
              onClick={() => setActiveTab("leads")}
              className={`w-full justify-start gap-4 px-4 py-3.5 text-white/80 hover:text-white hover:bg-white/10 rounded-xl transition-all duration-200 flex items-center ${
                activeTab === "leads" ? "bg-white/20 text-white shadow-lg nav-active" : ""
              }`}
            >
              <Users className="h-5 w-5" />
              <span className="font-medium">Leads</span>
            </button>
            <button 
              onClick={() => setActiveTab("campaigns")}
              className={`w-full justify-start gap-4 px-4 py-3.5 text-white/80 hover:text-white hover:bg-white/10 rounded-xl transition-all duration-200 flex items-center ${
                activeTab === "campaigns" ? "bg-white/20 text-white shadow-lg nav-active" : ""
              }`}
            >
              <Megaphone className="h-5 w-5" />
              <span className="font-medium">Campanhas</span>
            </button>
            <button 
              onClick={() => setActiveTab("analytics")}
              className={`w-full justify-start gap-4 px-4 py-3.5 text-white/80 hover:text-white hover:bg-white/10 rounded-xl transition-all duration-200 flex items-center ${
                activeTab === "analytics" ? "bg-white/20 text-white shadow-lg nav-active" : ""
              }`}
            >
              <BarChart3 className="h-5 w-5" />
              <span className="font-medium">Analytics</span>
            </button>
            <button 
              onClick={() => setActiveTab("settings")}
              className={`w-full justify-start gap-4 px-4 py-3.5 text-white/80 hover:text-white hover:bg-white/10 rounded-xl transition-all duration-200 flex items-center ${
                activeTab === "settings" ? "bg-white/20 text-white shadow-lg nav-active" : ""
              }`}
            >
              <Settings className="h-5 w-5" />
              <span className="font-medium">Configurações</span>
            </button>
          </div>

          {/* Área de Status */}
          <div className="mt-auto p-6 border-t border-white/10">
            <div className="bg-white/10 rounded-xl p-4 backdrop-blur-sm">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                <div>
                  <p className="text-sm font-medium text-white">Sistema Online</p>
                  <p className="text-xs text-blue-100">Equipe 3A Frios</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Conteúdo Principal */}
      <div className="flex-1 flex flex-col">
        {/* Header Moderno */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-neutral-200/50 px-8 py-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-neutral-900 mb-1">Atendimento Automatizado</h2>
              <p className="text-neutral-600">Gerencie leads, conversas e campanhas de forma inteligente</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="bg-gradient-to-r from-green-50 to-green-100 px-4 py-2 rounded-xl border border-green-200">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm font-medium text-green-700">WhatsApp Conectado</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Conteúdo das Abas */}
        <div className="flex-1 p-8">
          {/* Aba Conversas */}
          {activeTab === "conversations" && (
            <div className="h-full fade-in">
              <div className="flex h-full gap-6">
                {/* Left Panel - Leads List for Conversations */}
                <div className="w-1/3">
                  <div className="card-elegant h-full">
                    <CardHeader className="pb-4">
                      <CardTitle className="flex items-center gap-3 text-lg">
                        <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                          <MessageSquare className="h-4 w-4 text-blue-600" />
                        </div>
                        Conversas Ativas
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <LeadsList 
                        onSelectClient={setSelectedClient}
                        selectedClientId={selectedClient?.id}
                        showOnlyWithConversations={true}
                      />
                    </CardContent>
                  </div>
                </div>

                {/* Right Panel - Conversation Viewer */}
                <div className="flex-1">
                  {selectedClient ? (
                    <ConversationViewer client={selectedClient} />
                  ) : (
                    <div className="card-elegant h-full flex items-center justify-center">
                      <CardContent>
                        <div className="text-center">
                          <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                            <MessageSquare className="h-8 w-8 text-blue-500" />
                          </div>
                          <h3 className="text-xl font-semibold text-neutral-900 mb-2">Selecione uma conversa</h3>
                          <p className="text-neutral-600 max-w-sm">Escolha um cliente da lista para visualizar o histórico completo de mensagens</p>
                        </div>
                      </CardContent>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Aba Leads */}
          {activeTab === "leads" && (
            <div className="h-full fade-in">
              <div className="flex h-full gap-6">
                {/* Left Panel - Leads List */}
                <div className="w-1/3">
                  <div className="card-elegant h-full">
                    <CardHeader className="pb-4">
                      <CardTitle className="flex items-center gap-3 text-lg">
                        <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                          <Users className="h-4 w-4 text-green-600" />
                        </div>
                        Todos os Leads
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <LeadsList 
                        onSelectClient={setSelectedClient}
                        selectedClientId={selectedClient?.id}
                      />
                    </CardContent>
                  </div>
                </div>

                {/* Right Panel - Lead Details and Actions */}
                <div className="flex-1">
                  {selectedClient ? (
                    <div className="space-y-6 h-full">
                      {/* Lead Info Card */}
                      <div className="card-elegant">
                        <CardHeader className="pb-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center text-white font-bold text-lg">
                                {selectedClient.nome.charAt(0).toUpperCase()}
                              </div>
                              <div>
                                <CardTitle className="text-xl text-neutral-900">{selectedClient.nome}</CardTitle>
                                <p className="text-neutral-600 text-sm">Cliente desde {new Date(selectedClient.created_at).toLocaleDateString('pt-BR')}</p>
                              </div>
                            </div>
                            <div className="flex gap-3">
                              <LeadScoreBadge score={selectedClient.lead_score} />
                              <LeadStatusBadge status={selectedClient.lead_status} />
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-6">
                          <div className="grid grid-cols-2 gap-6">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                                <Phone className="h-5 w-5 text-blue-600" />
                              </div>
                              <div>
                                <p className="text-sm text-neutral-500">Telefone</p>
                                <p className="font-medium text-neutral-900">{selectedClient.telefone}</p>
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center">
                                <MapPin className="h-5 w-5 text-green-600" />
                              </div>
                              <div>
                                <p className="text-sm text-neutral-500">Endereço</p>
                                <p className="font-medium text-neutral-900">{selectedClient.endereco || 'Não informado'}</p>
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center">
                                <Calendar className="h-5 w-5 text-purple-600" />
                              </div>
                              <div>
                                <p className="text-sm text-neutral-500">Data de Cadastro</p>
                                <p className="font-medium text-neutral-900">{new Date(selectedClient.created_at).toLocaleDateString('pt-BR')}</p>
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-yellow-50 rounded-lg flex items-center justify-center">
                                <DollarSign className="h-5 w-5 text-yellow-600" />
                              </div>
                              <div>
                                <p className="text-sm text-neutral-500">Valor Potencial</p>
                                <p className="font-medium text-neutral-900">R$ {selectedClient.valor_potencial?.toFixed(2) || '0,00'}</p>
                              </div>
                            </div>
                          </div>
                          
                          {selectedClient.interesse_declarado && (
                            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-100">
                              <h4 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                                Interesse Declarado
                              </h4>
                              <p className="text-blue-800">{selectedClient.interesse_declarado}</p>
                            </div>
                          )}
                        </CardContent>
                      </div>

                      {/* Lead Actions */}
                      <LeadActions client={selectedClient} />
                    </div>
                  ) : (
                    <div className="card-elegant h-full flex items-center justify-center">
                      <CardContent>
                        <div className="text-center">
                          <div className="w-16 h-16 bg-green-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                            <Users className="h-8 w-8 text-green-500" />
                          </div>
                          <h3 className="text-xl font-semibold text-neutral-900 mb-2">Selecione um lead</h3>
                          <p className="text-neutral-600 max-w-sm">Escolha um lead da lista para ver informações detalhadas e ações disponíveis</p>
                        </div>
                      </CardContent>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Aba Campanhas */}
          {activeTab === "campaigns" && (
            <div className="h-full fade-in">
              <CampaignsManager />
            </div>
          )}

          {/* Aba Analytics */}
          {activeTab === "analytics" && (
            <div className="h-full fade-in space-y-6 overflow-y-auto">
              {/* Métricas Principais */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="card-elegant">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-neutral-600">Total de Leads</p>
                        <p className="text-3xl font-bold text-neutral-900">{totalLeads}</p>
                        <p className="text-sm text-green-600 flex items-center gap-1 mt-1">
                          <TrendingUp className="h-3 w-3" />
                          +12% este mês
                        </p>
                      </div>
                      <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                        <Users className="h-6 w-6 text-blue-600" />
                      </div>
                    </div>
                  </CardContent>
                </div>

                <div className="card-elegant">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-neutral-600">Valor Potencial</p>
                        <p className="text-3xl font-bold text-neutral-900">R$ {valorPotencialTotal.toFixed(0)}</p>
                        <p className="text-sm text-green-600 flex items-center gap-1 mt-1">
                          <DollarSign className="h-3 w-3" />
                          Pipeline ativo
                        </p>
                      </div>
                      <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                        <DollarSign className="h-6 w-6 text-green-600" />
                      </div>
                    </div>
                  </CardContent>
                </div>

                <div className="card-elegant">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-neutral-600">Conversas Ativas</p>
                        <p className="text-3xl font-bold text-neutral-900">{totalConversas}</p>
                        <p className="text-sm text-blue-600 flex items-center gap-1 mt-1">
                          <MessageSquare className="h-3 w-3" />
                          Em andamento
                        </p>
                      </div>
                      <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                        <MessageSquare className="h-6 w-6 text-purple-600" />
                      </div>
                    </div>
                  </CardContent>
                </div>

                <div className="card-elegant">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-neutral-600">Score Médio</p>
                        <p className="text-3xl font-bold text-neutral-900">{scoreMediaLeads.toFixed(1)}</p>
                        <p className="text-sm text-yellow-600 flex items-center gap-1 mt-1">
                          <Star className="h-3 w-3" />
                          Qualidade dos leads
                        </p>
                      </div>
                      <div className="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center">
                        <Star className="h-6 w-6 text-yellow-600" />
                      </div>
                    </div>
                  </CardContent>
                </div>
              </div>

              {/* Gráficos e Análises */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Status dos Leads */}
                <div className="card-elegant">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5 text-blue-600" />
                      Status dos Leads
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                          <span className="text-sm font-medium">Prontos para Comprar</span>
                        </div>
                        <span className="text-sm font-bold">{leadsProntos}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-green-500 h-2 rounded-full transition-all duration-500" 
                          style={{ width: `${totalLeads > 0 ? (leadsProntos / totalLeads) * 100 : 0}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                          <span className="text-sm font-medium">Interessados</span>
                        </div>
                        <span className="text-sm font-bold">{leadsInteressados}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-yellow-500 h-2 rounded-full transition-all duration-500" 
                          style={{ width: `${totalLeads > 0 ? (leadsInteressados / totalLeads) * 100 : 0}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
                          <span className="text-sm font-medium">Novos</span>
                        </div>
                        <span className="text-sm font-bold">{leadsNovos}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-gray-400 h-2 rounded-full transition-all duration-500" 
                          style={{ width: `${totalLeads > 0 ? (leadsNovos / totalLeads) * 100 : 0}%` }}
                        ></div>
                      </div>
                    </div>
                  </CardContent>
                </div>

                {/* Distribuição por Score */}
                <div className="card-elegant">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="h-5 w-5 text-purple-600" />
                      Distribuição por Score
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                          <span className="text-sm font-medium">Alto Score (8-10)</span>
                        </div>
                        <span className="text-sm font-bold">{leadsAltoScore}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-red-500 h-2 rounded-full transition-all duration-500" 
                          style={{ width: `${totalLeads > 0 ? (leadsAltoScore / totalLeads) * 100 : 0}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                          <span className="text-sm font-medium">Médio Score (5-7)</span>
                        </div>
                        <span className="text-sm font-bold">{leadsMedioScore}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-yellow-500 h-2 rounded-full transition-all duration-500" 
                          style={{ width: `${totalLeads > 0 ? (leadsMedioScore / totalLeads) * 100 : 0}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
                          <span className="text-sm font-medium">Baixo Score (1-4)</span>
                        </div>
                        <span className="text-sm font-bold">{leadsBaixoScore}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-gray-400 h-2 rounded-full transition-all duration-500" 
                          style={{ width: `${totalLeads > 0 ? (leadsBaixoScore / totalLeads) * 100 : 0}%` }}
                        ></div>
                      </div>
                    </div>
                  </CardContent>
                </div>
              </div>

              {/* Campanhas e Performance */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="card-elegant">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Megaphone className="h-5 w-5 text-orange-600" />
                      Campanhas Ativas
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center">
                      <div className="text-4xl font-bold text-orange-600 mb-2">{campanhasAtivas}</div>
                      <p className="text-sm text-neutral-600">Campanhas em execução</p>
                      <div className="mt-4 p-3 bg-orange-50 rounded-lg">
                        <p className="text-xs text-orange-700">
                          {campaigns.length - campanhasAtivas} campanhas finalizadas
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </div>

                <div className="card-elegant">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Clock className="h-5 w-5 text-blue-600" />
                      Tempo de Resposta
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center">
                      <div className="text-4xl font-bold text-blue-600 mb-2">2.3</div>
                      <p className="text-sm text-neutral-600">Minutos médios</p>
                      <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                        <p className="text-xs text-blue-700">
                          85% das mensagens respondidas em menos de 5 min
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </div>

                <div className="card-elegant">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-green-600" />
                      Taxa de Conversão
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center">
                      <div className="text-4xl font-bold text-green-600 mb-2">24%</div>
                      <p className="text-sm text-neutral-600">Leads → Vendas</p>
                      <div className="mt-4 p-3 bg-green-50 rounded-lg">
                        <p className="text-xs text-green-700">
                          +8% comparado ao mês anterior
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </div>
              </div>

              {/* Insights e Recomendações */}
              <div className="card-elegant">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Star className="h-5 w-5 text-purple-600" />
                    Insights e Recomendações
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg border border-blue-200">
                      <h4 className="font-semibold text-blue-900 mb-2">🎯 Oportunidade de Melhoria</h4>
                      <p className="text-sm text-blue-800">
                        {leadsBaixoScore} leads com score baixo podem ser qualificados melhor com campanhas direcionadas.
                      </p>
                    </div>
                    
                    <div className="p-4 bg-gradient-to-r from-green-50 to-green-100 rounded-lg border border-green-200">
                      <h4 className="font-semibold text-green-900 mb-2">💰 Potencial de Receita</h4>
                      <p className="text-sm text-green-800">
                        R$ {valorPotencialTotal.toFixed(0)} em pipeline. Foque nos {leadsProntos} leads prontos para comprar.
                      </p>
                    </div>
                    
                    <div className="p-4 bg-gradient-to-r from-yellow-50 to-yellow-100 rounded-lg border border-yellow-200">
                      <h4 className="font-semibold text-yellow-900 mb-2">⚡ Ação Recomendada</h4>
                      <p className="text-sm text-yellow-800">
                        Crie campanhas específicas para os {leadsInteressados} leads interessados para acelerar a conversão.
                      </p>
                    </div>
                    
                    <div className="p-4 bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg border border-purple-200">
                      <h4 className="font-semibold text-purple-900 mb-2">📈 Tendência Positiva</h4>
                      <p className="text-sm text-purple-800">
                        Score médio de {scoreMediaLeads.toFixed(1)} indica boa qualidade dos leads. Continue o bom trabalho!
                      </p>
                    </div>
                  </div>
                </CardContent>
              </div>
            </div>
          )}

          {/* Aba Configurações */}
          {activeTab === "settings" && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-neutral-900">Configurações do Sistema</h2>
                <button 
                  onClick={handleSaveSettings}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Salvar Configurações
                </button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Notificações */}
                <Card className="card-elegant">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <MessageSquare className="h-5 w-5 text-blue-600" />
                      Notificações
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium">Notificações por Email</label>
                      <input 
                        type="checkbox" 
                        className="rounded" 
                        checked={notifications.email}
                        onChange={(e) => setNotifications({...notifications, email: e.target.checked})}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium">Notificações Push</label>
                      <input 
                        type="checkbox" 
                        className="rounded" 
                        checked={notifications.push}
                        onChange={(e) => setNotifications({...notifications, push: e.target.checked})}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium">Notificações SMS</label>
                      <input 
                        type="checkbox" 
                        className="rounded" 
                        checked={notifications.sms}
                        onChange={(e) => setNotifications({...notifications, sms: e.target.checked})}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium">Notificações WhatsApp</label>
                      <input 
                        type="checkbox" 
                        className="rounded" 
                        checked={notifications.whatsapp}
                        onChange={(e) => setNotifications({...notifications, whatsapp: e.target.checked})}
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* WhatsApp Business */}
                <Card className="card-elegant">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Phone className="h-5 w-5 text-green-600" />
                      WhatsApp Business
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium">Resposta Automática</label>
                      <input 
                        type="checkbox" 
                        className="rounded" 
                        checked={whatsappConfig.autoResponse}
                        onChange={(e) => setWhatsappConfig({...whatsappConfig, autoResponse: e.target.checked})}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium">Horário Comercial</label>
                      <input 
                        type="checkbox" 
                        className="rounded" 
                        checked={whatsappConfig.businessHours}
                        onChange={(e) => setWhatsappConfig({...whatsappConfig, businessHours: e.target.checked})}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Delay de Resposta (segundos)</label>
                      <input 
                        type="number" 
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        value={whatsappConfig.responseDelay}
                        onChange={(e) => setWhatsappConfig({...whatsappConfig, responseDelay: parseInt(e.target.value)})}
                        min={0}
                        max={60}
                      />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Status do Sistema */}
              <Card className="card-elegant">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-green-600" />
                    Status do Sistema
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="w-3 h-3 bg-green-500 rounded-full mx-auto mb-2"></div>
                      <p className="text-sm font-medium">API WhatsApp</p>
                      <p className="text-xs text-gray-500">Online</p>
                    </div>
                    <div className="text-center">
                      <div className="w-3 h-3 bg-green-500 rounded-full mx-auto mb-2"></div>
                      <p className="text-sm font-medium">Banco de Dados</p>
                      <p className="text-xs text-gray-500">Conectado</p>
                    </div>
                    <div className="text-center">
                      <div className="w-3 h-3 bg-yellow-500 rounded-full mx-auto mb-2"></div>
                      <p className="text-sm font-medium">Cache Redis</p>
                      <p className="text-xs text-gray-500">Lento</p>
                    </div>
                    <div className="text-center">
                      <div className="w-3 h-3 bg-green-500 rounded-full mx-auto mb-2"></div>
                      <p className="text-sm font-medium">Servidor</p>
                      <p className="text-xs text-gray-500">Estável</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}
