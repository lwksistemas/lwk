'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { X, AlertCircle } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { logger } from '@/lib/logger';
import { formatCpfCnpj } from '@/lib/format-br';
import {
  NFSE_EMISSAO_INITIAL_FORM,
  buscarTomadorCadastroPorDocumento,
  defaultsServicoFromCrmConfig,
  preencherFormTomador,
  somenteDigitosDocumento,
} from '@/lib/nfse-emissao-form';
import { parseNfseEmissaoResult, type NfseEmissaoResult, type NfseEmitirResponse } from '@/lib/nfse-helpers';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import { useLojaInfoPublica } from '@/hooks/useLojaInfoPublica';
import { ServicoFields } from './ServicoFields';
import { ModalFormButtons } from './ModalFormButtons';
import { ModalEmitirNFSeStepInicio } from './ModalEmitirNFSeStepInicio';
import { ModalEmitirNFSeTomadorFields } from './ModalEmitirNFSeTomadorFields';
import { ModalEmitirNFSeEnderecoFields } from './ModalEmitirNFSeEnderecoFields';

interface ModalEmitirNFSeProps {
  onClose: () => void;
  onSuccess: (result: NfseEmissaoResult) => void;
  onRefreshList?: () => void;
}

export function ModalEmitirNFSe({ onClose, onSuccess, onRefreshList }: ModalEmitirNFSeProps) {
  const params = useParams();
  const slug = (params?.slug as string) || '';
  const { loja } = useLojaInfoPublica(slug);
  const emitenteNome = (loja?.nome || '').trim();
  const { config } = useCRMConfig();
  const defaultsServico = defaultsServicoFromCrmConfig(config);
  const [step, setStep] = useState<'inicio' | 'formulario'>('inicio');
  const [modoTomador, setModoTomador] = useState<'cadastrado' | 'manual'>('manual');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [erroInicio, setErroInicio] = useState('');
  const [buscandoTomador, setBuscandoTomador] = useState(false);
  const [fonteTomador, setFonteTomador] = useState<'conta' | 'lead' | 'nfse' | 'brasilapi' | 'paciente' | null>(null);
  const [documentoTomador, setDocumentoTomador] = useState('');
  const [contaBuscaId, setContaBuscaId] = useState('');
  const [formData, setFormData] = useState(NFSE_EMISSAO_INITIAL_FORM);

  const handleContaBuscaChange = async (id: string) => {
    setContaBuscaId(id);
    setErroInicio('');
    if (!id) return;
    setBuscandoTomador(true);
    try {
      const res = await apiClient.get<{ cnpj?: string }>(`/crm-vendas/contas/${id}/`);
      const cnpj = (res.data.cnpj || '').trim();
      if (cnpj) {
        setDocumentoTomador(formatCpfCnpj(cnpj));
      } else {
        setErroInicio('Esta conta não possui CNPJ cadastrado. Informe o documento manualmente.');
      }
    } catch {
      setErroInicio('Erro ao carregar dados da conta. Tente novamente.');
      setContaBuscaId('');
    } finally {
      setBuscandoTomador(false);
    }
  };

  const handleFieldChange = (field: string, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleContinuarInicio = async () => {
    setErroInicio('');
    const docDigits = somenteDigitosDocumento(documentoTomador);
    if (docDigits.length !== 11 && docDigits.length !== 14) {
      setErroInicio('Informe um CPF (11 dígitos) ou CNPJ (14 dígitos) válido.');
      return;
    }

    setBuscandoTomador(true);
    try {
      const encontrado = await buscarTomadorCadastroPorDocumento(documentoTomador);

      if (encontrado) {
        const temConta = encontrado._tipo === 'conta' && typeof encontrado.id === 'number';
        setFonteTomador(encontrado._fonte ?? (temConta ? 'conta' : 'lead'));
        setModoTomador(temConta ? 'cadastrado' : 'manual');
        setFormData({
          ...NFSE_EMISSAO_INITIAL_FORM,
          ...defaultsServico,
          ...preencherFormTomador(encontrado),
          tomador_cpf_cnpj: documentoTomador,
        });
      } else {
        setFonteTomador(null);
        setModoTomador('manual');
        setFormData({
          ...NFSE_EMISSAO_INITIAL_FORM,
          ...defaultsServico,
          tomador_cpf_cnpj: documentoTomador,
        });
      }
      setStep('formulario');
      setError('');
    } catch (err) {
      logger.warn('Erro ao buscar cliente para NFS-e:', err);
      setErroInicio('Erro ao buscar cliente no cadastro. Tente novamente.');
    } finally {
      setBuscandoTomador(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const basePayload = {
        servico_descricao: formData.servico_descricao,
        valor_servicos: formData.valor_servicos,
        enviar_email: formData.enviar_email,
        codigo_cnae: formData.codigo_cnae || undefined,
        codigo_servico: formData.codigo_servico || undefined,
        item_lista_servico: formData.item_lista_servico || undefined,
      };

      const payload =
        modoTomador === 'cadastrado' && formData.conta_id
          ? { ...basePayload, conta_id: formData.conta_id }
          : {
              ...basePayload,
              tomador_cpf_cnpj: formData.tomador_cpf_cnpj,
              tomador_nome: formData.tomador_nome,
              tomador_email: formData.tomador_email,
              tomador_logradouro: formData.tomador_logradouro,
              tomador_numero: formData.tomador_numero,
              tomador_complemento: formData.tomador_complemento,
              tomador_bairro: formData.tomador_bairro,
              tomador_cidade: formData.tomador_cidade,
              tomador_uf: formData.tomador_uf,
              tomador_cep: formData.tomador_cep,
            };

      const res = await apiClient.post<NfseEmitirResponse>('/nfse/emitir/', payload);
      if (res.data.success === false) {
        setError(res.data.error || 'Erro ao emitir NFS-e');
        onRefreshList?.();
        return;
      }
      onSuccess(parseNfseEmissaoResult(res.status, res.data));
    } catch (err: unknown) {
      logger.warn('Erro ao emitir NFS-e:', err);
      const ax = err as { response?: { data?: { error?: string } } };
      setError(ax.response?.data?.error || 'Erro ao emitir NFS-e');
      onRefreshList?.();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-[#16325c] rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">Emitir NFS-e</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
              <X size={24} />
            </button>
          </div>

          {error && step === 'formulario' && (
            <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
              <AlertCircle size={20} className="text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
              <span className="text-sm text-red-800 dark:text-red-200">{error}</span>
            </div>
          )}

          {step === 'inicio' && (
            <ModalEmitirNFSeStepInicio
              documentoTomador={documentoTomador}
              onDocumentoChange={(value) => {
                setDocumentoTomador(value);
                setContaBuscaId('');
                setErroInicio('');
              }}
              contaBuscaId={contaBuscaId}
              onContaBuscaChange={handleContaBuscaChange}
              erro={erroInicio}
              buscandoTomador={buscandoTomador}
              onContinuar={handleContinuarInicio}
              onClose={onClose}
              emitenteNome={emitenteNome}
            />
          )}

          {step === 'formulario' && (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="rounded-lg border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20 p-3 text-sm">
                <span className="font-medium text-blue-900 dark:text-blue-100">Emissor: </span>
                <span className="text-blue-800 dark:text-blue-200">
                  {emitenteNome || 'Loja atual (CNPJ do cadastro)'}
                </span>
              </div>

              {modoTomador === 'cadastrado' ? (
                <div className="rounded-lg border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20 p-4 text-sm space-y-1">
                  <p className="font-medium text-green-900 dark:text-green-100">Cliente encontrado no cadastro</p>
                  <p className="text-green-800 dark:text-green-200">{formData.tomador_nome}</p>
                  <p className="text-green-700 dark:text-green-300">{formData.tomador_cpf_cnpj}</p>
                  {formData.tomador_email && (
                    <p className="text-green-700 dark:text-green-300">{formData.tomador_email}</p>
                  )}
                </div>
              ) : (
                <>
                  {formData.tomador_nome ? (
                    <div className="rounded-lg border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20 p-3 text-sm text-green-900 dark:text-green-100">
                      {fonteTomador === 'conta'
                        ? 'Cliente encontrado no cadastro (Clientes).'
                        : fonteTomador === 'lead'
                          ? 'Cliente encontrado no cadastro (Leads).'
                          : fonteTomador === 'brasilapi'
                            ? 'Dados obtidos da Receita Federal. Confira abaixo e informe o e-mail do cliente.'
                            : fonteTomador === 'nfse'
                              ? 'Dados recuperados de nota fiscal anterior. Confira e complete o endereço se necessário.'
                              : 'Dados do cliente encontrados. Confira abaixo e complete o endereço se necessário.'}
                    </div>
                  ) : (
                    <div className="rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 p-3 text-sm text-amber-900 dark:text-amber-100">
                      Cliente não encontrado no cadastro. Preencha os dados manualmente.
                    </div>
                  )}
                  <ModalEmitirNFSeTomadorFields formData={formData} onChange={handleFieldChange} />
                  <ModalEmitirNFSeEnderecoFields formData={formData} onChange={handleFieldChange} />
                </>
              )}

              <ServicoFields
                servico_descricao={formData.servico_descricao}
                valor_servicos={formData.valor_servicos}
                enviar_email={formData.enviar_email}
                codigo_cnae={formData.codigo_cnae}
                codigo_servico={formData.codigo_servico}
                item_lista_servico={formData.item_lista_servico}
                onChange={handleFieldChange}
              />
              <ModalFormButtons
                loading={loading}
                onBack={() => {
                  setStep('inicio');
                  setFonteTomador(null);
                  setError('');
                }}
                onClose={onClose}
              />
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
