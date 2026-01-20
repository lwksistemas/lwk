'use client'

import { useState, useEffect } from 'react'
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

  useEffect(() => {
    carregarDados()
  }, [slug])

  const carregarDados = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/api/superadmin/loja/${slug}/financeiro/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
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
  }

  const baixarBoleto = async (pagamentoId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/superadmin/loja-pagamentos/${pagamentoId}/baixar_boleto_pdf/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      })
      
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `boleto_${slug}.pdf`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        alert('Erro ao baixar boleto')
      }
    } catch (error) {
      console.error('Erro ao baixar boleto:', error)
      alert('Erro ao baixar boleto')
    }
  }

  const atualizarStatusAsaas = async () => {
    if (!data?.financeiro.tem_asaas) return
    
    try {
      setAtualizandoStatus(true)
      const response = await fetch(`${API_BASE_URL}/api/superadmin/loja-financeiro/${data.loja.id}/atualizar_status_asaas/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
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

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR')
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
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Financeiro</h1>
          <p className="text-muted-foreground">
            {data.loja.nome} - {data.loja.plano} ({data.loja.tipo_assinatura})
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge variant={getStatusColor(data.financeiro.status_pagamento)}>
            {getStatusIcon(data.financeiro.status_pagamento)}
            {data.financeiro.status_pagamento}
          </Badge>
          
          {data.financeiro.tem_asaas && (
            <Button 
              variant="outline" 
              onClick={atualizarStatusAsaas}
              disabled={atualizandoStatus}
            >
              {atualizandoStatus ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4 mr-2" />
              )}
              Atualizar Status
            </Button>
          )}
        </div>
      </div>

      {/* Cards de Estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Mensalidade</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(data.financeiro.valor_mensalidade)}</div>
            <p className="text-xs text-muted-foreground">
              Vencimento dia {data.financeiro.dia_vencimento}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Próxima Cobrança</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatDate(data.financeiro.data_proxima_cobranca)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Pago</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(data.estatisticas.valor_total_pago)}</div>
            <p className="text-xs text-muted-foreground">
              {data.estatisticas.pagamentos_pagos} pagamentos
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pendente</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(data.estatisticas.valor_total_pendente)}</div>
            <p className="text-xs text-muted-foreground">
              {data.estatisticas.pagamentos_pendentes + data.estatisticas.pagamentos_atrasados} pagamentos
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Próximo Pagamento */}
      {data.proximo_pagamento && (
        <Card>
          <CardHeader>
            <CardTitle>Próximo Pagamento</CardTitle>
            <CardDescription>
              Vencimento: {formatDate(data.proximo_pagamento.data_vencimento)}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold">{formatCurrency(data.proximo_pagamento.valor)}</p>
                <p className="text-sm text-muted-foreground">
                  Referência: {formatDate(data.proximo_pagamento.referencia_mes)}
                </p>
              </div>
              
              <div className="flex gap-2">
                {data.proximo_pagamento.boleto_url && (
                  <Button 
                    variant="outline"
                    onClick={() => window.open(data.proximo_pagamento.boleto_url, '_blank')}
                  >
                    <CreditCard className="w-4 h-4 mr-2" />
                    Ver Boleto
                  </Button>
                )}
                
                {data.proximo_pagamento.asaas_payment_id && (
                  <Button onClick={() => baixarBoleto(data.proximo_pagamento.id)}>
                    <Download className="w-4 h-4 mr-2" />
                    Baixar PDF
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs para Boleto e PIX */}
      {data.financeiro.tem_asaas && (data.financeiro.boleto_url || data.financeiro.pix_qr_code) && (
        <Card>
          <CardHeader>
            <CardTitle>Formas de Pagamento</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="boleto">
              <TabsList>
                {data.financeiro.boleto_url && (
                  <TabsTrigger value="boleto">Boleto</TabsTrigger>
                )}
                {data.financeiro.pix_qr_code && (
                  <TabsTrigger value="pix">PIX</TabsTrigger>
                )}
              </TabsList>
              
              {data.financeiro.boleto_url && (
                <TabsContent value="boleto" className="space-y-4">
                  <div className="flex gap-2">
                    <Button 
                      variant="outline"
                      onClick={() => window.open(data.financeiro.boleto_url, '_blank')}
                    >
                      <CreditCard className="w-4 h-4 mr-2" />
                      Abrir Boleto
                    </Button>
                  </div>
                </TabsContent>
              )}
              
              {data.financeiro.pix_qr_code && (
                <TabsContent value="pix" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="text-center">
                      <h4 className="font-medium mb-2">QR Code</h4>
                      <div className="bg-white p-4 rounded border inline-block">
                        <img 
                          src={`data:image/png;base64,${data.financeiro.pix_qr_code}`} 
                          alt="QR Code PIX"
                          className="w-48 h-48"
                        />
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-2">Código PIX</h4>
                      <div className="bg-gray-100 p-3 rounded text-sm font-mono break-all">
                        {data.financeiro.pix_copy_paste}
                      </div>
                      <Button 
                        variant="outline" 
                        className="mt-2"
                        onClick={copiarPixCodigo}
                      >
                        <Copy className="w-4 h-4 mr-2" />
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
        <CardHeader>
          <CardTitle>Histórico de Pagamentos</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {data.pagamentos_recentes.map((pagamento) => (
              <div key={pagamento.id} className="flex items-center justify-between p-4 border rounded">
                <div>
                  <p className="font-medium">{formatCurrency(pagamento.valor)}</p>
                  <p className="text-sm text-muted-foreground">
                    {formatDate(pagamento.referencia_mes)} - Venc: {formatDate(pagamento.data_vencimento)}
                  </p>
                </div>
                
                <div className="flex items-center gap-2">
                  <Badge variant={getStatusColor(pagamento.status)}>
                    {pagamento.status}
                  </Badge>
                  
                  {pagamento.asaas_payment_id && (
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => baixarBoleto(pagamento.id)}
                    >
                      <Download className="w-4 h-4" />
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