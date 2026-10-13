'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'
import apiClient from '@/lib/api-client'
import { authService } from '@/lib/auth'
import { logger } from '@/lib/logger'

type ProvedorId = 'asaas' | 'mercadopago'

interface ProvedorCard {
  id: ProvedorId
  nome: string
  recebe: string
  href: string
  padrao: boolean
  configurado: boolean
  detalhe: string
}

export default function RecebimentoAssinaturasPage() {
  const router = useRouter()
  const [provedores, setProvedores] = useState<ProvedorCard[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login')
      return
    }
    carregar()
  }, [router])

  const carregar = async () => {
    const [asaas, statusAsaas, mercadoPago] = await Promise.all([
      apiClient.get('/asaas/config/').then((r) => r.data).catch((err) => {
        logger.warn('Erro ao carregar Asaas:', err)
        return null
      }),
      apiClient.get('/asaas/status/').then((r) => r.data).catch(() => null),
      apiClient.get('/superadmin/mercadopago-config/').then((r) => r.data).catch((err) => {
        logger.warn('Erro ao carregar Mercado Pago:', err)
        return null
      }),
    ])

    const mpPadrao = Boolean(mercadoPago && mercadoPago.use_for_boletos)
    const asaasLigado = Boolean(asaas && (asaas.enabled || asaas.api_key_configured))
    const mpLigado = Boolean(mercadoPago && (mercadoPago.enabled || mercadoPago.access_token_set))

    setProvedores([
      {
        id: 'asaas',
        nome: 'Asaas',
        recebe: 'Boleto, Pix e cartão recorrente',
        href: '/superadmin/asaas',
        padrao: !mpPadrao,
        configurado: asaasLigado || Boolean(statusAsaas && statusAsaas.api_connected),
        detalhe: statusAsaas?.api_connected
          ? 'Conexão com a API ativa'
          : asaasLigado
            ? 'Chave salva. Vale testar a conexão na configuração.'
            : 'Ainda sem chave salva',
      },
      {
        id: 'mercadopago',
        nome: 'Mercado Pago',
        recebe: 'Boleto e Pix',
        href: '/superadmin/mercadopago',
        padrao: mpPadrao,
        configurado: mpLigado,
        detalhe: mercadoPago?.access_token_set
          ? 'Access token salvo'
          : 'Ainda sem access token',
      },
    ])
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="w-full max-w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        <div className="flex items-center gap-4">
          <Link
            href="/superadmin/dashboard"
            className="flex items-center text-gray-500 hover:text-gray-900 dark:hover:text-gray-100"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Recebimento das assinaturas</h1>
            <p className="text-gray-600 dark:text-gray-400">
              Um provedor cobra a próxima mensalidade. O outro continua valendo para boleto que já foi emitido.
            </p>
          </div>
        </div>

        {loading ? (
          <p className="text-gray-500">Carregando...</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {provedores.map((provedor) => (
              <article
                key={provedor.id}
                className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 shadow-sm flex flex-col gap-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">{provedor.nome}</h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{provedor.recebe}</p>
                  </div>
                  {provedor.padrao ? (
                    <span className="shrink-0 text-xs font-medium px-2 py-1 rounded-full bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-200">
                      Padrão das novas lojas
                    </span>
                  ) : null}
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300">{provedor.detalhe}</p>
                <Link
                  href={provedor.href}
                  className="inline-flex justify-center mt-auto px-4 py-2 rounded-md bg-purple-700 hover:bg-purple-800 text-white text-sm font-medium"
                >
                  Configurar
                </Link>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
