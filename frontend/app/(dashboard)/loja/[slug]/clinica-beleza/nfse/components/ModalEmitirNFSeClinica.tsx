'use client';

import { useEffect, useState } from 'react';
import { X, AlertCircle } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { logger } from '@/lib/logger';
import { formatCpfCnpj } from '@/lib/format-br';
import { ensureArray } from '@/lib/array-helpers';
import {
  NFSE_EMISSAO_INITIAL_FORM,
  buscarTomadorCadastroPorDocumento,
  defaultsServicoFromCrmConfig,
  preencherFormTomador,
  somenteDigitosDocumento,
} from '@/lib/nfse-emissao-form';
import { parseNfseEmissaoResult, type NfseEmissaoResult, type NfseEmitirResponse } from '@/lib/nfse-helpers';
import { useClinicaNFSeConfig } from '@/contexts/ClinicaBelezaNFSeConfigContext';
import { ModalFormButtons } from '@/app/(dashboard)/loja/[slug]/crm-vendas/nfse/components/ModalFormButtons';
import { ModalEmitirNFSeTomadorFields } from '@/app/(dashboard)/loja/[slug]/crm-vendas/nfse/components/ModalEmitirNFSeTomadorFields';
import { ModalEmitirNFSeEnderecoFields } from '@/app/(dashboard)/loja/[slug]/crm-vendas/nfse/components/ModalEmitirNFSeEnderecoFields';
import { ModalEmitirNFSeStepInicioClinica } from './ModalEmitirNFSeStepInicioClinica';
import { ServicoFieldsClinica } from './ServicoFieldsClinica';

interface ModalEmitirNFSeClinicaProps {
  onClose: () => void;
  onSuccess: (result: NfseEmissaoResult) => void;
  onRefreshList?: () => void;
}

type PacienteOpcao = { id: number; nome: string; cpf: string };

export function ModalEmitirNFSeClinica({ onClose, onSuccess, onRefreshList }: ModalEmitirNFSeClinicaProps) {
  const { config } = useClinicaNFSeConfig();
  const defaultsServico = defaultsServicoFromCrmConfig(config);
  const [step, setStep] = useState<'inicio' | 'formulario'>('inicio');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [erroInicio, setErroInicio] = useState('');
  const [buscandoTomador, setBuscandoTomador] = useState(false);
  const [fonteTomador, setFonteTomador] = useState<'paciente' | 'nfse' | 'brasilapi' | null>(null);
  const [documentoTomador, setDocumentoTomador] = useState('');
  const [pacienteBusca, setPacienteBusca] = useState('');
  const [pacienteOpcoes, setPacienteOpcoes] = useState<PacienteOpcao[]>([]);
  const [pacienteSelecionadoId, setPacienteSelecionadoId] = useState('');
  const [formData, setFormData] = useState(NFSE_EMISSAO_INITIAL_FORM);

  useEffect(() => {
    const q = pacienteBusca.trim();
    if (q.length < 2) {
      setPacienteOpcoes([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await apiClient.get('/clinica-beleza/patients/', {
          params: { search: q, page_size: 15 },
        });
        const lista = ensureArray<Record<string, unknown>>(res.data).map((p) => ({
          id: Number(p.id),
          nome: String(p.nome || p.name || ''),
          cpf: String(p.cpf || ''),
        }));
        setPacienteOpcoes(lista);
      } catch {
        setPacienteOpcoes([]);
      }
    }, 350);
    return () => clearTimeout(timer);
  }, [pacienteBusca]);

  const handlePacienteSelecionado = (id: string) => {
    setPacienteSelecionadoId(id);
    setErroInicio('');
    const p = pacienteOpcoes.find((x) => String(x.id) === id);
    if (!p) return;
    if (p.cpf) {
      setDocumentoTomador(formatCpfCnpj(p.cpf));
    } else {
      setErroInicio('Este paciente não possui CPF cadastrado. Informe o documento manualmente.');
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
        const fonte: 'paciente' | 'nfse' | 'brasilapi' =
          encontrado._fonte === 'brasilapi' || encontrado._fonte === 'nfse'
            ? encontrado._fonte
            : 'paciente';
        setFonteTomador(fonte);
        setFormData({
          ...NFSE_EMISSAO_INITIAL_FORM,
          ...defaultsServico,
          ...preencherFormTomador(encontrado),
          conta_id: null,
          tomador_cpf_cnpj: documentoTomador,
        });
      } else {
        setFonteTomador(null);
        setFormData({
          ...NFSE_EMISSAO_INITIAL_FORM,
          ...defaultsServico,
          tomador_cpf_cnpj: documentoTomador,
        });
      }
      setStep('formulario');
      setError('');
    } catch (err) {
      logger.warn('Erro ao buscar cliente para NFS-e clínica:', err);
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
      const payload = {
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
        servico_descricao: formData.servico_descricao,
        valor_servicos: formData.valor_servicos,
        enviar_email: formData.enviar_email,
        codigo_cnae: formData.codigo_cnae || undefined,
        codigo_servico: formData.codigo_servico || undefined,
        item_lista_servico: formData.item_lista_servico || undefined,
      };

      const res = await apiClient.post<NfseEmitirResponse>('/nfse/emitir/', payload);
      if (res.data.success === false) {
        setError(res.data.error || 'Erro ao emitir NFS-e');
        onRefreshList?.();
        return;
      }
      onSuccess(parseNfseEmissaoResult(res.status, res.data));
    } catch (err: unknown) {
      logger.warn('Erro ao emitir NFS-e clínica:', err);
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
            <ModalEmitirNFSeStepInicioClinica
              documentoTomador={documentoTomador}
              onDocumentoChange={(value) => {
                setDocumentoTomador(value);
                setPacienteSelecionadoId('');
                setErroInicio('');
              }}
              pacienteBusca={pacienteBusca}
              onPacienteBuscaChange={(value) => {
                setPacienteBusca(value);
                setPacienteSelecionadoId('');
              }}
              pacienteOpcoes={pacienteOpcoes}
              pacienteSelecionadoId={pacienteSelecionadoId}
              onPacienteSelecionado={handlePacienteSelecionado}
              erro={erroInicio}
              buscandoTomador={buscandoTomador}
              onContinuar={handleContinuarInicio}
              onClose={onClose}
            />
          )}

          {step === 'formulario' && (
            <form onSubmit={handleSubmit} className="space-y-6">
              {formData.tomador_nome ? (
                <div className="rounded-lg border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20 p-3 text-sm text-green-900 dark:text-green-100">
                  {fonteTomador === 'paciente'
                    ? 'Cliente encontrado no cadastro de pacientes.'
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

              <ServicoFieldsClinica
                servico_descricao={formData.servico_descricao}
                valor_servicos={formData.valor_servicos}
                enviar_email={formData.enviar_email}
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
