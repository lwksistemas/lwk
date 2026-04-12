'use client';

import { useState, useEffect } from 'react';
import { FileText, Plus, X, AlertCircle } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { ServicoFields } from './ServicoFields';
import { ModalFormButtons } from './ModalFormButtons';

function unwrapDrfList<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === 'object' && Array.isArray((data as { results?: unknown }).results)) {
    return (data as { results: T[] }).results;
  }
  return [];
}

interface ModalEmitirNFSeProps {
  onClose: () => void;
  onSuccess: () => void;
  onRefreshList?: () => void;
}

const INITIAL_FORM = {
  conta_id: null as number | null,
  tomador_cpf_cnpj: '',
  tomador_nome: '',
  tomador_email: '',
  tomador_logradouro: '',
  tomador_numero: '',
  tomador_complemento: '',
  tomador_bairro: '',
  tomador_cidade: '',
  tomador_uf: '',
  tomador_cep: '',
  servico_descricao: '',
  valor_servicos: '',
  enviar_email: true,
};

export function ModalEmitirNFSe({ onClose, onSuccess, onRefreshList }: ModalEmitirNFSeProps) {
  const [step, setStep] = useState<'escolha' | 'manual' | 'conta'>('escolha');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [contas, setContas] = useState<any[]>([]);
  const [loadingContas, setLoadingContas] = useState(false);
  const [formData, setFormData] = useState(INITIAL_FORM);

  useEffect(() => {
    if (step === 'conta') {
      carregarContas();
    }
  }, [step]);

  const carregarContas = async () => {
    try {
      setLoadingContas(true);
      const res = await apiClient.get('/crm-vendas/contas/');
      setContas(unwrapDrfList(res.data));
    } catch (err) {
      console.error('Erro ao carregar contas:', err);
    } finally {
      setLoadingContas(false);
    }
  };

  const handleContaChange = (contaId: number) => {
    const conta = contas.find((c: any) => c.id === contaId);
    if (conta) {
      setFormData({
        ...formData,
        conta_id: contaId,
        tomador_cpf_cnpj: conta.cnpj || '',
        tomador_nome: conta.razao_social || conta.nome,
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
        step === 'conta'
          ? {
              conta_id: formData.conta_id,
              servico_descricao: formData.servico_descricao,
              valor_servicos: formData.valor_servicos,
              enviar_email: formData.enviar_email,
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
            };
      await apiClient.post('/nfse/emitir/', payload);
      onSuccess();
    } catch (err: any) {
      console.error('Erro ao emitir NFS-e:', err);
      setError(err.response?.data?.error || 'Erro ao emitir NFS-e');
      onRefreshList?.();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-[#16325c] rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
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

          {/* Step: Escolha */}
          {step === 'escolha' && (
            <StepEscolha onSelectConta={() => setStep('conta')} onSelectManual={() => setStep('manual')} onClose={onClose} />
          )}

          {/* Step: Conta */}
          {step === 'conta' && (
            <form onSubmit={handleSubmit} className="space-y-6">
              <ContaSelector contas={contas} loading={loadingContas} value={formData.conta_id} onChange={handleContaChange} />
              <ServicoFields
                servico_descricao={formData.servico_descricao}
                valor_servicos={formData.valor_servicos}
                enviar_email={formData.enviar_email}
                onChange={handleFieldChange}
              />
              <ModalFormButtons loading={loading} onBack={() => setStep('escolha')} onClose={onClose} />
            </form>
          )}

          {/* Step: Manual */}
          {step === 'manual' && (
            <form onSubmit={handleSubmit} className="space-y-6">
              <TomadorFields formData={formData} onChange={handleFieldChange} />
              <EnderecoFields formData={formData} onChange={handleFieldChange} />
              <ServicoFields
                servico_descricao={formData.servico_descricao}
                valor_servicos={formData.valor_servicos}
                enviar_email={formData.enviar_email}
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


/* ── Sub-components ── */

function StepEscolha({ onSelectConta, onSelectManual, onClose }: { onSelectConta: () => void; onSelectManual: () => void; onClose: () => void }) {
  return (
    <div className="space-y-4">
      <p className="text-gray-600 dark:text-gray-400 mb-6">Como deseja preencher os dados do cliente?</p>
      <button onClick={onSelectConta} className="w-full p-6 border-2 border-gray-200 dark:border-gray-600 rounded-lg hover:border-[#0176d3] hover:bg-[#e3f3ff] dark:hover:bg-[#0176d3]/10 transition-all text-left">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-[#0176d3]/10 rounded-lg"><FileText size={24} className="text-[#0176d3]" /></div>
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Selecionar Empresa Cadastrada</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">Escolha uma empresa já cadastrada no CRM.</p>
          </div>
        </div>
      </button>
      <button onClick={onSelectManual} className="w-full p-6 border-2 border-gray-200 dark:border-gray-600 rounded-lg hover:border-[#0176d3] hover:bg-[#e3f3ff] dark:hover:bg-[#0176d3]/10 transition-all text-left">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-[#0176d3]/10 rounded-lg"><Plus size={24} className="text-[#0176d3]" /></div>
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Preencher Manualmente</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">Digite os dados do cliente manualmente.</p>
          </div>
        </div>
      </button>
      <div className="flex justify-end pt-4">
        <button onClick={onClose} className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg">Cancelar</button>
      </div>
    </div>
  );
}

function ContaSelector({ contas, loading, value, onChange }: { contas: any[]; loading: boolean; value: number | null; onChange: (id: number) => void }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Empresa / Cliente *</label>
      {loading ? (
        <div className="text-center py-4"><div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-[#0176d3]" /></div>
      ) : (
        <select value={value || ''} onChange={(e) => onChange(Number(e.target.value))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white">
          <option value="">Selecione uma empresa...</option>
          {contas.map((c: any) => <option key={c.id} value={c.id}>{c.nome} {c.cnpj ? `- ${c.cnpj}` : ''}</option>)}
        </select>
      )}
    </div>
  );
}

const inputClass = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white";

function TomadorFields({ formData, onChange }: { formData: any; onChange: (f: string, v: string) => void }) {
  return (
    <div>
      <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Dados do Cliente</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">CPF/CNPJ *</label>
          <input type="text" value={formData.tomador_cpf_cnpj} onChange={(e) => onChange('tomador_cpf_cnpj', e.target.value)} required className={inputClass} placeholder="000.000.000-00" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Nome/Razão Social *</label>
          <input type="text" value={formData.tomador_nome} onChange={(e) => onChange('tomador_nome', e.target.value)} required className={inputClass} />
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Email</label>
          <input type="email" value={formData.tomador_email} onChange={(e) => onChange('tomador_email', e.target.value)} className={inputClass} />
        </div>
      </div>
    </div>
  );
}

function EnderecoFields({ formData, onChange }: { formData: any; onChange: (f: string, v: string) => void }) {
  return (
    <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
      <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Endereço</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">CEP</label>
          <input type="text" value={formData.tomador_cep} onChange={(e) => onChange('tomador_cep', e.target.value)} className={inputClass} placeholder="00000-000" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Logradouro</label>
          <input type="text" value={formData.tomador_logradouro} onChange={(e) => onChange('tomador_logradouro', e.target.value)} className={inputClass} />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Número</label>
          <input type="text" value={formData.tomador_numero} onChange={(e) => onChange('tomador_numero', e.target.value)} className={inputClass} />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Complemento</label>
          <input type="text" value={formData.tomador_complemento} onChange={(e) => onChange('tomador_complemento', e.target.value)} className={inputClass} />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Bairro</label>
          <input type="text" value={formData.tomador_bairro} onChange={(e) => onChange('tomador_bairro', e.target.value)} className={inputClass} />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Cidade *</label>
          <input type="text" value={formData.tomador_cidade} onChange={(e) => onChange('tomador_cidade', e.target.value)} required className={inputClass} />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">UF *</label>
          <input type="text" maxLength={2} value={formData.tomador_uf} onChange={(e) => onChange('tomador_uf', e.target.value.toUpperCase())} required className={inputClass} placeholder="SP" />
        </div>
      </div>
    </div>
  );
}
