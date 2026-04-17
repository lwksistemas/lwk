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
import { Users, Plus, Edit2, Trash2, ArrowLeft } from 'lucide-react';

export default function HotelHospedesPage() {
  const params = useParams();
  const slug = params.slug as string;
  const { items, loading, error, saving, setError, load, save, remove } = useHotelCrud<Hospede>({ endpoint: '/hotel/hospedes/' });
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Hospede | null>(null);
  const [form, setForm] = useState({ nome: '', documento: '', telefone: '', email: '', observacoes: '' });
  const resetForm = () => setForm({ nome: '', documento: '', telefone: '', email: '', observacoes: '' });
  useEffect(() => { load(); }, [load]);
  const openNew = () => { setEditing(null); resetForm(); setModalOpen(true); };
  const openEdit = (h: Hospede) => { setEditing(h); setForm({ nome: h.nome || '', documento: h.documento || '', telefone: h.telefone || '', email: h.email || '', observacoes: h.observacoes || '' }); setModalOpen(true); };
  const submit = async () => { const ok = await save({ nome: form.nome.trim(), documento: form.documento.trim(), telefone: form.telefone.trim(), email: form.email.trim(), observacoes: form.observacoes.trim() }, editing?.id); if (ok) { setModalOpen(false); setEditing(null); resetForm(); } };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <div className="bg-gradient-to-r from-sky-600 to-cyan-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/15 rounded-lg"><Users className="w-6 h-6" /></div>
              <div><h1 className="text-2xl font-bold">Hóspedes</h1><p className="text-white/80 text-sm">Cadastro de hóspedes ({items.length})</p></div>
            </div>
            <div className="flex items-center gap-2">
              <Link href={`/loja/${slug}/hotel`} className="px-3 py-2 bg-white/15 hover:bg-white/25 rounded-md transition-colors text-sm flex items-center gap-1"><ArrowLeft className="w-4 h-4" /> Voltar</Link>
              <button onClick={openNew} className="px-4 py-2 bg-white text-sky-700 font-semibold rounded-md hover:bg-sky-50 transition-colors text-sm flex items-center gap-1 shadow"><Plus className="w-4 h-4" /> Novo hóspede</button>
            </div>
          </div>
        </div>
      </div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {loading ? (<div className="flex items-center justify-center py-20"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600" /></div>
        ) : error && !modalOpen ? (<div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">{error}</div>
        ) : items.length === 0 ? (<div className="text-center py-20"><Users className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" /><p className="text-lg font-medium text-gray-600 dark:text-gray-400">Nenhum hóspede cadastrado</p></div>
        ) : (
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-800/80 border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Nome</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Documento</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Telefone</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Email</th>
                  <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Ações</th>
                </tr></thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {items.map((h) => (
                    <tr key={h.id} className="hover:bg-sky-50/50 dark:hover:bg-gray-800/50 transition-colors">
                      <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">{h.nome}</td>
                      <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{h.documento || '—'}</td>
                      <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{h.telefone || '—'}</td>
                      <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{h.email || '—'}</td>
                      <td className="py-3 px-4"><div className="flex items-center justify-end gap-1.5">
                        <button onClick={() => openEdit(h)} className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 hover:text-sky-600 transition-colors" title="Editar"><Edit2 className="w-4 h-4" /></button>
                        <button onClick={() => remove(h.id, h.nome)} className="p-1.5 rounded-md hover:bg-red-100 dark:hover:bg-red-900/30 text-gray-400 hover:text-red-600 transition-colors" title="Excluir"><Trash2 className="w-4 h-4" /></button>
                      </div></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} maxWidth="2xl">
        <div className="p-6 space-y-4">
          <div className="flex items-start justify-between gap-4"><h2 className="text-xl font-bold text-gray-900 dark:text-white">{editing ? 'Editar hóspede' : 'Novo hóspede'}</h2><button onClick={() => setModalOpen(false)} className="px-3 py-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 text-sm">Fechar</button></div>
          {error && <div className="text-sm text-red-600 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg border border-red-200 dark:border-red-800">{error}</div>}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2 md:col-span-2"><Label>Nome *</Label><Input value={form.nome} onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))} /></div>
            <div className="space-y-2"><Label>Documento</Label><Input value={form.documento} onChange={(e) => setForm((f) => ({ ...f, documento: e.target.value }))} /></div>
            <div className="space-y-2"><Label>Telefone</Label><Input value={form.telefone} onChange={(e) => setForm((f) => ({ ...f, telefone: e.target.value }))} /></div>
            <div className="space-y-2 md:col-span-2"><Label>Email</Label><Input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} /></div>
            <div className="space-y-2 md:col-span-2"><Label>Observações</Label><textarea className="w-full min-h-[96px] px-3 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100" value={form.observacoes} onChange={(e) => setForm((f) => ({ ...f, observacoes: e.target.value }))} /></div>
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
