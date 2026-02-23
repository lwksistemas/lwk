'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import apiClient from '@/lib/api-client'
import { authService } from '@/lib/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CheckCircle, XCircle, Settings, Eye, EyeOff, ArrowLeft } from 'lucide-react'

interface MercadoPagoConfigState {
  enabled: boolean
  use_for_boletos: boolean
  access_token_set: boolean
  access_token_masked: string
}

export default function MercadoPagoConfigPage() {
  const router = useRouter()
  const [config, setConfig] = useState<MercadoPagoConfigState>({
    enabled: false,
    use_for_boletos: false,
    access_token_set: false,
    access_token_masked: '',
  })
  const [accessToken, setAccessToken] = useState('')
  const [showToken, setShowToken] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

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
    } catch (err) {
      console.error('Erro ao carregar configuração Mercado Pago:', err)
      setMessage({ type: 'error', text: 'Erro ao carregar configuração. Verifique se está logado como superadmin.' })
    } finally {
      setLoading(false)
    }
  }

  const saveConfig = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setMessage(null)
    try {
      const body: { enabled?: boolean; use_for_boletos?: boolean; access_token?: string } = {
        enabled: config.enabled,
        use_for_boletos: config.use_for_boletos,
      }
      if (accessToken.trim()) body.access_token = accessToken.trim()
      await apiClient.patch('/superadmin/mercadopago-config/', body)
      setMessage({ type: 'success', text: 'Configuração salva com sucesso!' })
      setAccessToken('')
      await loadConfig()
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
        <div className="flex items-center gap-2">
          {config.access_token_set ? (
            <span className="inline-flex items-center text-green-600">
              <CheckCircle className="w-4 h-4 mr-1" />
              Token configurado
            </span>
          ) : (
            <span className="inline-flex items-center text-amber-600">
              <XCircle className="w-4 h-4 mr-1" />
              Token não configurado
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
            </a>{' '}
            e cole o Access Token abaixo. Ao criar uma nova loja, você poderá escolher se os boletos serão gerados por Asaas ou Mercado Pago.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={saveConfig} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="access_token">Access Token (Produção ou Teste)</Label>
              <div className="flex gap-2">
                <Input
                  id="access_token"
                  type={showToken ? 'text' : 'password'}
                  placeholder={config.access_token_set ? config.access_token_masked : 'Cole o Access Token aqui'}
                  value={accessToken}
                  onChange={(e) => setAccessToken(e.target.value)}
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
                Deixe em branco para não alterar o token já salvo.
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

            <div className="pt-2 flex gap-2">
              <Button type="submit" disabled={saving}>
                {saving ? 'Salvando...' : 'Salvar configuração'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
