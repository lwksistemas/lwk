'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import apiClient from '@/lib/api-client';
import { getPrimaryApiBaseUrl } from '@/lib/api-base';
import { FileText, Upload, AlertCircle, CheckCircle2, Info, Loader2 } from 'lucide-react';

export default function ConfiguracaoNotaFiscalPage() {
  const router = useRouter();
  const params = useParams();
  const lojaSlug = typeof params?.slug === 'string' ? params.slug : '';
  const asaasWebhookUrl = lojaSlug
    ? `${getPrimaryApiBaseUrl()}/crm-vendas/webhooks/asaas/${encodeURIComponent(lojaSlug)}/`
    : '';
  const { config, recarregar } = useCRMConfig();
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  const [formData, setFormData] = useState({
    provedor_nf: 'asaas' as 'asaas' | 'issnet' | 'nacional' | 'manual',
    asaas_api_key: '',
    asaas_sandbox: false,
    issnet_usuario: '',
    issnet_senha: '',
    issnet_senha_certificado: '',
    codigo_servico_municipal: '1401',
    descricao_servico_padrao: 'Desenvolvimento e licenciamento de software sob demanda',
    aliquota_iss: '2.00',
    emitir_nf_automaticamente: true,
  });
  
  const [certificadoFile, setCertificadoFile] = useState<File | null>(null);
  const [asaasTestLoading, setAsaasTestLoading] = useState(false);
  const [asaasTestMessage, setAsaasTestMessage] = useState<{ type: 'ok' | 'error'; text: string } | null>(
    null
  );

  useEffect(() => {
    if (config) {
      setFormData({
        provedor_nf: config.provedor_nf || 'asaas',
        asaas_api_key: '',
        asaas_sandbox: config.asaas_sandbox ?? false,
        issnet_usuario: config.issnet_usuario || '',
        issnet_senha: '',
        issnet_senha_certificado: '',
        codigo_servico_municipal: config.codigo_servico_municipal || '1401',
        descricao_servico_padrao: config.descricao_servico_padrao || 'Desenvolvimento e licenciamento de software sob demanda',
        aliquota_iss: config.aliquota_iss || '2.00',
        emitir_nf_automaticamente: config.emitir_nf_automaticamente ?? true,
      });
    }
  }, [config]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const data = new FormData();
      
      // Adicionar campos de texto
      Object.entries(formData).forEach(([key, value]) => {
        if (key === 'asaas_sandbox') return;
        if (value === '' || value === null || value === undefined) return;
        if (typeof value === 'boolean') {
          data.append(key, value ? 'true' : 'false');
          return;
        }
        data.append(key, String(value));
      });
      data.append('asaas_sandbox', formData.asaas_sandbox ? 'true' : 'false');

      // Adicionar certificado se houver
      if (certificadoFile) {
        data.append('issnet_certificado', certificadoFile);
      }

      await apiClient.patch('/crm-vendas/config/', data, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setMessage({ type: 'success', text: 'Configurações salvas com sucesso!' });
      await recarregar();
      
      // Limpar senhas após salvar
      setFormData(prev => ({
        ...prev,
        asaas_api_key: '',
        issnet_senha: '',
        issnet_senha_certificado: '',
      }));
      setCertificadoFile(null);
    } catch (error: any) {
      console.error('Erro ao salvar configurações:', error);
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Erro ao salvar configurações',
      });
    } finally {
      setLoading(false);
    }
  };

  const testarComunicacaoAsaas = async () => {
    setAsaasTestLoading(true);
    setAsaasTestMessage(null);
    try {
      const payload: { api_key?: string; asaas_sandbox: boolean } = {
        asaas_sandbox: formData.asaas_sandbox,
      };
      const key = formData.asaas_api_key.trim();
      if (key) {
        payload.api_key = key;
      }
      const res = await apiClient.post<{
        success?: boolean;
        message?: string;
        detail?: string;
        environment?: string;
      }>('/crm-vendas/config/test-asaas/', payload);
      if (res.data?.success) {
        setAsaasTestMessage({
          type: 'ok',
          text: res.data.message || 'Conexão com o Asaas OK.',
        });
      } else {
        setAsaasTestMessage({
          type: 'error',
          text: res.data?.detail || 'Não foi possível validar a chave.',
        });
      }
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string; message?: string } } };
      const detail =
        ax.response?.data?.detail ||
        ax.response?.data?.message ||
        (err instanceof Error ? err.message : 'Erro ao testar comunicação.');
      setAsaasTestMessage({ type: 'error', text: String(detail) });
    } finally {
      setAsaasTestLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validar extensão .pfx
      if (!file.name.endsWith('.pfx')) {
        setMessage({
          type: 'error',
          text: 'Por favor, selecione um arquivo .pfx (certificado digital A1)',
        });
        return;
      }
      setCertificadoFile(file);
      setMessage(null);
    }
  };

  const provedorInfo = {
    asaas: {
      titulo: 'Asaas (conta da sua loja)',
      descricao:
        'Usa a API v3 da conta Asaas da sua empresa. Cadastre a chave em Integrações no Asaas (permissão de notas fiscais).',
      campos: [],
    },
    issnet: {
      titulo: 'ISSNet - Ribeirão Preto (Direto)',
      descricao: 'Emissão direta na Prefeitura de Ribeirão Preto com o CNPJ da sua loja. Requer certificado digital A1 próprio.',
      campos: ['issnet_usuario', 'issnet_senha', 'issnet_certificado', 'issnet_senha_certificado'],
    },
    nacional: {
      titulo: 'API Nacional NFS-e (Direto)',
      descricao: 'Emissão através da API Nacional NFS-e com o CNPJ da sua loja. Em breve disponível.',
      campos: [],
    },
    manual: {
      titulo: 'Emissão Manual',
      descricao: 'Sem integração automática. Você emitirá as notas manualmente no portal da prefeitura.',
      campos: [],
    },
  };

  const camposObrigatorios = provedorInfo[formData.provedor_nf].campos;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <FileText size={28} />
          Configuração de Nota Fiscal da Loja
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Configure como sua loja emitirá notas fiscais para seus clientes
        </p>
        
        <div className="mt-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Info size={20} className="text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
            <div className="text-sm text-blue-800 dark:text-blue-200">
              <p className="font-medium mb-2">⚠️ Importante: Duas emissões diferentes</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li><strong>NF da sua assinatura LWK:</strong> Emitida automaticamente pela LWK Sistemas quando você paga sua mensalidade</li>
                <li><strong>NF para seus clientes:</strong> Esta configuração é para quando VOCÊ prestar serviços aos SEUS clientes</li>
              </ul>
              <p className="mt-2 text-xs">
                Cada loja tem seu próprio CNPJ e certificado digital. As configurações abaixo são exclusivas da sua loja.
              </p>
            </div>
          </div>
        </div>
      </div>

      {message && (
        <div
          className={`p-4 rounded-lg flex items-start gap-3 ${
            message.type === 'success'
              ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200'
              : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle2 size={20} className="shrink-0 mt-0.5" />
          ) : (
            <AlertCircle size={20} className="shrink-0 mt-0.5" />
          )}
          <span className="text-sm">{message.text}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Provedor de NF */}
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Provedor de Nota Fiscal
          </h2>
          
          <div className="space-y-3">
            {(Object.keys(provedorInfo) as Array<keyof typeof provedorInfo>).map((key) => {
              const info = provedorInfo[key];
              const isDisabled = key === 'nacional'; // API Nacional ainda não disponível
              
              return (
                <label
                  key={key}
                  className={`flex items-start gap-3 p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    formData.provedor_nf === key
                      ? 'border-[#0176d3] bg-[#e3f3ff] dark:bg-[#0176d3]/10'
                      : 'border-gray-200 dark:border-[#0d1f3c] hover:border-gray-300 dark:hover:border-gray-600'
                  } ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <input
                    type="radio"
                    name="provedor_nf"
                    value={key}
                    checked={formData.provedor_nf === key}
                    onChange={(e) => setFormData({ ...formData, provedor_nf: e.target.value as any })}
                    disabled={isDisabled}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900 dark:text-white">
                      {info.titulo}
                      {isDisabled && (
                        <span className="ml-2 text-xs text-gray-500">(Em breve)</span>
                      )}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {info.descricao}
                    </div>
                  </div>
                </label>
              );
            })}
          </div>
        </div>

        {/* Conta Asaas da loja (API própria — não é a cobrança LWK) */}
        {formData.provedor_nf === 'asaas' && (
          <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              API Asaas da sua loja
            </h2>
            <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 mb-6 flex items-start gap-3">
              <Info size={20} className="text-amber-700 dark:text-amber-300 shrink-0 mt-0.5" />
              <div className="text-sm text-amber-950 dark:text-amber-100">
                <p className="font-medium mb-2">Conta Asaas separada da LWK</p>
                <p className="text-xs mb-2">
                  A mensalidade do sistema é cobrada pela LWK no Asaas dela. Para emitir NFS-e com o{' '}
                  <strong>CNPJ da sua loja</strong>, você precisa de{' '}
                  <strong>conta própria no Asaas</strong> e colar aqui a <strong>API Key</strong> (menu
                  Integrações → API). A chave precisa permitir emissão de notas fiscais (escopo de
                  faturamento/NF conforme o painel Asaas).
                </p>
                <p className="text-xs mb-2 text-amber-900/90 dark:text-amber-100/90">
                  <strong>Serviço municipal na NF:</strong> o backend usa a{' '}
                  <strong>mesma configuração</strong> das notas de assinatura (variáveis{' '}
                  <code className="text-[11px] bg-amber-100/80 dark:bg-amber-950/50 px-1 rounded">
                    ASAAS_INVOICE_*
                  </code>{' '}
                  no servidor — código, nome e ID do serviço no Asaas), igual à emissão automática da
                  mensalidade. Assim, cada loja só precisa da própria API Key; o cadastro fiscal no
                  Asaas da loja deve ser compatível com esse mesmo serviço (ex.: mesmo município).
                  Abaixo, código e descrição são <strong>reserva</strong> se o ambiente não tiver
                  essas variáveis.
                </p>
                <a
                  href="https://www.asaas.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[#0176d3] underline text-xs font-medium"
                >
                  Site Asaas
                </a>
              </div>
            </div>
            <div className="space-y-4 max-w-xl">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  API Key (token v3)
                </label>
                <input
                  type="password"
                  autoComplete="off"
                  value={formData.asaas_api_key}
                  onChange={(e) => setFormData({ ...formData, asaas_api_key: e.target.value })}
                  placeholder={
                    config?.asaas_api_key_configured
                      ? '•••••••• (já configurada — digite para substituir)'
                      : 'Cole a chave da conta Asaas da loja'
                  }
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white font-mono text-sm"
                />
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.asaas_sandbox}
                  onChange={(e) => setFormData({ ...formData, asaas_sandbox: e.target.checked })}
                  className="w-4 h-4"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Usar ambiente sandbox (homologação Asaas)
                </span>
              </label>

              <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                <button
                  type="button"
                  onClick={() => void testarComunicacaoAsaas()}
                  disabled={asaasTestLoading || (!formData.asaas_api_key.trim() && !config?.asaas_api_key_configured)}
                  className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-[#0176d3] text-[#0176d3] dark:text-[#5eb0ff] dark:border-[#5eb0ff] hover:bg-[#0176d3]/10 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {asaasTestLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Testando…
                    </>
                  ) : (
                    'Testar comunicação com o Asaas'
                  )}
                </button>
                <p className="text-[11px] text-gray-500 dark:text-gray-400 sm:max-w-md">
                  Envia uma requisição de teste à API (lista de clientes). Use a chave digitada acima ou,
                  se o campo estiver vazio, a chave já salva.
                </p>
              </div>
              {asaasTestMessage && (
                <div
                  className={`flex items-start gap-2 p-3 rounded-lg text-sm ${
                    asaasTestMessage.type === 'ok'
                      ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200 border border-green-200 dark:border-green-800'
                      : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 border border-red-200 dark:border-red-800'
                  }`}
                >
                  {asaasTestMessage.type === 'ok' ? (
                    <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                  )}
                  <span>{asaasTestMessage.text}</span>
                </div>
              )}

              <div className="pt-4 border-t border-gray-200 dark:border-gray-700 mt-4">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                  Webhook no Asaas (conta da sua loja)
                </h3>
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
                  Cada loja usa <strong>sua própria conta</strong> no Asaas. No painel da{' '}
                  <strong>sua</strong> empresa, abra{' '}
                  <a
                    href="https://www.asaas.com/customerConfigIntegrations/webhooks"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[#0176d3] underline font-medium"
                  >
                    Integrações → Webhooks
                  </a>{' '}
                  e cadastre a URL abaixo (método POST). Assim o Asaas notifica este sistema sobre
                  eventos de <strong>cobranças e notas fiscais</strong> gerados nessa conta — não use
                  o webhook da LWK (mensalidade do sistema), que é outro endpoint.
                </p>
                {asaasWebhookUrl ? (
                  <div className="flex flex-col sm:flex-row gap-2 sm:items-center">
                    <code className="flex-1 text-[11px] sm:text-xs break-all p-3 rounded-lg bg-gray-100 dark:bg-[#0d1f3c] text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-[#0d1f3c]">
                      {asaasWebhookUrl}
                    </code>
                    <button
                      type="button"
                      onClick={() => {
                        void navigator.clipboard.writeText(asaasWebhookUrl);
                      }}
                      className="shrink-0 px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-800 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-[#0d1f3c]"
                    >
                      Copiar URL
                    </button>
                  </div>
                ) : (
                  <p className="text-xs text-amber-700 dark:text-amber-300">
                    Não foi possível montar a URL (slug da loja indisponível).
                  </p>
                )}
                <p className="text-[11px] text-gray-500 dark:text-gray-500 mt-2">
                  Sugestão de eventos: pagamentos confirmados/atualizados e, se o painel oferecer,
                  notificações fiscais relacionadas à NF (conforme as opções do seu Asaas).
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Configurações ISSNet */}
        {formData.provedor_nf === 'issnet' && (
          <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Credenciais ISSNet
            </h2>
            
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6 flex items-start gap-3">
              <Info size={20} className="text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
              <div className="text-sm text-blue-800 dark:text-blue-200">
                <p className="font-medium mb-1">Requisitos para emissão direta com CNPJ da sua loja:</p>
                <ul className="list-disc list-inside space-y-1 text-xs">
                  <li>Certificado Digital A1 (e-CNPJ) válido <strong>da sua loja</strong></li>
                  <li>Credenciais de acesso ao webservice da Prefeitura <strong>no nome da sua loja</strong></li>
                  <li>Cadastro ativo no portal ISSNet de Ribeirão Preto <strong>com CNPJ da sua loja</strong></li>
                </ul>
                <p className="mt-2 text-xs font-medium">
                  ⚠️ Este certificado é diferente do certificado da LWK Sistemas usado para emitir NF da sua assinatura.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Usuário ISSNet *
                </label>
                <input
                  type="text"
                  value={formData.issnet_usuario}
                  onChange={(e) => setFormData({ ...formData, issnet_usuario: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Senha ISSNet *
                </label>
                <input
                  type="password"
                  value={formData.issnet_senha}
                  onChange={(e) => setFormData({ ...formData, issnet_senha: e.target.value })}
                  placeholder="Digite para alterar"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Certificado Digital A1 (.pfx) *
                </label>
                <div className="flex items-center gap-3">
                  <label className="flex-1 flex items-center gap-3 px-4 py-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:border-[#0176d3] transition-colors">
                    <Upload size={20} className="text-gray-400" />
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {certificadoFile
                        ? certificadoFile.name
                        : config?.issnet_certificado
                        ? 'Certificado já enviado - Clique para alterar'
                        : 'Clique para selecionar o arquivo .pfx'}
                    </span>
                    <input
                      type="file"
                      accept=".pfx"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                  </label>
                </div>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Senha do Certificado *
                </label>
                <input
                  type="password"
                  value={formData.issnet_senha_certificado}
                  onChange={(e) => setFormData({ ...formData, issnet_senha_certificado: e.target.value })}
                  placeholder="Senha do arquivo .pfx"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                />
              </div>
            </div>
          </div>
        )}

        {/* Configurações Gerais */}
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Configurações Gerais
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Código do Serviço Municipal
              </label>
              <input
                type="text"
                value={formData.codigo_servico_municipal}
                onChange={(e) => setFormData({ ...formData, codigo_servico_municipal: e.target.value })}
                placeholder="Ex: 1401"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Código do serviço na lista municipal (ex: 1401 para desenvolvimento de software)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Alíquota ISS (%)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={formData.aliquota_iss}
                onChange={(e) => setFormData({ ...formData, aliquota_iss: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Descrição Padrão do Serviço
              </label>
              <textarea
                value={formData.descricao_servico_padrao}
                onChange={(e) => setFormData({ ...formData, descricao_servico_padrao: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
              />
            </div>

            <div className="md:col-span-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.emitir_nf_automaticamente}
                  onChange={(e) => setFormData({ ...formData, emitir_nf_automaticamente: e.target.checked })}
                  className="w-4 h-4"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Emitir nota fiscal automaticamente ao confirmar pagamento
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Botões */}
        <div className="flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg transition-colors"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Salvando...' : 'Salvar Configurações'}
          </button>
        </div>
      </form>
    </div>
  );
}
