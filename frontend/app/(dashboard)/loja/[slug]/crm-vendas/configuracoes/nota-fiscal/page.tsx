'use client';

import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { useRouter, useParams } from 'next/navigation';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import apiClient from '@/lib/api-client';
import { logger } from '@/lib/logger';
import { formatApiErrorBody } from '@/lib/api-errors';
import { FileText, Upload, AlertCircle, CheckCircle2, Info, Loader2, ArrowLeft } from 'lucide-react';

type ConfiguracaoNotaFiscalPageProps = {
  params?: Promise<{ slug: string }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

type ProvedorNf = 'asaas' | 'issnet' | 'nacional' | 'manual';

/** Opções visíveis na tela (4 caminhos de emissão). */
type EmissaoOpcao = 'asaas' | 'issnet_abrasf' | 'issnet_nacional' | 'nacional_adn';

const DEFAULT_DESCRICAO_SERVICO = 'Desenvolvimento e licenciamento de software sob demanda';
const DEFAULT_CODIGO_SERVICO = '1401';

const EMISSAO_OPCOES: Array<{
  key: EmissaoOpcao;
  numero: number;
  titulo: string;
  descricao: string;
  badge?: string;
  disabled?: boolean;
}> = [
  {
    key: 'asaas',
    numero: 1,
    titulo: 'Asaas (conta da sua loja)',
    descricao:
      'Emissão de NFS-e pela conta Asaas da loja. A API Key fica em Configurações → Asaas (banco).',
  },
  {
    key: 'issnet_abrasf',
    numero: 2,
    titulo: 'ISSNet — Ribeirão Preto (Direto, layout ABRASF)',
    descricao:
      'Descontinuado pelo município em 31/07/2026. O sistema já emite automaticamente pelo Padrão Nacional (opção 3) mesmo que esta opção esteja selecionada.',
    badge: 'Descontinuado',
    disabled: true,
  },
  {
    key: 'issnet_nacional',
    numero: 3,
    titulo: 'ISSNet — Padrão Nacional (DPS / RTC)',
    descricao:
      'Layout NFS-e via webservice Nacional da ISSNet (Ribeirão Preto). Padrão vigente desde a Reforma Tributária.',
    badge: 'Padrão atual',
  },
  {
    key: 'nacional_adn',
    numero: 4,
    titulo: 'API Nacional NFS-e (Direto)',
    descricao:
      'Emissão direta na API Nacional (ADN/SEFIN), sem intermediário. Para municípios com emissão direta liberada.',
  },
];

function resolvEmissaoOpcao(provedor: ProvedorNf, _usarNacional: boolean): EmissaoOpcao {
  if (provedor === 'asaas') return 'asaas';
  if (provedor === 'nacional') return 'nacional_adn';
  // ABRASF (issnet_abrasf) foi descontinuado em 31/07/2026: o backend força
  // Nacional independente da flag (ver service.py). Resolve sempre para
  // issnet_nacional para refletir o comportamento real.
  if (provedor === 'issnet') return 'issnet_nacional';
  return 'asaas';
}

function aplicarEmissaoOpcao(opcao: EmissaoOpcao): {
  provedor_nf: ProvedorNf;
  issnet_usar_padrao_nacional: boolean;
} {
  switch (opcao) {
    case 'asaas':
      return { provedor_nf: 'asaas', issnet_usar_padrao_nacional: false };
    case 'issnet_abrasf':
      return { provedor_nf: 'issnet', issnet_usar_padrao_nacional: false };
    case 'issnet_nacional':
      return { provedor_nf: 'issnet', issnet_usar_padrao_nacional: true };
    case 'nacional_adn':
      return { provedor_nf: 'nacional', issnet_usar_padrao_nacional: false };
  }
}

const INPUT =
  'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white';
const CARD =
  'bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6';

export default function ConfiguracaoNotaFiscalPage(_props: ConfiguracaoNotaFiscalPageProps) {
  const descricaoServicoPadrao = DEFAULT_DESCRICAO_SERVICO;
  const codigoServicoPadrao = DEFAULT_CODIGO_SERVICO;
  const router = useRouter();
  const params = useParams();
  const lojaSlug = typeof params?.slug === 'string' ? params.slug : '';
  const configBase = `/loja/${lojaSlug}/crm-vendas/configuracoes`;
  const { config, recarregar } = useCRMConfig();

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const [formData, setFormData] = useState({
    provedor_nf: 'asaas' as ProvedorNf,
    issnet_usuario: '',
    issnet_senha: '',
    issnet_senha_certificado: '',
    codigo_servico_municipal: codigoServicoPadrao,
    descricao_servico_padrao: descricaoServicoPadrao,
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
    issnet_ambiente_homologacao: false,
    issnet_usar_padrao_nacional: true,
    codigo_tributacao_nacional: '',
    codigo_tributacao_municipal: '',
    nacional_codigo_municipio: '',
    indicador_operacao: '',
    cst_ibscbs: '',
    cclass_trib_ibscbs: '',
    p_tot_trib_sn: '',
    emitir_nf_automaticamente: true,
  });

  const [certificadoFile, setCertificadoFile] = useState<File | null>(null);
  const [issnetTestLoading, setIssnetTestLoading] = useState(false);
  const [issnetTestMessage, setIssnetTestMessage] = useState<{ type: 'ok' | 'error'; text: string } | null>(
    null,
  );

  useEffect(() => {
    if (!config) return;
    setFormData({
      provedor_nf: (config.provedor_nf as ProvedorNf) || 'asaas',
      issnet_usuario: config.issnet_usuario || '',
      issnet_senha: '',
      issnet_senha_certificado: '',
      codigo_servico_municipal: config.codigo_servico_municipal || codigoServicoPadrao,
      descricao_servico_padrao: config.descricao_servico_padrao || descricaoServicoPadrao,
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
        config.issnet_ultimo_rps_conhecido != null ? String(config.issnet_ultimo_rps_conhecido) : '',
      issnet_numero_lote: config.issnet_numero_lote != null ? String(config.issnet_numero_lote) : '',
      issnet_ambiente_homologacao: config.issnet_ambiente_homologacao ?? false,
      issnet_usar_padrao_nacional: config.issnet_usar_padrao_nacional ?? true,
      codigo_tributacao_nacional: config.codigo_tributacao_nacional || '',
      codigo_tributacao_municipal: config.codigo_tributacao_municipal || '',
      nacional_codigo_municipio: config.nacional_codigo_municipio || '',
      indicador_operacao: config.indicador_operacao || '',
      cst_ibscbs: config.cst_ibscbs || '',
      cclass_trib_ibscbs: config.cclass_trib_ibscbs || '',
      p_tot_trib_sn: config.p_tot_trib_sn != null ? String(config.p_tot_trib_sn) : '',
      emitir_nf_automaticamente: config.emitir_nf_automaticamente ?? true,
    });
  }, [config, codigoServicoPadrao, descricaoServicoPadrao]);

  const emissaoOpcao = useMemo(
    () => resolvEmissaoOpcao(formData.provedor_nf, formData.issnet_usar_padrao_nacional),
    [formData.provedor_nf, formData.issnet_usar_padrao_nacional],
  );

  const selecionarEmissao = (opcao: EmissaoOpcao) => {
    const mapped = aplicarEmissaoOpcao(opcao);
    setFormData((prev) => ({ ...prev, ...mapped }));
    setMessage(null);
    setIssnetTestMessage(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      const data = new FormData();
      const clearableFields = [
        'codigo_cnae',
        'codigo_nbs',
        'item_lista_servico',
        'inscricao_municipal',
        'codigo_tributacao_nacional',
        'codigo_tributacao_municipal',
        'nacional_codigo_municipio',
      ];
      Object.entries(formData).forEach(([key, value]) => {
        if (value === null || value === undefined) return;
        if (value === '' && !clearableFields.includes(key)) return;
        if (typeof value === 'boolean') {
          data.append(key, value ? 'true' : 'false');
          return;
        }
        data.append(key, String(value));
      });
      if (certificadoFile) data.append('issnet_certificado', certificadoFile);

      await apiClient.patch('/crm-vendas/config/', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setMessage({ type: 'success', text: 'Configurações salvas com sucesso!' });
      await recarregar();
      setFormData((prev) => ({ ...prev, issnet_senha: '', issnet_senha_certificado: '' }));
      setCertificadoFile(null);
    } catch (error) {
      logger.warn('Erro ao salvar configurações fiscais:', error);
      setMessage({
        type: 'error',
        text: formatApiErrorBody(error) || 'Erro ao salvar configurações',
      });
    } finally {
      setLoading(false);
    }
  };

  const testarConexaoIssnet = async () => {
    setIssnetTestLoading(true);
    setIssnetTestMessage(null);
    try {
      const fd = new FormData();
      fd.append('homologacao', formData.issnet_ambiente_homologacao ? 'true' : 'false');
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
      }>('/crm-vendas/config/test-issnet/', fd);

      if (res.data?.success) {
        setIssnetTestMessage({ type: 'ok', text: res.data.message || 'Conexão com o ISSNet OK.' });
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
    if (!file) return;
    if (!file.name.endsWith('.pfx')) {
      setMessage({ type: 'error', text: 'Selecione um arquivo .pfx (certificado digital A1).' });
      return;
    }
    setCertificadoFile(file);
    setMessage(null);
  };

  const isIssnet = emissaoOpcao === 'issnet_abrasf' || emissaoOpcao === 'issnet_nacional';
  const isIssnetNacional = emissaoOpcao === 'issnet_nacional';
  const isNacionalAdn = emissaoOpcao === 'nacional_adn';
  const isAsaas = emissaoOpcao === 'asaas';
  const showCertConfig = isIssnet || isNacionalAdn;
  const showServicoConfig = !isAsaas;

  return (
    <div className="space-y-6">
      <Link
        href={configBase}
        className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-[#0176d3]"
      >
        <ArrowLeft size={16} />
        Voltar para Configurações
      </Link>

      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <FileText size={28} />
          Nota fiscal — emissão
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Escolha um modo de emissão. As configurações do emissor aparecem abaixo da opção selecionada.
        </p>
        <div className="mt-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 flex items-start gap-3">
          <Info size={20} className="text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
          <div className="text-sm text-blue-800 dark:text-blue-200">
            <p className="font-medium mb-1">NF para seus clientes (não é a NF da assinatura LWK)</p>
            <p className="text-xs">
              Esta tela define como a loja emite NFS-e aos clientes. A nota da mensalidade LWK é outro fluxo
              (Superadmin).
            </p>
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
        <div className={CARD}>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
            Como deseja emitir?
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            Selecione uma das 4 opções. Em seguida configure o emissor escolhido.
          </p>

          <div className="space-y-3">
            {EMISSAO_OPCOES.map((op) => {
              const selected = emissaoOpcao === op.key;
              return (
                <label
                  key={op.key}
                  className={`flex items-start gap-3 p-4 rounded-lg border-2 transition-all ${
                    op.disabled
                      ? 'opacity-60 cursor-not-allowed border-gray-200 dark:border-[#0d1f3c]'
                      : 'cursor-pointer'
                  } ${
                    selected && !op.disabled
                      ? 'border-[#0176d3] bg-[#e3f3ff] dark:bg-[#0176d3]/10'
                      : !op.disabled
                        ? 'border-gray-200 dark:border-[#0d1f3c] hover:border-gray-300 dark:hover:border-gray-600'
                        : ''
                  }`}
                >
                  <input
                    type="radio"
                    name="emissao_opcao"
                    value={op.key}
                    checked={selected}
                    disabled={op.disabled}
                    onChange={() => !op.disabled && selecionarEmissao(op.key)}
                    className="mt-1"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-semibold text-[#0176d3] tabular-nums">
                        {op.numero}.
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">{op.titulo}</span>
                      {op.badge ? (
                        <span
                          className={`text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full ${
                            op.disabled
                              ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300'
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                          }`}
                        >
                          {op.badge}
                        </span>
                      ) : null}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{op.descricao}</p>
                  </div>
                </label>
              );
            })}
          </div>
        </div>

        {/* —— 1. Asaas —— */}
        {isAsaas && (
          <div className={CARD}>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Configurações — Asaas
            </h2>
            <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">
              Configure a API Key da loja em{' '}
              <Link href={`${configBase}/asaas`} className="text-[#0176d3] underline font-medium">
                Configurações → Asaas (banco)
              </Link>
              {config?.asaas_api_key_configured ? (
                <span className="text-green-700 dark:text-green-300"> — chave já cadastrada.</span>
              ) : (
                <span className="text-amber-700 dark:text-amber-300"> — chave ainda não configurada.</span>
              )}
            </p>
            <CamposServicoBasicos formData={formData} setFormData={setFormData} inputClass={INPUT} />
          </div>
        )}

        {/* —— 2 e 3. ISSNet —— */}
        {isIssnet && (
          <>
            <div className={CARD}>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {isIssnetNacional
                  ? 'Configurações — ISSNet Padrão Nacional'
                  : 'Configurações — ISSNet ABRASF (legado)'}
              </h2>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
                {isIssnetNacional
                  ? 'Endpoint: wsnfsenacional/ribeiraopreto (DPS). Homologação: wsnfsenacional/homologacao.'
                  : 'Endpoint ABRASF 2.04 (RPS). Em 03/08/2026 o município deixa de validar este layout.'}
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Usuário ISSNet *
                  </label>
                  <input
                    type="text"
                    value={formData.issnet_usuario}
                    onChange={(e) => setFormData({ ...formData, issnet_usuario: e.target.value })}
                    className={INPUT}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Senha ISSNet
                  </label>
                  <input
                    type="password"
                    value={formData.issnet_senha}
                    onChange={(e) => setFormData({ ...formData, issnet_senha: e.target.value })}
                    placeholder="Digite para alterar"
                    className={INPUT}
                  />
                </div>
              </div>

              <CertificadoFields
                certificadoFile={certificadoFile}
                temCertificadoSalvo={Boolean(config?.issnet_certificado)}
                senha={formData.issnet_senha_certificado}
                onSenha={(v) => setFormData({ ...formData, issnet_senha_certificado: v })}
                onFileChange={handleFileChange}
                inputClass={INPUT}
              />

              <label className="flex items-center gap-2 cursor-pointer mt-4">
                <input
                  type="checkbox"
                  checked={formData.issnet_ambiente_homologacao}
                  onChange={(e) =>
                    setFormData({ ...formData, issnet_ambiente_homologacao: e.target.checked })
                  }
                  className="w-4 h-4"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Homologação / teste
                  {isIssnetNacional ? ' (webservice Nacional)' : ' (ISSNet)'}
                </span>
              </label>

              <div className="mt-4 flex flex-col sm:flex-row sm:items-center gap-3">
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
                  className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-[#0176d3] text-[#0176d3] text-sm font-medium disabled:opacity-50"
                >
                  {issnetTestLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Testando…
                    </>
                  ) : (
                    'Testar conexão ISSNet'
                  )}
                </button>
                {issnetTestMessage && (
                  <span
                    className={`text-sm ${
                      issnetTestMessage.type === 'ok'
                        ? 'text-green-700 dark:text-green-300'
                        : 'text-red-700 dark:text-red-300'
                    }`}
                  >
                    {issnetTestMessage.text}
                  </span>
                )}
              </div>
            </div>

            <div className={CARD}>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Dados do prestador e da nota
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Inscrição municipal *
                  </label>
                  <input
                    type="text"
                    value={formData.inscricao_municipal}
                    onChange={(e) => setFormData({ ...formData, inscricao_municipal: e.target.value })}
                    className={INPUT}
                    placeholder="Ex.: 20130440"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Código CNAE
                  </label>
                  <input
                    type="text"
                    value={formData.codigo_cnae}
                    onChange={(e) => setFormData({ ...formData, codigo_cnae: e.target.value })}
                    className={INPUT}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Item da lista de serviços
                  </label>
                  <input
                    type="text"
                    value={formData.item_lista_servico}
                    onChange={(e) => setFormData({ ...formData, item_lista_servico: e.target.value })}
                    placeholder="Ex.: 14.01"
                    className={INPUT}
                  />
                </div>
                {isIssnetNacional && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        cTribNac (tributação nacional)
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        maxLength={6}
                        value={formData.codigo_tributacao_nacional}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            codigo_tributacao_nacional: e.target.value.replace(/\D/g, '').slice(0, 6),
                          })
                        }
                        placeholder="140100"
                        className={INPUT}
                      />
                      <p className="text-[11px] text-gray-500 mt-1">6 dígitos. Vazio → deriva do item (14.01 → 140100).</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        cTribMun (tributação municipal)
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        maxLength={6}
                        value={formData.codigo_tributacao_municipal}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            codigo_tributacao_municipal: e.target.value.replace(/\D/g, '').slice(0, 6),
                          })
                        }
                        placeholder="140118"
                        className={INPUT}
                      />
                      <p className="text-[11px] text-gray-500 mt-1">
                        Código cadastrado no ISSNet p/ este contribuinte (NÃO é o item da lista). Confirme
                        emitindo manualmente no portal e inspecionando o XML. Vazio → usa o cTribNac.
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Código NBS
                      </label>
                      <input
                        type="text"
                        value={formData.codigo_nbs}
                        onChange={(e) => setFormData({ ...formData, codigo_nbs: e.target.value })}
                        className={INPUT}
                      />
                    </div>
                  </>
                )}
                {isIssnetNacional && (
                  <div className="md:col-span-2 mt-2 pt-4 border-t border-gray-200 dark:border-[#0d1f3c]">
                    <p className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                      IBS/CBS (Reforma Tributária)
                    </p>
                    <p className="text-[11px] text-gray-500 dark:text-gray-400 mb-3">
                      Campos opcionais do bloco IBS/CBS da DPS. Deixe em branco para usar os valores
                      padrão (CST 000, cClassTrib 000001).
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Indicador da Operação
                        </label>
                        <input
                          type="text"
                          inputMode="numeric"
                          maxLength={2}
                          value={formData.indicador_operacao}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              indicador_operacao: e.target.value.replace(/\D/g, '').slice(0, 2),
                            })
                          }
                          className={INPUT}
                        />
                        <p className="text-[11px] text-gray-500 mt-1">Vazio: deriva automaticamente do cTribNac.</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Situação Tributária (CST)
                        </label>
                        <input
                          type="text"
                          inputMode="numeric"
                          maxLength={3}
                          value={formData.cst_ibscbs}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              cst_ibscbs: e.target.value.replace(/\D/g, '').slice(0, 3),
                            })
                          }
                          placeholder="000"
                          className={INPUT}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Classificação Tributária (cClassTrib)
                        </label>
                        <input
                          type="text"
                          inputMode="numeric"
                          maxLength={6}
                          value={formData.cclass_trib_ibscbs}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              cclass_trib_ibscbs: e.target.value.replace(/\D/g, '').slice(0, 6),
                            })
                          }
                          placeholder="000001"
                          className={INPUT}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          % Total de Tributos (Simples Nacional)
                        </label>
                        <input
                          type="text"
                          inputMode="decimal"
                          value={formData.p_tot_trib_sn}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              p_tot_trib_sn: e.target.value.replace(/[^0-9.,]/g, ''),
                            })
                          }
                          placeholder="2.50"
                          className={INPUT}
                        />
                        <p className="text-[11px] text-gray-500 mt-1">Vazio: usa a alíquota de ISS informada abaixo.</p>
                      </div>
                    </div>
                  </div>
                )}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Regime especial de tributação
                  </label>
                  <select
                    value={formData.regime_especial_tributacao}
                    onChange={(e) =>
                      setFormData({ ...formData, regime_especial_tributacao: e.target.value })
                    }
                    className={INPUT}
                  >
                    <option value="0">Nenhum</option>
                    <option value="1">Microempresa Municipal</option>
                    <option value="2">Estimativa</option>
                    <option value="3">Sociedade de Profissionais</option>
                    <option value="4">Cooperativa</option>
                    <option value="5">MEI</option>
                    <option value="6">ME/EPP Simples Nacional</option>
                  </select>
                </div>
                <div className="flex flex-col gap-3 justify-end">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.optante_simples_nacional}
                      onChange={(e) =>
                        setFormData({ ...formData, optante_simples_nacional: e.target.checked })
                      }
                      className="w-4 h-4"
                    />
                    <span className="text-sm">Optante pelo Simples Nacional</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.incentivador_cultural}
                      onChange={(e) =>
                        setFormData({ ...formData, incentivador_cultural: e.target.checked })
                      }
                      className="w-4 h-4"
                    />
                    <span className="text-sm">Incentivador cultural</span>
                  </label>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Série {isIssnetNacional ? 'DPS / RPS' : 'RPS'}
                  </label>
                  <input
                    type="text"
                    value={formData.issnet_serie_rps}
                    onChange={(e) => setFormData({ ...formData, issnet_serie_rps: e.target.value })}
                    className={INPUT}
                    placeholder="1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Último RPS/DPS emitido
                  </label>
                  <input
                    type="text"
                    inputMode="numeric"
                    value={formData.issnet_ultimo_rps_conhecido}
                    onChange={(e) =>
                      setFormData({ ...formData, issnet_ultimo_rps_conhecido: e.target.value })
                    }
                    className={INPUT}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Número do lote (opcional)
                  </label>
                  <input
                    type="text"
                    inputMode="numeric"
                    value={formData.issnet_numero_lote}
                    onChange={(e) => setFormData({ ...formData, issnet_numero_lote: e.target.value })}
                    className={INPUT}
                  />
                </div>
              </div>
              <div className="mt-6 pt-4 border-t border-gray-200 dark:border-[#0d1f3c]">
                <CamposServicoBasicos formData={formData} setFormData={setFormData} inputClass={INPUT} />
              </div>
            </div>
          </>
        )}

        {/* —— 4. API Nacional ADN —— */}
        {isNacionalAdn && (
          <div className={CARD}>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Configurações — API Nacional NFS-e
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
              Emissão direta (ADN). Requer certificado A1 da loja e município habilitado para emissão sem
              intermediário.
            </p>

            <CertificadoFields
              certificadoFile={certificadoFile}
              temCertificadoSalvo={Boolean(config?.issnet_certificado)}
              senha={formData.issnet_senha_certificado}
              onSenha={(v) => setFormData({ ...formData, issnet_senha_certificado: v })}
              onFileChange={handleFileChange}
              inputClass={INPUT}
              labelCertificado="Certificado Digital A1 (.pfx) *"
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Inscrição municipal *
                </label>
                <input
                  type="text"
                  value={formData.inscricao_municipal}
                  onChange={(e) => setFormData({ ...formData, inscricao_municipal: e.target.value })}
                  className={INPUT}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Código IBGE do município *
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={7}
                  value={formData.nacional_codigo_municipio}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      nacional_codigo_municipio: e.target.value.replace(/\D/g, '').slice(0, 7),
                    })
                  }
                  placeholder="3543402"
                  className={INPUT}
                />
                <p className="text-[11px] text-gray-500 mt-1">7 dígitos (ex.: 3543402 Ribeirão Preto).</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Código NBS
                </label>
                <input
                  type="text"
                  value={formData.codigo_nbs}
                  onChange={(e) => setFormData({ ...formData, codigo_nbs: e.target.value })}
                  className={INPUT}
                />
              </div>
              <label className="flex items-center gap-2 cursor-pointer self-end pb-2">
                <input
                  type="checkbox"
                  checked={formData.optante_simples_nacional}
                  onChange={(e) =>
                    setFormData({ ...formData, optante_simples_nacional: e.target.checked })
                  }
                  className="w-4 h-4"
                />
                <span className="text-sm">Optante pelo Simples Nacional</span>
              </label>
            </div>

            <div className="mt-6 pt-4 border-t border-gray-200 dark:border-[#0d1f3c]">
              <CamposServicoBasicos formData={formData} setFormData={setFormData} inputClass={INPUT} />
            </div>
          </div>
        )}

        {(showCertConfig || showServicoConfig || isAsaas) && (
          <div className="flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => router.back()}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90 disabled:opacity-50"
            >
              {loading ? 'Salvando...' : 'Salvar configurações'}
            </button>
          </div>
        )}
      </form>
    </div>
  );
}

function CamposServicoBasicos({
  formData,
  setFormData,
  inputClass,
}: {
  formData: {
    codigo_servico_municipal: string;
    aliquota_iss: string;
    descricao_servico_padrao: string;
    emitir_nf_automaticamente: boolean;
  };
  setFormData: React.Dispatch<React.SetStateAction<any>>;
  inputClass: string;
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Código do serviço municipal
        </label>
        <input
          type="text"
          value={formData.codigo_servico_municipal}
          onChange={(e) => setFormData((p: any) => ({ ...p, codigo_servico_municipal: e.target.value }))}
          className={inputClass}
          placeholder="Ex: 1401"
        />
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
          onChange={(e) => setFormData((p: any) => ({ ...p, aliquota_iss: e.target.value }))}
          className={inputClass}
        />
      </div>
      <div className="md:col-span-2">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Descrição padrão do serviço
        </label>
        <textarea
          value={formData.descricao_servico_padrao}
          onChange={(e) => setFormData((p: any) => ({ ...p, descricao_servico_padrao: e.target.value }))}
          rows={3}
          className={inputClass}
        />
      </div>
      <div className="md:col-span-2">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={formData.emitir_nf_automaticamente}
            onChange={(e) =>
              setFormData((p: any) => ({ ...p, emitir_nf_automaticamente: e.target.checked }))
            }
            className="w-4 h-4"
          />
          <span className="text-sm text-gray-700 dark:text-gray-300">
            Emitir nota fiscal automaticamente ao confirmar pagamento
          </span>
        </label>
      </div>
    </div>
  );
}

function CertificadoFields({
  certificadoFile,
  temCertificadoSalvo,
  senha,
  onSenha,
  onFileChange,
  inputClass,
  labelCertificado = 'Certificado Digital A1 (.pfx) *',
}: {
  certificadoFile: File | null;
  temCertificadoSalvo: boolean;
  senha: string;
  onSenha: (v: string) => void;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  inputClass: string;
  labelCertificado?: string;
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
      <div className="md:col-span-2">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {labelCertificado}
        </label>
        <label className="flex items-center gap-3 px-4 py-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:border-[#0176d3]">
          <Upload size={20} className="text-gray-400" />
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {certificadoFile
              ? certificadoFile.name
              : temCertificadoSalvo
                ? 'Certificado já enviado — clique para alterar'
                : 'Clique para selecionar o arquivo .pfx'}
          </span>
          <input type="file" accept=".pfx" onChange={onFileChange} className="hidden" />
        </label>
      </div>
      <div className="md:col-span-2">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Senha do certificado
        </label>
        <input
          type="password"
          value={senha}
          onChange={(e) => onSenha(e.target.value)}
          placeholder="Senha do arquivo .pfx"
          className={inputClass}
        />
      </div>
    </div>
  );
}
