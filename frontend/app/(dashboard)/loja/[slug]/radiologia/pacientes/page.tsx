'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useState } from 'react';
import { ArrowLeft, Plus, Users } from 'lucide-react';
import { useRadiologiaCrud } from '@/hooks/useRadiologiaCrud';
import type { PacienteRadiologia } from '@/lib/radiologia-types';

const empty = { nome: '', cpf: '', data_nascimento: '', sexo: '', telefone: '', email: '' };

export default function RadiologiaPacientesPage() {
  const slug = useParams().slug as string;
  const { items, loading, error, saving, save, remove } = useRadiologiaCrud<PacienteRadiologia>(
    '/radiologia/pacientes/',
  );
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<PacienteRadiologia | null>(null);
  const [form, setForm] = useState(empty);

  const openNew = () => {
    setEditing(null);
    setForm(empty);
    setOpen(true);
  };
  const openEdit = (p: PacienteRadiologia) => {
    setEditing(p);
    setForm({
      nome: p.nome || '',
      cpf: p.cpf || '',
      data_nascimento: p.data_nascimento || '',
      sexo: p.sexo || '',
      telefone: p.telefone || '',
      email: p.email || '',
    });
    setOpen(true);
  };
  const submit = async () => {
    const ok = await save(
      {
        nome: form.nome.trim(),
        cpf: form.cpf.trim(),
        data_nascimento: form.data_nascimento || null,
        sexo: form.sexo,
        telefone: form.telefone.trim(),
        email: form.email.trim(),
        is_active: true,
      },
      editing?.id,
    );
    if (ok) setOpen(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <header className="bg-gradient-to-r from-teal-700 to-teal-900 text-white shadow">
        <div className="flex w-full max-w-full flex-col gap-3 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <Users className="hidden h-6 w-6 sm:block" />
            <div>
              <h1 className="text-xl font-bold sm:text-2xl">Pacientes</h1>
              <p className="text-xs text-white/80">{items.length} cadastrados</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Link
              href={`/loja/${slug}/radiologia`}
              className="inline-flex items-center gap-1 rounded-md bg-white/15 px-3 py-2 text-sm hover:bg-white/25"
            >
              <ArrowLeft className="h-4 w-4" /> Voltar
            </Link>
            <button
              type="button"
              onClick={openNew}
              className="ml-auto inline-flex items-center gap-1 rounded-md bg-white px-3 py-2 text-sm font-semibold text-teal-800"
            >
              <Plus className="h-4 w-4" /> Novo
            </button>
          </div>
        </div>
      </header>

      <main className="w-full max-w-full px-4 py-6 sm:px-6 lg:px-8">
        {loading ? (
          <div className="flex justify-center py-16">
            <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-teal-700" />
          </div>
        ) : error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">{error}</div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs uppercase text-gray-500 dark:bg-gray-800">
                  <th className="px-4 py-3">Nome</th>
                  <th className="px-4 py-3">CPF</th>
                  <th className="px-4 py-3">Telefone</th>
                  <th className="px-4 py-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody>
                {items.map((p) => (
                  <tr key={p.id} className="border-b border-gray-100 dark:border-gray-800">
                    <td className="px-4 py-3 font-medium">{p.nome}</td>
                    <td className="px-4 py-3">{p.cpf || '—'}</td>
                    <td className="px-4 py-3">{p.telefone || '—'}</td>
                    <td className="px-4 py-3 text-right">
                      <button type="button" className="mr-2 text-teal-700" onClick={() => openEdit(p)}>
                        Editar
                      </button>
                      <button type="button" className="text-red-600" onClick={() => remove(p.id, p.nome)}>
                        Excluir
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl dark:bg-gray-900">
            <h2 className="mb-4 text-lg font-semibold">{editing ? 'Editar paciente' : 'Novo paciente'}</h2>
            <div className="space-y-3">
              <input
                className="w-full rounded-md border px-3 py-2"
                placeholder="Nome"
                value={form.nome}
                onChange={(e) => setForm({ ...form, nome: e.target.value })}
              />
              <input
                className="w-full rounded-md border px-3 py-2"
                placeholder="CPF"
                value={form.cpf}
                onChange={(e) => setForm({ ...form, cpf: e.target.value })}
              />
              <input
                type="date"
                className="w-full rounded-md border px-3 py-2"
                value={form.data_nascimento}
                onChange={(e) => setForm({ ...form, data_nascimento: e.target.value })}
              />
              <select
                className="w-full rounded-md border px-3 py-2"
                value={form.sexo}
                onChange={(e) => setForm({ ...form, sexo: e.target.value })}
              >
                <option value="">Sexo</option>
                <option value="M">Masculino</option>
                <option value="F">Feminino</option>
                <option value="O">Outro</option>
              </select>
              <input
                className="w-full rounded-md border px-3 py-2"
                placeholder="Telefone"
                value={form.telefone}
                onChange={(e) => setForm({ ...form, telefone: e.target.value })}
              />
              <input
                className="w-full rounded-md border px-3 py-2"
                placeholder="E-mail"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" className="rounded-md px-3 py-2 text-sm" onClick={() => setOpen(false)}>
                Cancelar
              </button>
              <button
                type="button"
                disabled={saving || !form.nome.trim()}
                className="rounded-md bg-teal-700 px-3 py-2 text-sm text-white disabled:opacity-50"
                onClick={() => void submit()}
              >
                Salvar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
