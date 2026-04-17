'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useHotelCrud } from '@/hooks/useHotelCrud';
import type { Quarto } from '@/lib/hotel-types';
import { QUARTO_STATUS_LABEL, QUARTO_STATUS_BADGE } from '@/lib/hotel-types';
import { BedDouble, Plus, Edit2, Trash2, ArrowLeft } from 'lucide-react';

export default function HotelQuartosPage() {
  const params = useParams();
  const slug = params.slug as string;

  const { items, loading, error, saving, load, save, remove } =
    useHotelCrud<Quarto>({ endpoint: '/hotel/quartos/' });

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Quarto | null>(null);
  const [form, setForm] = useState({ numero: '', nome: '', tipo: '', capacidade: 2, status: 'disponivel' as Quarto['status'], observacoes: '' });

  const resetForm = () => setForm({ numero: '', nome: '', tipo: '', capacidade: 2, status: 'disponivel', observacoes: '' });

  useEffect(() => { load(); }, [load]);

  const openNew = () => { setEditing(null); resetForm(); setModalOpen(true); };
  const openEdit = (q: Quarto) => {
    setEditing(q);
    setForm({ numero: q.numero || '', nome: q.nome || '', tipo: q.tipo || '', capacidade: Number(q.capacidade || 2), status: q.status || 'disponivel', observacoes: q.observacoes || '' });
    setModalOpen(true);
  };

  const submit = async () => {
    const ok = await save(
      { numero: form.numero.trim(), nome: form.nome.trim(), tipo: form.tipo.trim(), capacidade: Number(form.capacidade || 0), status: form.status, observacoes: form.observacoes.trim() },
      editing?.id,
    );
    if (ok) { setModalOpen(false); setEditing(null); resetForm(); }
  };

  const summary = useMemo(() => {
    const byStatus = items.reduce((acc, it) => { acc[it.status] = (acc[it.status] || 0) + 1; return acc; }, {} as Record<string, number>);
    return { total: items.length, byStatus };
  }, [items]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <div className="bg-gradient-to-r from-sky-600 to-cyan-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/15 rounded-lg"><BedDouble className="w-6 h-6" /></div>
              <div>
                <h1 className="text-2xl font-bold">Quartos / Apartamentos</h1>
                <p className="text-white/80 text-sm">
                  Total: {summary.total} • Disponível: {summary.byStatus.disponivel || 0} • Ocupado: {summary.byStatus.ocupado || 0} • Limpeza: {summary.byStatus.limpeza || 0}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Link href={`/loja/${slug}/hotel`} className="px-3 py-2 bg-white/15 hover:bg-white/25 rounded-md transition-colors text-sm flex items-center gap-1"><ArrowLeft className="w-4 h-4" /> Voltar</Link>
              <button onClick={openNew} className="px-4 py-2 bg-white text-sky-700 font-semibold rounded-md hover:bg-sky-50 transition-colors text-sm flex items-center gap-1 shadow"><Plus className="w-4 h-4" /> Novo quarto</button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
        {loading ? (
          <div className="flex items-center justify-center py-20"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600" /></div>
        ) : error && !modalOpen ? (
          <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">{error}</div>
        ) : items.length === 0 ? (
          <div className="text-center py-20">
            <BedDouble className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
            <p className="text-lg font-medium text-gray-600 dark:text-gray-400">Nenhum quarto cadastrado</p>
          </div>
        ) : (
          <>
            {/* Mobile: Cards */}
            <div className="sm:hidden space-y-3">
              {items.map((q) => (
                <div key={q.id} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 shadow-sm">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <p className="font-semibold text-gray-900 dark:text-white">Quarto {q.numero}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{q.nome || q.tipo || '—'} • Cap: {q.capacidade}</p>
                    </div>
                    <span className={`shrink-0 px-2.5 py-0.5 rounded-full text-xs font-medium ${QUARTO_STATUS_BADGE[q.status] || 'bg-gray-100 text-gray-600'}`}>{QUARTO_STATUS_LABEL[q.status]}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-3">
                    <button onClick={() => openEdit(q)} className="px-3 py-1.5 rounded-md bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-xs font-medium flex items-center gap-1 active:scale-95"><Edit2 className="w-3.5 h-3.5" /> Editar</button>
                    <button onClick={() => remove(q.id, q.numero)} className="px-3 py-1.5 rounded-md bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-400 text-xs font-medium flex items-center gap-1 active:scale-95 ml-auto"><Trash2 className="w-3.5 h-3.5" /> Excluir</button>
                  </div>
                </div>
              ))}
            </div>
            {/* Desktop: Table */}
            <div className="hidden sm:block bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-800/80 border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Número</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Nome</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Tipo</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Capacidade</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Status</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {items.map((q) => (
                    <tr key={q.id} className="hover:bg-sky-50/50 dark:hover:bg-gray-800/50 transition-colors">
                      <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">{q.numero}</td>
                      <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{q.nome || '—'}</td>
                      <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{q.tipo || '—'}</td>
                      <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{q.capacidade}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${QUARTO_STATUS_BADGE[q.status] || 'bg-gray-100 text-gray-600'}`}>
                          {QUARTO_STATUS_LABEL[q.status]}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center justify-end gap-1.5">
                          <button onClick={() => openEdit(q)} className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 hover:text-sky-600 transition-colors" title="Editar"><Edit2 className="w-4 h-4" /></button>
                          <button onClick={() => remove(q.id, q.numero)} className="p-1.5 rounded-md hover:bg-red-100 dark:hover:bg-red-900/30 text-gray-400 hover:text-red-600 transition-colors" title="Excluir"><Trash2 className="w-4 h-4" /></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          </>
        )}
      </div>

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} maxWidth="2xl">
        <div className="p-6 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">{editing ? 'Editar quarto' : 'Novo quarto'}</h2>
            <button onClick={() => setModalOpen(false)} className="px-3 py-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 text-sm">Fechar</button>
          </div>
          {error && <div className="text-sm text-red-600 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg border border-red-200 dark:border-red-800">{error}</div>}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2"><Label>Número *</Label><Input value={form.numero} onChange={(e) => setForm((f) => ({ ...f, numero: e.target.value }))} /></div>
            <div className="space-y-2"><Label>Nome</Label><Input value={form.nome} onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))} placeholder="Ex.: Suíte 203" /></div>
            <div className="space-y-2"><Label>Tipo</Label><Input value={form.tipo} onChange={(e) => setForm((f) => ({ ...f, tipo: e.target.value }))} placeholder="Ex.: Standard" /></div>
            <div className="space-y-2"><Label>Capacidade</Label><Input type="number" value={form.capacidade} onChange={(e) => setForm((f) => ({ ...f, capacidade: Number(e.target.value || 0) }))} min={1} /></div>
            <div className="space-y-2">
              <Label>Status</Label>
              <select className="w-full h-10 px-3 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100" value={form.status} onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as Quarto['status'] }))}>
                <option value="disponivel">Disponível</option><option value="ocupado">Ocupado</option><option value="limpeza">Limpeza</option><option value="manutencao">Manutenção</option>
              </select>
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label>Observações</Label>
              <textarea className="w-full min-h-[96px] px-3 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100" value={form.observacoes} onChange={(e) => setForm((f) => ({ ...f, observacoes: e.target.value }))} />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setModalOpen(false)} className="min-h-[40px]" disabled={saving}>Cancelar</Button>
            <Button onClick={submit} className="min-h-[40px]" disabled={saving || !form.numero.trim()}>{saving ? 'Salvando...' : 'Salvar'}</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
