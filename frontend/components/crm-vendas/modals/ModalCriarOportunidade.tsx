'use client';

import { X } from 'lucide-react';
import type { Lead } from '@/components/crm-vendas/LeadsTable';
import { ETAPAS_OPORTUNIDADE } from '@/constants/crm';

interface FormOportunidade {
  titulo: string;
  valor: string;
  etapa: string;
}

interface ModalCriarOportunidadeProps {
  lead: Lead;
  form: FormOportunidade;
  formErro: string | null;
  enviando: boolean;
  onFormChange: (updater: (f: FormOportunidade) => FormOportunidade) => void;
  onSubmit: (e: React.FormEvent) => void;
  onClose: () => void;
}

export default function ModalCriarOportunidade({
  lead,
  form,
  formErro,
  enviando,
  onFormChange,
  onSubmit,
  onClose,
}: ModalCriarOportunidadeProps) {
  return (
    <div
      className="fixed inset-0 z-[80] flex items-center justify-center p-4 bg-black/50"
      onClick={() => !enviando && onClose()}
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Criar oportunidade (venda)
          </h2>
          <button
            type="button"
            onClick={() => !enviando && onClose()}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>
        <p className="px-4 pt-2 text-sm text-gray-500 dark:text-gray-400">
          Lead: <strong className="text-gray-800 dark:text-white">{lead.nome}</strong>
        </p>
        <form onSubmit={onSubmit} className="p-4 space-y-4">
          {formErro && (
            <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg">
              {formErro}
            </p>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Título *</label>
            <input
              type="text"
              value={form.titulo}
              onChange={(e) => onFormChange((f) => ({ ...f, titulo: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Ex: Venda produto X"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Valor (R$)</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={form.valor}
              onChange={(e) => onFormChange((f) => ({ ...f, valor: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Etapa inicial</label>
            <select
              value={form.etapa}
              onChange={(e) => onFormChange((f) => ({ ...f, etapa: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              {ETAPAS_OPORTUNIDADE.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={() => !enviando && onClose()}
              className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={enviando}
              className="flex-1 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-medium"
            >
              {enviando ? 'Criando...' : 'Criar e ir ao pipeline'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
