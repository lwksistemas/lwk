'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useState } from 'react';
import { ArrowLeft, Plus, Stethoscope } from 'lucide-react';
import { useRadiologiaCrud } from '@/hooks/useRadiologiaCrud';
import type { Procedimento } from '@/lib/radiologia-types';

const empty = { codigo: '', nome: '', modality: 'US', descricao: '', template_laudo: '' };

export default function RadiologiaProcedimentosPage() {
  const slug = useParams().slug as string;
  const { items, loading, error, saving, save, remove } = useRadiologiaCrud<Procedimento>(
    '/radiologia/procedimentos/',
  );
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Procedimento | null>(null);
  const [form, setForm] = useState(empty);

  const openNew = () => {
    setEditing(null);
    setForm(empty);
    setOpen(true);
  };
  const openEdit = (p: Procedimento) => {
    setEditing(p);
    setForm({
      codigo: p.codigo || '',
      nome: p.nome,
      modality: p.modality || 'US',
      descricao: p.descricao || '',
      template_laudo: p.template_laudo || '',
    });
    setOpen(true);
  };
  const submit = async () => {
    const ok = await save({ ...form, nome: form.nome.trim(), is_active: true }, editing?.id);
    if (ok) setOpen(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <header className="bg-gradient-to-r from-teal-700 to-teal-900 text-white shadow">
        <div className="flex w-full max-w-full flex-col gap-3 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <Stethoscope className="hidden h-6 w-6 sm:block" />
            <div>
              <h1 className="text-xl font-bold sm:text-2xl">Procedimentos</h1>
              <p className="text-xs text-white/80">Catálogo e template de laudo</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Link href={`/loja/${slug}/radiologia`} className="inline-flex items-center gap-1 rounded-md bg-white/15 px-3 py-2 text-sm hover:bg-white/25">
              <ArrowLeft className="h-4 w-4" /> Voltar
            </Link>
            <button type="button" onClick={openNew} className="ml-auto inline-flex items-center gap-1 rounded-md bg-white px-3 py-2 text-sm font-semibold text-teal-800">
              <Plus className="h-4 w-4" /> Novo
            </button>
          </div>
        </div>
      </header>

      <main className="w-full max-w-full px-4 py-6 sm:px-6 lg:px-8">
        {loading ? (
          <div className="flex justify-center py-16"><div className="h-8 w-8 animate-spin rounded-full border-b-2 border-teal-700" /></div>
        ) : error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">{error}</div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs uppercase text-gray-500 dark:bg-gray-800">
                  <th className="px-4 py-3">Código</th>
                  <th className="px-4 py-3">Nome</th>
                  <th className="px-4 py-3">Mod.</th>
                  <th className="px-4 py-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody>
                {items.map((p) => (
                  <tr key={p.id} className="border-b border-gray-100 dark:border-gray-800">
                    <td className="px-4 py-3">{p.codigo || '—'}</td>
                    <td className="px-4 py-3 font-medium">{p.nome}</td>
                    <td className="px-4 py-3">{p.modality}</td>
                    <td className="px-4 py-3 text-right">
                      <button type="button" className="mr-2 text-teal-700" onClick={() => openEdit(p)}>Editar</button>
                      <button type="button" className="text-red-600" onClick={() => remove(p.id, p.nome)}>Excluir</button>
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
          <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white p-5 shadow-xl dark:bg-gray-900">
            <h2 className="mb-4 text-lg font-semibold">{editing ? 'Editar procedimento' : 'Novo procedimento'}</h2>
            <div className="space-y-3">
              <input className="w-full rounded-md border px-3 py-2" placeholder="Código" value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value })} />
              <input className="w-full rounded-md border px-3 py-2" placeholder="Nome" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} />
              <input className="w-full rounded-md border px-3 py-2" placeholder="Modalidade" value={form.modality} onChange={(e) => setForm({ ...form, modality: e.target.value.toUpperCase() })} />
              <textarea className="w-full rounded-md border px-3 py-2" rows={2} placeholder="Descrição" value={form.descricao} onChange={(e) => setForm({ ...form, descricao: e.target.value })} />
              <textarea className="w-full rounded-md border px-3 py-2" rows={6} placeholder="Template de laudo" value={form.template_laudo} onChange={(e) => setForm({ ...form, template_laudo: e.target.value })} />
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" className="rounded-md px-3 py-2 text-sm" onClick={() => setOpen(false)}>Cancelar</button>
              <button type="button" disabled={saving || !form.nome.trim()} className="rounded-md bg-teal-700 px-3 py-2 text-sm text-white disabled:opacity-50" onClick={() => void submit()}>Salvar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
