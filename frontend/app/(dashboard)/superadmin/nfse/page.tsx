'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle, RefreshCw, FileText, Download, Mail, XCircle } from 'lucide-react'
import apiClient from '@/lib/api-client'

interface NFSeEmitida {
  id: number
  numero_nf: string
  codigo_verificacao: string
  numero_rps: number
  serie_rps: string
  provedor: 'issnet' | 'asaas'
  status: 'emitida' | 'cancelada' | 'erro' | 'pendente'
  valor: string
  aliquota_iss: string
  valor_iss: string
  tomador_nome: string
  tomador_cpf_cnpj: string
  tomador_email: string
  descricao_servico: string
  loja_nome: string
  loja_slug: string
  asaas_payment_id: string
  data_emissao: string | null
  data_cancelamento: string | null
  created_at: string | null
  tem_xml: boolean
  pdf_url: string
  erro_mensagem: string
}

function getStatusBadge(status: string) {
  switch (status) {
    case 'emitida':
      return <Badge variant="default" className="bg-green-600">Emitida</Badge>
    case 'cancelada':
      return <Badge variant="destructive">Cancelada</Badge>
    case 'erro':
      return <Badge variant="destructive">Erro</Badge>
    case 'pendente':
      return <Badge variant="secondary">Pendente</Badge>
    default:
      return <Badge variant="secondary">{status}</Badge>
  }
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return '-'
  try {
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
    })
  } catch { return dateStr }
}

export default function NFSeEmitidasPage() {
  const [notas, setNotas] = useState<NFSeEmitida[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [filtroStatus, setFiltroStatus] = useState('')

  useEffect(() => {
    loadNotas()
  }, [filtroStatus])

  const loadNotas = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filtroStatus) params.append('status', filtroStatus)
      const { data } = await apiClient.get(`/superadmin/nfse-emitidas/?${params.toString()}`)
      setNotas(data.notas || [])
      setTotal(data.total || 0)
    } catch (error) {
      console.error('Erro ao carregar NFS-e:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleBaixarXml = async (nf: NFSeEmitida) => {
    try {
      const { data } = await apiClient.get(`/superadmin/nfse-emitidas/${nf.id}/xml/`)
      if (data.success && data.xml) {
        const blob = new Blob([data.xml], { type: 'application/xml' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `nfse_${nf.numero_nf || nf.id}.xml`
        a.click()
        URL.revokeObjectURL(url)
      } else {
        setMessage({ type: 'error', text: data.error || 'XML não disponível' })
      }
    } catch {
      setMessage({ type: 'error', text: 'Erro ao baixar XML' })
    }
  }

  const handleReenviar = async (nf: NFSeEmitida) => {
    if (!confirm(`Reenviar NFS-e ${nf.numero_nf} por email para ${nf.tomador_email}?`)) return
    try {
      const { data } = await apiClient.post(`/superadmin/nfse-emitidas/${nf.id}/reenviar/`)
      if (data.success) {
        setMessage({ type: 'success', text: data.message })
      } else {
        setMessage({ type: 'error', text: data.error })
      }
    } catch {
      setMessage({ type: 'error', text: 'Erro ao reenviar' })
    }
  }

  const handleCancelar = async (nf: NFSeEmitida) => {
    if (!confirm(`CANCELAR NFS-e ${nf.numero_nf}? Esta ação não pode ser desfeita.`)) return
    try {
      const { data } = await apiClient.post(`/superadmin/nfse-emitidas/${nf.id}/cancelar/`)
      if (data.success) {
        setMessage({ type: 'success', text: data.message })
        loadNotas()
      } else {
        setMessage({ type: 'error', text: data.error })
      }
    } catch {
      setMessage({ type: 'error', text: 'Erro ao cancelar' })
    }
  }

  return (
    <div className="w-full max-w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">NFS-e Emitidas</h1>
          <p className="text-muted-foreground">
            Notas fiscais emitidas pela LWK para as lojas ({total} notas)
          </p>
        </div>
        <Button variant="outline" onClick={loadNotas} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Atualizar
        </Button>
      </div>

      {message && (
        <Alert variant={message.type === 'error' ? 'destructive' : 'default'}>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{message.text}</AlertDescription>
        </Alert>
      )}

      {/* Filtros */}
      <div className="flex gap-2">
        {['', 'emitida', 'cancelada', 'erro'].map((s) => (
          <Button
            key={s}
            variant={filtroStatus === s ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFiltroStatus(s)}
          >
            {s === '' ? 'Todas' : s === 'emitida' ? '✅ Emitidas' : s === 'cancelada' ? '❌ Canceladas' : '⚠️ Erros'}
          </Button>
        ))}
      </div>

      {/* Tabela */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Notas Fiscais
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Carregando...</div>
          ) : notas.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              Nenhuma NFS-e encontrada. As notas aparecerão aqui quando forem emitidas automaticamente após pagamentos.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    {['NF', 'Data', 'Tomador', 'Valor', 'ISS', 'Status', 'Provedor', 'Ações'].map((h) => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {notas.map((nf) => (
                    <tr key={nf.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td className="px-4 py-3">
                        <div className="font-medium">{nf.numero_nf || '-'}</div>
                        <div className="text-xs text-muted-foreground">RPS {nf.numero_rps}</div>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {formatDate(nf.data_emissao)}
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-sm">{nf.tomador_nome}</div>
                        <div className="text-xs text-muted-foreground">{nf.tomador_cpf_cnpj}</div>
                        <div className="text-xs text-muted-foreground">{nf.loja_nome}</div>
                      </td>
                      <td className="px-4 py-3 text-sm font-medium">
                        R$ {parseFloat(nf.valor).toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-sm text-muted-foreground">
                        R$ {parseFloat(nf.valor_iss).toFixed(2)}
                        <div className="text-xs">{nf.aliquota_iss}%</div>
                      </td>
                      <td className="px-4 py-3">
                        {getStatusBadge(nf.status)}
                        {nf.erro_mensagem && (
                          <div className="text-xs text-red-500 mt-1 max-w-[200px] truncate" title={nf.erro_mensagem}>
                            {nf.erro_mensagem}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="secondary" className="text-xs">
                          {nf.provedor === 'issnet' ? '🏛️ ISSNet' : '🔵 Asaas'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 space-x-1">
                        {nf.tem_xml && (
                          <Button size="sm" variant="ghost" onClick={() => handleBaixarXml(nf)} title="Baixar XML">
                            <Download className="w-4 h-4" />
                          </Button>
                        )}
                        {nf.status === 'emitida' && nf.tomador_email && (
                          <Button size="sm" variant="ghost" onClick={() => handleReenviar(nf)} title="Reenviar email">
                            <Mail className="w-4 h-4" />
                          </Button>
                        )}
                        {nf.status === 'emitida' && (
                          <Button size="sm" variant="ghost" onClick={() => handleCancelar(nf)} title="Cancelar NF" className="text-red-500 hover:text-red-700">
                            <XCircle className="w-4 h-4" />
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
