'use client';

import { useState } from 'react';
import { Edit2, ChevronUp, ChevronDown } from 'lucide-react';

interface Etapa { key: string; label: string; ativo: boolean; ordem: number; }

interface Props {
  etapas: Etapa[];
  onSave: (etapas: Etapa[]) => void;
  onError: (msg: string) => void;
}

export function EtapasSection({ etapas, onSave, onError }: Props) {
  const [editando, setEditando] = useState<string | null>(null);
  const sorted = [...etapas].sort((a, b) => a.ordem - b.ordem);

  const toggle = (key: string) => {
    if (['closed_won', 'closed_lost'].includes(key)) { onError('Etapas de fechamento não podem ser desabilitadas.'); return; }
    onSave(etapas.map((e) => e.key === key ? { ...e, ativo: !e.ativo } : e));
  };

  const editar = (key: string, label: string) => { onSave(etapas.map((e) => e.key === key ? { ...e, label } : e)); setEditando(null); };

  const mover = (key: string, dir: 'up' | 'down') => {
    const arr = [...sorted];
    const i = arr.findIndex((e) => e.key === key);
    if (i === -1 || (dir === 'up' && i === 0) || (dir === 'down' && i === arr.length - 1)) return;
    const j = dir === 'up' ? i - 1 : i + 1;
    [arr[i], arr[j]] = [arr[j], arr[i]];
    onSave(arr.map((e, idx) => ({ ...e, ordem: idx + 1 })));
  };

  return (
    <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-6">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Etapas do Pipeline</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Personalize as etapas do seu pipeline de vendas.</p>
      </div>
      <div className="space-y-2">
        {sorted.map((etapa, index) => {
          const isFechamento = ['closed_won', 'closed_lost'].includes(etapa.key);
          return (
            <div key={etapa.key} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-[#0d1f3c] rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="flex flex-col gap-1">
                <button onClick={() => mover(etapa.key, 'up')} disabled={index === 0} className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-30" title="Mover para cima"><ChevronUp size={16} /></button>
                <button onClick={() => mover(etapa.key, 'down')} disabled={index === sorted.length - 1} className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-30" title="Mover para baixo"><ChevronDown size={16} /></button>
              </div>
              <div className="flex items-center gap-3 flex-1">
                <input type="checkbox" checked={etapa.ativo} onChange={() => toggle(etapa.key)} disabled={isFechamento} className="w-4 h-4 text-[#0176d3] rounded disabled:opacity-50" />
                {editando === etapa.key ? (
                  <input type="text" defaultValue={etapa.label} onBlur={(e) => editar(etapa.key, e.target.value)} onKeyDown={(e) => e.key === 'Enter' && editar(etapa.key, e.currentTarget.value)} autoFocus className="px-2 py-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
                ) : (
                  <span className={`text-sm font-medium ${etapa.ativo ? 'text-gray-900 dark:text-white' : 'text-gray-400 line-through'}`}>{etapa.label}</span>
                )}
                <span className="text-xs text-gray-500">({etapa.key})</span>
                {isFechamento && <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-1 rounded">Obrigatória</span>}
              </div>
              <button onClick={() => setEditando(etapa.key)} className="p-2 text-gray-600 hover:text-[#0176d3] dark:text-gray-400" title="Editar"><Edit2 size={16} /></button>
            </div>
          );
        })}
      </div>
      <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <p className="text-sm text-blue-700 dark:text-blue-300"><strong>💡 Dica:</strong> Etapas desabilitadas não aparecem no pipeline, mas oportunidades existentes continuam visíveis.</p>
      </div>
    </div>
  );
}
