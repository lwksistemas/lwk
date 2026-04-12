'use client';

import { X } from 'lucide-react';

interface Conta {
  id: number;
  nome: string;
}

interface ContatoFormData {
  nome: string;
  email: string;
  telefone: string;
  cargo: string;
  conta: string;
  observacoes: string;
}

interface ContatoFormModalProps {
  title: string;
  formData: ContatoFormData;
  contas: Conta[];
  submitting: boolean;
  onChange: (data: ContatoFormData) => void;
  onSubmit: (e: React.FormEvent) => void;
  onClose: () => void;
}

const inputClass = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent";

export function ContatoFormModal({ title, formData, contas, submitting, onChange, onSubmit, onClose }: ContatoFormModalProps) {
  const set = (field: keyof ContatoFormData, value: string) => onChange({ ...formData, [field]: value });

  return (
    <ModalWrapper title={title} onClose={onClose}>
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Nome <span className="text-red-500">*</span>
            </label>
            <input type="text" value={formData.nome} onChange={(e) => set('nome', e.target.value)} className={inputClass} required />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Conta <span className="text-red-500">*</span>
            </label>
            <select value={formData.conta} onChange={(e) => set('conta', e.target.value)} className={inputClass} required>
              <option value="">Selecione uma conta</option>
              {contas.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cargo</label>
            <input type="text" value={formData.cargo} onChange={(e) => set('cargo', e.target.value)} className={inputClass} placeholder="Ex: Gerente de Compras" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefone</label>
            <input type="tel" value={formData.telefone} onChange={(e) => set('telefone', e.target.value)} className={inputClass} />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
            <input type="email" value={formData.email} onChange={(e) => set('email', e.target.value)} className={inputClass} />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Observações</label>
            <textarea value={formData.observacoes} onChange={(e) => set('observacoes', e.target.value)} rows={3} className={inputClass} />
          </div>
        </div>
        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={onClose} disabled={submitting} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            Cancelar
          </button>
          <button type="submit" disabled={submitting} className="px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded transition-colors disabled:opacity-50">
            {submitting ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </form>
    </ModalWrapper>
  );
}

/* Shared modal wrapper */
export function ModalWrapper({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{title}</h2>
            <button type="button" onClick={onClose} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400">
              <X size={20} />
            </button>
          </div>
          <div className="p-6">{children}</div>
        </div>
      </div>
    </>
  );
}
