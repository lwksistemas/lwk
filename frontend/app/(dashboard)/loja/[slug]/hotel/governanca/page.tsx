'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import apiClient from '@/lib/api-client';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useHotelCrud } from '@/hooks/useHotelCrud';
import type { GovernancaTarefa, Quarto } from '@/lib/hotel-types';
import { GOVERNANCA_TIPO_LABEL, GOVERNANCA_STATUS_LABEL, GOVERNANCA_STATUS_BADGE, GOVERNANCA_TIPO_BADGE } from '@/lib/hotel-types';
import { Wrench, Plus, Edit2, Trash2, CheckCircle, ArrowLeft } from 'lucide-react';

export default function HotelGovernancaPage() {
  const params = useParams();
  const slug = params.slug as string;
  const { items, loading, error, saving, load, save, remove, postAction } = useHotelCrud<GovernancaTarefa>({ endpoint: '/hotel/governanca-tarefas/' });
  const [quartos, setQuartos] = useState<Pick<Quarto, 'id' | 'numero' | 'nome'>[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<GovernancaTarefa | null>(null);
  const [form, setForm] = useState({ quarto: '', tipo: 'limpeza' as GovernancaTarefa['tipo'], status: 'aberta' as GovernancaTarefa['status'], descricao: '', prioridade: 2 });
  const resetForm = () => setForm({ quarto: '', tipo: 'limpeza', status: 'aberta', descricao: '', prioridade: 2 });
  const loadQuartos = useCallback(async () => { try { const q = await apiClient.get<Quarto[] | { results?: Quarto[] }>('/hotel/quartos/'); setQuartos(Array.isArray(q.data) ? q.data : (q.data.results ?? [])); } catch { setQuartos([]); } }, []);
  useEffect(() => { loadQuartos(); load(); }, [loadQuartos, load]);
  const openNew = () => { setEditing(null); resetForm(); setModalOpen(true); };
  const openEdit = (t: GovernancaTarefa) => { setEditing(t); setForm({ quarto: String(t.quarto ?? ''), tipo: t.tipo, status: t.status, descricao: t.descricao || '', prioridade: Number(t.prioridade ?? 2) }); setModalOpen(true); };
  const submit = async () => { const ok = await save({ quarto: Number(form.quarto), tipo: form.tipo, status: form.status, descricao: (form.descricao || '').trim(), prioridade: Number(form.prioridade || 2) }, editing?.id); if (ok) { setModalOpen(false); setEditing(null); resetForm(); } };
  const prioridadeLabel = (p: number) => p === 1 ? 'Alta' : p === 2 ? 'Média' : 'Baixa';
  const prioridadeBadge = (p: number) => p === 1 ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300' : p === 2 ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300' : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300';

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <div className="bg-gradient-to-r from-sky-600 to-cyan-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/15 rounded-lg"><Wrench className="w-6 h-6" /></div>
              <div><h1 className="text-2xl font-bold">Governança</h1><p className="text-white/80 text-sm">Pendências por quarto ({items.length})</p></div>
            </div>
            <div className="flex items-center gap-2">
              <Link href={`/loja/${slug}/hotel`} className="px-3 py-2 bg-white/15 hover:bg-white/25 rounded-md transition-colors text-sm flex items-center gap-1"><ArrowLeft className="w-4 h-4" /> Voltar</Link>
              <button onClick={openNew} className="px-4 py-2 bg-white text-sky-700 font-semibold rounded-md hover:bg-sky-50 transition-colors text-sm flex items-center gap-1 shadow"><Plus className="w-4 h-4" /> Nova tarefa</button>
            </div>
          </div>
        </div>
      </div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {loading ? (<div className="flex items-center justify-center py-20"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600" /></div>
        ) : error && !modalOpen ? (<div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">{error}</div>
        ) : items.length === 0 ? (<div className="text-center py-20"><Wrench className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" /><p className="text-lg font-medium text-gray-600 dark:text-gray-400">Nenhuma tarefa cadastrada</p></div>
        ) : (
          <>
            {/* Mobile: Cards */}
            <div className="sm:hidden space-y-3">
              {items.map((t) => (
                <div key={t.id} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 shadow-sm">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <p className="font-semibold text-gray-900 dark:text-white">Quarto {t.quarto_numero || String(t.quarto)}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{t.descricao || '—'}</p>
                    </div>
                    <span className={`shrink-0 px-2.5 py-0.5 rounded-full text-xs font-medium ${prioridadeBadge(t.prioridade)}`}>{prioridadeLabel(t.prioridade)}</span>
                  </div>
                  <div className="flex items-center gap-2 flex-wrap mb-3">
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${GOVERNANCA_TIPO_BADGE[t.tipo] || 'bg-gray-100 text-gray-600'}`}>{GOVERNANCA_TIPO_LABEL[t.tipo]}</span>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${GOVERNANCA_STATUS_BADGE[t.status] || 'bg-gray-100 text-gray-600'}`}>{GOVERNANCA_STATUS_LABEL[t.status]}</span>
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <button onClick={() => openEdit(t)} className="px-3 py-1.5 rounded-md bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-xs font-medium flex items-center gap-1 active:scale-95"><Edit2 className="w-3.5 h-3.5" /> Editar</button>
                    {t.status !== 'concluida' && <button onClick={() => postAction(t.id, 'concluir')} className="px-3 py-1.5 rounded-md bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300 text-xs font-medium flex items-center gap-1 active:scale-95"><CheckCircle className="w-3.5 h-3.5" /> Concluir</button>}
                    <button onClick={() => remove(t.id, `tarefa #${t.id}`)} className="px-3 py-1.5 rounded-md bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-400 text-xs font-medium flex items-center gap-1 active:scale-95 ml-auto"><Trash2 className="w-3.5 h-3.5" /> Excluir</button>
                  </div>
                </div>
              ))}
            </div>
            {/* Desktop: Table */}
            <div className="hidden sm:block bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-800/80 border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">#</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Quarto</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Tipo</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Status</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Prioridade</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Descrição</th>
                  <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Ações</th>
                </tr></thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {items.map((t) => (
                    <tr key={t.id} className="hover:bg-sky-50/50 dark:hover:bg-gray-800/50 transition-colors">
                      <td className="py-3 px-4 font-mono text-gray-500">#{t.id}</td>
                      <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">{t.quarto_numero || String(t.quarto)}</td>
                      <td className="py-3 px-4"><span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${GOVERNANCA_TIPO_BADGE[t.tipo] || 'bg-gray-100 text-gray-600'}`}>{GOVERNANCA_TIPO_LABEL[t.tipo]}</span></td>
                      <td className="py-3 px-4"><span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${GOVERNANCA_STATUS_BADGE[t.status] || 'bg-gray-100 text-gray-600'}`}>{GOVERNANCA_STATUS_LABEL[t.status]}</span></td>
                      <td className="py-3 px-4"><span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${prioridadeBadge(t.prioridade)}`}>{prioridadeLabel(t.prioridade)}</span></td>
                      <td className="py-3 px-4 text-gray-600 dark:text-gray-400 max-w-[200px] truncate">{t.descricao || '—'}</td>
                      <td className="py-3 px-4"><div className="flex items-center justify-end gap-1.5">
                        <button onClick={() => openEdit(t)} className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 hover:text-sky-600 transition-colors" title="Editar"><Edit2 className="w-4 h-4" /></button>
                        {t.status !== 'concluida' && <button onClick={() => postAction(t.id, 'concluir')} className="px-2.5 py-1 rounded-md bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-300 dark:hover:bg-green-900/50 text-xs font-medium transition-colors flex items-center gap-1" title="Concluir"><CheckCircle className="w-3.5 h-3.5" /> Concluir</button>}
                        <button onClick={() => remove(t.id, `tarefa #${t.id}`)} className="p-1.5 rounded-md hover:bg-red-100 dark:hover:bg-red-900/30 text-gray-400 hover:text-red-600 transition-colors" title="Excluir"><Trash2 className="w-4 h-4" /></button>
                      </div></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          </>
        )}
      </div>
      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} maxWidth="3xl">
        <div className="p-6 space-y-4">
          <div className="flex items-start justify-between gap-4"><h2 className="text-xl font-bold text-gray-900 dark:text-white">{editing ? 'Editar tarefa' : 'Nova tarefa'}</h2><button onClick={() => setModalOpen(false)} className="px-3 py-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 text-sm">Fechar</button></div>
          {error && <div className="text-sm text-red-600 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg border border-red-200 dark:border-red-800">{error}</div>}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Quarto *</Label>
              <select className="w-full h-10 px-3 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100" value={form.quarto} onChange={(e) => setForm((f) => ({ ...f, quarto: e.target.value }))}>
                <option value="">Selecione</option>{quartos.map((q) => <option key={q.id} value={q.id}>{q.numero} {q.nome ? `- ${q.nome}` : ''}</option>)}
              </select>
              <Link href={`/loja/${slug}/hotel/quartos`} className="text-xs text-sky-700 hover:underline">+ cadastrar quarto</Link>
            </div>
            <div className="space-y-2"><Label>Tipo</Label><select className="w-full h-10 px-3 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100" value={form.tipo} onChange={(e) => setForm((f) => ({ ...f, tipo: e.target.value as GovernancaTarefa['tipo'] }))}><option value="limpeza">Limpeza</option><option value="manutencao">Manutenção</option><option value="enxoval">Enxoval</option><option value="outros">Outros</option></select></div>
            <div className="space-y-2"><Label>Status</Label><select className="w-full h-10 px-3 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100" value={form.status} onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as GovernancaTarefa['status'] }))}><option value="aberta">Aberta</option><option value="em_andamento">Em andamento</option><option value="concluida">Concluída</option></select></div>
            <div className="space-y-2"><Label>Prioridade (1 alta - 3 baixa)</Label><Input type="number" min={1} max={3} value={form.prioridade} onChange={(e) => setForm((f) => ({ ...f, prioridade: Number(e.target.value || 2) }))} /></div>
            <div className="space-y-2 md:col-span-2"><Label>Descrição</Label><Input value={form.descricao} onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))} placeholder="Ex.: Limpeza pós check-out" /></div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setModalOpen(false)} className="min-h-[40px]" disabled={saving}>Cancelar</Button>
            <Button onClick={submit} className="min-h-[40px]" disabled={saving || !form.quarto}>{saving ? 'Salvando...' : 'Salvar'}</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
