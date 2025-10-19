'use client'

import { useEffect, useState } from 'react'
import { useConversations } from '@/hooks/use-conversations'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ClienteDelivery } from '@/lib/supabase'
import { Send, RotateCcw, Bot, User, Volume2, Clock } from 'lucide-react'

interface ConversationViewerProps {
  client: ClienteDelivery
}

export function ConversationViewer({ client }: ConversationViewerProps) {
  const [message, setMessage] = useState('')
  const { data: conversations, isLoading } = useConversations(client.id)
  type LocalConv = {
    id: string
    cliente_id: string
    mensagem_cliente: string
    resposta_bot?: string
    tipo_mensagem: 'texto' | 'audio'
    agente_responsavel?: string
    acao_especial?: string
    timestamp: string
  }
  const [localConversations, setLocalConversations] = useState<LocalConv[]>([])
  const [manualMode, setManualMode] = useState(false)

  useEffect(() => {
    // Reset local overlay when switching client or reloading conversations
    setLocalConversations([])
  }, [client.id])

  // Usa sempre o proxy Next para evitar CORS
  const resolveWebhookUrl = () => '/api/webhook'

  // Fonte única de mensagens para renderização, mesclando banco e overlay local
  const msgs: LocalConv[] = [
    ...(((conversations ?? []) as LocalConv[])),
    ...localConversations,
  ].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())

  const handleSendMessage = async () => {
    const webhookUrl = resolveWebhookUrl()
    const evoServer = process.env.NEXT_PUBLIC_EVOLUTION_SERVER_URL
    const evoInstance = process.env.NEXT_PUBLIC_EVOLUTION_INSTANCE
    const evoApiKey = process.env.NEXT_PUBLIC_EVOLUTION_API_KEY
    const dryRun = process.env.NEXT_PUBLIC_WHATSAPP_DRY_RUN === 'true'

    if (!message.trim() || !webhookUrl) return

    const now = new Date().toISOString()
    // Adiciona imediatamente a mensagem manual à lista local
    if (manualMode) {
      setLocalConversations(prev => [
        ...prev,
        {
          id: `tmp-${Date.now()}-bot`,
          cliente_id: client.id,
          mensagem_cliente: '',
          resposta_bot: message.trim(),
          tipo_mensagem: 'texto',
          agente_responsavel: 'Operador',
          acao_especial: 'mensagem_manual_dashboard',
          timestamp: now,
        }
      ])
      setMessage('')
    } else {
      setLocalConversations(prev => [
        ...prev,
        {
          id: `tmp-${Date.now()}-user`,
          cliente_id: client.id,
          mensagem_cliente: message.trim(),
          tipo_mensagem: 'texto',
          timestamp: now,
        }
      ])
      setMessage('')
    }

    // Envia para o backend normalmente
    try {
      const payload = manualMode
        ? {
            acao: 'responder-manual',
            telefone: client.telefone,
            telefoneCliente: client.telefone,
            clienteId: client.id,
            mensagem: message.trim(),
            dryRun,
            whatsapp: { evo: { server_url: evoServer, nomeInstancia: evoInstance, apikey: evoApiKey } },
          }
        : {
            acao: 'enviar-mensagem',
            telefone: client.telefone,
            telefoneCliente: client.telefone,
            clienteId: client.id,
            mensagem: message.trim(),
            dryRun,
            whatsapp: { evo: { server_url: evoServer, nomeInstancia: evoInstance, apikey: evoApiKey } },
          }

      const res = await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const ct = res.headers.get('content-type') || ''
      if (!res.ok) {
        try {
          const raw = ct.includes('application/json') ? await res.json() : await res.text()
          const detail = typeof raw === 'string' ? raw : raw?.detail || raw?.error || JSON.stringify(raw)
          console.error('Webhook falhou:', { status: res.status, detail })
          alert(`Falha no webhook: ${res.status}${detail ? ` – ${String(detail).slice(0, 200)}` : ''}`)
        } catch (e) {
          console.error('Falha ao ler corpo do erro do webhook', e)
          alert(`Falha no webhook: ${res.status}`)
        }
        return
      }
      // Quando o backend responder, aguarde o realtime atualizar a lista principal
      // Opcional: se quiser garantir, pode forçar um refetch das conversas
      // (mas normalmente o realtime já faz isso)
    } catch (err) {
      console.error('Erro ao enviar:', err)
    }
  }

  const handleReprocess = async () => {
    const webhookUrl = resolveWebhookUrl()
    const evoServer = process.env.NEXT_PUBLIC_EVOLUTION_SERVER_URL
    const evoInstance = process.env.NEXT_PUBLIC_EVOLUTION_INSTANCE
    const evoApiKey = process.env.NEXT_PUBLIC_EVOLUTION_API_KEY
    const dryRun = process.env.NEXT_PUBLIC_WHATSAPP_DRY_RUN === 'true'

    if (!webhookUrl) {
      console.warn('Endpoint não configurado')
      return
    }

    try {
      const res = await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          acao: 'reprocessar',
          telefoneCliente: client.telefone,
          telefone: client.telefone,
          nomeCliente: client.nome,
          mensagem: message.trim() || '',
          dryRun,
          whatsapp: {
            evo: {
              server_url: evoServer,
              nomeInstancia: evoInstance,
              apikey: evoApiKey,
            },
          },
        }),
      })
      const ct = res.headers.get('content-type') || ''
      if (!res.ok) {
        try {
          const raw = ct.includes('application/json') ? await res.json() : await res.text()
          const detail = typeof raw === 'string' ? raw : raw?.detail || raw?.error || JSON.stringify(raw)
          console.error('Falha no webhook ao reprocessar:', { status: res.status, detail })
          alert(`Falha no webhook: ${res.status}${detail ? ` – ${String(detail).slice(0, 200)}` : ''}`)
        } catch (e) {
          console.error('Falha ao ler corpo do erro do webhook (reprocessar)', e)
          alert(`Falha no webhook: ${res.status}`)
        }
        return
      }
    } catch (err) {
      console.error('Erro ao reprocessar:', err)
    }
  }

  if (isLoading) {
    return (
      <Card className="h-full">
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p className="text-sm text-gray-500">Carregando conversas...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3 border-b bg-green-50">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center text-white font-medium">
              {client.nome.charAt(0).toUpperCase()}
            </div>
            <div>
              <CardTitle className="text-lg text-green-800 line-clamp-1">{client.nome}</CardTitle>
              <p className="text-sm text-green-600">{client.telefone || 'Sem telefone'}</p>

              {/* Indicador de recência da conversa */}
              {Array.isArray(conversations) && conversations.length > 0 && (
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex items-center gap-1 text-xs text-green-700">
                    <Clock className="h-3 w-3" />
                    <span>
                      {new Date((conversations as any[])[(conversations as any[]).length - 1].timestamp).toLocaleTimeString('pt-BR', {
                        hour: '2-digit', minute: '2-digit'
                      })}
                    </span>
                  </div>
                  <Badge variant="outline" className="text-xs">Recente</Badge>
                </div>
              )}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
            <Badge variant={manualMode ? 'secondary' : 'outline'} className="text-xs">
              {manualMode ? 'Manual ON' : 'Manual OFF'}
            </Badge>
            <Button
              variant={manualMode ? 'default' : 'outline'}
              size="sm"
              onClick={() => setManualMode((v) => !v)}
              className={`${manualMode ? 'bg-green-600 hover:bg-green-700' : ''} flex-1 sm:flex-none`}
            >
              <span className="hidden sm:inline">{manualMode ? 'Desativar Manual' : 'Ativar Manual'}</span>
              <span className="sm:hidden">{manualMode ? 'Desativar' : 'Ativar'}</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleReprocess}
              className="flex items-center gap-2 flex-1 sm:flex-none"
            >
              <RotateCcw className="h-4 w-4" />
              <span className="hidden sm:inline">Reprocessar</span>
            </Button>
          </div>
        </div>
      </CardHeader>

      {/* Messages Area - WhatsApp Style */}
      <CardContent className="flex-1 p-0 overflow-hidden">
        <div className="h-full flex flex-col">
          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
            {msgs.length > 0 ? (
              msgs.map((conv: LocalConv, index: number) => (
                <div key={index} className="space-y-2">
                  {conv.mensagem_cliente && conv.mensagem_cliente.trim().length > 0 && (
                    <div className="flex justify-start">
                      <div className="max-w-[95%] xs:max-w-[85%] sm:max-w-[75%] md:max-w-[70%] bg-white rounded-lg px-3 py-2 shadow-sm border break-words">
                        <div className="flex flex-wrap items-center gap-2 mb-1">
                          <User className="h-3 w-3 text-gray-500 shrink-0" />
                          <span className="text-xs text-gray-500 font-medium">Cliente</span>
                          {conv.tipo_mensagem === 'audio' && (
                            <Volume2 className="h-3 w-3 text-blue-500 shrink-0" />
                          )}
                        </div>
                        <p className="text-sm text-gray-800 whitespace-pre-wrap">{conv.mensagem_cliente}</p>
                        <div className="flex items-center justify-between mt-1">
                          <span className="text-xs text-gray-400">
                            {new Date(conv.timestamp).toLocaleTimeString('pt-BR', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Bot/Operador Response */}
                  {conv.resposta_bot && (
                    <div className="flex justify-end">
                      <div className="max-w-[95%] xs:max-w-[85%] sm:max-w-[75%] md:max-w-[70%] bg-green-500 text-white rounded-lg px-3 py-2 shadow-sm break-words">
                        <div className="flex flex-wrap items-center gap-2 mb-1">
                          <Bot className="h-3 w-3 shrink-0" />
                          <span className="text-xs font-medium opacity-90">
                            {conv.agente_responsavel || 'Bot'}
                          </span>
                          {conv.agente_responsavel === 'Operador' && (
                            <Badge variant="secondary" className="text-xs px-1 py-0 bg-green-600 shrink-0">
                              Manual
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm whitespace-pre-wrap">{conv.resposta_bot}</p>
                        <div className="flex items-center justify-between mt-1">
                          <span className="text-xs opacity-75">
                            {new Date(conv.timestamp).toLocaleTimeString('pt-BR', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </span>
                          <div className="text-xs opacity-75 ml-2">✓✓</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Special Actions Indicators */}
                  {conv.acao_especial && (
                    <div className="flex justify-center">
                      <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs font-medium">
                        {conv.acao_especial}
                      </div>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center text-gray-500">
                  <Bot className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                  <p className="text-sm">Nenhuma conversa encontrada</p>
                  <p className="text-xs">As mensagens aparecerão aqui quando o cliente interagir</p>
                </div>
              </div>
            )}
          </div>

          {/* Message Input - WhatsApp Style */}
          <div className="border-t bg-white p-2 sm:p-4">
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="flex-1 flex items-center gap-2 bg-gray-100 rounded-full px-3 sm:px-4 py-2">
                <Input
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Digite uma mensagem..."
                  className="border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 text-sm sm:text-base"
                  onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                />
              </div>
              <Button
                onClick={handleSendMessage}
                disabled={!message.trim()}
                size="sm"
                className="rounded-full w-8 h-8 sm:w-10 sm:h-10 p-0 bg-green-500 hover:bg-green-600 flex-shrink-0"
              >
                <Send className="h-3 w-3 sm:h-4 sm:w-4" />
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}