'use client';

import { useState, useEffect } from 'react';
import { X, AlertCircle } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { logger } from '@/lib/logger';
import {
  NFSE_EMISSAO_INITIAL_FORM,
  carregarContasLeadsParaNfse,
  type NfseEmissaoContaOption,
} from '@/lib/nfse-emissao-form';
import { ServicoFields } from './ServicoFields';
import { ModalFormButtons } from './ModalFormButtons';
import { ModalEmitirNFSeStepEscolha } from './ModalEmitirNFSeStepEscolha';
import { ModalEmitirNFSeContaSelector } from './ModalEmitirNFSeContaSelector';
import { ModalEmitirNFSeTomadorFields } from './ModalEmitirNFSeTomadorFields';
import { ModalEmitirNFSeEnderecoFields } from './ModalEmitirNFSeEnderecoFields';

interface ModalEmitirNFSeProps {
  onClose: () => void;
  onSuccess: () => void;
  onRefreshList?: () => void;
}

export function ModalEmitirNFSe({ onClose, onSuccess, onRefreshList }: ModalEmitirNFSeProps) {
  const [step, setStep] = useState<'escolha' | 'manual' | 'conta'>('escolha');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [contas, setContas] = useState<NfseEmissaoContaOption[]>([]);
  const [loadingContas, setLoadingContas] = useState(false);
  const [formData, setFormData] = useState(NFSE_EMISSAO_INITIAL_FORM);
  const [selectedId, setSelectedId] = useState('');

  useEffect(() => {
    if (step === 'conta') {
      carregarContas();
    }
  }, [step]);

  const carregarContas = async () => {
    try {
      setLoadingContas(true);
      setContas(await carregarContasLeadsParaNfse());
    } catch (err) {
      logger.warn('Erro ao carregar contas para NFS-e:', err);
    } finally {
      setLoadingContas(false);
    }
  };

  const handleContaChange = (contaId: number | string) => {
    setSelectedId(String(contaId));
    const conta = contas.find((c) => String(c.id) === String(contaId));
    if (conta) {
      setFormData({
        ...formData,
        conta_id: conta._tipo === 'conta' ? Number(conta.id) : null,
        tomador_cpf_cnpj: conta.cnpj || '',
        tomador_nome: conta.razao_social || conta.nome || '',
        tomador_email: conta.email || '',
        tomador_logradouro: conta.logradouro || '',
        tomador_numero: conta.numero || '',
        tomador_complemento: conta.complemento || '',
        tomador_bairro: conta.bairro || '',
        tomador_cidade: conta.cidade || '',
        tomador_uf: conta.uf || '',
        tomador_cep: conta.cep || '',
      });
    }
  };

  const handleFieldChange = (field: string, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const payload =
        step === 'conta' && formData.conta_id
          ? {
              conta_id: formData.conta_id,
              servico_descricao: formData.servico_descricao,
              valor_servicos: formData.valor_servicos,
              enviar_email: formData.enviar_email,
              codigo_cnae: formData.codigo_cnae || undefined,
              codigo_servico: formData.codigo_servico || undefined,
            }
          : {
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
            };
      await apiClient.post('/nfse/emitir/', payload);
      onSuccess();
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

          {error && (
            <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
              <AlertCircle size={20} className="text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
              <span className="text-sm text-red-800 dark:text-red-200">{error}</span>
            </div>
          )}

          {step === 'escolha' && (
            <ModalEmitirNFSeStepEscolha
              onSelectConta={() => setStep('conta')}
              onSelectManual={() => setStep('manual')}
              onClose={onClose}
            />
          )}

          {step === 'conta' && (
            <form onSubmit={handleSubmit} className="space-y-6">
              <ModalEmitirNFSeContaSelector
                contas={contas}
                loading={loadingContas}
                value={selectedId}
                onChange={handleContaChange}
              />
              <ServicoFields
                servico_descricao={formData.servico_descricao}
                valor_servicos={formData.valor_servicos}
                enviar_email={formData.enviar_email}
                codigo_cnae={formData.codigo_cnae}
                codigo_servico={formData.codigo_servico}
                onChange={handleFieldChange}
              />
              <ModalFormButtons loading={loading} onBack={() => setStep('escolha')} onClose={onClose} />
            </form>
          )}

          {step === 'manual' && (
            <form onSubmit={handleSubmit} className="space-y-6">
              <ModalEmitirNFSeTomadorFields formData={formData} onChange={handleFieldChange} />
              <ModalEmitirNFSeEnderecoFields formData={formData} onChange={handleFieldChange} />
              <ServicoFields
                servico_descricao={formData.servico_descricao}
                valor_servicos={formData.valor_servicos}
                enviar_email={formData.enviar_email}
                codigo_cnae={formData.codigo_cnae}
                codigo_servico={formData.codigo_servico}
                onChange={handleFieldChange}
              />
              <ModalFormButtons loading={loading} onBack={() => setStep('escolha')} onClose={onClose} />
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
