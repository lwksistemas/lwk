'use client';

import { useState } from 'react';
import { Plus, Trash2, Edit2, Save, X } from 'lucide-react';

interface Origem { key: string; label: string; ativo: boolean; }

interface Props {
  origens: Origem[];
  saving: boolean;
  onSave: (origens: Origem[]) => void;
  onError: (msg: string) => void;
}

export function OrigensSection({ origens, saving, onSave, onError }: Props) {
  const [editandoOrigem, setEditandoOrigem] = useState<string | null>(null);
  const [novaOrigem, setNovaOrigem] = useState({ key: '', label: '' });
  const [mostrarNova, setMostrarNova] = useState(false);

  const adicionar = () => {
    if (!novaOrigem.label) { onError('Preencha o nome da origem.'); return; }
    let key = (novaOrigem.key.trim() || novaOrigem.label)
      .toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9\s_-]/g, '').replace(/\s+/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '');
    if (!key) { onError('Chave inválida.'); return; }
    if (origens.some((o) => o.key === key)) { onError('Origem já existe.'); return; }
    onSave([...origens, { key, label: novaOrigem.label, ativo: true }]);
    setNovaOrigem({ key: '', label: '' }); setMostrarNova(false);
  };

  const remover = (key: string) => {
    if (!confirm('Remover esta origem?')) return;
    onSave(origens.filter((o) => o.key !== key));
  };

  const toggle = (key: string) => onSave(origens.map((o) => o.key === key ? { ...o, ativo: !o.ativo } : o));
  const editar = (key: string, label: string) => { onSave(origens.map((o) => o.key === key ? { ...o, label } : o)); setEditandoOrigem(null); };

  return (
    <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Origens de Leads</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Gerencie as origens disponíveis ao cadastrar novos leads</p>
        </div>
        <button onClick={() => setMostrarNova(true)} className="px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded-lg text-sm font-medium flex items-center gap-2">
          <Plus size={16} /> Nova Origem
        </button>
      </div>

      {mostrarNova && (
        <div className="mb-4 p-4 bg-gray-50 dark:bg-[#0d1f3c] rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome (exibição) *</label>
              <input type="text" value={novaOrigem.label} onChange={(e) => setNovaOrigem({ ...novaOrigem, label: e.target.value })} placeholder="ex: Fatesa (escola)" className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Chave (opcional)</label>
              <input type="text" value={novaOrigem.key} onChange={(e) => setNovaOrigem({ ...novaOrigem, key: e.target.value })} placeholder="ex: fatesa_escola" className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={adicionar} disabled={saving} className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium flex items-center gap-2 disabled:opacity-50"><Save size={16} /> Salvar</button>
            <button onClick={() => { setMostrarNova(false); setNovaOrigem({ key: '', label: '' }); }} className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg text-sm font-medium flex items-center gap-2"><X size={16} /> Cancelar</button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {origens.map((o) => (
          <div key={o.key} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-[#0d1f3c] rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3 flex-1">
              <input type="checkbox" checked={o.ativo} onChange={() => toggle(o.key)} className="w-4 h-4 text-[#0176d3] rounded" />
              {editandoOrigem === o.key ? (
                <input type="text" defaultValue={o.label} onBlur={(e) => editar(o.key, e.target.value)} onKeyDown={(e) => e.key === 'Enter' && editar(o.key, e.currentTarget.value)} autoFocus className="px-2 py-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
              ) : (
                <span className={`text-sm font-medium ${o.ativo ? 'text-gray-900 dark:text-white' : 'text-gray-400 dark:text-gray-500 line-through'}`}>{o.label}</span>
              )}
              <span className="text-xs text-gray-500 dark:text-gray-400">({o.key})</span>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => setEditandoOrigem(o.key)} className="p-2 text-gray-600 hover:text-[#0176d3] dark:text-gray-400" title="Editar"><Edit2 size={16} /></button>
              <button onClick={() => remover(o.key)} className="p-2 text-gray-600 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400" title="Remover"><Trash2 size={16} /></button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
