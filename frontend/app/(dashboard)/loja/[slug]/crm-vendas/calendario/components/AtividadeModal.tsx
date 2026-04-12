'use client';

import type { Atividade } from '../page';

const TIPO_LABEL: Record<string, string> = {
  call: 'Ligação', meeting: 'Reunião', email: 'Email', task: 'Tarefa',
};

interface FormData {
  titulo: string;
  tipo: Atividade['tipo'];
  data: string;
  duracao_minutos: number;
  observacoes: string;
}

interface Props {
  atividade: Atividade | null;
  form: FormData;
  saving: boolean;
  error: string | null;
  onChange: (form: FormData) => void;
  onSave: () => void;
  onClose: () => void;
  onToggleConcluido?: () => void;
  onDelete?: () => void;
}

const inputClass = 'w-full px-3 py-2.5 min-h-[44px] rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white touch-manipulation';

export function AtividadeModal({ atividade, form, saving, error, onChange, onSave, onClose, onToggleConcluido, onDelete }: Props) {
  const set = (field: keyof FormData, value: string | number) => onChange({ ...form, [field]: value });

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} aria-hidden="true" />
      <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 overflow-y-auto">
        <div className="bg-white dark:bg-gray-800 rounded-t-xl sm:rounded-xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {atividade ? 'Editar atividade' : 'Nova atividade'}
            </h2>
          </div>
          <div className="p-6 space-y-4">
            {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Título</label>
              <input type="text" value={form.titulo} onChange={(e) => set('titulo', e.target.value)} className={inputClass} placeholder="Ex: Ligar para cliente" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label>
              <select value={form.tipo} onChange={(e) => set('tipo', e.target.value)} className={inputClass}>
                {Object.entries(TIPO_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data e hora</label>
              <input type="datetime-local" value={form.data} onChange={(e) => set('data', e.target.value)} className={inputClass} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Duração (minutos)</label>
              <select value={form.duracao_minutos} onChange={(e) => set('duracao_minutos', Number(e.target.value))} className={inputClass}>
                {[15, 30, 45, 60, 90, 120, 180, 240].map((m) => <option key={m} value={m}>{m < 60 ? `${m} min` : `${m / 60}h${m % 60 ? ` ${m % 60}min` : ''}`}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Observações</label>
              <textarea value={form.observacoes} onChange={(e) => set('observacoes', e.target.value)} rows={2} className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" placeholder="Opcional" />
            </div>
            {atividade && (
              <div className="flex gap-2 flex-wrap">
                {onToggleConcluido && (
                  <button type="button" onClick={onToggleConcluido} disabled={saving} className="px-3 py-2 rounded-lg text-sm font-medium bg-green-600 hover:bg-green-700 text-white disabled:opacity-50">
                    {atividade.concluido ? 'Desmarcar concluída' : 'Marcar concluída'}
                  </button>
                )}
                {onDelete && (
                  <button type="button" onClick={onDelete} disabled={saving} className="px-3 py-2 rounded-lg text-sm font-medium bg-red-600 hover:bg-red-700 text-white disabled:opacity-50">
                    Excluir
                  </button>
                )}
              </div>
            )}
          </div>
          <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-2">
            <button type="button" onClick={onClose} className="px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 touch-manipulation min-h-[44px]">Cancelar</button>
            <button type="button" onClick={onSave} disabled={saving} className="px-4 py-2.5 rounded-lg bg-[#0176d3] hover:bg-[#0159a8] text-white font-medium disabled:opacity-50 touch-manipulation min-h-[44px]">{saving ? 'Salvando...' : 'Salvar'}</button>
          </div>
        </div>
      </div>
    </>
  );
}
