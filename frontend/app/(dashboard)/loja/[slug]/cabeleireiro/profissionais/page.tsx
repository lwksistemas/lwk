'use client';

import { useCallback, useEffect, useState } from 'react';
import { Clock, Edit2, Trash2, UserCog } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { ModalHorariosSalao } from '@/components/cabeleireiro/ModalHorariosSalao';
import { SalaoPageHeader } from '@/components/cabeleireiro/SalaoPageHeader';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';
import { CabeleireiroAPI, type SalaoProfissional } from '@/lib/cabeleireiro-api';
import { formatTelefone, telefoneInternacionalBr, toUpperCase } from '@/lib/format-br';

const EMPTY = {
  nome: '',
  telefone: '',
  email: '',
  especialidade: 'Cabeleireiro(a)',
  cor_agenda: SALAO_PRIMARY,
};

export default function SalaoProfissionaisPage() {
  const [list, setList] = useState<SalaoProfissional[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<SalaoProfissional | null>(null);
  const [horariosProf, setHorariosProf] = useState<SalaoProfissional | null>(null);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setList(await CabeleireiroAPI.profissionais.list());
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

  const openEdit = (p: SalaoProfissional) => {
    setEditing(p);
    setForm({
      nome: p.nome,
      telefone: formatTelefone(p.telefone || ''),
      email: p.email || '',
      especialidade: p.especialidade || 'Cabeleireiro(a)',
      cor_agenda: p.cor_agenda || SALAO_PRIMARY,
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
        telefone: form.telefone ? telefoneInternacionalBr(form.telefone) : '',
        email: form.email.trim(),
        especialidade: form.especialidade.trim(),
        cor_agenda: form.cor_agenda,
      };
      if (editing) {
        await CabeleireiroAPI.profissionais.update(editing.id, payload);
        setOpen(false);
        await load();
      } else {
        const created = await CabeleireiroAPI.profissionais.create(payload);
        setOpen(false);
        await load();
        // Abre dias/horários logo após criar (já vem com seg–sex padrão no backend)
        setHorariosProf(created);
      }
    } catch {
      setError('Erro ao salvar');
    } finally {
      setSaving(false);
    }
  };

  const remove = async (p: SalaoProfissional) => {
    if (!confirm(`Excluir profissional "${p.nome}"?`)) return;
    try {
      await CabeleireiroAPI.profissionais.remove(p.id);
      await load();
    } catch {
      alert('Erro ao excluir');
    }
  };

  return (
    <div>
      <SalaoPageHeader
        title="Profissionais"
        subtitle="Equipe, cores na agenda e dias de trabalho"
        icon={UserCog}
        onNew={openNew}
        newLabel="Novo profissional"
      />
      <div className="p-4 md:p-6">
        {loading ? (
          <p className="text-sm text-gray-500 text-center py-10">Carregando...</p>
        ) : list.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-10">Nenhum profissional cadastrado</p>
        ) : (
          <div className="bg-white rounded-xl border border-[#E8D5DC] overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[#F7F0F3] text-left text-xs uppercase text-gray-500">
                  <th className="px-4 py-3">Nome</th>
                  <th className="px-4 py-3 hidden sm:table-cell">Especialidade</th>
                  <th className="px-4 py-3 hidden md:table-cell">Telefone</th>
                  <th className="px-4 py-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {list.map((p) => (
                  <tr key={p.id}>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span
                          className="w-3 h-3 rounded-full shrink-0"
                          style={{ backgroundColor: p.cor_agenda || SALAO_PRIMARY }}
                        />
                        <span className="font-medium">{p.nome}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-600 hidden sm:table-cell">{p.especialidade || '—'}</td>
                    <td className="px-4 py-3 text-gray-600 hidden md:table-cell">{p.telefone || '—'}</td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-1">
                        <button
                          type="button"
                          title="Dias e horários de trabalho"
                          onClick={() => setHorariosProf(p)}
                          className="p-2 hover:bg-amber-50 rounded-md text-amber-700"
                        >
                          <Clock size={16} />
                        </button>
                        <button type="button" onClick={() => openEdit(p)} className="p-2 hover:bg-gray-100 rounded-md">
                          <Edit2 size={16} />
                        </button>
                        <button type="button" onClick={() => void remove(p)} className="p-2 hover:bg-red-50 rounded-md">
                          <Trash2 size={16} className="text-red-500" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Modal isOpen={open} onClose={() => setOpen(false)} maxWidth="lg">
        <div className="p-6 space-y-4">
          <h2 className="text-lg font-semibold">{editing ? 'Editar profissional' : 'Novo profissional'}</h2>
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
              <span>Telefone</span>
              <input
                className="w-full border rounded-lg px-3 py-2"
                value={form.telefone}
                onChange={(e) => setForm((f) => ({ ...f, telefone: formatTelefone(e.target.value) }))}
              />
            </label>
            <label className="text-sm space-y-1">
              <span>E-mail</span>
              <input
                type="email"
                className="w-full border rounded-lg px-3 py-2"
                value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
              />
            </label>
            <label className="text-sm space-y-1">
              <span>Especialidade</span>
              <input
                className="w-full border rounded-lg px-3 py-2"
                value={form.especialidade}
                onChange={(e) => setForm((f) => ({ ...f, especialidade: toUpperCase(e.target.value) }))}
              />
            </label>
            <label className="text-sm space-y-1">
              <span>Cor na agenda</span>
              <input
                type="color"
                className="w-full h-10 border rounded-lg px-1"
                value={form.cor_agenda}
                onChange={(e) => setForm((f) => ({ ...f, cor_agenda: e.target.value }))}
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

      {horariosProf && (
        <ModalHorariosSalao
          profissionalId={horariosProf.id}
          profissionalNome={horariosProf.nome}
          onClose={() => setHorariosProf(null)}
        />
      )}
    </div>
  );
}
