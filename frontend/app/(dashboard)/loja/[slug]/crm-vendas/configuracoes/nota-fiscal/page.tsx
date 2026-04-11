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
    inscricao_municipal: '',
    codigo_cnae: '',
    optante_simples_nacional: true,
    regime_especial_tributacao: '0',
    incentivador_cultural: false,
    item_lista_servico: '',
    codigo_nbs: '',
    issnet_serie_rps: '',
    issnet_ultimo_rps_conhecido: '',
    issnet_numero_lote: '',
    emitir_nf_automaticamente: true,
  });
  
  const [certificadoFile, setCertificadoFile] = useState<File | null>(null);
  const [asaasTestLoading, setAsaasTestLoading] = useState(false);
  const [asaasTestMessage, setAsaasTestMessage] = useState<{ type: 'ok' | 'error'; text: string } | null>(
    null
  );
  const [issnetHomologacao, setIssnetHomologacao] = useState(false);
  const [issnetTestLoading, setIssnetTestLoading] = useState(false);
  const [issnetTestMessage, setIssnetTestMessage] = useState<{ type: 'ok' | 'error'; text: string } | null>(
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
        inscricao_municipal: config.inscricao_municipal || '',
        codigo_cnae: config.codigo_cnae || '',
        optante_simples_nacional: config.optante_simples_nacional ?? true,
        regime_especial_tributacao: config.regime_especial_tributacao || '0',
        incentivador_cultural: config.incentivador_cultural ?? false,
        item_lista_servico: config.item_lista_servico || '',
        codigo_nbs: config.codigo_nbs || '',
        issnet_serie_rps: config.issnet_serie_rps || '',
        issnet_ultimo_rps_conhecido:
          config.issnet_ultimo_rps_conhecido != null && config.issnet_ultimo_rps_conhecido !== undefined
            ? String(config.issnet_ultimo_rps_conhecido)
            : '',
        issnet_numero_lote:
          config.issnet_numero_lote != null && config.issnet_numero_lote !== undefined
            ? String(config.issnet_numero_lote)
            : '',
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

  const testarConexaoIssnet = async () => {
    setIssnetTestLoading(true);
    setIssnetTestMessage(null);
    try {
      const fd = new FormData();
      fd.append('homologacao', issnetHomologacao ? 'true' : 'false');
      fd.append('issnet_usuario', formData.issnet_usuario.trim());
      if (formData.issnet_senha) fd.append('issnet_senha', formData.issnet_senha);
      if (formData.issnet_senha_certificado) {
        fd.append('issnet_senha_certificado', formData.issnet_senha_certificado);
      }
      if (certificadoFile) fd.append('issnet_certificado', certificadoFile);

      const res = await apiClient.post<{
        success?: boolean;
        message?: string;
        detail?: string;
        ambiente?: string;
      }>('/crm-vendas/config/test-issnet/', fd);

      if (res.data?.success) {
        setIssnetTestMessage({
          type: 'ok',
          text: res.data.message || 'Conexão com o ISSNet OK.',
        });
      } else {
        setIssnetTestMessage({
          type: 'error',
          text: res.data?.detail || 'Não foi possível validar o ISSNet.',
        });
      }
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string; message?: string } } };
      const detail =
        ax.response?.data?.detail ||
        ax.response?.data?.message ||
        (err instanceof Error ? err.message : 'Erro ao testar conexão.');
      setIssnetTestMessage({ type: 'error', text: String(detail) });
    } finally {
      setIssnetTestLoading(false);
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
          {formData.provedor_nf === 'issnet' && (
            <p className="mt-4 text-sm text-gray-700 dark:text-gray-300 border-t border-gray-200 dark:border-[#0d1f3c] pt-4">
              <strong>ISSNet:</strong> preencha inscrição municipal, série do RPS e último RPS em{' '}
              <strong>Configurações Gerais</strong> (logo abaixo). Credenciais e certificado ficam na
              seção seguinte.
            </p>
          )}
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
              <div className="space-y-2">
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
                <p className="text-[11px] text-gray-600 dark:text-gray-400 pl-7">
                  <strong>Produção (recomendado para uso real):</strong> deixe{' '}
                  <strong>desmarcado</strong> — a API usada é{' '}
                  <code className="text-[10px] bg-gray-100 dark:bg-[#0d1f3c] px-1 rounded">api.asaas.com</code>{' '}
                  com chave de produção (
                  <code className="text-[10px] bg-gray-100 dark:bg-[#0d1f3c] px-1 rounded">$aact_prod_...</code>
                  ).{' '}
                  <strong>Sandbox:</strong> marque para testes —{' '}
                  <code className="text-[10px] bg-gray-100 dark:bg-[#0d1f3c] px-1 rounded">sandbox.asaas.com</code>{' '}
                  e chave de testes (
                  <code className="text-[10px] bg-gray-100 dark:bg-[#0d1f3c] px-1 rounded">$aact_hmlg_...</code>
                  ).
                </p>
                <p className="text-[11px] pl-7">
                  <span
                    className={
                      formData.asaas_sandbox
                        ? 'text-amber-700 dark:text-amber-300 font-medium'
                        : 'text-green-800 dark:text-green-300 font-medium'
                    }
                  >
                    {formData.asaas_sandbox
                      ? 'Modo atual: sandbox (homologação)'
                      : 'Modo atual: produção'}
                  </span>
                </p>
              </div>

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
                  O teste usa o mesmo modo (produção ou sandbox) indicado acima. Envia um GET à API Asaas
                  (lista de clientes). Use a chave digitada ou, com campo vazio, a chave já salva.
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

              <div className="md:col-span-2 space-y-3 pt-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={issnetHomologacao}
                    onChange={(e) => setIssnetHomologacao(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    Mensagem para cenário de homologação / testes
                  </span>
                </label>
                <p className="text-[11px] text-gray-500 dark:text-gray-400 pl-7">
                  O ISS Digital de Ribeirão Preto não publica um hostname separado só para homologação deste
                  webservice (o endereço antigo não resolve no DNS). O teste de conexão usa o mesmo WSDL de
                  produção para validar certificado e rede. Credenciais de teste, se existirem, vêm da
                  prefeitura ou{' '}
                  <a
                    href="https://www.ribeiraopreto.sp.gov.br/portal/fazenda/iss-digital"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[#0176d3] underline"
                  >
                    ISS Digital
                  </a>
                  / Nota Control.
                </p>
                <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                  <button
                    type="button"
                    onClick={() => void testarConexaoIssnet()}
                    disabled={
                      issnetTestLoading ||
                      !formData.issnet_usuario.trim() ||
                      (!certificadoFile && !config?.issnet_certificado) ||
                      (!formData.issnet_senha &&
                        !formData.issnet_senha_certificado &&
                        !config?.issnet_senhas_salvas)
                    }
                    className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-[#0176d3] text-[#0176d3] dark:text-[#5eb0ff] dark:border-[#5eb0ff] hover:bg-[#0176d3]/10 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {issnetTestLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Testando…
                      </>
                    ) : (
                      'Testar conexão com o ISSNet (Ribeirão Preto)'
                    )}
                  </button>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400 sm:max-w-md">
                    Valida o .pfx e tenta acessar o WSDL do webservice (sem emitir nota). Use credenciais
                    digitadas ou as já salvas; envie um novo .pfx se ainda não salvou.
                  </p>
                </div>
                {issnetTestMessage && (
                  <div
                    className={`flex items-start gap-2 p-3 rounded-lg text-sm ${
                      issnetTestMessage.type === 'ok'
                        ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200 border border-green-200 dark:border-green-800'
                        : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 border border-red-200 dark:border-red-800'
                    }`}
                  >
                    {issnetTestMessage.type === 'ok' ? (
                      <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5" />
                    ) : (
                      <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                    )}
                    <span>{issnetTestMessage.text}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Configurações Gerais */}
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Configurações Gerais
          </h2>

          {formData.provedor_nf === 'issnet' && (
            <div className="mb-6 rounded-lg border border-amber-200 dark:border-amber-900/50 bg-amber-50/80 dark:bg-amber-950/20 p-4">
              <h3 className="text-sm font-semibold text-amber-950 dark:text-amber-100 mb-1">
                ISSNet — Informações do Portal Emissor
              </h3>
              <p className="text-xs text-amber-900/90 dark:text-amber-200/90 mb-4">
                Preencha com os mesmos dados do Asaas (Informações da empresa / NFS-e) e da prefeitura de Ribeirão Preto.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                    Inscrição municipal (prestador) *
                  </label>
                  <input
                    type="text"
                    value={formData.inscricao_municipal}
                    onChange={(e) => setFormData({ ...formData, inscricao_municipal: e.target.value })}
                    placeholder="Ex.: 20130440"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                    autoComplete="off"
                  />
                  <p className="text-[11px] text-gray-600 dark:text-gray-400 mt-1">
                    Mesmos dígitos do cadastro (ex.: <strong>20130440</strong> no Asaas). Só números.
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                    Código CNAE (opcional)
                  </label>
                  <input
                    type="text"
                    value={formData.codigo_cnae}
                    onChange={(e) => setFormData({ ...formData, codigo_cnae: e.target.value })}
                    placeholder="Apenas números"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                    autoComplete="off"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                    Item da Lista de Serviços (opcional)
                  </label>
                  <input
                    type="text"
                    value={formData.item_lista_servico}
                    onChange={(e) => setFormData({ ...formData, item_lista_servico: e.target.value })}
                    placeholder="Ex.: 17.02 ou 08.02"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                    autoComplete="off"
                  />
                  <p className="text-[11px] text-gray-600 dark:text-gray-400 mt-1">
                    Manter formatação com pontos (ex.: 17.02).
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                    Código NBS (opcional)
                  </label>
                  <input
                    type="text"
                    value={formData.codigo_nbs}
                    onChange={(e) => setFormData({ ...formData, codigo_nbs: e.target.value })}
                    placeholder="Nomenclatura Brasileira de Serviços"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                    autoComplete="off"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                    Regime Especial de Tributação
                  </label>
                  <select
                    value={formData.regime_especial_tributacao}
                    onChange={(e) => setFormData({ ...formData, regime_especial_tributacao: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                  >
                    <option value="0">Nenhum</option>
                    <option value="1">Microempresa Municipal</option>
                    <option value="2">Estimativa</option>
                    <option value="3">Sociedade de Profissionais</option>
                    <option value="4">Cooperativa</option>
                    <option value="5">MEI - Simples Nacional</option>
                    <option value="6">ME/EPP - Simples Nacional</option>
                  </select>
                </div>

                <div className="flex flex-col gap-3">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.optante_simples_nacional}
                      onChange={(e) => setFormData({ ...formData, optante_simples_nacional: e.target.checked })}
                      className="w-4 h-4"
                    />
                    <span className="text-sm text-gray-800 dark:text-gray-200">
                      Optante pelo Simples Nacional
                    </span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.incentivador_cultural}
                      onChange={(e) => setFormData({ ...formData, incentivador_cultural: e.target.checked })}
                      className="w-4 h-4"
                    />
                    <span className="text-sm text-gray-800 dark:text-gray-200">
                      Incentivador Cultural
                    </span>
                  </label>
                </div>
                <div className="md:col-span-2 border-t border-amber-200 dark:border-amber-800 pt-4 mt-2">
                  <h4 className="text-sm font-semibold text-amber-950 dark:text-amber-100 mb-3">
                    Informações da Nota Fiscal de Serviço
                  </h4>
                </div>
                <div className="md:col-span-2 grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                      Série do RPS
                    </label>
                    <input
                      type="text"
                      value={formData.issnet_serie_rps}
                      onChange={(e) => setFormData({ ...formData, issnet_serie_rps: e.target.value })}
                      placeholder="NFSE"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                      autoComplete="off"
                    />
                    <p className="text-[11px] text-gray-600 dark:text-gray-400 mt-1">
                      Série da NF no Asaas (ex.: NFSE). Vazio = A.
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                      Último RPS já emitido
                    </label>
                    <input
                      type="text"
                      inputMode="numeric"
                      value={formData.issnet_ultimo_rps_conhecido}
                      onChange={(e) =>
                        setFormData({ ...formData, issnet_ultimo_rps_conhecido: e.target.value })
                      }
                      placeholder="106"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                      autoComplete="off"
                    />
                    <p className="text-[11px] text-gray-600 dark:text-gray-400 mt-1">
                      Próximo envio será esse + 1 (ex.: 107) se ainda não houver NF aqui.
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                      Número do lote (opcional)
                    </label>
                    <input
                      type="text"
                      inputMode="numeric"
                      value={formData.issnet_numero_lote}
                      onChange={(e) => setFormData({ ...formData, issnet_numero_lote: e.target.value })}
                      placeholder="Só se a prefeitura exigir"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                      autoComplete="off"
                    />
                    <p className="text-[11px] text-gray-600 dark:text-gray-400 mt-1">
                      Só se o lote for diferente do RPS; vazio = mesmo número do RPS.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

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
