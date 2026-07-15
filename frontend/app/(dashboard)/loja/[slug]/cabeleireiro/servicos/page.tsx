'use client';

import { useCallback, useEffect, useState } from 'react';
import { Edit2, Scissors, Trash2 } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { SalaoPageHeader } from '@/components/cabeleireiro/SalaoPageHeader';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';
import { CabeleireiroAPI, type SalaoServico } from '@/lib/cabeleireiro-api';
import { toUpperCase } from '@/lib/format-br';

const EMPTY = { nome: '', descricao: '', duracao_minutos: 40, preco: '', categoria: 'Geral' };

export default function SalaoServicosPage() {
  const [list, setList] = useState<SalaoServico[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<SalaoServico | null>(null);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setList(await CabeleireiroAPI.servicos.list());
    } catch {
      setList([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const openNew = () => {
    setEditing(null);
    setForm(EMPTY);
    setError('');
    setOpen(true);
  };

  const openEdit = (s: SalaoServico) => {
    setEditing(s);
    setForm({
      nome: s.nome,
      descricao: s.descricao || '',
      duracao_minutos: s.duracao_minutos,
      preco: String(s.preco ?? ''),
      categoria: s.categoria || 'Geral',
    });
    setError('');
    setOpen(true);
  };

  const save = async () => {
    if (!form.nome.trim()) {
      setError('Nome é obrigatório');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const payload = {
        nome: form.nome.trim(),
        descricao: form.descricao.trim(),
        duracao_minutos: Number(form.duracao_minutos) || 40,
        preco: form.preco || 0,
        categoria: form.categoria.trim() || 'Geral',
      };
      if (editing) await CabeleireiroAPI.servicos.update(editing.id, payload);
      else await CabeleireiroAPI.servicos.create(payload);
      setOpen(false);
      await load();
    } catch {
      setError('Erro ao salvar');
    } finally {
      setSaving(false);
    }
  };

  const remove = async (s: SalaoServico) => {
    if (!confirm(`Excluir serviço "${s.nome}"?`)) return;
    try {
      await CabeleireiroAPI.servicos.remove(s.id);
      await load();
    } catch {
      alert('Erro ao excluir');
    }
  };

  return (
    <div>
      <SalaoPageHeader
        title="Serviços"
        subtitle={`${list.length} serviço(s)`}
        icon={Scissors}
        onNew={openNew}
        newLabel="Novo serviço"
      />
      <div className="p-4 md:p-6">
        {loading ? (
          <p className="text-sm text-gray-500 text-center py-10">Carregando...</p>
        ) : list.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-10">Nenhum serviço cadastrado</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {list.map((s) => (
              <div key={s.id} className="bg-white rounded-xl border border-[#E8D5DC] p-4">
                <div className="flex justify-between gap-2">
                  <div>
                    <p className="font-semibold text-gray-900">{s.nome}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {s.duracao_minutos} min · {s.categoria || 'Geral'}
                    </p>
                    <p className="text-sm mt-2 font-medium" style={{ color: SALAO_PRIMARY }}>
                      R$ {Number(s.preco).toFixed(2)}
                    </p>
                  </div>
                  <div className="flex gap-1">
                    <button type="button" onClick={() => openEdit(s)} className="p-2 hover:bg-gray-100 rounded-md">
                      <Edit2 size={16} className="text-gray-500" />
                    </button>
                    <button type="button" onClick={() => void remove(s)} className="p-2 hover:bg-red-50 rounded-md">
                      <Trash2 size={16} className="text-red-500" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Modal isOpen={open} onClose={() => setOpen(false)} maxWidth="lg">
        <div className="p-6 space-y-4">
          <h2 className="text-lg font-semibold">{editing ? 'Editar serviço' : 'Novo serviço'}</h2>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label className="sm:col-span-2 text-sm space-y-1">
              <span>Nome *</span>
              <input
                className="w-full border rounded-lg px-3 py-2"
                value={form.nome}
                onChange={(e) => setForm((f) => ({ ...f, nome: toUpperCase(e.target.value) }))}
              />
            </label>
            <label className="text-sm space-y-1">
              <span>Duração (min)</span>
              <input
                type="number"
                className="w-full border rounded-lg px-3 py-2"
                value={form.duracao_minutos}
                onChange={(e) => setForm((f) => ({ ...f, duracao_minutos: Number(e.target.value) }))}
              />
            </label>
            <label className="text-sm space-y-1">
              <span>Preço</span>
              <input
                className="w-full border rounded-lg px-3 py-2"
                value={form.preco}
                onChange={(e) => setForm((f) => ({ ...f, preco: e.target.value }))}
              />
            </label>
            <label className="sm:col-span-2 text-sm space-y-1">
              <span>Categoria</span>
              <input
                className="w-full border rounded-lg px-3 py-2"
                value={form.categoria}
                onChange={(e) => setForm((f) => ({ ...f, categoria: toUpperCase(e.target.value) }))}
              />
            </label>
            <label className="sm:col-span-2 text-sm space-y-1">
              <span>Descrição</span>
              <textarea
                className="w-full border rounded-lg px-3 py-2 min-h-[80px]"
                value={form.descricao}
                onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))}
              />
            </label>
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setOpen(false)} className="px-4 py-2 border rounded-lg text-sm">
              Cancelar
            </button>
            <button
              type="button"
              disabled={saving}
              onClick={() => void save()}
              className="px-4 py-2 rounded-lg text-sm text-white disabled:opacity-60"
              style={{ backgroundColor: SALAO_PRIMARY }}
            >
              {saving ? 'Salvando...' : 'Salvar'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
