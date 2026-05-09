'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  Settings,
  FileText,
  Upload,
  Eye,
  EyeOff,
  Shield,
  Building2,
  Hash,
} from 'lucide-react'
import apiClient from '@/lib/api-client'

interface NFSeConfig {
  provedor_nfse: 'asaas' | 'issnet' | 'desabilitado'
  emitir_automaticamente: boolean
  prestador_cnpj: string
  prestador_razao_social: string
  prestador_inscricao_municipal: string
  prestador_email: string
  regime_especial_tributacao: string
  issnet_usuario: string
  issnet_senha_set: boolean
  issnet_certificado_nome: string
  issnet_certificado_set: boolean
  issnet_senha_certificado_set: boolean
  codigo_servico_municipal: string
  descricao_servico_padrao: string
  aliquota_iss: string
  codigo_cnae: string
  optante_simples_nacional: boolean
  serie_rps: string
  ultimo_rps: number
}

export default function NFSeConfigPage() {
  const [config, setConfig] = useState<NFSeConfig>({
    provedor_nfse: 'asaas',
    emitir_automaticamente: true,
    prestador_cnpj: '',
    prestador_razao_social: '',
    prestador_inscricao_municipal: '',
    prestador_email: '',
    regime_especial_tributacao: '',
    issnet_usuario: '',
    issnet_senha_set: false,
    issnet_certificado_nome: '',
    issnet_certificado_set: false,
    issnet_senha_certificado_set: false,
    codigo_servico_municipal: '1401',
    descricao_servico_padrao: 'Licenciamento de uso de software SaaS',
    aliquota_iss: '2.00',
    codigo_cnae: '',
    optante_simples_nacional: true,
    serie_rps: 'E',
    ultimo_rps: 0,
  })

  // Campos de senha (não vêm do GET, só enviam no PATCH)
  const [issnetSenha, setIssnetSenha] = useState('')
  const [issnetSenhaCertificado, setIssnetSenhaCertificado] = useState('')
  const [certificadoFile, setCertificadoFile] = useState<File | null>(null)

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [showSenha, setShowSenha] = useState(false)
  const [showSenhaCert, setShowSenhaCert] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    setLoading(true)
    try {
      const { data } = await apiClient.get('/asaas/nfse-config/')
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
      // Se tem certificado, usar FormData (multipart)
      if (certificadoFile) {
        const formData = new FormData()
        // Campos simples
        formData.append('provedor_nfse', config.provedor_nfse)
        formData.append('emitir_automaticamente', String(config.emitir_automaticamente))
        formData.append('prestador_cnpj', config.prestador_cnpj)
        formData.append('prestador_razao_social', config.prestador_razao_social)
        formData.append('prestador_inscricao_municipal', config.prestador_inscricao_municipal)
        formData.append('prestador_email', config.prestador_email)
        formData.append('regime_especial_tributacao', config.regime_especial_tributacao)
        formData.append('issnet_usuario', config.issnet_usuario)
        formData.append('codigo_servico_municipal', config.codigo_servico_municipal)
        formData.append('descricao_servico_padrao', config.descricao_servico_padrao)
        formData.append('aliquota_iss', config.aliquota_iss)
        formData.append('codigo_cnae', config.codigo_cnae)
        formData.append('optante_simples_nacional', String(config.optante_simples_nacional))
        formData.append('serie_rps', config.serie_rps)
        formData.append('ultimo_rps', String(config.ultimo_rps))
        // Senhas (só se preenchidas)
        if (issnetSenha) formData.append('issnet_senha', issnetSenha)
        if (issnetSenhaCertificado) formData.append('issnet_senha_certificado', issnetSenhaCertificado)
        // Certificado
        formData.append('issnet_certificado', certificadoFile)

        await apiClient.patch('/asaas/nfse-config/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
      } else {
        // JSON normal
        const payload: Record<string, unknown> = {
          provedor_nfse: config.provedor_nfse,
          emitir_automaticamente: config.emitir_automaticamente,
          prestador_cnpj: config.prestador_cnpj,
          prestador_razao_social: config.prestador_razao_social,
          prestador_inscricao_municipal: config.prestador_inscricao_municipal,
          prestador_email: config.prestador_email,
          regime_especial_tributacao: config.regime_especial_tributacao,
          issnet_usuario: config.issnet_usuario,
          codigo_servico_municipal: config.codigo_servico_municipal,
          descricao_servico_padrao: config.descricao_servico_padrao,
          aliquota_iss: config.aliquota_iss,
          codigo_cnae: config.codigo_cnae,
          optante_simples_nacional: config.optante_simples_nacional,
          serie_rps: config.serie_rps,
          ultimo_rps: config.ultimo_rps,
        }
        if (issnetSenha) payload.issnet_senha = issnetSenha
        if (issnetSenhaCertificado) payload.issnet_senha_certificado = issnetSenhaCertificado

        await apiClient.patch('/asaas/nfse-config/', payload)
      }

      setMessage({ type: 'success', text: 'Configuração NFS-e salva com sucesso!' })
      setIssnetSenha('')
      setIssnetSenhaCertificado('')
      setCertificadoFile(null)
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

  const testISSNet = async () => {
    setTesting(true)
    setMessage(null)
    try {
      const { data } = await apiClient.post('/asaas/nfse-config/test-issnet/')
      setMessage({
        type: 'success',
        text: data.message || 'Conexão ISSNet testada com sucesso!',
      })
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Erro ao testar conexão ISSNet',
      })
    } finally {
      setTesting(false)
    }
  }

  const provedorLabel = {
    asaas: 'Asaas (Intermediário)',
    issnet: 'ISSNet Ribeirão Preto (Direto)',
    desabilitado: 'Desabilitado',
  }

  const provedorBadgeVariant = {
    asaas: 'default' as const,
    issnet: 'default' as const,
    desabilitado: 'secondary' as const,
  }

  if (loading) {
    return (
      <div className="w-full max-w-full px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-6 h-6 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">Carregando configuração...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full max-w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Configuração NFS-e</h1>
          <p className="text-muted-foreground">
            Configure a emissão de notas fiscais de serviço para assinaturas das lojas
          </p>
        </div>
        <Badge variant={provedorBadgeVariant[config.provedor_nfse]}>
          {config.provedor_nfse === 'desabilitado' ? (
            <>
              <XCircle className="w-4 h-4 mr-1" />
              Desabilitado
            </>
          ) : (
            <>
              <CheckCircle className="w-4 h-4 mr-1" />
              {provedorLabel[config.provedor_nfse]}
            </>
          )}
        </Badge>
      </div>

      {/* Mensagem */}
      {message && (
        <Alert variant={message.type === 'error' ? 'destructive' : 'default'}>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{message.text}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="config" className="space-y-4">
        <TabsList>
          <TabsTrigger value="config">
            <Settings className="w-4 h-4 mr-2" />
            Configuração
          </TabsTrigger>
          <TabsTrigger value="issnet">
            <Shield className="w-4 h-4 mr-2" />
            Certificado ISSNet
          </TabsTrigger>
          <TabsTrigger value="fiscal">
            <FileText className="w-4 h-4 mr-2" />
            Dados Fiscais
          </TabsTrigger>
        </TabsList>

        {/* === ABA CONFIGURAÇÃO GERAL === */}
        <TabsContent value="config" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Provedor de NFS-e
              </CardTitle>
              <CardDescription>
                Escolha como as notas fiscais serão emitidas quando uma loja pagar a assinatura
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Seleção de provedor */}
              <div className="space-y-2">
                <Label>Provedor de Emissão</Label>
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant={config.provedor_nfse === 'asaas' ? 'default' : 'outline'}
                    onClick={() => setConfig(prev => ({ ...prev, provedor_nfse: 'asaas' }))}
                  >
                    Asaas (Intermediário)
                  </Button>
                  <Button
                    type="button"
                    variant={config.provedor_nfse === 'issnet' ? 'default' : 'outline'}
                    onClick={() => setConfig(prev => ({ ...prev, provedor_nfse: 'issnet' }))}
                  >
                    ISSNet (Direto)
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
                  {config.provedor_nfse === 'asaas' && 'Emite via Asaas — cobra taxa por nota emitida.'}
                  {config.provedor_nfse === 'issnet' && 'Emite direto na prefeitura de Ribeirão Preto — sem taxa, requer certificado digital.'}
                  {config.provedor_nfse === 'desabilitado' && 'Nenhuma NFS-e será emitida automaticamente.'}
                </p>
              </div>

              {/* Emissão automática */}
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
              <CardDescription>
                Empresa que emite as notas fiscais (ex: LWK Sistemas)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="cnpj">CNPJ</Label>
                  <Input
                    id="cnpj"
                    value={config.prestador_cnpj}
                    onChange={(e) => setConfig(prev => ({ ...prev, prestador_cnpj: e.target.value }))}
                    placeholder="00.000.000/0001-00"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="razao_social">Razão Social</Label>
                  <Input
                    id="razao_social"
                    value={config.prestador_razao_social}
                    onChange={(e) => setConfig(prev => ({ ...prev, prestador_razao_social: e.target.value }))}
                    placeholder="LWK Sistemas Ltda"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="inscricao_municipal">Inscrição Municipal</Label>
                  <Input
                    id="inscricao_municipal"
                    value={config.prestador_inscricao_municipal}
                    onChange={(e) => setConfig(prev => ({ ...prev, prestador_inscricao_municipal: e.target.value }))}
                    placeholder="123456"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="prestador_email">E-mail do Prestador</Label>
                  <Input
                    id="prestador_email"
                    type="email"
                    value={config.prestador_email}
                    onChange={(e) => setConfig(prev => ({ ...prev, prestador_email: e.target.value }))}
                    placeholder="fiscal@lwksistemas.com.br"
                  />
                  <p className="text-xs text-muted-foreground">E-mail para notificações de NFS-e emitidas</p>
                </div>
                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="regime_especial">Regime Especial de Tributação</Label>
                  <select
                    id="regime_especial"
                    value={config.regime_especial_tributacao}
                    onChange={(e) => setConfig(prev => ({ ...prev, regime_especial_tributacao: e.target.value }))}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  >
                    <option value="">- (Nenhum)</option>
                    <option value="1">Microempresa Municipal</option>
                    <option value="2">Estimativa</option>
                    <option value="3">Sociedade de Profissionais</option>
                    <option value="4">Cooperativa</option>
                    <option value="5">Microempresário Individual (MEI)</option>
                    <option value="6">Microempresário e Empresa de Pequeno Porte (ME EPP)</option>
                  </select>
                  <p className="text-xs text-muted-foreground">
                    Identifica o regime de tributação da empresa. Empresas do Simples Nacional geralmente optam por &quot;Microempresa Municipal&quot;.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Botão Salvar */}
          <div className="flex gap-2">
            <Button onClick={saveConfig} disabled={saving}>
              {saving ? 'Salvando...' : 'Salvar Configuração'}
            </Button>
          </div>
        </TabsContent>

        {/* === ABA CERTIFICADO ISSNET === */}
        <TabsContent value="issnet" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Credenciais ISSNet
              </CardTitle>
              <CardDescription>
                Configurações para emissão direta via ISSNet (Ribeirão Preto)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="issnet_usuario">Usuário ISSNet</Label>
                  <Input
                    id="issnet_usuario"
                    value={config.issnet_usuario}
                    onChange={(e) => setConfig(prev => ({ ...prev, issnet_usuario: e.target.value }))}
                    placeholder="usuario@issnet"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="issnet_senha">
                    Senha ISSNet
                    {config.issnet_senha_set && (
                      <Badge variant="secondary" className="ml-2 text-xs">Configurada</Badge>
                    )}
                  </Label>
                  <div className="relative">
                    <Input
                      id="issnet_senha"
                      type={showSenha ? 'text' : 'password'}
                      value={issnetSenha}
                      onChange={(e) => setIssnetSenha(e.target.value)}
                      placeholder={config.issnet_senha_set ? '••••••• (deixe vazio para manter)' : 'Digite a senha'}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3"
                      onClick={() => setShowSenha(!showSenha)}
                    >
                      {showSenha ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="w-5 h-5" />
                Certificado Digital A1
              </CardTitle>
              <CardDescription>
                Upload do certificado .pfx/.p12 para assinatura das notas
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Status do certificado atual */}
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
                  <Label htmlFor="certificado">Arquivo do Certificado (.pfx / .p12)</Label>
                  <Input
                    id="certificado"
                    type="file"
                    accept=".pfx,.p12"
                    onChange={(e) => {
                      const file = e.target.files?.[0] || null
                      setCertificadoFile(file)
                    }}
                  />
                  <p className="text-xs text-muted-foreground">Máximo 5MB. Formatos: .pfx, .p12</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="senha_cert">
                    Senha do Certificado
                    {config.issnet_senha_certificado_set && (
                      <Badge variant="secondary" className="ml-2 text-xs">Configurada</Badge>
                    )}
                  </Label>
                  <div className="relative">
                    <Input
                      id="senha_cert"
                      type={showSenhaCert ? 'text' : 'password'}
                      value={issnetSenhaCertificado}
                      onChange={(e) => setIssnetSenhaCertificado(e.target.value)}
                      placeholder={config.issnet_senha_certificado_set ? '••••••• (deixe vazio para manter)' : 'Senha do .pfx'}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3"
                      onClick={() => setShowSenhaCert(!showSenhaCert)}
                    >
                      {showSenhaCert ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
              </div>

              {/* Botões */}
              <div className="flex gap-2 pt-2">
                <Button onClick={saveConfig} disabled={saving}>
                  {saving ? 'Salvando...' : 'Salvar Certificado'}
                </Button>
                <Button
                  variant="outline"
                  onClick={testISSNet}
                  disabled={testing || config.provedor_nfse !== 'issnet'}
                >
                  {testing ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Testando...
                    </>
                  ) : (
                    'Testar Conexão ISSNet'
                  )}
                </Button>
              </div>

              {config.provedor_nfse !== 'issnet' && (
                <p className="text-xs text-muted-foreground">
                  ⚠️ O teste de conexão só funciona quando o provedor está configurado como &quot;ISSNet&quot;.
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* === ABA DADOS FISCAIS === */}
        <TabsContent value="fiscal" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Hash className="w-5 h-5" />
                Dados Fiscais do Serviço
              </CardTitle>
              <CardDescription>
                Informações fiscais usadas na emissão das notas
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="cod_servico">Código do Serviço Municipal</Label>
                  <Input
                    id="cod_servico"
                    value={config.codigo_servico_municipal}
                    onChange={(e) => setConfig(prev => ({ ...prev, codigo_servico_municipal: e.target.value }))}
                    placeholder="1401"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="codigo_cnae">Código CNAE</Label>
                  <Input
                    id="codigo_cnae"
                    value={config.codigo_cnae}
                    onChange={(e) => setConfig(prev => ({ ...prev, codigo_cnae: e.target.value }))}
                    placeholder="6201-5/01"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="aliquota">Alíquota ISS (%)</Label>
                  <Input
                    id="aliquota"
                    type="number"
                    step="0.01"
                    min="0"
                    max="10"
                    value={config.aliquota_iss}
                    onChange={(e) => setConfig(prev => ({ ...prev, aliquota_iss: e.target.value }))}
                    placeholder="2.00"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="serie_rps">Série do RPS</Label>
                  <Input
                    id="serie_rps"
                    value={config.serie_rps}
                    onChange={(e) => setConfig(prev => ({ ...prev, serie_rps: e.target.value }))}
                    placeholder="E"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ultimo_rps">Último RPS Emitido</Label>
                  <Input
                    id="ultimo_rps"
                    type="number"
                    min="0"
                    value={config.ultimo_rps}
                    onChange={(e) => setConfig(prev => ({ ...prev, ultimo_rps: parseInt(e.target.value) || 0 }))}
                    placeholder="0"
                  />
                  <p className="text-xs text-muted-foreground">Próxima emissão usará este número + 1</p>
                </div>
              </div>

              <div className="space-y-2 pt-4">
                <Label htmlFor="descricao_servico">Descrição Padrão do Serviço</Label>
                <textarea
                  id="descricao_servico"
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={config.descricao_servico_padrao}
                  onChange={(e) => setConfig(prev => ({ ...prev, descricao_servico_padrao: e.target.value }))}
                  placeholder="Licenciamento de uso de software SaaS"
                />
              </div>

              <div className="flex items-center space-x-2 pt-4">
                <input
                  type="checkbox"
                  id="simples_nacional"
                  checked={config.optante_simples_nacional}
                  onChange={(e) => setConfig(prev => ({ ...prev, optante_simples_nacional: e.target.checked }))}
                  className="rounded"
                />
                <Label htmlFor="simples_nacional">Optante pelo Simples Nacional</Label>
              </div>
            </CardContent>
          </Card>

          {/* Botão Salvar */}
          <div className="flex gap-2">
            <Button onClick={saveConfig} disabled={saving}>
              {saving ? 'Salvando...' : 'Salvar Dados Fiscais'}
            </Button>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
