'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { CalendarDays, Check } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { SalaoPageHeader } from '@/components/cabeleireiro/SalaoPageHeader';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';
import {
  CabeleireiroAPI,
  type SalaoAgendamento,
  type SalaoCliente,
  type SalaoProfissional,
  type SalaoServico,
} from '@/lib/cabeleireiro-api';

function todayISO() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export default function SalaoAgendaPage() {
  const [data, setData] = useState(todayISO());
  const [list, setList] = useState<SalaoAgendamento[]>([]);
  const [clientes, setClientes] = useState<SalaoCliente[]>([]);
  const [profissionais, setProfissionais] = useState<SalaoProfissional[]>([]);
  const [servicos, setServicos] = useState<SalaoServico[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    cliente: '',
    profissional: '',
    servico: '',
    hora_inicio: '09:00',
    observacoes: '',
  });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [ags, cls, prs, svs] = await Promise.all([
        CabeleireiroAPI.agendamentos.list({ data }),
        CabeleireiroAPI.clientes.list(),
        CabeleireiroAPI.profissionais.list(),
        CabeleireiroAPI.servicos.list(),
      ]);
      setList(ags);
      setClientes(cls);
      setProfissionais(prs);
      setServicos(svs);
    } catch {
      setList([]);
    } finally {
      setLoading(false);
    }
  }, [data]);

  useEffect(() => {
    void load();
  }, [load]);

  const sorted = useMemo(
    () => [...list].sort((a, b) => (a.hora_inicio || '').localeCompare(b.hora_inicio || '')),
    [list],
  );

  const openNew = () => {
    setForm({
      cliente: clientes[0] ? String(clientes[0].id) : '',
      profissional: profissionais[0] ? String(profissionais[0].id) : '',
      servico: servicos[0] ? String(servicos[0].id) : '',
      hora_inicio: '09:00',
      observacoes: '',
    });
    setError('');
    setOpen(true);
  };

  const save = async () => {
    if (!form.cliente) {
      setError('Selecione um cliente');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const servico = servicos.find((s) => String(s.id) === form.servico);
      await CabeleireiroAPI.agendamentos.create({
        cliente: Number(form.cliente),
        profissional: form.profissional ? Number(form.profissional) : null,
        servico: form.servico ? Number(form.servico) : null,
        data,
        hora_inicio: form.hora_inicio,
        valor: servico?.preco ?? 0,
        observacoes: form.observacoes,
        status: 'SCHEDULED',
      });
      setOpen(false);
      await load();
    } catch {
      setError('Erro ao criar agendamento');
    } finally {
      setSaving(false);
    }
  };

  const confirmarChegada = async (ag: SalaoAgendamento) => {
    try {
      await CabeleireiroAPI.confirmarChegada(ag.id);
      await load();
    } catch {
      alert('Não foi possível confirmar chegada');
    }
  };

  return (
    <div>
      <SalaoPageHeader
        title="Agenda"
        subtitle="Agendamentos do dia"
        icon={CalendarDays}
        onNew={openNew}
        newLabel="Novo agendamento"
      >
        <input
          type="date"
          value={data}
          onChange={(e) => setData(e.target.value)}
          className="px-3 py-2 rounded-lg border border-gray-200 text-sm bg-white"
        />
      </SalaoPageHeader>

      <div className="p-4 md:p-6 space-y-3">
        {loading ? (
          <p className="text-sm text-gray-500 text-center py-10">Carregando...</p>
        ) : sorted.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-10">Nenhum agendamento neste dia</p>
        ) : (
          sorted.map((ag) => (
            <div
              key={ag.id}
              className="flex flex-col sm:flex-row sm:items-center gap-3 bg-white rounded-xl border border-[#E8D5DC] px-4 py-3"
            >
              <div
                className="w-16 text-center rounded-lg py-1.5 shrink-0"
                style={{ backgroundColor: '#F3E4EA', color: SALAO_PRIMARY }}
              >
                <div className="text-sm font-bold">{(ag.hora_inicio || '').slice(0, 5)}</div>
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-gray-900 truncate">{ag.cliente_nome}</p>
                <p className="text-xs text-gray-500 truncate">
                  {ag.servico_nome || 'Serviço'}
                  {ag.profissional_nome ? ` · ${ag.profissional_nome}` : ''}
                  {ag.status_display ? ` · ${ag.status_display}` : ''}
                </p>
              </div>
              {(ag.status === 'SCHEDULED' || ag.status === 'ARRIVED') && (
                <button
                  type="button"
                  disabled={ag.status === 'ARRIVED'}
                  onClick={() => void confirmarChegada(ag)}
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-white disabled:opacity-60"
                  style={{ backgroundColor: SALAO_PRIMARY }}
                >
                  <Check size={14} />
                  {ag.status === 'ARRIVED' ? 'Chegou' : 'Confirmar chegada'}
                </button>
              )}
            </div>
          ))
        )}
      </div>

      <Modal isOpen={open} onClose={() => setOpen(false)} maxWidth="lg">
        <div className="p-6 space-y-4">
          <h2 className="text-lg font-semibold">Novo agendamento</h2>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label className="sm:col-span-2 text-sm space-y-1">
              <span>Cliente *</span>
              <select
                className="w-full border rounded-lg px-3 py-2"
                value={form.cliente}
                onChange={(e) => setForm((f) => ({ ...f, cliente: e.target.value }))}
              >
                <option value="">Selecione</option>
                {clientes.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome || c.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm space-y-1">
              <span>Profissional</span>
              <select
                className="w-full border rounded-lg px-3 py-2"
                value={form.profissional}
                onChange={(e) => setForm((f) => ({ ...f, profissional: e.target.value }))}
              >
                <option value="">—</option>
                {profissionais.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nome}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm space-y-1">
              <span>Serviço</span>
              <select
                className="w-full border rounded-lg px-3 py-2"
                value={form.servico}
                onChange={(e) => setForm((f) => ({ ...f, servico: e.target.value }))}
              >
                <option value="">—</option>
                {servicos.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.nome}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm space-y-1">
              <span>Horário</span>
              <input
                type="time"
                className="w-full border rounded-lg px-3 py-2"
                value={form.hora_inicio}
                onChange={(e) => setForm((f) => ({ ...f, hora_inicio: e.target.value }))}
              />
            </label>
            <label className="sm:col-span-2 text-sm space-y-1">
              <span>Observações</span>
              <textarea
                className="w-full border rounded-lg px-3 py-2 min-h-[70px]"
                value={form.observacoes}
                onChange={(e) => setForm((f) => ({ ...f, observacoes: e.target.value }))}
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
              {saving ? 'Salvando...' : 'Agendar'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
