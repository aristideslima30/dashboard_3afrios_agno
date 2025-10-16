'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
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
import { Plus, Calendar, Target, Users, Edit, Trash2, AlertCircle } from 'lucide-react'
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
        
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span>{activeCampaigns?.length || 0} Ativas</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
            <span>{campaigns?.length || 0} Total</span>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
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
      </CardContent>
    </Card>
  )
}