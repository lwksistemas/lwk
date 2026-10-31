'use client';

import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { useRouter, useParams } from 'next/navigation';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import apiClient from '@/lib/api-client';
import { logger } from '@/lib/logger';
import { formatApiErrorBody } from '@/lib/api-errors';
import { FileText, AlertCircle, CheckCircle2, Info, ArrowLeft } from 'lucide-react';
import { salvarDescricoesPrestadoraNfse } from './components/DescricoesPorPrestadora';
import { NfseEmissaoSecoes } from './components/NfseEmissaoSecoes';
import {
  aplicarEmissaoOpcao,
  resolverEmissaoOpcao,
  type EmissaoOpcao,
  type ProvedorNf,
} from '@/lib/nfse-emissao-opcoes';

type ConfiguracaoNotaFiscalPageProps = {
  params?: Promise<{ slug: string }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

const DEFAULT_DESCRICAO_SERVICO = 'Desenvolvimento e licenciamento de software sob demanda';
const DEFAULT_CODIGO_SERVICO = '1401';

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
    () => resolverEmissaoOpcao(formData.provedor_nf, formData.issnet_usar_padrao_nacional),
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

      await salvarDescricoesPrestadoraNfse();
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

  const isIssnet = emissaoOpcao === 'issnet_nacional';
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
        <NfseEmissaoSecoes
          configBase={configBase}
          emissaoOpcao={emissaoOpcao}
          selecionarEmissao={selecionarEmissao}
          isAsaas={isAsaas}
          isIssnet={isIssnet}
          isIssnetNacional={isIssnetNacional}
          isNacionalAdn={isNacionalAdn}
          showCertConfig={showCertConfig}
          showServicoConfig={showServicoConfig}
          asaasConfigurada={Boolean(config?.asaas_api_key_configured)}
          temCertificado={Boolean(config?.issnet_certificado)}
          senhasSalvas={Boolean(config?.issnet_senhas_salvas)}
          formData={formData}
          setFormData={setFormData}
          certificadoFile={certificadoFile}
          onFileChange={handleFileChange}
          onTestarConexao={() => void testarConexaoIssnet()}
          testando={issnetTestLoading}
          testeMensagem={issnetTestMessage}
          onVoltar={() => router.back()}
          loading={loading}
        />
      </form>
    </div>
  );
}

