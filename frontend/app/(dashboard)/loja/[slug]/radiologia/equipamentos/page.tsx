'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useState } from 'react';
import { ArrowLeft, Monitor, Plus } from 'lucide-react';
import { useRadiologiaCrud } from '@/hooks/useRadiologiaCrud';
import type { Equipamento } from '@/lib/radiologia-types';

const empty = {
  nome: '',
  ae_title: '',
  modality: 'US',
  fabricante: '',
  modelo: '',
  suporte_mwl: true,
  suporte_dicom_storage: true,
  suporte_sr: false,
};

export default function RadiologiaEquipamentosPage() {
  const slug = useParams().slug as string;
  const { items, loading, error, saving, save, remove } = useRadiologiaCrud<Equipamento>(
    '/radiologia/equipamentos/',
  );
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Equipamento | null>(null);
  const [form, setForm] = useState(empty);

  const openNew = () => {
    setEditing(null);
    setForm(empty);
    setOpen(true);
  };
  const openEdit = (e: Equipamento) => {
    setEditing(e);
    setForm({
      nome: e.nome,
      ae_title: e.ae_title,
      modality: e.modality || 'US',
      fabricante: e.fabricante || '',
      modelo: e.modelo || '',
      suporte_mwl: e.suporte_mwl,
      suporte_dicom_storage: e.suporte_dicom_storage,
      suporte_sr: e.suporte_sr,
    });
    setOpen(true);
  };
  const submit = async () => {
    const ok = await save({ ...form, nome: form.nome.trim(), ae_title: form.ae_title.trim(), is_active: true }, editing?.id);
    if (ok) setOpen(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <header className="bg-gradient-to-r from-teal-700 to-teal-900 text-white shadow">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <Monitor className="hidden h-6 w-6 sm:block" />
            <div>
              <h1 className="text-xl font-bold sm:text-2xl">Equipamentos</h1>
              <p className="text-xs text-white/80">AE Title por aparelho</p>
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

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {loading ? (
          <div className="flex justify-center py-16"><div className="h-8 w-8 animate-spin rounded-full border-b-2 border-teal-700" /></div>
        ) : error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">{error}</div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs uppercase text-gray-500 dark:bg-gray-800">
                  <th className="px-4 py-3">Nome</th>
                  <th className="px-4 py-3">AE Title</th>
                  <th className="px-4 py-3">Mod.</th>
                  <th className="px-4 py-3">MWL / Storage / SR</th>
                  <th className="px-4 py-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody>
                {items.map((e) => (
                  <tr key={e.id} className="border-b border-gray-100 dark:border-gray-800">
                    <td className="px-4 py-3 font-medium">{e.nome}</td>
                    <td className="px-4 py-3 font-mono text-xs">{e.ae_title}</td>
                    <td className="px-4 py-3">{e.modality}</td>
                    <td className="px-4 py-3 text-xs">
                      {[e.suporte_mwl && 'MWL', e.suporte_dicom_storage && 'C-STORE', e.suporte_sr && 'SR']
                        .filter(Boolean)
                        .join(' · ') || '—'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button type="button" className="mr-2 text-teal-700" onClick={() => openEdit(e)}>Editar</button>
                      <button type="button" className="text-red-600" onClick={() => remove(e.id, e.nome)}>Excluir</button>
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
            <h2 className="mb-4 text-lg font-semibold">{editing ? 'Editar equipamento' : 'Novo equipamento'}</h2>
            <div className="space-y-3">
              <input className="w-full rounded-md border px-3 py-2" placeholder="Nome" value={form.nome} onChange={(ev) => setForm({ ...form, nome: ev.target.value })} />
              <input className="w-full rounded-md border px-3 py-2 font-mono" placeholder="AE Title (máx. 16)" maxLength={16} value={form.ae_title} onChange={(ev) => setForm({ ...form, ae_title: ev.target.value.toUpperCase() })} />
              <input className="w-full rounded-md border px-3 py-2" placeholder="Modalidade (US, CR, DX…)" value={form.modality} onChange={(ev) => setForm({ ...form, modality: ev.target.value.toUpperCase() })} />
              <input className="w-full rounded-md border px-3 py-2" placeholder="Fabricante" value={form.fabricante} onChange={(ev) => setForm({ ...form, fabricante: ev.target.value })} />
              <input className="w-full rounded-md border px-3 py-2" placeholder="Modelo" value={form.modelo} onChange={(ev) => setForm({ ...form, modelo: ev.target.value })} />
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.suporte_mwl} onChange={(ev) => setForm({ ...form, suporte_mwl: ev.target.checked })} /> Consulta MWL</label>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.suporte_dicom_storage} onChange={(ev) => setForm({ ...form, suporte_dicom_storage: ev.target.checked })} /> DICOM Storage</label>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.suporte_sr} onChange={(ev) => setForm({ ...form, suporte_sr: ev.target.checked })} /> SR de medidas</label>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" className="rounded-md px-3 py-2 text-sm" onClick={() => setOpen(false)}>Cancelar</button>
              <button type="button" disabled={saving || !form.nome.trim() || !form.ae_title.trim()} className="rounded-md bg-teal-700 px-3 py-2 text-sm text-white disabled:opacity-50" onClick={() => void submit()}>Salvar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
