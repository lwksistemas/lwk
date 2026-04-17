'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useHotelCrud } from '@/hooks/useHotelCrud';
import type { Hospede } from '@/lib/hotel-types';

export default function HotelHospedesPage() {
  const params = useParams();
  const slug = params.slug as string;

  const { items, loading, error, saving, setError, load, save, remove } =
    useHotelCrud<Hospede>({ endpoint: '/hotel/hospedes/' });

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Hospede | null>(null);
  const [form, setForm] = useState({ nome: '', documento: '', telefone: '', email: '', observacoes: '' });

  const resetForm = () => setForm({ nome: '', documento: '', telefone: '', email: '', observacoes: '' });

  useEffect(() => { load(); }, [load]);

  const openNew = () => { setEditing(null); resetForm(); setModalOpen(true); };
  const openEdit = (h: Hospede) => {
    setEditing(h);
    setForm({ nome: h.nome || '', documento: h.documento || '', telefone: h.telefone || '', email: h.email || '', observacoes: h.observacoes || '' });
    setModalOpen(true);
  };

  const submit = async () => {
    const ok = await save(
      { nome: form.nome.trim(), documento: form.documento.trim(), telefone: form.telefone.trim(), email: form.email.trim(), observacoes: form.observacoes.trim() },
      editing?.id,
    );
    if (ok) { setModalOpen(false); setEditing(null); resetForm(); }
  };

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Hóspedes</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400">Cadastro de hóspedes (documento, telefone, email).</p>
          <Link href={`/loja/${slug}/hotel`} className="text-sm text-sky-700 hover:underline">← Voltar</Link>
        </div>
        <Button onClick={openNew} className="min-h-[40px]">+ Novo hóspede</Button>
      </div>

      {loading ? (
        <div className="text-sm text-gray-600 dark:text-gray-400">Carregando...</div>
      ) : error && !modalOpen ? (
        <div className="text-sm text-red-600">{error}</div>
      ) : (
        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg overflow-x-auto">
          <table className="min-w-[900px] w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-200">
              <tr>
                <th className="text-left p-3">Nome</th>
                <th className="text-left p-3">Documento</th>
                <th className="text-left p-3">Telefone</th>
                <th className="text-left p-3">Email</th>
                <th className="text-left p-3">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
              {items.map((h) => (
                <tr key={h.id} className="text-gray-900 dark:text-gray-100">
                  <td className="p-3 font-medium">{h.nome}</td>
                  <td className="p-3">{h.documento || '—'}</td>
                  <td className="p-3">{h.telefone || '—'}</td>
                  <td className="p-3">{h.email || '—'}</td>
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <Button variant="outline" onClick={() => openEdit(h)} className="min-h-[36px]">Editar</Button>
                      <Button variant="destructive" onClick={() => remove(h.id, h.nome)} className="min-h-[36px]">Excluir</Button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr><td className="p-3 text-gray-600 dark:text-gray-400" colSpan={5}>Nenhum hóspede cadastrado.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} maxWidth="2xl">
        <div className="p-6 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <h2 className="text-xl font-bold">{editing ? 'Editar hóspede' : 'Novo hóspede'}</h2>
            <button onClick={() => setModalOpen(false)} className="px-3 py-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 text-sm">Fechar</button>
          </div>
          {error && <div className="text-sm text-red-600">{error}</div>}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2 md:col-span-2"><Label>Nome *</Label><Input value={form.nome} onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))} /></div>
            <div className="space-y-2"><Label>Documento</Label><Input value={form.documento} onChange={(e) => setForm((f) => ({ ...f, documento: e.target.value }))} /></div>
            <div className="space-y-2"><Label>Telefone</Label><Input value={form.telefone} onChange={(e) => setForm((f) => ({ ...f, telefone: e.target.value }))} /></div>
            <div className="space-y-2 md:col-span-2"><Label>Email</Label><Input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} /></div>
            <div className="space-y-2 md:col-span-2">
              <Label>Observações</Label>
              <textarea className="w-full min-h-[96px] px-3 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100" value={form.observacoes} onChange={(e) => setForm((f) => ({ ...f, observacoes: e.target.value }))} />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setModalOpen(false)} className="min-h-[40px]" disabled={saving}>Cancelar</Button>
            <Button onClick={submit} className="min-h-[40px]" disabled={saving || !form.nome.trim()}>{saving ? 'Salvando...' : 'Salvar'}</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
