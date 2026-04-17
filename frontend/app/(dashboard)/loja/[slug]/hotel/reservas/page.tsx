'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import apiClient from '@/lib/api-client';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useHotelCrud } from '@/hooks/useHotelCrud';
import type { Reserva, Hospede, Quarto, Tarifa } from '@/lib/hotel-types';
import { RESERVA_STATUS_LABEL, RESERVA_STATUS_BADGE, formatDateBR } from '@/lib/hotel-types';
import { CalendarDays, Plus, Edit2, LogIn, LogOut, Trash2, ArrowLeft } from 'lucide-react';

type HospedeOption = Pick<Hospede, 'id' | 'nome'>;
type QuartoOption = Pick<Quarto, 'id' | 'numero' | 'nome'>;
type TarifaOption = Pick<Tarifa, 'id' | 'nome' | 'valor_diaria'>;

export default function HotelReservasPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const slug = params.slug as string;

  const { items, loading, error, saving, setError, load, save, remove, postAction } =
    useHotelCrud<Reserva>({ endpoint: '/hotel/reservas/' });

  const [hospedes, setHospedes] = useState<HospedeOption[]>([]);
  const [quartos, setQuartos] = useState<QuartoOption[]>([]);
  const [tarifas, setTarifas] = useState<TarifaOption[]>([]);

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Reserva | null>(null);
  const [form, setForm] = useState({
    hospede: '', quarto: '', tarifa: '', data_checkin: '', data_checkout: '',
    adultos: 2, criancas: 0, canal: 'Direto', status: 'pendente' as Reserva['status'],
    valor_diaria: '', valor_total: '', observacoes: '',
  });

  const resetForm = () => setForm({
    hospede: '', quarto: '', tarifa: '', data_checkin: '', data_checkout: '',
    adultos: 2, criancas: 0, canal: 'Direto', status: 'pendente',
    valor_diaria: '', valor_total: '', observacoes: '',
  });

  const loadBase = useCallback(async () => {
    try {
      const [h, q, t] = await Promise.all([
        apiClient.get<HospedeOption[] | { results?: HospedeOption[] }>('/hotel/hospedes/'),
        apiClient.get<QuartoOption[] | { results?: QuartoOption[] }>('/hotel/quartos/'),
        apiClient.get<TarifaOption[] | { results?: TarifaOption[] }>('/hotel/tarifas/'),
      ]);
      setHospedes(Array.isArray(h.data) ? h.data : (h.data.results ?? []));
      setQuartos(Array.isArray(q.data) ? q.data : (q.data.results ?? []));
      setTarifas(Array.isArray(t.data) ? t.data : (t.data.results ?? []));
    } catch { /* best-effort */ }
  }, []);

  useEffect(() => { loadBase(); load(); }, [loadBase, load]);
  useEffect(() => { if (searchParams.get('novo') === '1') openNew(); }, []);

  const openNew = () => { setEditing(null); resetForm(); setModalOpen(true); };
  const openEdit = (r: Reserva) => {
    setEditing(r);
    setForm({
      hospede: String(r.hospede ?? ''), quarto: String(r.quarto ?? ''),
      tarifa: r.tarifa ? String(r.tarifa) : '', data_checkin: r.data_checkin || '',
      data_checkout: r.data_checkout || '', adultos: Number(r.adultos ?? 2),
      criancas: Number(r.criancas ?? 0), canal: r.canal || '',
      status: r.status || 'pendente', valor_diaria: String(r.valor_diaria ?? ''),
      valor_total: String(r.valor_total ?? ''), observacoes: r.observacoes || '',
    });
    setModalOpen(true);
  };

  const submit = async () => {
    const ok = await save({
      hospede: Number(form.hospede), quarto: Number(form.quarto),
      tarifa: form.tarifa ? Number(form.tarifa) : null,
      data_checkin: form.data_checkin, data_checkout: form.data_checkout,
      adultos: Number(form.adultos || 0), criancas: Number(form.criancas || 0),
      canal: (form.canal || '').trim(), status: form.status,
      valor_diaria: Number(String(form.valor_diaria || '').replace(',', '.')) || 0,
      valor_total: Number(String(form.valor_total || '').replace(',', '.')) || 0,
      observacoes: (form.observacoes || '').trim(),
    }, editing?.id);
    if (ok) { setModalOpen(false); setEditing(null); resetForm(); }
  };

  const calcNoites = (checkin: string, checkout: string): number => {
    if (!checkin || !checkout) return 0;
    const d1 = new Date(checkin + 'T00:00:00');
    const d2 = new Date(checkout + 'T00:00:00');
    const diff = Math.round((d2.getTime() - d1.getTime()) / (1000 * 60 * 60 * 24));
    return diff > 0 ? diff : 0;
  };

  const recalcTotal = (diaria: string, checkin: string, checkout: string): string => {
    const noites = calcNoites(checkin, checkout);
    const valorDiaria = Number(String(diaria).replace(',', '.')) || 0;
    if (noites > 0 && valorDiaria > 0) return (noites * valorDiaria).toFixed(2);
    return '';
  };

  const handleCheckinChange = (v: string) => {
    setForm((f) => { const u = { ...f, data_checkin: v }; u.valor_total = recalcTotal(u.valor_diaria, v, u.data_checkout); return u; });
  };
  const handleCheckoutChange = (v: string) => {
    setForm((f) => { const u = { ...f, data_checkout: v }; u.valor_total = recalcTotal(u.valor_diaria, u.data_checkin, v); return u; });
  };
  const handleDiariaChange = (v: string) => {
    setForm((f) => { const u = { ...f, valor_diaria: v }; u.valor_total = recalcTotal(v, u.data_checkin, u.data_checkout); return u; });
  };
  const autofillTarifa = (tarifaId: string) => {
    const t = tarifas.find((x) => String(x.id) === String(tarifaId));
    const diaria = t ? (Number(String(t.valor_diaria).replace(',', '.')) || 0).toFixed(2) : '';
    setForm((f) => { const u = { ...f, tarifa: tarifaId, valor_diaria: diaria }; u.valor_total = recalcTotal(diaria, u.data_checkin, u.data_checkout); return u; });
  };

  const noites = calcNoites(form.data_checkin, form.data_checkout);

  const resumo = useMemo(() => ({
    total: items.length,
    checkin: items.filter((i) => i.status === 'checkin').length,
    confirmadas: items.filter((i) => i.status === 'confirmada').length,
  }), [items]);

  const selectClass = 'w-full h-10 px-3 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100';

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      {/* Header */}
      <div className="bg-gradient-to-r from-sky-600 to-cyan-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/15 rounded-lg">
                <CalendarDays className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Reservas</h1>
                <p className="text-white/80 text-sm">
                  Total: {resumo.total} • Confirmadas: {resumo.confirmadas} • Hospedagem: {resumo.checkin}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Link href={`/loja/${slug}/hotel`} className="px-3 py-2 bg-white/15 hover:bg-white/25 rounded-md transition-colors text-sm flex items-center gap-1">
                <ArrowLeft className="w-4 h-4" /> Voltar
              </Link>
              <button onClick={openNew} className="px-4 py-2 bg-white text-sky-700 font-semibold rounded-md hover:bg-sky-50 transition-colors text-sm flex items-center gap-1 shadow">
                <Plus className="w-4 h-4" /> Nova reserva
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600" />
          </div>
        ) : error && !modalOpen ? (
          <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">{error}</div>
        ) : items.length === 0 ? (
          <div className="text-center py-20">
            <CalendarDays className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
            <p className="text-lg font-medium text-gray-600 dark:text-gray-400">Nenhuma reserva cadastrada</p>
            <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">Clique em "Nova reserva" para começar</p>
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-800/80 border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">#</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Hóspede</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Quarto</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Período</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Status</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Canal</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {items.map((r) => (
                    <tr key={r.id} className="hover:bg-sky-50/50 dark:hover:bg-gray-800/50 transition-colors">
                      <td className="py-3 px-4 font-mono text-gray-500">#{r.id}</td>
                      <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">{r.hospede_nome || String(r.hospede)}</td>
                      <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{r.quarto_numero || String(r.quarto)}</td>
                      <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{formatDateBR(r.data_checkin)} → {formatDateBR(r.data_checkout)}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${RESERVA_STATUS_BADGE[r.status] || 'bg-gray-100 text-gray-600'}`}>
                          {RESERVA_STATUS_LABEL[r.status]}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{r.canal || '—'}</td>
                      <td className="py-3 px-4">
                        <div className="flex items-center justify-end gap-1.5">
                          <button onClick={() => openEdit(r)} className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 hover:text-sky-600 transition-colors" title="Editar">
                            <Edit2 className="w-4 h-4" />
                          </button>
                          {r.status !== 'checkin' && r.status !== 'checkout' && r.status !== 'cancelada' && (
                            <button onClick={() => postAction(r.id, 'checkin')} className="px-2.5 py-1 rounded-md bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-300 dark:hover:bg-green-900/50 text-xs font-medium transition-colors flex items-center gap-1" title="Check-in">
                              <LogIn className="w-3.5 h-3.5" /> Check-in
                            </button>
                          )}
                          {r.status === 'checkin' && (
                            <button onClick={() => postAction(r.id, 'checkout')} className="px-2.5 py-1 rounded-md bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:hover:bg-blue-900/50 text-xs font-medium transition-colors flex items-center gap-1" title="Check-out">
                              <LogOut className="w-3.5 h-3.5" /> Check-out
                            </button>
                          )}
                          <button onClick={() => remove(r.id, `reserva #${r.id}`)} className="p-1.5 rounded-md hover:bg-red-100 dark:hover:bg-red-900/30 text-gray-400 hover:text-red-600 transition-colors" title="Excluir">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Modal */}
      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} maxWidth="4xl">
        <div className="p-6 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">{editing ? 'Editar reserva' : 'Nova reserva'}</h2>
            <button onClick={() => setModalOpen(false)} className="px-3 py-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 text-sm">Fechar</button>
          </div>
          {error && <div className="text-sm text-red-600 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg border border-red-200 dark:border-red-800">{error}</div>}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Hóspede *</Label>
              <select className={selectClass} value={form.hospede} onChange={(e) => setForm((f) => ({ ...f, hospede: e.target.value }))}>
                <option value="">Selecione</option>
                {hospedes.map((h) => <option key={h.id} value={h.id}>{h.nome}</option>)}
              </select>
              <Link href={`/loja/${slug}/hotel/hospedes`} className="text-xs text-sky-700 hover:underline">+ cadastrar hóspede</Link>
            </div>
            <div className="space-y-2">
              <Label>Quarto *</Label>
              <select className={selectClass} value={form.quarto} onChange={(e) => setForm((f) => ({ ...f, quarto: e.target.value }))}>
                <option value="">Selecione</option>
                {quartos.map((q) => <option key={q.id} value={q.id}>{q.numero} {q.nome ? `- ${q.nome}` : ''}</option>)}
              </select>
              <Link href={`/loja/${slug}/hotel/quartos`} className="text-xs text-sky-700 hover:underline">+ cadastrar quarto</Link>
            </div>
            <div className="space-y-2">
              <Label>Tarifa</Label>
              <select className={selectClass} value={form.tarifa} onChange={(e) => autofillTarifa(e.target.value)}>
                <option value="">(sem tarifa)</option>
                {tarifas.map((t) => <option key={t.id} value={t.id}>{t.nome}</option>)}
              </select>
            </div>
            <div className="space-y-2"><Label>Check-in *</Label><Input type="date" value={form.data_checkin} onChange={(e) => handleCheckinChange(e.target.value)} /></div>
            <div className="space-y-2"><Label>Check-out *</Label><Input type="date" value={form.data_checkout} onChange={(e) => handleCheckoutChange(e.target.value)} /></div>
            <div className="space-y-2">
              <Label>Status</Label>
              <select className={selectClass} value={form.status} onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as Reserva['status'] }))}>
                <option value="pendente">Pendente</option><option value="confirmada">Confirmada</option><option value="checkin">Check-in</option>
                <option value="checkout">Check-out</option><option value="cancelada">Cancelada</option><option value="no_show">No-show</option>
              </select>
            </div>
            <div className="space-y-2"><Label>Adultos</Label><Input type="number" min={0} value={form.adultos} onChange={(e) => setForm((f) => ({ ...f, adultos: Number(e.target.value || 0) }))} /></div>
            <div className="space-y-2"><Label>Crianças</Label><Input type="number" min={0} value={form.criancas} onChange={(e) => setForm((f) => ({ ...f, criancas: Number(e.target.value || 0) }))} /></div>
            <div className="space-y-2"><Label>Canal</Label><Input value={form.canal} onChange={(e) => setForm((f) => ({ ...f, canal: e.target.value }))} placeholder="Direto / Booking / Expedia" /></div>
            <div className="space-y-2">
              <Label>Valor diária (R$)</Label>
              <Input value={form.valor_diaria} onChange={(e) => handleDiariaChange(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Valor total (R$){noites > 0 ? ` — ${noites} noite${noites > 1 ? 's' : ''}` : ''}</Label>
              <Input value={form.valor_total} onChange={(e) => setForm((f) => ({ ...f, valor_total: e.target.value }))} />
              {noites > 0 && form.valor_diaria && (
                <p className="text-xs text-green-600 dark:text-green-400">
                  {noites} noite{noites > 1 ? 's' : ''} × R$ {Number(String(form.valor_diaria).replace(',', '.')).toFixed(2)} = R$ {(noites * Number(String(form.valor_diaria).replace(',', '.'))).toFixed(2)}
                </p>
              )}
            </div>
            <div className="space-y-2 lg:col-span-3">
              <Label>Observações</Label>
              <textarea className="w-full min-h-[96px] px-3 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100" value={form.observacoes} onChange={(e) => setForm((f) => ({ ...f, observacoes: e.target.value }))} />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setModalOpen(false)} className="min-h-[40px]" disabled={saving}>Cancelar</Button>
            <Button onClick={submit} className="min-h-[40px]" disabled={saving || !form.hospede || !form.quarto || !form.data_checkin || !form.data_checkout}>{saving ? 'Salvando...' : 'Salvar'}</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
