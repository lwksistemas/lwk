'use client'

import { useState, useEffect, useRef } from 'react'
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
import { consultaCnpj, formatCpfCnpj } from '@/lib/consulta-cnpj'
import { logger } from '@/lib/logger'

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
  // ISSNet
  issnet_usuario: string
  issnet_senha_set: boolean
  issnet_certificado_nome: string
  issnet_certificado_set: boolean
  issnet_senha_certificado_set: boolean
  serie_rps: string
  ultimo_rps: number
  // Nacional
  nacional_certificado_nome: string
  nacional_certificado_set: boolean
  nacional_senha_certificado_set: boolean
  nacional_ambiente: string
  nacional_codigo_municipio: string
  nacional_serie_dps: string
  nacional_ultimo_dps: number
}

function normalizeConfigResponse(data: Record<string, unknown>): NFSeConfig {
  const {
    success: _success,
    message: _message,
    ...config
  } = data
  return config as NFSeConfig
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
    issnet_usuario: '',
    issnet_senha_set: false,
    issnet_certificado_nome: '',
    issnet_certificado_set: false,
    issnet_senha_certificado_set: false,
    serie_rps: 'E',
    ultimo_rps: 0,
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
  const [issnetSenha, setIssnetSenha] = useState('')
  const [issnetSenhaCertificado, setIssnetSenhaCertificado] = useState('')
  const [issnetCertificadoFile, setIssnetCertificadoFile] = useState<File | null>(null)
  const issnetCertInputRef = useRef<HTMLInputElement>(null)
  const nacionalCertInputRef = useRef<HTMLInputElement>(null)

  const buildSaveFormData = () => {
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
    formData.append('issnet_usuario', config.issnet_usuario)
    formData.append('serie_rps', config.serie_rps)
    formData.append('ultimo_rps', String(config.ultimo_rps))
    if (nacionalSenhaCertificado) formData.append('nacional_senha_certificado', nacionalSenhaCertificado)
    if (issnetSenha) formData.append('issnet_senha', issnetSenha)
    if (issnetSenhaCertificado) formData.append('issnet_senha_certificado', issnetSenhaCertificado)
    if (nacionalCertificadoFile) formData.append('nacional_certificado', nacionalCertificadoFile)
    if (issnetCertificadoFile) formData.append('issnet_certificado', issnetCertificadoFile)
    return formData
  }

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [buscarCnpjLoading, setBuscarCnpjLoading] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const handleBuscarCnpj = async () => {
    const digits = config.prestador_cnpj.replace(/\D/g, '')
    if (digits.length !== 14) {
      setMessage({ type: 'error', text: 'Informe um CNPJ válido com 14 dígitos.' })
      return
    }
    setBuscarCnpjLoading(true)
    setMessage(null)
    try {
      const data = await consultaCnpj(digits)
      if (!data) {
        setMessage({ type: 'error', text: 'CNPJ não encontrado ou serviço indisponível.' })
        return
      }
      setConfig((prev) => ({
        ...prev,
        prestador_cnpj: formatCpfCnpj(digits),
        prestador_razao_social: data.razao_social || prev.prestador_razao_social,
        prestador_email: data.email || prev.prestador_email,
        codigo_cnae: data.cnae_fiscal || prev.codigo_cnae,
        nacional_codigo_municipio: data.codigo_municipio_ibge || prev.nacional_codigo_municipio,
        optante_simples_nacional:
          data.optante_simples !== undefined ? data.optante_simples : prev.optante_simples_nacional,
      }))
      setMessage({ type: 'success', text: 'Dados do prestador preenchidos pela Receita Federal.' })
    } catch {
      setMessage({ type: 'error', text: 'Erro ao consultar CNPJ. Tente novamente.' })
    } finally {
      setBuscarCnpjLoading(false)
    }
  }

  const handleCnpjChange = (value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 14)
    setConfig((prev) => ({ ...prev, prestador_cnpj: formatCpfCnpj(digits) }))
  }

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    setLoading(true)
    try {
      const { data } = await apiClient.get('/asaas/nfse-config/', { timeout: 20000 })
      setConfig(normalizeConfigResponse(data as Record<string, unknown>))
    } catch (error) {
      logger.warn('Erro ao carregar configuração NFS-e:', error)
      setMessage({ type: 'error', text: 'Erro ao carregar configuração' })
    } finally {
      setLoading(false)
    }
  }

  const saveConfig = async () => {
    setSaving(true)
    setMessage(null)
    try {
      if (config.provedor_nfse === 'issnet') {
        if (!config.issnet_usuario.trim()) {
          setMessage({ type: 'error', text: 'Informe o usuário ISSNet antes de salvar.' })
          return
        }
        if (
          !config.issnet_senha_set &&
          !issnetSenha &&
          !config.issnet_certificado_set &&
          !issnetCertificadoFile
        ) {
          setMessage({
            type: 'error',
            text: 'Informe a senha ISSNet e/ou o certificado A1 (.pfx) na primeira configuração.',
          })
          return
        }
        if (issnetCertificadoFile && !issnetSenhaCertificado && !config.issnet_senha_certificado_set) {
          setMessage({ type: 'error', text: 'Informe a senha do certificado A1 (.pfx).' })
          return
        }
      }

      const formData = buildSaveFormData()
      const { data } = await apiClient.patch('/asaas/nfse-config/', formData)

      const saved = normalizeConfigResponse(data as Record<string, unknown>)
      if (saved?.provedor_nfse) {
        setConfig(saved)
      } else {
        await loadConfig()
      }

      const issnetOk =
        saved.provedor_nfse !== 'issnet' ||
        (Boolean(saved.issnet_usuario?.trim()) &&
          (saved.issnet_senha_set || saved.issnet_certificado_set))

      setMessage({
        type: 'success',
        text: issnetOk
          ? 'Configuração NFS-e salva com sucesso!'
          : 'Salvo, mas credenciais ISSNet incompletas — confira usuário, senha e certificado.',
      })
      setNacionalSenhaCertificado('')
      setNacionalCertificadoFile(null)
      setIssnetSenha('')
      setIssnetSenhaCertificado('')
      setIssnetCertificadoFile(null)
      if (issnetCertInputRef.current) issnetCertInputRef.current.value = ''
      if (nacionalCertInputRef.current) nacionalCertInputRef.current.value = ''
    } catch (error: unknown) {
      const err = error as {
        response?: { status?: number; data?: { error?: string; detail?: string | string[] } }
        message?: string
      }
      const detail = err.response?.data?.detail
      const detailStr = Array.isArray(detail) ? detail.join(', ') : typeof detail === 'string' ? detail : ''
      setMessage({
        type: 'error',
        text:
          err.response?.data?.error ||
          detailStr ||
          (err.response?.status === 405
            ? 'Método não permitido na API — recarregue a página após o deploy ou use Salvar novamente.'
            : '') ||
          (err.response?.status === 403 ? 'Sem permissão para salvar (superadmin).' : '') ||
          err.message ||
          'Erro ao salvar configuração',
      })
    } finally {
      setSaving(false)
    }
  }

  const testConexao = async () => {
    setTesting(true)
    setMessage(null)
    try {
      const fd = new FormData()
      fd.append('issnet_usuario', config.issnet_usuario.trim())
      if (issnetSenha) fd.append('issnet_senha', issnetSenha)
      if (issnetSenhaCertificado) fd.append('issnet_senha_certificado', issnetSenhaCertificado)
      if (issnetCertificadoFile) fd.append('issnet_certificado', issnetCertificadoFile)
      fd.append('nacional_ambiente', config.nacional_ambiente)

      const { data } = await apiClient.post('/asaas/nfse-config/test-nacional/', fd)
      setMessage({
        type: 'success',
        text: data.message || 'Conexão testada com sucesso!',
      })
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string; error?: string } } }
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || err.response?.data?.error || 'Erro ao testar conexão',
      })
    } finally {
      setTesting(false)
    }
  }

  const canTestIssnet =
    config.issnet_certificado_set ||
    Boolean(issnetCertificadoFile) ||
    (Boolean(config.issnet_usuario.trim()) && (config.issnet_senha_set || Boolean(issnetSenha)))

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
            <div className="space-y-2 md:col-span-2">
              <Label>CNPJ</Label>
              <div className="flex flex-col sm:flex-row gap-2">
                <Input
                  value={config.prestador_cnpj}
                  onChange={(e) => handleCnpjChange(e.target.value)}
                  placeholder="00.000.000/0001-00"
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleBuscarCnpj}
                  disabled={buscarCnpjLoading || config.prestador_cnpj.replace(/\D/g, '').length !== 14}
                  className="shrink-0"
                >
                  {buscarCnpjLoading ? (
                    <><RefreshCw className="w-4 h-4 mr-2 animate-spin" />Consultando...</>
                  ) : (
                    'Consultar CNPJ'
                  )}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Preenche razão social, e-mail, CNAE e código IBGE do município automaticamente.
              </p>
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

      {/* Credenciais ISSNet */}
      {config.provedor_nfse === 'issnet' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Credenciais ISSNet
            </CardTitle>
            <CardDescription>
              Usuário, senha e certificado A1 do portal ISSNet da prefeitura
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {config.issnet_certificado_set && (
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  Certificado configurado: <strong>{config.issnet_certificado_nome}</strong>
                </AlertDescription>
              </Alert>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Usuário ISSNet</Label>
                <Input
                  value={config.issnet_usuario}
                  onChange={(e) => setConfig((prev) => ({ ...prev, issnet_usuario: e.target.value }))}
                  placeholder="Login do webservice ISSNet"
                />
              </div>
              <div className="space-y-2">
                <Label>
                  Senha ISSNet
                  {config.issnet_senha_set && (
                    <Badge variant="secondary" className="ml-2 text-xs">Configurada</Badge>
                  )}
                </Label>
                <Input
                  type="password"
                  value={issnetSenha}
                  onChange={(e) => setIssnetSenha(e.target.value)}
                  placeholder={config.issnet_senha_set ? 'Digite para alterar' : 'Senha do webservice'}
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label>Certificado Digital A1 (.pfx / .p12)</Label>
                <Input
                  ref={issnetCertInputRef}
                  type="file"
                  accept=".pfx,.p12"
                  onChange={(e) => setIssnetCertificadoFile(e.target.files?.[0] || null)}
                />
                <p className="text-xs text-muted-foreground">
                  Certificado e-CNPJ da empresa prestadora. Máx 5MB.
                </p>
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label>
                  Senha do Certificado
                  {config.issnet_senha_certificado_set && (
                    <Badge variant="secondary" className="ml-2 text-xs">Configurada</Badge>
                  )}
                </Label>
                <Input
                  type="password"
                  value={issnetSenhaCertificado}
                  onChange={(e) => setIssnetSenhaCertificado(e.target.value)}
                  placeholder={config.issnet_senha_certificado_set ? 'Digite para alterar' : 'Senha do arquivo .pfx'}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Ambiente</Label>
                <select
                  value={config.nacional_ambiente}
                  onChange={(e) => setConfig((prev) => ({ ...prev, nacional_ambiente: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                >
                  <option value="homologacao">Homologação (testes)</option>
                  <option value="producao">Produção</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label>Série RPS</Label>
                <Input
                  value={config.serie_rps}
                  onChange={(e) => setConfig((prev) => ({ ...prev, serie_rps: e.target.value }))}
                  placeholder="E"
                  maxLength={10}
                />
              </div>
              <div className="space-y-2">
                <Label>Último nº RPS emitido</Label>
                <Input
                  type="number"
                  value={config.ultimo_rps}
                  onChange={(e) => setConfig((prev) => ({ ...prev, ultimo_rps: parseInt(e.target.value) || 0 }))}
                  placeholder="Ex: 150"
                />
                <p className="text-xs text-muted-foreground">
                  Informe o último RPS já usado no ISSNet (não é o número público da NFS-e).
                  A próxima emissão usará este valor + 1.
                </p>
              </div>
            </div>

            <div className="flex gap-2 pt-2">
              <Button
                variant="outline"
                onClick={testConexao}
                disabled={testing || !canTestIssnet}
              >
                {testing ? (
                  <><RefreshCw className="w-4 h-4 mr-2 animate-spin" />Testando...</>
                ) : (
                  'Testar Conexão ISSNet'
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Certificado Digital Nacional */}
      {config.provedor_nfse === 'nacional' && (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Certificado Digital e Ambiente (Nacional)
          </CardTitle>
          <CardDescription>Certificado ICP-Brasil A1 para assinatura e mTLS no ADN</CardDescription>
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
                ref={nacionalCertInputRef}
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
            <div className="space-y-2">
              <Label>Último nº RPS / DPS emitido</Label>
              <Input
                type="number"
                value={config.nacional_ultimo_dps}
                onChange={(e) => setConfig(prev => ({ ...prev, nacional_ultimo_dps: parseInt(e.target.value) || 0 }))}
                placeholder="Ex: 150"
              />
              <p className="text-xs text-muted-foreground">
                Informe o último RPS/DPS já emitido no portal Nacional. A próxima nota usará +1.
              </p>
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <Button
              variant="outline"
              onClick={testConexao}
              disabled={testing || !config.nacional_certificado_set}
            >
              {testing ? (
                <><RefreshCw className="w-4 h-4 mr-2 animate-spin" />Testando...</>
              ) : (
                'Testar Conexão Nacional'
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
      )}

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
