'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  Settings,
  Activity,
  DollarSign,
  Users,
  CreditCard,
  Eye,
  EyeOff
} from 'lucide-react'
import { formatCurrency, formatDateTime } from '@/lib/financeiro-helpers'
import apiClient from '@/lib/api-client'

interface AsaasConfig {
  api_key: string
  sandbox: boolean
  enabled: boolean
  last_sync: string | null
}

interface AsaasStats {
  total_customers: number
  total_payments: number
  pending_payments: number
  confirmed_payments: number
  total_revenue: number
  last_payment_date: string | null
}

interface AsaasStatus {
  api_connected: boolean
  last_check: string
  error_message: string | null
}

export default function AsaasConfigPage() {
  const [config, setConfig] = useState<AsaasConfig>({
    api_key: '',
    sandbox: true,
    enabled: false,
    last_sync: null
  })
  
  const [stats, setStats] = useState<AsaasStats>({
    total_customers: 0,
    total_payments: 0,
    pending_payments: 0,
    confirmed_payments: 0,
    total_revenue: 0,
    last_payment_date: null
  })
  
  const [status, setStatus] = useState<AsaasStatus>({
    api_connected: false,
    last_check: '',
    error_message: null
  })
  
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [showApiKey, setShowApiKey] = useState(false)
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)

  // Carregar configurações (execução única ao montar)
  useEffect(() => {
    loadConfig()
    loadStats()
    checkStatus()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadConfig = async () => {
    try {
      const { data } = await apiClient.get('/asaas/config/')
      setConfig(data)
    } catch (error) {
      console.error('Erro ao carregar configuração:', error)
    }
  }

  const loadStats = async () => {
    try {
      const { data } = await apiClient.get('/asaas/stats/')
      setStats(data)
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error)
    }
  }

  const checkStatus = async () => {
    try {
      const { data } = await apiClient.get('/asaas/status/')
      setStatus(data)
    } catch (error) {
      console.error('Erro ao verificar status:', error)
    }
  }

  const saveConfig = async () => {
    setSaving(true)
    try {
      const { data } = await apiClient.post('/asaas/config/', config)
      setMessage({ type: 'success', text: data.message || 'Configuração salva com sucesso!' })
      checkStatus()
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Erro de conexão ao salvar configuração'
      })
    } finally {
      setSaving(false)
    }
  }

  const testConnection = async () => {
    setLoading(true)
    try {
      const { data } = await apiClient.post('/asaas/test/')
      setMessage({ type: 'success', text: data.message || 'Conexão com Asaas testada com sucesso!' })
      setStatus(prev => ({ ...prev, api_connected: true, error_message: null }))
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Erro de conexão ao testar API' })
      setStatus(prev => ({ ...prev, api_connected: false, error_message: err.response?.data?.detail || null }))
    } finally {
      setLoading(false)
    }
  }

  const syncPayments = async () => {
    setSyncing(true)
    try {
      const { data } = await apiClient.post('/asaas/sync/')
      setMessage({ type: 'success', text: `Sincronização concluída! ${data.synced_count} pagamentos sincronizados.` })
      loadStats()
      setConfig(prev => ({ ...prev, last_sync: new Date().toISOString() }))
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Erro de conexão na sincronização' })
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className="w-full max-w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Configuração Asaas</h1>
          <p className="text-muted-foreground">
            Configure e monitore a integração com a API do Asaas
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge variant={status.api_connected ? "default" : "destructive"}>
            {status.api_connected ? (
              <>
                <CheckCircle className="w-4 h-4 mr-1" />
                Conectado
              </>
            ) : (
              <>
                <XCircle className="w-4 h-4 mr-1" />
                Desconectado
              </>
            )}
          </Badge>
        </div>
      </div>

      {message && (
        <Alert variant={message.type === 'error' ? 'destructive' : 'default'}>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{message.text}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="config" className="space-y-4">
        <TabsList>
          <TabsTrigger value="config">
            <Settings className="w-4 h-4 mr-2" />
            Configuração
          </TabsTrigger>
          <TabsTrigger value="monitoring">
            <Activity className="w-4 h-4 mr-2" />
            Monitoramento
          </TabsTrigger>
        </TabsList>

        <TabsContent value="config" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Configurações da API</CardTitle>
              <CardDescription>
                Configure sua chave de API e preferências do Asaas
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  saveConfig()
                }}
                className="space-y-4"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="api_key">Chave da API Asaas</Label>
                    <div className="relative">
                      <Input
                        id="api_key"
                        name="api_key"
                        type={showApiKey ? 'text' : 'password'}
                        autoComplete="off"
                        value={config.api_key}
                        onChange={(e) => setConfig(prev => ({ ...prev, api_key: e.target.value }))}
                        placeholder="$aact_YTU5YjRlM2..."
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3"
                        onClick={() => setShowApiKey(!showApiKey)}
                      >
                        {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Ambiente</Label>
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        variant={config.sandbox ? 'default' : 'outline'}
                        onClick={() => setConfig(prev => ({ ...prev, sandbox: true }))}
                      >
                        Sandbox
                      </Button>
                      <Button
                        type="button"
                        variant={!config.sandbox ? 'default' : 'outline'}
                        onClick={() => setConfig(prev => ({ ...prev, sandbox: false }))}
                      >
                        Produção
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="enabled"
                    checked={config.enabled}
                    onChange={(e) => setConfig(prev => ({ ...prev, enabled: e.target.checked }))}
                    className="rounded"
                  />
                  <Label htmlFor="enabled">Habilitar integração Asaas</Label>
                </div>

                <div className="flex gap-2">
                  <Button type="submit" disabled={saving}>
                    {saving ? 'Salvando...' : 'Salvar Configuração'}
                  </Button>
                  <Button type="button" variant="outline" onClick={testConnection} disabled={loading}>
                    {loading ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Testando...
                      </>
                    ) : (
                      'Testar Conexão'
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {status.error_message && (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertDescription>
                <strong>Erro na API:</strong> {status.error_message}
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>

        <TabsContent value="monitoring" className="space-y-4">
          {/* Estatísticas */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total de Clientes</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_customers}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total de Pagamentos</CardTitle>
                <CreditCard className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_payments}</div>
                <p className="text-xs text-muted-foreground">
                  {stats.pending_payments} pendentes
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Receita Total</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(stats.total_revenue)}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Última Sincronização</CardTitle>
                <RefreshCw className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-sm">{formatDateTime(config.last_sync, 'Nunca')}</div>
              </CardContent>
            </Card>
          </div>

          {/* Controles de Sincronização */}
          <Card>
            <CardHeader>
              <CardTitle>Sincronização</CardTitle>
              <CardDescription>
                Sincronize pagamentos e clientes com a API do Asaas
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Button onClick={syncPayments} disabled={syncing || !config.enabled}>
                  {syncing ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Sincronizando...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Sincronizar Agora
                    </>
                  )}
                </Button>
                <Button variant="outline" onClick={loadStats}>
                  Atualizar Estatísticas
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Status da API */}
          <Card>
            <CardHeader>
              <CardTitle>Status da API</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Status da Conexão:</span>
                  <Badge variant={status.api_connected ? "default" : "destructive"}>
                    {status.api_connected ? "Conectado" : "Desconectado"}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span>Última Verificação:</span>
                  <span className="text-sm text-muted-foreground">
                    {formatDateTime(status.last_check, 'Nunca')}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Ambiente:</span>
                  <Badge variant={config.sandbox ? "secondary" : "default"}>
                    {config.sandbox ? "Sandbox" : "Produção"}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}