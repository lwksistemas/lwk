'use client';

import { ChevronUp, ChevronDown } from 'lucide-react';

interface Props {
  colunas: string[];
  onSave: (colunas: string[]) => void;
  onError: (msg: string) => void;
}

const COLUNAS_DISPONIVEIS = [
  { key: 'nome', label: 'Nome' },
  { key: 'empresa', label: 'Empresa' },
  { key: 'email', label: 'E-mail' },
  { key: 'telefone', label: 'Telefone' },
  { key: 'origem', label: 'Origem' },
  { key: 'status', label: 'Status' },
  { key: 'valor_estimado', label: 'Valor Estimado' },
  { key: 'created_at', label: 'Data de Criação' },
];

export function ColunasSection({ colunas, onSave, onError }: Props) {
  const toggle = (key: string) => {
    if (colunas.includes(key)) {
      if (colunas.length <= 3) { onError('Mantenha pelo menos 3 colunas visíveis.'); return; }
      onSave(colunas.filter((c) => c !== key));
    } else {
      onSave([...colunas, key]);
    }
  };

  const mover = (key: string, dir: 'up' | 'down') => {
    const arr = [...colunas];
    const i = arr.indexOf(key);
    if (i === -1 || (dir === 'up' && i === 0) || (dir === 'down' && i === arr.length - 1)) return;
    const j = dir === 'up' ? i - 1 : i + 1;
    [arr[i], arr[j]] = [arr[j], arr[i]];
    onSave(arr);
  };

  return (
    <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-6">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Colunas Visíveis nos Leads</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Escolha quais informações aparecem na listagem. Mínimo 3.</p>
      </div>
      <div className="space-y-2">
        {COLUNAS_DISPONIVEIS.map((col) => {
          const isVisible = colunas.includes(col.key);
          const idx = colunas.indexOf(col.key);
          return (
            <div key={col.key} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-[#0d1f3c] rounded-lg border border-gray-200 dark:border-gray-700">
              {isVisible && (
                <div className="flex flex-col gap-1">
                  <button onClick={() => mover(col.key, 'up')} disabled={idx === 0} className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"><ChevronUp size={16} /></button>
                  <button onClick={() => mover(col.key, 'down')} disabled={idx === colunas.length - 1} className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"><ChevronDown size={16} /></button>
                </div>
              )}
              <div className="flex items-center gap-3 flex-1">
                <input type="checkbox" checked={isVisible} onChange={() => toggle(col.key)} className="w-4 h-4 text-[#0176d3] rounded" />
                <span className={`text-sm font-medium ${isVisible ? 'text-gray-900 dark:text-white' : 'text-gray-400'}`}>{col.label}</span>
                {isVisible && <span className="text-xs bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 px-2 py-1 rounded">Posição {idx + 1}</span>}
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <p className="text-sm text-blue-700 dark:text-blue-300"><strong>💡 Dica:</strong> As colunas aparecerão na ordem definida. Use as setas para reordenar.</p>
      </div>
    </div>
  );
}
