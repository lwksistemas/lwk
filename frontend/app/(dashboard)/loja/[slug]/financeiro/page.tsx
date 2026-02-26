'use client'

import { useState, useEffect, useCallback } from 'react'
import Image from 'next/image'
import { useParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  DollarSign, 
  Calendar, 
  CreditCard, 
  Download, 
  RefreshCw,
  CheckCircle,
  Clock,
  AlertTriangle,
  QrCode,
  Copy
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/financeiro-helpers'

interface FinanceiroData {
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
    total_pago: number
    total_pendente: number
    tem_asaas: boolean
    tem_mercadopago?: boolean
    provedor_boleto?: 'asaas' | 'mercadopago'
    boleto_url: string
    pix_qr_code: string
    pix_copy_paste: string
  }
  estatisticas: {
    total_pagamentos: number
    pagamentos_pagos: number
    pagamentos_pendentes: number
    pagamentos_atrasados: number
    valor_total_pago: number
    valor_total_pendente: number
    taxa_pagamento: number
  }
  proximo_pagamento: any
  pagamentos_recentes: any[]
}

export default function FinanceiroLojaPage() {
  const params = useParams()
  const slug = params.slug as string
  
  const [data, setData] = useState<FinanceiroData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [atualizandoStatus, setAtualizandoStatus] = useState(false)

  const API_BASE_URL = process.env.NODE_ENV === 'production' 
    ? 'https://lwksistemas-38ad47519238.herokuapp.com' 
    : 'http://localhost:8000'

  const carregarDados = useCallback(async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/api/superadmin/loja/${slug}/financeiro/`, {
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`
        }
      })
      if (response.ok) {
        const dados = await response.json()
        setData(dados)
      } else {
        setError('Erro ao carregar dados financeiros')
      }
    } catch (error) {
      console.error('Erro:', error)
      setError('Erro de conexão')
    } finally {
      setLoading(false)
    }
  }, [slug, API_BASE_URL])

  useEffect(() => {
    carregarDados()
  }, [carregarDados])

  const baixarBoleto = async (pagamentoId: number, mercadopagoPaymentId?: string, provedor?: string) => {
    try {
      // Se for Mercado Pago e tiver o payment_id, usar endpoint direto
      if (provedor === 'mercadopago' && mercadopagoPaymentId) {
        // Buscar URL do boleto diretamente da API do Mercado Pago via backend
        const response = await fetch(`${API_BASE_URL}/api/superadmin/loja-pagamentos/${pagamentoId}/baixar_boleto_pdf/`, {
          headers: {
            'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`
          }
        })
        if (!response.ok) {
          alert('Erro ao abrir boleto')
          return
        }
        const data = await response.json() as { boleto_url?: string; provedor?: string; error?: string }
        if (data.error) {
          alert(data.error)
          return
        }
        if (data.boleto_url) {
          window.open(data.boleto_url, '_blank', 'noopener,noreferrer')
          return
        }
        alert('Link do boleto não disponível')
        return
      }
      
      // Fluxo normal para Asaas
      const response = await fetch(`${API_BASE_URL}/api/superadmin/loja-pagamentos/${pagamentoId}/baixar_boleto_pdf/`, {
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`
        }
      })
      if (!response.ok) {
        alert('Erro ao abrir/baixar boleto')
        return
      }
      const contentType = response.headers.get('content-type') || ''
      const blob = await response.blob()
      // Mercado Pago retorna JSON com link para abrir em nova aba
      if (contentType.includes('application/json')) {
        const text = await blob.text()
        const data = JSON.parse(text) as { boleto_url?: string; provedor?: string }
        if (data?.boleto_url && data.provedor === 'mercadopago') {
          window.open(data.boleto_url, '_blank', 'noopener,noreferrer')
          return
        }
      }
      // Asaas: PDF para download
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `boleto_${slug}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Erro ao baixar boleto:', error)
      alert('Erro ao abrir/baixar boleto')
    }
  }

  const atualizarStatusAsaas = async () => {
    if (!data?.financeiro.tem_asaas) return
    
    try {
      setAtualizandoStatus(true)
      const response = await fetch(`${API_BASE_URL}/api/superadmin/loja-financeiro/${data.loja.id}/atualizar_status_asaas/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`
        }
      })
      
      if (response.ok) {
        await carregarDados() // Recarregar dados
        alert('Status atualizado com sucesso!')
      } else {
        alert('Erro ao atualizar status')
      }
    } catch (error) {
      console.error('Erro:', error)
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
    switch (status.toLowerCase()) {
      case 'ativo': return 'default'
      case 'pendente': return 'secondary'
      case 'atrasado': return 'destructive'
      case 'suspenso': return 'destructive'
      default: return 'secondary'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'ativo': return <CheckCircle className="w-4 h-4" />
      case 'pendente': return <Clock className="w-4 h-4" />
      case 'atrasado': return <AlertTriangle className="w-4 h-4" />
      case 'suspenso': return <AlertTriangle className="w-4 h-4" />
      default: return <Clock className="w-4 h-4" />
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin" />
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error || 'Dados não encontrados'}</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-3 sm:p-6 space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0">
        <div className="w-full sm:w-auto">
          <h1 className="text-2xl sm:text-3xl font-bold">Financeiro</h1>
          <p className="text-sm sm:text-base text-muted-foreground">
            {data.loja.nome} - {data.loja.plano} ({data.loja.tipo_assinatura})
          </p>
        </div>
        
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Badge variant={getStatusColor(data.financeiro.status_pagamento)} className="text-xs sm:text-sm">
            {getStatusIcon(data.financeiro.status_pagamento)}
            {data.financeiro.status_pagamento}
          </Badge>
          
          {data.financeiro.tem_asaas && (
            <Button 
              variant="outline" 
              onClick={atualizarStatusAsaas}
              disabled={atualizandoStatus}
              className="text-xs sm:text-sm min-h-[40px]"
            >
              {atualizandoStatus ? (
                <RefreshCw className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2 animate-spin" />
              ) : (
                <RefreshCw className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
              )}
              <span className="hidden sm:inline">Atualizar Status</span>
              <span className="sm:hidden">Atualizar</span>
            </Button>
          )}
        </div>
      </div>

      {/* Cards de Estatísticas */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 p-4 sm:p-6">
            <CardTitle className="text-xs sm:text-sm font-medium">Mensalidade</CardTitle>
            <DollarSign className="h-3 w-3 sm:h-4 sm:w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent className="p-4 sm:p-6 pt-0">
            <div className="text-xl sm:text-2xl font-bold">{formatCurrency(data.financeiro.valor_mensalidade)}</div>
            <p className="text-xs text-muted-foreground">
              Vencimento dia {data.financeiro.dia_vencimento}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 p-4 sm:p-6">
            <CardTitle className="text-xs sm:text-sm font-medium">Próxima Cobrança</CardTitle>
            <Calendar className="h-3 w-3 sm:h-4 sm:w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent className="p-4 sm:p-6 pt-0">
            <div className="text-xl sm:text-2xl font-bold">{formatDate(data.financeiro.data_proxima_cobranca)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 p-4 sm:p-6">
            <CardTitle className="text-xs sm:text-sm font-medium">Total Pago</CardTitle>
            <CheckCircle className="h-3 w-3 sm:h-4 sm:w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent className="p-4 sm:p-6 pt-0">
            <div className="text-xl sm:text-2xl font-bold">{formatCurrency(data.estatisticas.valor_total_pago)}</div>
            <p className="text-xs text-muted-foreground">
              {data.estatisticas.pagamentos_pagos} pagamentos
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 p-4 sm:p-6">
            <CardTitle className="text-xs sm:text-sm font-medium">Pendente</CardTitle>
            <Clock className="h-3 w-3 sm:h-4 sm:w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent className="p-4 sm:p-6 pt-0">
            <div className="text-xl sm:text-2xl font-bold">{formatCurrency(data.estatisticas.valor_total_pendente)}</div>
            <p className="text-xs text-muted-foreground">
              {data.estatisticas.pagamentos_pendentes + data.estatisticas.pagamentos_atrasados} pagamentos
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Próximo Pagamento */}
      {data.proximo_pagamento && (
        <Card>
          <CardHeader className="p-4 sm:p-6">
            <CardTitle className="text-base sm:text-lg">Próximo Pagamento</CardTitle>
            <CardDescription className="text-xs sm:text-sm">
              Vencimento: {formatDate(data.proximo_pagamento.data_vencimento)}
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 sm:p-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <p className="text-xl sm:text-2xl font-bold">{formatCurrency(data.proximo_pagamento.valor)}</p>
                <p className="text-xs sm:text-sm text-muted-foreground">
                  Referência: {formatDate(data.proximo_pagamento.referencia_mes)}
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
                {data.proximo_pagamento.boleto_url && (
                  <Button 
                    variant="outline"
                    onClick={() => window.open(data.proximo_pagamento.boleto_url, '_blank')}
                    className="text-xs sm:text-sm min-h-[40px] w-full sm:w-auto"
                  >
                    <CreditCard className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                    Ver Boleto
                  </Button>
                )}
                
                {data.proximo_pagamento.asaas_payment_id && (
                  <Button 
                    onClick={() => baixarBoleto(
                      data.proximo_pagamento.id,
                      data.proximo_pagamento.mercadopago_payment_id,
                      data.proximo_pagamento.provedor_boleto || 'asaas'
                    )}
                    className="text-xs sm:text-sm min-h-[40px] w-full sm:w-auto"
                  >
                    <Download className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                    Baixar PDF
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs para Boleto e PIX */}
      {(data.financeiro.tem_asaas || data.financeiro.tem_mercadopago) && (data.financeiro.boleto_url || data.financeiro.pix_qr_code) && (
        <Card>
          <CardHeader className="p-4 sm:p-6">
            <CardTitle className="text-base sm:text-lg">Formas de Pagamento</CardTitle>
          </CardHeader>
          <CardContent className="p-4 sm:p-6">
            <Tabs defaultValue="boleto">
              <TabsList className="w-full sm:w-auto">
                {data.financeiro.boleto_url && (
                  <TabsTrigger value="boleto" className="flex-1 sm:flex-none text-xs sm:text-sm">Boleto</TabsTrigger>
                )}
                {data.financeiro.pix_qr_code && (
                  <TabsTrigger value="pix" className="flex-1 sm:flex-none text-xs sm:text-sm">PIX</TabsTrigger>
                )}
              </TabsList>
              
              {data.financeiro.boleto_url && (
                <TabsContent value="boleto" className="space-y-4">
                  <div className="flex gap-2">
                    <Button 
                      variant="outline"
                      onClick={() => window.open(data.financeiro.boleto_url, '_blank')}
                      className="text-xs sm:text-sm min-h-[40px] w-full sm:w-auto"
                    >
                      <CreditCard className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                      Abrir Boleto
                    </Button>
                  </div>
                </TabsContent>
              )}
              
              {data.financeiro.pix_qr_code && (
                <TabsContent value="pix" className="space-y-4">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <div className="text-center">
                      <h4 className="font-medium mb-2 text-sm sm:text-base">QR Code</h4>
                      <div className="bg-white p-3 sm:p-4 rounded border inline-block">
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
                    
                    <div>
                      <h4 className="font-medium mb-2 text-sm sm:text-base">Código PIX</h4>
                      <div className="bg-gray-100 p-2 sm:p-3 rounded text-xs sm:text-sm font-mono break-all">
                        {data.financeiro.pix_copy_paste}
                      </div>
                      <Button 
                        variant="outline" 
                        className="mt-2 text-xs sm:text-sm min-h-[40px] w-full sm:w-auto"
                        onClick={copiarPixCodigo}
                      >
                        <Copy className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                        Copiar Código
                      </Button>
                    </div>
                  </div>
                </TabsContent>
              )}
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* Histórico de Pagamentos */}
      <Card>
        <CardHeader className="p-4 sm:p-6">
          <CardTitle className="text-base sm:text-lg">Histórico de Pagamentos ({data.pagamentos_recentes.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-4 sm:p-6">
          <div className="space-y-3 sm:space-y-4">
            {data.pagamentos_recentes.map((pagamento) => (
              <div key={pagamento.id} className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-3 sm:p-4 border rounded gap-3">
                <div className="w-full sm:w-auto">
                  <p className="font-medium text-sm sm:text-base">#{pagamento.id}</p>
                  <p className="text-lg sm:text-xl font-bold">{formatCurrency(pagamento.valor)}</p>
                  <p className="text-xs sm:text-sm text-muted-foreground">
                    Vencimento: {formatDate(pagamento.data_vencimento)}
                  </p>
                </div>
                
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 w-full sm:w-auto">
                  <Badge variant={getStatusColor(pagamento.status)} className="text-xs">
                    {getStatusIcon(pagamento.status)}
                    {pagamento.status}
                  </Badge>
                  
                  {/* Botões de ação para pagamentos pendentes */}
                  {pagamento.status.toLowerCase() === 'pendente' && (
                    <div className="flex gap-2 w-full sm:w-auto">
                      {(pagamento.asaas_payment_id || pagamento.mercadopago_payment_id) && (
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => baixarBoleto(
                            pagamento.id,
                            pagamento.mercadopago_payment_id,
                            pagamento.provedor_boleto || 'asaas'
                          )}
                          className="min-h-[36px] flex-1 sm:flex-none"
                        >
                          <Download className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                          <span className="text-xs">Ver Boleto</span>
                        </Button>
                      )}
                      
                      {pagamento.pix_copy_paste && (
                        <Button 
                          variant="default" 
                          size="sm"
                          onClick={() => {
                            navigator.clipboard.writeText(pagamento.pix_copy_paste)
                            alert('Código PIX copiado!')
                          }}
                          className="min-h-[36px] flex-1 sm:flex-none"
                        >
                          <QrCode className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                          <span className="text-xs">Pagar com PIX</span>
                        </Button>
                      )}
                    </div>
                  )}
                  
                  {/* Botão de download para pagamentos pagos */}
                  {pagamento.status.toLowerCase() === 'pago' && (pagamento.asaas_payment_id || pagamento.mercadopago_payment_id) && (
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => baixarBoleto(
                        pagamento.id,
                        pagamento.mercadopago_payment_id,
                        pagamento.provedor_boleto || 'asaas'
                      )}
                      className="min-h-[36px]"
                    >
                      <Download className="w-3 h-3 sm:w-4 sm:h-4" />
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}