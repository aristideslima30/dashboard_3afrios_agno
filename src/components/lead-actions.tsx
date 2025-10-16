'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Star, TrendingUp, Save, History } from 'lucide-react'
import { useUpdateLead } from '@/hooks/use-leads'
import { ClienteDelivery } from '@/lib/supabase'
import { LeadScoreBadge } from './lead-score-badge'
import { LeadStatusBadge } from './lead-status-badge'

interface LeadActionsProps {
  client: ClienteDelivery
}

export function LeadActions({ client }: LeadActionsProps) {
  const updateLead = useUpdateLead()
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState({
    lead_score: client.lead_score || 0,
    lead_status: client.lead_status,
    interesse_declarado: client.interesse_declarado || '',
    frequencia_compra: client.frequencia_compra || '',
    valor_potencial: client.valor_potencial || 0,
    endereco: client.endereco || ''
  })

  const handleSave = async () => {
    try {
      await updateLead.mutateAsync({
        id: client.id,
        updates: {
          ...formData,
          updated_at: new Date().toISOString()
        }
      })
      setIsEditing(false)
    } catch (error) {
      console.error('Erro ao atualizar lead:', error)
      alert('Erro ao atualizar lead')
    }
  }

  const handleQualifyAsHot = async () => {
    try {
      await updateLead.mutateAsync({
        id: client.id,
        updates: {
          lead_score: 10,
          lead_status: 'pronto_para_comprar',
          updated_at: new Date().toISOString()
        }
      })
      setFormData({
        ...formData,
        lead_score: 10,
        lead_status: 'pronto_para_comprar'
      })
    } catch (error) {
      console.error('Erro ao qualificar lead:', error)
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Ações do Lead
          </CardTitle>
          
          <div className="flex gap-2">
            {!isEditing ? (
              <>
                <Button
                  onClick={() => setIsEditing(true)}
                  variant="outline"
                  size="sm"
                >
                  Editar
                </Button>
                <Button
                  onClick={handleQualifyAsHot}
                  className="bg-red-500 hover:bg-red-600"
                  size="sm"
                  disabled={updateLead.isPending}
                >
                  <Star className="h-3 w-3 mr-1" />
                  Qualificar como Quente
                </Button>
              </>
            ) : (
              <>
                <Button
                  onClick={() => setIsEditing(false)}
                  variant="outline"
                  size="sm"
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleSave}
                  size="sm"
                  disabled={updateLead.isPending}
                >
                  <Save className="h-3 w-3 mr-1" />
                  Salvar
                </Button>
              </>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Status Atual */}
        <div className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
          <div>
            <span className="text-sm font-medium">Score Atual:</span>
            <LeadScoreBadge score={client.lead_score || 0} className="ml-2" />
          </div>
          <div>
            <span className="text-sm font-medium">Status:</span>
            <LeadStatusBadge status={client.lead_status} className="ml-2" />
          </div>
        </div>

        {/* Formulário de Edição */}
        {isEditing ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="lead_score">Lead Score (0-10)</Label>
                <Input
                  id="lead_score"
                  type="number"
                  min="0"
                  max="10"
                  value={formData.lead_score}
                  onChange={(e) => setFormData({
                    ...formData,
                    lead_score: parseInt(e.target.value) || 0
                  })}
                />
              </div>
              
              <div>
                <Label htmlFor="lead_status">Status do Lead</Label>
                <Select
                  value={formData.lead_status}
                  onValueChange={(value: any) => setFormData({
                    ...formData,
                    lead_status: value
                  })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="novo">Novo</SelectItem>
                    <SelectItem value="interessado">Interessado</SelectItem>
                    <SelectItem value="pronto_para_comprar">Pronto para Comprar</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div>
              <Label htmlFor="interesse_declarado">Interesse Declarado</Label>
              <Textarea
                id="interesse_declarado"
                value={formData.interesse_declarado}
                onChange={(e) => setFormData({
                  ...formData,
                  interesse_declarado: e.target.value
                })}
                placeholder="Ex: Interessado em queijos premium para festa"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="frequencia_compra">Frequência de Compra</Label>
                <Input
                  id="frequencia_compra"
                  value={formData.frequencia_compra}
                  onChange={(e) => setFormData({
                    ...formData,
                    frequencia_compra: e.target.value
                  })}
                  placeholder="Ex: Semanal, Mensal"
                />
              </div>
              
              <div>
                <Label htmlFor="valor_potencial">Valor Potencial (R$)</Label>
                <Input
                  id="valor_potencial"
                  type="number"
                  step="0.01"
                  value={formData.valor_potencial}
                  onChange={(e) => setFormData({
                    ...formData,
                    valor_potencial: parseFloat(e.target.value) || 0
                  })}
                />
              </div>
            </div>
            
            <div>
              <Label htmlFor="endereco">Endereço</Label>
              <Input
                id="endereco"
                value={formData.endereco}
                onChange={(e) => setFormData({
                  ...formData,
                  endereco: e.target.value
                })}
                placeholder="Endereço completo para entrega"
              />
            </div>
          </div>
        ) : (
          /* Visualização dos dados */
          <div className="space-y-3">
            {client.interesse_declarado && (
              <div>
                <span className="text-sm font-medium">Interesse:</span>
                <p className="text-sm text-gray-700 mt-1">{client.interesse_declarado}</p>
              </div>
            )}
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              {client.frequencia_compra && (
                <div>
                  <span className="font-medium">Frequência:</span>
                  <p className="text-gray-700">{client.frequencia_compra}</p>
                </div>
              )}
              
              {client.valor_potencial && (
                <div>
                  <span className="font-medium">Valor Potencial:</span>
                  <p className="text-green-600 font-medium">
                    R$ {client.valor_potencial.toFixed(2)}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Histórico de Alterações */}
        <div className="border-t pt-4">
          <div className="flex items-center gap-2 mb-2">
            <History className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium">Última Atualização</span>
          </div>
          <p className="text-xs text-gray-500">
            {new Date(client.updated_at).toLocaleString('pt-BR')}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}