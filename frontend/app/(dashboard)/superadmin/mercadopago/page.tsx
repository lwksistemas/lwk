'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Script from 'next/script'
import apiClient from '@/lib/api-client'
import { authService } from '@/lib/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CheckCircle, XCircle, Settings, Eye, EyeOff, ArrowLeft, Key, PlayCircle } from 'lucide-react'

declare global {
  interface Window {
    MercadoPago?: new (publicKey: string) => { getInstallments?: (params: unknown) => Promise<unknown> }
  }
}

interface MercadoPagoConfigState {
  enabled: boolean
  use_for_boletos: boolean
  access_token_set: boolean
  access_token_masked: string
  public_key: string
  chave_pix_estatica: string
}

export default function MercadoPagoConfigPage() {
  const router = useRouter()
  const [config, setConfig] = useState<MercadoPagoConfigState>({
    enabled: false,
    use_for_boletos: false,
    access_token_set: false,
    access_token_masked: '',
    public_key: '',
    chave_pix_estatica: '',
  })
  const [accessToken, setAccessToken] = useState('')
  const [publicKey, setPublicKey] = useState('')
  const [showToken, setShowToken] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [sdkReady, setSdkReady] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const initMercadoPago = useCallback((publicKeyValue: string) => {
    if (typeof window === 'undefined' || !publicKeyValue.trim() || !window.MercadoPago) return
    try {
      new window.MercadoPago(publicKeyValue.trim())
      setSdkReady(true)
    } catch {
      setSdkReady(false)
    }
  }, [])

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login')
      return
    }
    loadConfig()
  }, [router])

  const loadConfig = async () => {
    try {
      setLoading(true)
      const { data } = await apiClient.get('/superadmin/mercadopago-config/')
      setConfig(data)
      if (data.public_key) {
        setPublicKey(data.public_key)
        if (typeof window !== 'undefined' && window.MercadoPago) {
          initMercadoPago(data.public_key)
        }
      }
    } catch (err) {
      console.error('Erro ao carregar configuração Mercado Pago:', err)
      setMessage({ type: 'error', text: 'Erro ao carregar configuração. Verifique se está logado como superadmin.' })
    } finally {
      setLoading(false)
    }
  }

  const testConnection = async () => {
    setMessage(null)
    setTesting(true)
    try {
      const { data } = await apiClient.get('/superadmin/mercadopago-config/test/')
      if (data.success) {
        setMessage({ type: 'success', text: data.message || 'Conexão com a API do Mercado Pago OK.' })
      } else {
        setMessage({ type: 'error', text: data.error || 'Falha no teste.' })
      }
    } catch (err: unknown) {
      const ax = err && typeof err === 'object' && 'response' in err ? (err as { response?: { data?: { error?: string } } }).response : undefined
      const errorMsg = ax?.data?.error
      setMessage({ type: 'error', text: typeof errorMsg === 'string' ? errorMsg : 'Erro ao testar conexão. Verifique o Access Token.' })
    } finally {
      setTesting(false)
    }
  }

  const saveConfig = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setMessage(null)
    try {
      const body: { enabled?: boolean; use_for_boletos?: boolean; access_token?: string; public_key?: string; chave_pix_estatica?: string } = {
        enabled: config.enabled,
        use_for_boletos: config.use_for_boletos,
        chave_pix_estatica: config.chave_pix_estatica.trim(),
      }
      if (accessToken.trim()) body.access_token = accessToken.trim()
      body.public_key = publicKey.trim()
      await apiClient.patch('/superadmin/mercadopago-config/', body)
      setMessage({ type: 'success', text: 'Configuração salva com sucesso!' })
      setAccessToken('')
      await loadConfig()
      if (publicKey.trim()) initMercadoPago(publicKey.trim())
    } catch (err: unknown) {
      const ax = err && typeof err === 'object' && 'response' in err ? (err as { response?: { data?: { detail?: string } } }).response : undefined
      const detail = ax?.data?.detail
      setMessage({ type: 'error', text: typeof detail === 'string' ? detail : 'Erro ao salvar configuração.' })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="w-full max-w-full px-4 sm:px-6 lg:px-8 py-6 flex items-center justify-center min-h-[300px]">
        <p className="text-gray-500">Carregando...</p>
      </div>
    )
  }

  return (
    <div className="w-full max-w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* SDK Mercado Pago - ambiente de desenvolvimento (client-side) */}
      <Script
        src="https://sdk.mercadopago.com/js/v2"
        strategy="afterInteractive"
        onLoad={() => {
          if (config.public_key && typeof window !== 'undefined' && window.MercadoPago) {
            initMercadoPago(config.public_key)
          }
        }}
      />
      <div className="flex items-center gap-4">
        <Link
          href="/superadmin/dashboard"
          className="flex items-center text-purple-600 hover:text-purple-800"
        >
          <ArrowLeft className="w-5 h-5 mr-1" />
          Voltar ao dashboard
        </Link>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Configuração Mercado Pago</h1>
          <p className="text-muted-foreground">
            Configure a integração para gerar boletos das lojas via Mercado Pago
          </p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {config.access_token_set && (
            <span className="inline-flex items-center text-green-600">
              <CheckCircle className="w-4 h-4 mr-1" />
              Token configurado
            </span>
          )}
          {config.public_key ? (
            <span className="inline-flex items-center text-green-600">
              <Key className="w-4 h-4 mr-1" />
              Public Key configurada
            </span>
          ) : (
            <span className="inline-flex items-center text-amber-600">
              <XCircle className="w-4 h-4 mr-1" />
              Public Key não configurada
            </span>
          )}
          {sdkReady && (
            <span className="inline-flex items-center text-blue-600">
              <CheckCircle className="w-4 h-4 mr-1" />
              SDK MercadoPago.js inicializado
            </span>
          )}
        </div>
      </div>

      {message && (
        <Alert variant={message.type === 'error' ? 'destructive' : 'default'}>
          <AlertDescription>{message.text}</AlertDescription>
        </Alert>
      )}

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Configurações da API
          </CardTitle>
          <CardDescription>
            Crie uma aplicação em{' '}
            <a
              href="https://www.mercadopago.com.br/settings/account/applications/create-app"
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-600 underline"
            >
              Mercado Pago – Suas integrações
            </a>
            . Use a <strong>Public Key</strong> (teste ou produção) para inicializar o SDK no frontend e o <strong>Access Token</strong> no backend para gerar boletos. Ao criar uma nova loja, você pode escolher Asaas ou Mercado Pago.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={saveConfig} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="public_key">Public Key (para o frontend – teste ou produção)</Label>
              <Input
                id="public_key"
                type="text"
                placeholder="APP_USR-xxxx ou TEST-xxxx"
                value={publicKey}
                onChange={(e) => setPublicKey(e.target.value)}
                className="font-mono text-sm"
              />
              <p className="text-xs text-gray-500">
                Usada para inicializar a biblioteca MercadoPago.js no frontend. Pode ser exposta no cliente.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="access_token">Access Token (Produção ou Teste)</Label>
              <div className="flex gap-2">
                <Input
                  id="access_token"
                  type={showToken ? 'text' : 'password'}
                  placeholder={config.access_token_set ? config.access_token_masked : 'Cole o Access Token aqui'}
                  value={accessToken}
                  onChange={(e) => setAccessToken(e.target.value)}
                  autoComplete="off"
                  className="font-mono text-sm"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => setShowToken(!showToken)}
                  aria-label={showToken ? 'Ocultar token' : 'Mostrar token'}
                >
                  {showToken ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </Button>
              </div>
              <p className="text-xs text-gray-500">
                Usado apenas no backend para criar pagamentos. Deixe em branco para não alterar o token já salvo.
              </p>
            </div>

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.enabled}
                  onChange={(e) => setConfig((c) => ({ ...c, enabled: e.target.checked }))}
                  className="rounded border-gray-300"
                />
                <span>Integração habilitada</span>
              </label>
            </div>

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.use_for_boletos}
                  onChange={(e) => setConfig((c) => ({ ...c, use_for_boletos: e.target.checked }))}
                  className="rounded border-gray-300"
                />
                <span>Usar Mercado Pago como padrão para novos boletos</span>
              </label>
            </div>
            <p className="text-xs text-gray-500">
              Se marcado, ao criar uma nova loja o padrão será Mercado Pago; você ainda pode escolher Asaas no formulário de nova loja.
            </p>

            <div className="space-y-2">
              <Label htmlFor="chave_pix_estatica">Chave PIX estática (fallback)</Label>
              <Input
                id="chave_pix_estatica"
                type="text"
                placeholder="Ex.: 6beb2cc6-3d68-48a1-820d-03aae62d8b44"
                value={config.chave_pix_estatica}
                onChange={(e) => setConfig((c) => ({ ...c, chave_pix_estatica: e.target.value }))}
                className="font-mono text-sm"
              />
              <p className="text-xs text-gray-500">
                Exibida na página do boleto/assinatura da loja quando não houver PIX dinâmico do Mercado Pago. O cliente pode copiar e colar para pagar via PIX (pagamento manual).
              </p>
            </div>

            <div className="pt-2 flex flex-wrap gap-2">
              <Button type="submit" disabled={saving}>
                {saving ? 'Salvando...' : 'Salvar configuração'}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={testConnection}
                disabled={testing || !config.access_token_set}
              >
                <PlayCircle className="w-4 h-4 mr-2" />
                {testing ? 'Testando...' : 'Testar conexão com a API'}
              </Button>
            </div>
            <p className="text-xs text-gray-500">
              O teste valida o Access Token e verifica se o boleto (bolbradesco) está disponível. Para o sistema atualizar a assinatura quando um boleto for pago, configure no Mercado Pago (Suas integrações → Webhooks) a URL do webhook: <strong>https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/mercadopago-webhook/</strong> e o evento <strong>payment</strong>.
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
