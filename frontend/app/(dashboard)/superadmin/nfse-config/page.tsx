'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  Settings,
  FileText,
  Upload,
  Shield,
  Building2,
  Hash,
  ArrowLeft,
} from 'lucide-react'
import Link from 'next/link'
import apiClient from '@/lib/api-client'

interface NFSeConfig {
  provedor_nfse: 'issnet' | 'nacional' | 'desabilitado'
  emitir_automaticamente: boolean
  prestador_cnpj: string
  prestador_razao_social: string
  prestador_inscricao_municipal: string
  prestador_email: string
  regime_especial_tributacao: string
  codigo_servico_municipal: string
  descricao_servico_padrao: string
  aliquota_iss: string
  codigo_cnae: string
  optante_simples_nacional: boolean
  incentivador_cultural: boolean
  // Nacional
  nacional_certificado_nome: string
  nacional_certificado_set: boolean
  nacional_senha_certificado_set: boolean
  nacional_ambiente: string
  nacional_codigo_municipio: string
  nacional_serie_dps: string
  nacional_ultimo_dps: number
}

export default function NFSeConfigPage() {
  const [config, setConfig] = useState<NFSeConfig>({
    provedor_nfse: 'issnet',
    emitir_automaticamente: true,
    prestador_cnpj: '',
    prestador_razao_social: '',
    prestador_inscricao_municipal: '',
    prestador_email: '',
    regime_especial_tributacao: '',
    codigo_servico_municipal: '1401',
    descricao_servico_padrao: 'Licenciamento de uso de software SaaS',
    aliquota_iss: '2.00',
    codigo_cnae: '',
    optante_simples_nacional: true,
    incentivador_cultural: false,
    nacional_certificado_nome: '',
    nacional_certificado_set: false,
    nacional_senha_certificado_set: false,
    nacional_ambiente: 'homologacao',
    nacional_codigo_municipio: '',
    nacional_serie_dps: '900',
    nacional_ultimo_dps: 0,
  })

  const [nacionalSenhaCertificado, setNacionalSenhaCertificado] = useState('')
  const [nacionalCertificadoFile, setNacionalCertificadoFile] = useState<File | null>(null)

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    setLoading(true)
    try {
      const { data } = await apiClient.get('/asaas/nfse-config/', { timeout: 20000 })
      setConfig(data)
    } catch (error) {
      console.error('Erro ao carregar configuração NFS-e:', error)
      setMessage({ type: 'error', text: 'Erro ao carregar configuração' })
    } finally {
      setLoading(false)
    }
  }

  const saveConfig = async () => {
    setSaving(true)
    setMessage(null)
    try {
      if (nacionalCertificadoFile) {
        const formData = new FormData()
        formData.append('provedor_nfse', config.provedor_nfse)
        formData.append('emitir_automaticamente', String(config.emitir_automaticamente))
        formData.append('prestador_cnpj', config.prestador_cnpj)
        formData.append('prestador_razao_social', config.prestador_razao_social)
        formData.append('prestador_inscricao_municipal', config.prestador_inscricao_municipal)
        formData.append('prestador_email', config.prestador_email)
        formData.append('regime_especial_tributacao', config.regime_especial_tributacao)
        formData.append('codigo_servico_municipal', config.codigo_servico_municipal)
        formData.append('descricao_servico_padrao', config.descricao_servico_padrao)
        formData.append('aliquota_iss', config.aliquota_iss)
        formData.append('codigo_cnae', config.codigo_cnae)
        formData.append('optante_simples_nacional', String(config.optante_simples_nacional))
        formData.append('incentivador_cultural', String(config.incentivador_cultural))
        formData.append('nacional_ambiente', config.nacional_ambiente)
        formData.append('nacional_codigo_municipio', config.nacional_codigo_municipio)
        formData.append('nacional_serie_dps', config.nacional_serie_dps)
        formData.append('nacional_ultimo_dps', String(config.nacional_ultimo_dps))
        if (nacionalSenhaCertificado) formData.append('nacional_senha_certificado', nacionalSenhaCertificado)
        formData.append('nacional_certificado', nacionalCertificadoFile)

        await apiClient.patch('/asaas/nfse-config/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
      } else {
        const payload: Record<string, unknown> = {
          provedor_nfse: config.provedor_nfse,
          emitir_automaticamente: config.emitir_automaticamente,
          prestador_cnpj: config.prestador_cnpj,
          prestador_razao_social: config.prestador_razao_social,
          prestador_inscricao_municipal: config.prestador_inscricao_municipal,
          prestador_email: config.prestador_email,
          regime_especial_tributacao: config.regime_especial_tributacao,
          codigo_servico_municipal: config.codigo_servico_municipal,
          descricao_servico_padrao: config.descricao_servico_padrao,
          aliquota_iss: config.aliquota_iss,
          codigo_cnae: config.codigo_cnae,
          optante_simples_nacional: config.optante_simples_nacional,
          incentivador_cultural: config.incentivador_cultural,
          nacional_ambiente: config.nacional_ambiente,
          nacional_codigo_municipio: config.nacional_codigo_municipio,
          nacional_serie_dps: config.nacional_serie_dps,
          nacional_ultimo_dps: config.nacional_ultimo_dps,
        }
        if (nacionalSenhaCertificado) payload.nacional_senha_certificado = nacionalSenhaCertificado

        await apiClient.patch('/asaas/nfse-config/', payload)
      }

      setMessage({ type: 'success', text: 'Configuração NFS-e salva com sucesso!' })
      setNacionalSenhaCertificado('')
      setNacionalCertificadoFile(null)
      loadConfig()
    } catch (error: unknown) {
      const err = error as { response?: { data?: { error?: string; detail?: string } } }
      setMessage({
        type: 'error',
        text: err.response?.data?.error || err.response?.data?.detail || 'Erro ao salvar configuração',
      })
    } finally {
      setSaving(false)
    }
  }

  const testNacional = async () => {
    setTesting(true)
    setMessage(null)
    try {
      const { data } = await apiClient.post('/asaas/nfse-config/test-nacional/')
      setMessage({
        type: 'success',
        text: data.message || 'Conexão ADN Nacional testada com sucesso!',
      })
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Erro ao testar conexão Nacional',
      })
    } finally {
      setTesting(false)
    }
  }

  if (loading) {
    return (
      <div className="w-full max-w-full px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    )
  }

  return (
    <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/superadmin/dashboard">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-1" />
              Voltar
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold">Configuração NFS-e</h1>
            <p className="text-sm text-muted-foreground">
              Emissão de notas fiscais via padrão Nacional (ADN)
            </p>
          </div>
        </div>
        <Badge variant={config.provedor_nfse === 'desabilitado' ? 'secondary' : 'default'}>
          {config.provedor_nfse === 'desabilitado' ? (
            <><XCircle className="w-4 h-4 mr-1" />Desabilitado</>
          ) : config.provedor_nfse === 'issnet' ? (
            <><CheckCircle className="w-4 h-4 mr-1" />ISSNet (Municipal)</>
          ) : (
            <><CheckCircle className="w-4 h-4 mr-1" />Nacional (ADN)</>
          )}
        </Badge>
      </div>

      {/* Mensagem */}
      {message && (
        <Alert variant={message.type === 'error' ? 'destructive' : 'default'}>
          {message.type === 'error' ? <AlertCircle className="h-4 w-4" /> : <CheckCircle className="h-4 w-4" />}
          <AlertDescription>{message.text}</AlertDescription>
        </Alert>
      )}

      {/* Provedor e Emissão Automática */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Configuração Geral
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Provedor de Emissão</Label>
            <div className="flex gap-2">
              <Button
                type="button"
                variant={config.provedor_nfse === 'issnet' ? 'default' : 'outline'}
                onClick={() => setConfig(prev => ({ ...prev, provedor_nfse: 'issnet' }))}
              >
                ISSNet (Municipal)
              </Button>
              <Button
                type="button"
                variant={config.provedor_nfse === 'nacional' ? 'default' : 'outline'}
                onClick={() => setConfig(prev => ({ ...prev, provedor_nfse: 'nacional' }))}
              >
                Nacional (ADN)
              </Button>
              <Button
                type="button"
                variant={config.provedor_nfse === 'desabilitado' ? 'destructive' : 'outline'}
                onClick={() => setConfig(prev => ({ ...prev, provedor_nfse: 'desabilitado' }))}
              >
                Desabilitado
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              {config.provedor_nfse === 'issnet' && 'Emite via WebService ISSNet da prefeitura — para municípios que não aderiram ao Emissor Nacional.'}
              {config.provedor_nfse === 'nacional' && 'Emite via ADN (Ambiente de Dados Nacional) — apenas para municípios que aderiram ao Emissor Nacional.'}
              {config.provedor_nfse === 'desabilitado' && 'Nenhuma NFS-e será emitida automaticamente.'}
            </p>
          </div>

          <div className="flex items-center space-x-2 pt-2">
            <input
              type="checkbox"
              id="emitir_auto"
              checked={config.emitir_automaticamente}
              onChange={(e) => setConfig(prev => ({ ...prev, emitir_automaticamente: e.target.checked }))}
              className="rounded"
            />
            <Label htmlFor="emitir_auto">
              Emitir NFS-e automaticamente quando pagamento é confirmado
            </Label>
          </div>
        </CardContent>
      </Card>

      {/* Dados do Prestador */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="w-5 h-5" />
            Dados do Prestador
          </CardTitle>
          <CardDescription>Empresa que emite as notas fiscais</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>CNPJ</Label>
              <Input
                value={config.prestador_cnpj}
                onChange={(e) => setConfig(prev => ({ ...prev, prestador_cnpj: e.target.value }))}
                placeholder="00.000.000/0001-00"
              />
            </div>
            <div className="space-y-2">
              <Label>Razão Social</Label>
              <Input
                value={config.prestador_razao_social}
                onChange={(e) => setConfig(prev => ({ ...prev, prestador_razao_social: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Inscrição Municipal</Label>
              <Input
                value={config.prestador_inscricao_municipal}
                onChange={(e) => setConfig(prev => ({ ...prev, prestador_inscricao_municipal: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>E-mail</Label>
              <Input
                type="email"
                value={config.prestador_email}
                onChange={(e) => setConfig(prev => ({ ...prev, prestador_email: e.target.value }))}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Certificado Digital e Ambiente */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Certificado Digital e Ambiente
          </CardTitle>
          <CardDescription>Certificado ICP-Brasil A1 para assinatura e mTLS</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {config.nacional_certificado_set && (
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                Certificado configurado: <strong>{config.nacional_certificado_nome}</strong>
              </AlertDescription>
            </Alert>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Arquivo do Certificado (.pfx / .p12)</Label>
              <Input
                type="file"
                accept=".pfx,.p12"
                onChange={(e) => setNacionalCertificadoFile(e.target.files?.[0] || null)}
              />
              <p className="text-xs text-muted-foreground">Certificado ICP-Brasil A1 com CNPJ. Máx 5MB.</p>
            </div>
            <div className="space-y-2">
              <Label>
                Senha do Certificado
                {config.nacional_senha_certificado_set && (
                  <Badge variant="secondary" className="ml-2 text-xs">Configurada</Badge>
                )}
              </Label>
              <Input
                type="password"
                value={nacionalSenhaCertificado}
                onChange={(e) => setNacionalSenhaCertificado(e.target.value)}
                placeholder={config.nacional_senha_certificado_set ? '••••••• (deixe vazio para manter)' : 'Senha do .pfx'}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Ambiente</Label>
              <select
                value={config.nacional_ambiente}
                onChange={(e) => setConfig(prev => ({ ...prev, nacional_ambiente: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
              >
                <option value="homologacao">Homologação (testes)</option>
                <option value="producao">Produção</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label>Código IBGE Município</Label>
              <Input
                value={config.nacional_codigo_municipio}
                onChange={(e) => setConfig(prev => ({ ...prev, nacional_codigo_municipio: e.target.value }))}
                placeholder="Ex: 3543402"
                maxLength={7}
              />
              <p className="text-xs text-muted-foreground">7 dígitos (IBGE)</p>
            </div>
            <div className="space-y-2">
              <Label>Série DPS</Label>
              <Input
                value={config.nacional_serie_dps}
                onChange={(e) => setConfig(prev => ({ ...prev, nacional_serie_dps: e.target.value }))}
                placeholder="900"
                maxLength={5}
              />
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <Button
              variant="outline"
              onClick={testNacional}
              disabled={testing || !config.nacional_certificado_set}
            >
              {testing ? (
                <><RefreshCw className="w-4 h-4 mr-2 animate-spin" />Testando...</>
              ) : (
                'Testar Conexão'
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Dados Fiscais */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Hash className="w-5 h-5" />
            Dados Fiscais
          </CardTitle>
          <CardDescription>Informações fiscais usadas na emissão</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Código do Serviço (LC 116)</Label>
              <Input
                value={config.codigo_servico_municipal}
                onChange={(e) => setConfig(prev => ({ ...prev, codigo_servico_municipal: e.target.value }))}
                placeholder="14.01"
              />
            </div>
            <div className="space-y-2">
              <Label>Código CNAE</Label>
              <Input
                value={config.codigo_cnae}
                onChange={(e) => setConfig(prev => ({ ...prev, codigo_cnae: e.target.value }))}
                placeholder="6201501"
              />
            </div>
            <div className="space-y-2">
              <Label>Alíquota ISS (%)</Label>
              <Input
                value={config.aliquota_iss}
                onChange={(e) => setConfig(prev => ({ ...prev, aliquota_iss: e.target.value }))}
                placeholder="2.00"
              />
            </div>
            <div className="space-y-2">
              <Label>Regime Especial</Label>
              <select
                value={config.regime_especial_tributacao}
                onChange={(e) => setConfig(prev => ({ ...prev, regime_especial_tributacao: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
              >
                <option value="">Nenhum</option>
                <option value="1">Microempresa Municipal</option>
                <option value="2">Estimativa</option>
                <option value="3">Sociedade de Profissionais</option>
                <option value="4">Cooperativa</option>
                <option value="5">MEI</option>
                <option value="6">ME/EPP</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Descrição Padrão do Serviço</Label>
            <Input
              value={config.descricao_servico_padrao}
              onChange={(e) => setConfig(prev => ({ ...prev, descricao_servico_padrao: e.target.value }))}
              placeholder="Licenciamento de uso de software SaaS"
            />
          </div>

          <div className="flex gap-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="simples"
                checked={config.optante_simples_nacional}
                onChange={(e) => setConfig(prev => ({ ...prev, optante_simples_nacional: e.target.checked }))}
                className="rounded"
              />
              <Label htmlFor="simples">Optante Simples Nacional</Label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="cultural"
                checked={config.incentivador_cultural}
                onChange={(e) => setConfig(prev => ({ ...prev, incentivador_cultural: e.target.checked }))}
                className="rounded"
              />
              <Label htmlFor="cultural">Incentivador Cultural</Label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Botão Salvar */}
      <div className="flex justify-end">
        <Button onClick={saveConfig} disabled={saving} size="lg">
          {saving ? (
            <><RefreshCw className="w-4 h-4 mr-2 animate-spin" />Salvando...</>
          ) : (
            'Salvar Configuração'
          )}
        </Button>
      </div>
    </div>
  )
}
