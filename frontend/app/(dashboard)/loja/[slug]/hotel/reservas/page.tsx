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
import { RESERVA_STATUS_LABEL } from '@/lib/hotel-types';

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

  useEffect(() => {
    if (searchParams.get('novo') === '1') openNew();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

  const autofillTarifa = (tarifaId: string) => {
    setForm((f) => ({ ...f, tarifa: tarifaId }));
    const t = tarifas.find((x) => String(x.id) === String(tarifaId));
    if (!t) return;
    const diaria = Number(String(t.valor_diaria).replace(',', '.')) || 0;
    setForm((f) => ({ ...f, valor_diaria: String(diaria.toFixed(2)) }));
  };

  const resumo = useMemo(() => ({
    total: items.length,
    checkin: items.filter((i) => i.status === 'checkin').length,
    confirmadas: items.filter((i) => i.status === 'confirmada').length,
  }), [items]);

  const selectClass = 'w-full h-10 px-3 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100';

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Reservas</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Total: {resumo.total} • Confirmadas: {resumo.confirmadas} • Em hospedagem: {resumo.checkin}
          </p>
          <Link href={`/loja/${slug}/hotel`} className="text-sm text-sky-700 hover:underline">← Voltar</Link>
        </div>
        <Button onClick={openNew} className="min-h-[40px]">+ Nova reserva</Button>
      </div>

      {loading ? (
        <div className="text-sm text-gray-600 dark:text-gray-400">Carregando...</div>
      ) : error && !modalOpen ? (
        <div className="text-sm text-red-600">{error}</div>
      ) : (
        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg overflow-x-auto">
          <table className="min-w-[1100px] w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-200">
              <tr>
                <th className="text-left p-3">#</th><th className="text-left p-3">Hóspede</th><th className="text-left p-3">Quarto</th>
                <th className="text-left p-3">Período</th><th className="text-left p-3">Status</th><th className="text-left p-3">Canal</th><th className="text-left p-3">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
              {items.map((r) => (
                <tr key={r.id} className="text-gray-900 dark:text-gray-100">
                  <td className="p-3 font-medium">#{r.id}</td>
                  <td className="p-3">{r.hospede_nome || String(r.hospede)}</td>
                  <td className="p-3">{r.quarto_numero || String(r.quarto)}</td>
                  <td className="p-3">{r.data_checkin} → {r.data_checkout}</td>
                  <td className="p-3">{RESERVA_STATUS_LABEL[r.status]}</td>
                  <td className="p-3">{r.canal || '—'}</td>
                  <td className="p-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Button variant="outline" onClick={() => openEdit(r)} className="min-h-[36px]">Editar</Button>
                      {r.status !== 'checkin' && r.status !== 'checkout' && r.status !== 'cancelada' && (
                        <Button onClick={() => postAction(r.id, 'checkin')} className="min-h-[36px]">Check-in</Button>
                      )}
                      {r.status === 'checkin' && (
                        <Button onClick={() => postAction(r.id, 'checkout')} className="min-h-[36px]">Check-out</Button>
                      )}
                      <Button variant="destructive" onClick={() => remove(r.id, `reserva #${r.id}`)} className="min-h-[36px]">Excluir</Button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && <tr><td className="p-3 text-gray-600 dark:text-gray-400" colSpan={7}>Nenhuma reserva cadastrada.</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} maxWidth="4xl">
        <div className="p-6 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <h2 className="text-xl font-bold">{editing ? 'Editar reserva' : 'Nova reserva'}</h2>
            <button onClick={() => setModalOpen(false)} className="px-3 py-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 text-sm">Fechar</button>
          </div>
          {error && <div className="text-sm text-red-600">{error}</div>}
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
            <div className="space-y-2"><Label>Check-in *</Label><Input type="date" value={form.data_checkin} onChange={(e) => setForm((f) => ({ ...f, data_checkin: e.target.value }))} /></div>
            <div className="space-y-2"><Label>Check-out *</Label><Input type="date" value={form.data_checkout} onChange={(e) => setForm((f) => ({ ...f, data_checkout: e.target.value }))} /></div>
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
            <div className="space-y-2"><Label>Valor diária (R$)</Label><Input value={form.valor_diaria} onChange={(e) => setForm((f) => ({ ...f, valor_diaria: e.target.value }))} /></div>
            <div className="space-y-2"><Label>Valor total (R$)</Label><Input value={form.valor_total} onChange={(e) => setForm((f) => ({ ...f, valor_total: e.target.value }))} /></div>
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
