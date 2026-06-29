'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useClinicaNFSeConfig } from '@/contexts/ClinicaBelezaNFSeConfigContext';
import apiClient from '@/lib/api-client';
import { logger } from '@/lib/logger';
import {
  FileText, Upload, AlertCircle, CheckCircle2,
  Info, Loader2, ArrowLeft,
} from 'lucide-react';

type Props = { configBackHref: string };

export default function ClinicaNFSeForm({ configBackHref }: Props) {
  const { config, recarregar } = useClinicaNFSeConfig();

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{
    type: 'success' | 'error'; text: string;
  } | null>(null);

  const [formData, setFormData] = useState({
    provedor_nf: 'asaas' as 'asaas' | 'issnet' | 'nacional' | 'manual',
    issnet_usuario: '',
    issnet_senha: '',
    issnet_senha_certificado: '',
    codigo_servico_municipal: '0601',
    descricao_servico_padrao: 'Serviços de estética, saúde e bem-estar',
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
    emitir_nf_automaticamente: true,
  });

  const [certificadoFile, setCertificadoFile] = useState<File | null>(null);
  const [issnetTestLoading, setIssnetTestLoading] = useState(false);

  const [issnetTestMessage, setIssnetTestMessage] = useState<{
    type: 'ok' | 'error'; text: string;
  } | null>(null);

  useEffect(() => {
    if (config) {
      setFormData({
        provedor_nf: config.provedor_nf || 'asaas',
        issnet_usuario: config.issnet_usuario || '',
        issnet_senha: '',
        issnet_senha_certificado: '',
        codigo_servico_municipal: config.codigo_servico_municipal || '0601',
        descricao_servico_padrao:
          config.descricao_servico_padrao || 'Serviços de estética, saúde e bem-estar',
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
          config.issnet_ultimo_rps_conhecido != null
            ? String(config.issnet_ultimo_rps_conhecido) : '',
        issnet_numero_lote:
          config.issnet_numero_lote != null
            ? String(config.issnet_numero_lote) : '',
        issnet_ambiente_homologacao: config.issnet_ambiente_homologacao ?? false,
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
      const clearableFields = [
        'codigo_cnae', 'codigo_nbs', 'item_lista_servico', 'inscricao_municipal',
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
      if (certificadoFile) {
        data.append('issnet_certificado', certificadoFile);
      }

      await apiClient.patch('/clinica-beleza/nfse-config/', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setMessage({ type: 'success', text: 'Configurações salvas com sucesso!' });
      await recarregar();
      setFormData(prev => ({ ...prev, issnet_senha: '', issnet_senha_certificado: '' }));
      setCertificadoFile(null);
    } catch (error: any) {
      logger.warn('Erro ao salvar config NFS-e clínica:', error);
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Erro ao salvar configurações',
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
        success?: boolean; message?: string; detail?: string;
      }>('/clinica-beleza/nfse-config/test-issnet/', fd);

      if (res.data?.success) {
        setIssnetTestMessage({ type: 'ok', text: res.data.message || 'Conexão ISSNet OK.' });
      } else {
        setIssnetTestMessage({
          type: 'error', text: res.data?.detail || 'Não foi possível validar.',
        });
      }
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string; message?: string } } };
      const detail = ax.response?.data?.detail || ax.response?.data?.message
        || (err instanceof Error ? err.message : 'Erro ao testar conexão.');
      setIssnetTestMessage({ type: 'error', text: String(detail) });
    } finally {
      setIssnetTestLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.pfx')) {
        setMessage({ type: 'error', text: 'Selecione um arquivo .pfx (certificado digital A1)' });
        return;
      }
      setCertificadoFile(file);
      setMessage(null);
    }
  };

  const provedorInfo = {
    asaas: {
      titulo: 'Asaas (conta da sua loja)',
      descricao: 'Emissão de NFS-e pela conta Asaas da loja.',
    },
    issnet: {
      titulo: 'ISSNet - Ribeirão Preto (Direto)',
      descricao: 'Emissão direta na Prefeitura com o CNPJ da sua loja. Requer certificado digital A1.',
    },
    nacional: {
      titulo: 'API Nacional NFS-e (Direto)',
      descricao: 'Emissão através da API Nacional NFS-e. Em breve disponível.',
    },
    manual: {
      titulo: 'Emissão Manual',
      descricao: 'Sem integração automática.',
    },
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <FileText size={28} />
          Nota Fiscal — Configuração da Clínica
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Configuração individual de NFS-e desta clínica para emissão aos seus clientes
        </p>
      </div>

      {message && (
        <div className={`p-4 rounded-lg flex items-start gap-3 ${
          message.type === 'success'
            ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200'
            : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200'
        }`}>
          {message.type === 'success'
            ? <CheckCircle2 size={20} className="shrink-0 mt-0.5" />
            : <AlertCircle size={20} className="shrink-0 mt-0.5" />}
          <span className="text-sm">{message.text}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Provedor */}
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Provedor de Nota Fiscal
          </h2>
          <div className="space-y-3">
            {(Object.keys(provedorInfo) as Array<keyof typeof provedorInfo>).map((key) => {
              const info = provedorInfo[key];
              const isDisabled = key === 'nacional';
              return (
                <label key={key} className={`flex items-start gap-3 p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  formData.provedor_nf === key
                    ? 'border-[#0176d3] bg-[#e3f3ff] dark:bg-[#0176d3]/10'
                    : 'border-gray-200 dark:border-[#0d1f3c] hover:border-gray-300'
                } ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}>
                  <input type="radio" name="provedor_nf" value={key}
                    checked={formData.provedor_nf === key}
                    onChange={(e) => setFormData({ ...formData, provedor_nf: e.target.value as any })}
                    disabled={isDisabled} className="mt-1" />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900 dark:text-white">
                      {info.titulo}
                      {isDisabled && <span className="ml-2 text-xs text-gray-500">(Em breve)</span>}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">{info.descricao}</div>
                  </div>
                </label>
              );
            })}
          </div>
        </div>

        {/* Credenciais ISSNet */}
        {formData.provedor_nf === 'issnet' && (
          <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Credenciais ISSNet
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Usuário ISSNet *
                </label>
                <input type="text" value={formData.issnet_usuario}
                  onChange={(e) => setFormData({ ...formData, issnet_usuario: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                  required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Senha ISSNet *
                </label>
                <input type="password" value={formData.issnet_senha}
                  onChange={(e) => setFormData({ ...formData, issnet_senha: e.target.value })}
                  placeholder="Digite para alterar"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Certificado Digital A1 (.pfx) *
                </label>
                <label className="flex items-center gap-3 px-4 py-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:border-[#0176d3] transition-colors">
                  <Upload size={20} className="text-gray-400" />
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {certificadoFile ? certificadoFile.name
                      : config?.issnet_certificado ? 'Certificado já enviado - Clique para alterar'
                      : 'Clique para selecionar o arquivo .pfx'}
                  </span>
                  <input type="file" accept=".pfx" onChange={handleFileChange} className="hidden" />
                </label>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Senha do Certificado *
                </label>
                <input type="password" value={formData.issnet_senha_certificado}
                  onChange={(e) => setFormData({ ...formData, issnet_senha_certificado: e.target.value })}
                  placeholder="Senha do arquivo .pfx"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white" />
              </div>
              <div className="md:col-span-2 space-y-3 pt-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={formData.issnet_ambiente_homologacao}
                    onChange={(e) => setFormData({ ...formData, issnet_ambiente_homologacao: e.target.checked })}
                    className="w-4 h-4" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    Homologação / teste (ISSNet)
                  </span>
                </label>
                <button type="button" onClick={() => void testarConexaoIssnet()}
                  disabled={issnetTestLoading || !formData.issnet_usuario.trim()
                    || (!certificadoFile && !config?.issnet_certificado)
                    || (!formData.issnet_senha && !formData.issnet_senha_certificado && !config?.issnet_senhas_salvas)}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-[#0176d3] text-[#0176d3] hover:bg-[#0176d3]/10 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed">
                  {issnetTestLoading ? <><Loader2 className="w-4 h-4 animate-spin" />Testando…</> : 'Testar conexão ISSNet'}
                </button>
                {issnetTestMessage && (
                  <div className={`flex items-start gap-2 p-3 rounded-lg text-sm ${
                    issnetTestMessage.type === 'ok'
                      ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200 border border-green-200'
                      : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 border border-red-200'
                  }`}>
                    {issnetTestMessage.type === 'ok'
                      ? <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5" />
                      : <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />}
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Código do Serviço Municipal
              </label>
              <input type="text" value={formData.codigo_servico_municipal}
                onChange={(e) => setFormData({ ...formData, codigo_servico_municipal: e.target.value })}
                placeholder="Ex: 0601"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Alíquota ISS (%)
              </label>
              <input type="text" value={formData.aliquota_iss}
                onChange={(e) => setFormData({ ...formData, aliquota_iss: e.target.value })}
                placeholder="2.00"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Descrição Padrão do Serviço
              </label>
              <textarea value={formData.descricao_servico_padrao}
                onChange={(e) => setFormData({ ...formData, descricao_servico_padrao: e.target.value })}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white" />
            </div>

            {formData.provedor_nf === 'issnet' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Inscrição Municipal
                  </label>
                  <input type="text" value={formData.inscricao_municipal}
                    onChange={(e) => setFormData({ ...formData, inscricao_municipal: e.target.value })}
                    placeholder="Ex.: 20130440"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Código CNAE (opcional)
                  </label>
                  <input type="text" value={formData.codigo_cnae}
                    onChange={(e) => setFormData({ ...formData, codigo_cnae: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Item Lista Serviço (opcional)
                  </label>
                  <input type="text" value={formData.item_lista_servico}
                    onChange={(e) => setFormData({ ...formData, item_lista_servico: e.target.value })}
                    placeholder="Ex.: 06.01"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Série do RPS
                  </label>
                  <input type="text" value={formData.issnet_serie_rps}
                    onChange={(e) => setFormData({ ...formData, issnet_serie_rps: e.target.value })}
                    placeholder="Ex.: E ou NFSE"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Último RPS emitido
                  </label>
                  <input type="number" value={formData.issnet_ultimo_rps_conhecido}
                    onChange={(e) => setFormData({ ...formData, issnet_ultimo_rps_conhecido: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Regime Especial Tributação
                  </label>
                  <select value={formData.regime_especial_tributacao}
                    onChange={(e) => setFormData({ ...formData, regime_especial_tributacao: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white">
                    <option value="0">Nenhum</option>
                    <option value="1">Microempresa Municipal</option>
                    <option value="2">Estimativa</option>
                    <option value="3">Sociedade de Profissionais</option>
                    <option value="4">Cooperativa</option>
                    <option value="5">MEI - Simples Nacional</option>
                    <option value="6">ME/EPP - Simples Nacional</option>
                  </select>
                </div>
              </>
            )}

            <div className="md:col-span-2 space-y-3 pt-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={formData.optante_simples_nacional}
                  onChange={(e) => setFormData({ ...formData, optante_simples_nacional: e.target.checked })}
                  className="w-4 h-4" />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Optante pelo Simples Nacional
                </span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={formData.incentivador_cultural}
                  onChange={(e) => setFormData({ ...formData, incentivador_cultural: e.target.checked })}
                  className="w-4 h-4" />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Incentivador Cultural
                </span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={formData.emitir_nf_automaticamente}
                  onChange={(e) => setFormData({ ...formData, emitir_nf_automaticamente: e.target.checked })}
                  className="w-4 h-4" />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Emitir NF automaticamente ao confirmar pagamento
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Botão Salvar */}
        <div className="flex justify-end">
          <button type="submit" disabled={loading}
            className="px-6 py-3 bg-[#0176d3] text-white rounded-lg font-medium hover:bg-[#0156a3] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
            Salvar Configurações
          </button>
        </div>
      </form>
    </div>
  );
}
