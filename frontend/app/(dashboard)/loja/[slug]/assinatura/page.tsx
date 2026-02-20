'use client'

import { useState, useEffect, useCallback } from 'react'
import Image from 'next/image'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  CreditCard,
  Download,
  RefreshCw,
  CheckCircle,
  Clock,
  AlertTriangle,
  Copy,
  ArrowLeft,
} from 'lucide-react'
import apiClient from '@/lib/api-client'
import { formatCurrency, formatDate } from '@/lib/financeiro-helpers'
import { useClinicaBelezaDark } from '@/hooks/useClinicaBelezaDark'

interface AssinaturaData {
  loja: {
    id: number
    nome: string
    slug: string
    plano: string
    tipo_assinatura: string
  }
  financeiro: {
    status_pagamento: string
    valor_mensalidade: number
    data_proxima_cobranca: string
    dia_vencimento: number
    tem_asaas: boolean
    boleto_url: string
    pix_qr_code: string
    pix_copy_paste: string
  }
  proximo_pagamento: {
    id: number
    valor: number
    data_vencimento: string
    referencia_mes: string
    boleto_url?: string
    asaas_payment_id?: string
  } | null
}

export default function AssinaturaLojaPage() {
  const params = useParams()
  const slug = params.slug as string
  useClinicaBelezaDark()

  const [data, setData] = useState<AssinaturaData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [atualizandoStatus, setAtualizandoStatus] = useState(false)

  const carregarDados = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const { data: dados } = await apiClient.get(`/superadmin/loja/${slug}/financeiro/`)
      setData(dados)
    } catch (err: unknown) {
      console.error('Erro:', err)
      const ax = err && typeof err === 'object' && 'response' in err ? (err as { response?: { status?: number; data?: { error?: string } } }).response : undefined
      const msg = ax?.status === 403
        ? 'Sem permissão para ver assinatura. Apenas o responsável pela loja pode acessar.'
        : (ax?.data?.error || 'Erro de conexão')
      setError(msg)
    } finally {
      setLoading(false)
    }
  }, [slug])

  useEffect(() => {
    carregarDados()
  }, [carregarDados])

  const baixarBoleto = async (pagamentoId: number) => {
    try {
      const response = await apiClient.get(
        `/superadmin/loja-pagamentos/${pagamentoId}/baixar_boleto_pdf/`,
        { responseType: 'blob' }
      )
      const blob = response.data
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `boleto_${slug}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      console.error('Erro ao baixar boleto:', err)
      alert('Erro ao baixar boleto')
    }
  }

  const atualizarStatusAsaas = async () => {
    if (!data?.financeiro.tem_asaas) return

    try {
      setAtualizandoStatus(true)
      await apiClient.post(`/superadmin/loja-financeiro/${data.loja.id}/atualizar_status_asaas/`)
      await carregarDados()
      alert('Status atualizado com sucesso!')
    } catch (err) {
      console.error('Erro:', err)
      alert('Erro ao atualizar status')
    } finally {
      setAtualizandoStatus(false)
    }
  }

  const copiarPixCodigo = () => {
    if (data?.financeiro.pix_copy_paste) {
      navigator.clipboard.writeText(data.financeiro.pix_copy_paste)
      alert('Código PIX copiado!')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'ativo':
        return 'default'
      case 'pendente':
        return 'secondary'
      case 'atrasado':
        return 'destructive'
      case 'suspenso':
        return 'destructive'
      default:
        return 'secondary'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'ativo':
        return <CheckCircle className="w-4 h-4" />
      case 'atrasado':
      case 'suspenso':
        return <AlertTriangle className="w-4 h-4" />
      default:
        return <Clock className="w-4 h-4" />
    }
  }

  const pageWrapper = 'min-h-screen bg-gradient-to-br from-pink-50 via-purple-50 to-white dark:from-neutral-900 dark:via-neutral-800 dark:to-neutral-900 text-gray-800 dark:text-gray-100'

  if (loading) {
    return (
      <div className={`${pageWrapper} flex items-center justify-center p-6`}>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className={`${pageWrapper} container mx-auto p-6`}>
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error || 'Dados não encontrados'}</AlertDescription>
        </Alert>
        <Button variant="outline" className="mt-4" asChild>
          <Link href={`/loja/${slug}/dashboard`}>Voltar ao dashboard</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className={`${pageWrapper} container mx-auto p-3 sm:p-6 space-y-4 sm:space-y-6`}>
      {/* Header */}
      <div className="flex flex-col gap-3">
        <Button variant="ghost" size="sm" className="w-fit dark:text-gray-200 dark:hover:bg-neutral-800" asChild>
          <Link href={`/loja/${slug}/dashboard`} className="flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" />
            Voltar ao dashboard
          </Link>
        </Button>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold dark:text-gray-100">Pagar Assinatura</h1>
            <p className="text-sm text-muted-foreground dark:text-gray-400">
              {data.loja.nome} – {data.loja.plano} ({data.loja.tipo_assinatura})
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={getStatusColor(data.financeiro.status_pagamento)} className="text-xs sm:text-sm">
              {getStatusIcon(data.financeiro.status_pagamento)}
              {data.financeiro.status_pagamento}
            </Badge>
            {data.financeiro.tem_asaas && (
              <Button
                variant="outline"
                size="sm"
                onClick={atualizarStatusAsaas}
                disabled={atualizandoStatus}
              >
                {atualizandoStatus ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4 mr-2" />
                )}
                Atualizar status
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Valor e próxima cobrança */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Card className="dark:bg-neutral-800 dark:border-neutral-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-base dark:text-gray-100">Valor da assinatura</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold dark:text-gray-100">{formatCurrency(data.financeiro.valor_mensalidade)}</p>
            <p className="text-xs text-muted-foreground dark:text-gray-400">
              Vencimento todo dia {data.financeiro.dia_vencimento}
            </p>
          </CardContent>
        </Card>
        <Card className="dark:bg-neutral-800 dark:border-neutral-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-base dark:text-gray-100">Próxima cobrança</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xl font-bold dark:text-gray-100">{formatDate(data.financeiro.data_proxima_cobranca)}</p>
          </CardContent>
        </Card>
      </div>

      {/* Boleto / PIX – igual à loja clínica de estética */}
      {data.financeiro.tem_asaas && (data.financeiro.boleto_url || data.financeiro.pix_copy_paste) ? (
        <Card className="dark:bg-neutral-800 dark:border-neutral-700">
          <CardHeader>
            <CardTitle className="dark:text-gray-100">Formas de pagamento</CardTitle>
            <CardDescription className="dark:text-gray-400">
              Pague por boleto bancário ou PIX (API Asaas)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue={data.financeiro.boleto_url ? 'boleto' : 'pix'}>
              <TabsList className="w-full sm:w-auto dark:bg-neutral-700">
                {data.financeiro.boleto_url && (
                  <TabsTrigger value="boleto" className="flex-1 sm:flex-none">
                    Boleto
                  </TabsTrigger>
                )}
                {(data.financeiro.pix_qr_code || data.financeiro.pix_copy_paste) && (
                  <TabsTrigger value="pix" className="flex-1 sm:flex-none">
                    PIX
                  </TabsTrigger>
                )}
              </TabsList>

              {data.financeiro.boleto_url && (
                <TabsContent value="boleto" className="space-y-4 pt-4">
                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="outline"
                      onClick={() => window.open(data.financeiro.boleto_url, '_blank')}
                    >
                      <CreditCard className="w-4 h-4 mr-2" />
                      Abrir boleto
                    </Button>
                    {data.proximo_pagamento?.asaas_payment_id && (
                      <Button onClick={() => baixarBoleto(data.proximo_pagamento!.id)}>
                        <Download className="w-4 h-4 mr-2" />
                        Baixar PDF
                      </Button>
                    )}
                  </div>
                </TabsContent>
              )}

              {(data.financeiro.pix_qr_code || data.financeiro.pix_copy_paste) && (
                <TabsContent value="pix" className="space-y-4 pt-4">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {data.financeiro.pix_qr_code && (
                      <div className="text-center">
                        <h4 className="font-medium mb-2 dark:text-gray-200">QR Code PIX</h4>
                        <div className="bg-white dark:bg-neutral-700 p-4 rounded border dark:border-neutral-600 inline-block">
                          <Image
                            src={`data:image/png;base64,${data.financeiro.pix_qr_code}`}
                            alt="QR Code PIX"
                            width={192}
                            height={192}
                            className="w-32 h-32 sm:w-48 sm:h-48"
                            unoptimized
                          />
                        </div>
                      </div>
                    )}
                    <div>
                      <h4 className="font-medium mb-2 dark:text-gray-200">Código PIX (copia e cola)</h4>
                      <div className="bg-muted dark:bg-neutral-700 p-3 rounded text-sm font-mono break-all dark:text-gray-200">
                        {data.financeiro.pix_copy_paste || '—'}
                      </div>
                      {data.financeiro.pix_copy_paste && (
                        <Button variant="outline" className="mt-2" onClick={copiarPixCodigo}>
                          <Copy className="w-4 h-4 mr-2" />
                          Copiar código
                        </Button>
                      )}
                    </div>
                  </div>
                </TabsContent>
              )}
            </Tabs>
          </CardContent>
        </Card>
      ) : (
        <Card className="dark:bg-neutral-800 dark:border-neutral-700">
          <CardContent className="py-8">
            <p className="text-center text-muted-foreground dark:text-gray-400">
              Nenhum boleto ou PIX disponível no momento. Entre em contato com o suporte para
              regularizar sua assinatura.
            </p>
            <div className="flex justify-center mt-4">
              <Button variant="outline" asChild>
                <Link href={`/loja/${slug}/financeiro`}>Ver área financeira</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Próximo pagamento (card extra quando há proximo_pagamento) */}
      {data.proximo_pagamento && (
        <Card className="dark:bg-neutral-800 dark:border-neutral-700">
          <CardHeader>
            <CardTitle className="text-base dark:text-gray-100">Próximo pagamento</CardTitle>
            <CardDescription className="dark:text-gray-400">
              Vencimento: {formatDate(data.proximo_pagamento.data_vencimento)} – Ref.{' '}
              {formatDate(data.proximo_pagamento.referencia_mes)}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <p className="text-xl font-bold dark:text-gray-100">{formatCurrency(data.proximo_pagamento.valor)}</p>
              <div className="flex gap-2">
                {data.proximo_pagamento.boleto_url && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open(data.proximo_pagamento!.boleto_url, '_blank')}
                  >
                    Ver boleto
                  </Button>
                )}
                {data.proximo_pagamento.asaas_payment_id && (
                  <Button size="sm" onClick={() => baixarBoleto(data.proximo_pagamento!.id)}>
                    <Download className="w-4 h-4 mr-1" />
                    Baixar PDF
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
