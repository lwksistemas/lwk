'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'
import apiClient from '@/lib/api-client'
import { authService } from '@/lib/auth'

interface CoraConfigState {
  enabled: boolean
  use_for_boletos: boolean
  client_id: string
  credential_ready: boolean
}

export default function CoraConfigPage() {
  const router = useRouter()
  const [config, setConfig] = useState<CoraConfigState>({
    enabled: false,
    use_for_boletos: false,
    client_id: '',
    credential_ready: false,
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [message, setMessage] = useState<{ type: 'ok' | 'error'; text: string } | null>(null)

  const carregar = useCallback(async () => {
    const { data } = await apiClient.get('/superadmin/cora-config/')
    setConfig(data)
  }, [])

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login')
      return
    }
    carregar()
      .catch(() => setMessage({ type: 'error', text: 'Não foi possível carregar a Cora.' }))
      .finally(() => setLoading(false))
  }, [router, carregar])

  const salvar = async () => {
    setSaving(true)
    setMessage(null)
    try {
      const { data } = await apiClient.patch('/superadmin/cora-config/', {
        enabled: config.enabled,
        use_for_boletos: config.use_for_boletos,
      })
      setConfig(data)
      setMessage({ type: 'ok', text: 'Configuração salva.' })
    } catch {
      setMessage({ type: 'error', text: 'Não foi possível salvar.' })
    } finally {
      setSaving(false)
    }
  }

  const testar = async () => {
    setTesting(true)
    setMessage(null)
    try {
      const { data } = await apiClient.post('/superadmin/cora-config/test/')
      const webhook = data.webhook === 'registrado'
        ? 'O aviso de pagamento foi registrado na Cora.'
        : `Cadastre este aviso na Cora: ${data.webhook}`
      setMessage({ type: 'ok', text: `${data.message || 'Conexão ok.'} ${webhook}` })
    } catch {
      setMessage({ type: 'error', text: 'A Cora não aceitou o certificado.' })
    } finally {
      setTesting(false)
    }
  }

  if (loading) {
    return <p className="p-8 text-gray-500">Carregando...</p>
  }

  return (
    <div className="w-full max-w-3xl px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/superadmin/recebimento" className="text-gray-500 hover:text-gray-900">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Cora</h1>
          <p className="text-gray-600">Recebimento das assinaturas — boleto e Pix na conta da LWK</p>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 space-y-4">
        <p className="text-sm text-gray-700 dark:text-gray-300">
          {config.credential_ready
            ? `Certificado ativo. Client-id ${config.client_id}`
            : 'O certificado ainda não foi importado no servidor.'}
        </p>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={config.enabled}
            onChange={(e) => setConfig((prev) => ({ ...prev, enabled: e.target.checked }))}
          />
          Habilitar a Cora
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={config.use_for_boletos}
            onChange={(e) => setConfig((prev) => ({ ...prev, use_for_boletos: e.target.checked }))}
          />
          Usar a Cora nas lojas novas
        </label>
        <p className="text-xs text-gray-500">
          O cartão recorrente continua no Asaas. A Cora cobra boleto e Pix e, quando o pagamento cai, libera e renova a loja.
        </p>
        {message ? (
          <p className={message.type === 'ok' ? 'text-sm text-green-700' : 'text-sm text-red-700'}>{message.text}</p>
        ) : null}
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => void salvar()}
            disabled={saving}
            className="px-4 py-2 rounded-md bg-purple-700 text-white text-sm disabled:opacity-60"
          >
            {saving ? 'Salvando...' : 'Salvar'}
          </button>
          <button
            type="button"
            onClick={() => void testar()}
            disabled={testing || !config.credential_ready}
            className="px-4 py-2 rounded-md border border-gray-300 text-sm disabled:opacity-60"
          >
            {testing ? 'Testando...' : 'Testar conexão'}
          </button>
        </div>
      </div>
    </div>
  )
}
