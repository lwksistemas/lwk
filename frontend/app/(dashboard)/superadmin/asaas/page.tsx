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
  EyeOff,
  ArrowLeft,
  ClipboardCheck,
  Mail,
  FileText,
  Webhook,
} from 'lucide-react'
import Link from 'next/link'
import { formatCurrency, formatDateTime } from '@/lib/financeiro-helpers'
import apiClient from '@/lib/api-client'
import { logger } from '@/lib/logger'

interface AsaasConfig {
  api_key: string
  api_key_masked?: string
  api_key_configured?: boolean
  api_key_length?: number
  sandbox: boolean
  enabled: boolean
  last_sync: string | null
  webhook_url?: string
  webhook_token?: string
  webhook_token_configured?: boolean
  webhook_token_length?: number
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

interface DiagnosticoCheck {
  id: string
  label: string
  ok: boolean
  level: 'ok' | 'warn' | 'error'
  message: string
  details: string[]
  action_path: string
}

interface DiagnosticoResponse {
  ready: boolean
  summary: string
  cadastro_fluxo: { ok: boolean; message: string }
  checks: DiagnosticoCheck[]
  checked_at: string
}

export default function AsaasConfigPage() {
  const [config, setConfig] = useState<AsaasConfig>({
    api_key: '',
    sandbox: true,
    enabled: false,
    last_sync: null
  })
  const [apiKeyInput, setApiKeyInput] = useState('')
  
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
  const [showWebhookToken, setShowWebhookToken] = useState(false)
  const [webhookToken, setWebhookToken] = useState('')
  const [webhookUrl, setWebhookUrl] = useState('')
  const [webhookConfigured, setWebhookConfigured] = useState(false)
  const [webhookTokenLength, setWebhookTokenLength] = useState(0)
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)
  const [diagnostico, setDiagnostico] = useState<DiagnosticoResponse | null>(null)
  const [diagLoading, setDiagLoading] = useState(false)

  // Carregar configurações (execução única ao montar)
  useEffect(() => {
    loadConfig()
    loadStats()
    checkStatus()
    loadDiagnostico()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadConfig = async () => {
    try {
      const { data } = await apiClient.get('/asaas/config/')
      setConfig(data)
      setApiKeyInput('')
      setWebhookUrl(data.webhook_url || '')
      setWebhookConfigured(Boolean(data.webhook_token_configured))
      setWebhookTokenLength(data.webhook_token_length || 0)
      setWebhookToken('')
    } catch (error) {
      logger.warn('Erro ao carregar configuração Asaas:', error)
    }
  }

  const loadStats = async () => {
    try {
      const { data } = await apiClient.get('/asaas/stats/')
      setStats(data)
    } catch (error) {
      logger.warn('Erro ao carregar estatísticas Asaas:', error)
    }
  }

  const checkStatus = async () => {
    try {
      const { data } = await apiClient.get('/asaas/status/')
      setStatus(data)
    } catch (error) {
      logger.warn('Erro ao verificar status Asaas:', error)
    }
  }

  const loadDiagnostico = async () => {
    setDiagLoading(true)
    try {
      const { data } = await apiClient.get('/asaas/diagnostico/')
      setDiagnostico(data)
    } catch (error) {
      logger.warn('Erro ao carregar diagnóstico:', error)
    } finally {
      setDiagLoading(false)
    }
  }

  const checkIconForLevel = (level: DiagnosticoCheck['level']) => {
    if (level === 'ok') return <CheckCircle className="h-5 w-5 text-green-600" />
    if (level === 'warn') return <AlertCircle className="h-5 w-5 text-amber-600" />
    return <XCircle className="h-5 w-5 text-destructive" />
  }

  const badgeVariantForLevel = (level: DiagnosticoCheck['level']) => {
    if (level === 'ok') return 'default' as const
    if (level === 'warn') return 'secondary' as const
    return 'destructive' as const
  }

  const iconForCheck = (id: string) => {
    if (id === 'email') return <Mail className="h-4 w-4" />
    if (id === 'nfse') return <FileText className="h-4 w-4" />
    if (id === 'asaas_webhook') return <Webhook className="h-4 w-4" />
    return <CreditCard className="h-4 w-4" />
  }

  const saveConfig = async () => {
    setSaving(true)
    try {
      const payload: Record<string, unknown> = {
        enabled: config.enabled,
        sandbox: config.sandbox,
      }
      if (apiKeyInput.trim()) {
        payload.api_key = apiKeyInput.trim()
      }
      if (webhookToken.trim()) {
        payload.webhook_token = webhookToken.trim()
      }
      const { data } = await apiClient.post('/asaas/config/', payload)
      setMessage({ type: 'success', text: data.message || 'Configuração salva com sucesso!' })
      setWebhookUrl(data.webhook_url || webhookUrl)
      setWebhookConfigured(Boolean(data.webhook_token_configured))
      setWebhookTokenLength(data.webhook_token_length || 0)
      setWebhookToken('')
      if (data.api_key_masked !== undefined) {
        setConfig(prev => ({
          ...prev,
          api_key: '',
          api_key_masked: data.api_key_masked,
          api_key_configured: data.api_key_configured,
          api_key_length: data.api_key_length,
          sandbox: data.sandbox,
          enabled: data.enabled,
        }))
      }
      setApiKeyInput('')
      checkStatus()
      loadDiagnostico()
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

  const copyWebhookUrl = async () => {
    if (!webhookUrl) return
    try {
      await navigator.clipboard.writeText(webhookUrl)
      setMessage({ type: 'success', text: 'URL do webhook copiada!' })
    } catch {
      setMessage({ type: 'error', text: 'Não foi possível copiar a URL' })
    }
  }

  const copyWebhookToken = async () => {
    if (!webhookToken.trim()) {
      setMessage({
        type: 'error',
        text: 'Digite o token completo no campo abaixo para copiar e colar no painel Asaas.',
      })
      return
    }
    try {
      await navigator.clipboard.writeText(webhookToken.trim())
      setMessage({ type: 'success', text: 'Token copiado! Cole no painel Asaas → Integrações → Webhooks.' })
    } catch {
      setMessage({ type: 'error', text: 'Não foi possível copiar o token' })
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
        <div className="flex items-center gap-4">
          <Link
            href="/superadmin/dashboard"
            className="flex items-center text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold">Configuração Asaas</h1>
            <p className="text-muted-foreground">
              Configure e monitore a integração com a API do Asaas
            </p>
          </div>
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
          <TabsTrigger value="diagnostico">
            <ClipboardCheck className="w-4 h-4 mr-2" />
            Diagnóstico
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
                        value={apiKeyInput}
                        onChange={(e) => setApiKeyInput(e.target.value)}
                        placeholder="Cole a chave completa de Asaas → Integrações → API"
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
                    {config.api_key_configured && config.api_key_masked && (
                      <p className="text-xs text-muted-foreground">
                        Chave salva: {config.api_key_masked}
                        {config.api_key_length ? ` (${config.api_key_length} caracteres)` : ''}
                        {' — deixe o campo vazio para manter'}
                      </p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      Sandbox: chave contém <code>hmlg</code>. Produção: sem <code>hmlg</code>.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label>Ambiente detectado</Label>
                    <div className="flex gap-2 items-center">
                      <Badge variant={config.sandbox ? 'secondary' : 'default'}>
                        {config.sandbox ? 'Sandbox' : 'Produção'}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        Definido automaticamente pela chave salva
                      </span>
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

          <Card>
            <CardHeader>
              <CardTitle>Webhook de pagamentos</CardTitle>
              <CardDescription>
                Confirmação automática de PIX/boleto após cadastro (senha provisória + NFS-e)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={webhookConfigured ? 'default' : 'destructive'}>
                  {webhookConfigured ? (
                    <>
                      <CheckCircle className="w-4 h-4 mr-1" />
                      Token configurado ({webhookTokenLength} caracteres)
                    </>
                  ) : (
                    <>
                      <XCircle className="w-4 h-4 mr-1" />
                      Token não configurado
                    </>
                  )}
                </Badge>
              </div>

              <div className="space-y-2">
                <Label>URL do webhook (cole no painel Asaas)</Label>
                <div className="flex flex-col gap-2 sm:flex-row">
                  <Input
                    readOnly
                    value={webhookUrl}
                    className="font-mono text-sm"
                  />
                  <Button type="button" variant="outline" onClick={copyWebhookUrl} disabled={!webhookUrl}>
                    Copiar URL
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="webhook_token">Token de autenticação</Label>
                <div className="relative">
                  <Input
                    id="webhook_token"
                    type={showWebhookToken ? 'text' : 'password'}
                    autoComplete="off"
                    value={webhookToken}
                    onChange={(e) => setWebhookToken(e.target.value)}
                    placeholder={
                      webhookConfigured
                        ? 'Deixe vazio para manter o token atual — ou cole um novo (mín. 32 caracteres)'
                        : 'Cole o token do Asaas ou gere um novo e salve aqui'
                    }
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3"
                    onClick={() => setShowWebhookToken(!showWebhookToken)}
                  >
                    {showWebhookToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
                {config.webhook_token && (
                  <p className="text-xs text-muted-foreground">
                    Token salvo: {config.webhook_token}
                  </p>
                )}
              </div>

              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription className="text-sm space-y-2">
                  <p>
                    No <strong>Asaas</strong> → Integrações → Webhooks → <strong>LWK Sistemas</strong>:
                  </p>
                  <ol className="list-decimal list-inside space-y-1">
                    <li>URL: use a URL acima</li>
                    <li>Token: o mesmo valor salvo aqui (copie o token completo — Asaas exige 32+ caracteres)</li>
                    <li>Ative o webhook e aguarde a fila de sincronização retomar</li>
                  </ol>
                </AlertDescription>
              </Alert>

              <Button type="button" variant="outline" onClick={copyWebhookToken}>
                Copiar token para o Asaas
              </Button>
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

        <TabsContent value="diagnostico" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-start justify-between gap-4">
              <div>
                <CardTitle>Diagnóstico do cadastro (PIX → senha + NFS-e)</CardTitle>
                <CardDescription>
                  Verifica se o fluxo automático após pagamento está pronto
                </CardDescription>
              </div>
              <Button variant="outline" size="sm" onClick={loadDiagnostico} disabled={diagLoading}>
                {diagLoading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Atualizar
                  </>
                )}
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              {diagnostico ? (
                <>
                  <Alert variant={diagnostico.ready ? 'default' : 'destructive'}>
                    {diagnostico.ready ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : (
                      <XCircle className="h-4 w-4" />
                    )}
                    <AlertDescription>
                      <p className="font-medium">{diagnostico.cadastro_fluxo.message}</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        {diagnostico.summary} · verificado em{' '}
                        {formatDateTime(diagnostico.checked_at, '—')}
                      </p>
                    </AlertDescription>
                  </Alert>

                  <div className="space-y-3">
                    {diagnostico.checks.map((check) => (
                      <div
                        key={check.id}
                        className="rounded-lg border p-4 space-y-2"
                      >
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <div className="flex items-start gap-3">
                            {checkIconForLevel(check.level)}
                            <div>
                              <div className="flex items-center gap-2 font-medium">
                                {iconForCheck(check.id)}
                                {check.label}
                              </div>
                              <p className="text-sm text-muted-foreground mt-1">{check.message}</p>
                            </div>
                          </div>
                          <Badge variant={badgeVariantForLevel(check.level)}>
                            {check.level === 'ok' ? 'OK' : check.level === 'warn' ? 'Aviso' : 'Pendente'}
                          </Badge>
                        </div>
                        {check.details.length > 0 && (
                          <ul className="text-sm text-muted-foreground list-disc list-inside ml-8 space-y-1">
                            {check.details.map((detail, idx) => (
                              <li key={idx} className="break-all">{detail}</li>
                            ))}
                          </ul>
                        )}
                        {check.action_path && check.level !== 'ok' && (
                          <Link
                            href={check.action_path}
                            className="inline-block text-sm text-blue-600 hover:underline ml-8"
                          >
                            Ir para configuração →
                          </Link>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">
                  {diagLoading ? 'Carregando diagnóstico…' : 'Não foi possível carregar o diagnóstico.'}
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}