'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Calendar,
  DollarSign,
  Download,
  Mail,
  MessageCircle,
  RefreshCw,
  TrendingUp,
  Wallet,
} from 'lucide-react';
import { SalaoPageHeader } from '@/components/cabeleireiro/SalaoPageHeader';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';
import { formatCurrency } from '@/lib/financeiro-helpers';
import {
  CabeleireiroAPI,
  type SalaoComissoesRelatorio,
  type SalaoFinanceiroResumo,
  type SalaoPayment,
  type SalaoProfissional,
} from '@/lib/cabeleireiro-api';

type Tab = 'receitas' | 'comissoes';

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

function monthStartISO() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
}

export function SalaoFinanceiroPageContent() {
  const [tab, setTab] = useState<Tab>('receitas');
  const [loading, setLoading] = useState(true);
  const [resumo, setResumo] = useState<SalaoFinanceiroResumo | null>(null);
  const [payments, setPayments] = useState<SalaoPayment[]>([]);
  const [profissionais, setProfissionais] = useState<SalaoProfissional[]>([]);
  const [statusFilter, setStatusFilter] = useState('PAID');
  const [profFilter, setProfFilter] = useState('');
  const [dateFilter, setDateFilter] = useState('');
  const [sendingRecibo, setSendingRecibo] = useState<number | null>(null);

  const [dataInicio, setDataInicio] = useState(monthStartISO);
  const [dataFim, setDataFim] = useState(todayISO);
  const [comissaoProf, setComissaoProf] = useState('');
  const [comissoes, setComissoes] = useState<SalaoComissoesRelatorio | null>(null);
  const [loadingComissoes, setLoadingComissoes] = useState(false);

  const loadReceitas = useCallback(async () => {
    setLoading(true);
    try {
      const now = new Date();
      const [r, pays, profs] = await Promise.all([
        CabeleireiroAPI.financeiro.resumo({ mes: now.getMonth() + 1, ano: now.getFullYear() }),
        CabeleireiroAPI.payments.list({
          status: statusFilter || undefined,
          date: dateFilter || undefined,
          profissional: profFilter || undefined,
        }),
        CabeleireiroAPI.profissionais.list(),
      ]);
      setResumo(r);
      setPayments(pays);
      setProfissionais(profs);
    } catch {
      setResumo(null);
      setPayments([]);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, dateFilter, profFilter]);

  const loadComissoes = useCallback(async () => {
    setLoadingComissoes(true);
    try {
      const data = await CabeleireiroAPI.relatorios.comissoes({
        data_inicio: dataInicio,
        data_fim: dataFim,
        profissional_id: comissaoProf || undefined,
      });
      setComissoes(data);
    } catch {
      setComissoes(null);
    } finally {
      setLoadingComissoes(false);
    }
  }, [dataInicio, dataFim, comissaoProf]);

  useEffect(() => {
    void loadReceitas();
  }, [loadReceitas]);

  useEffect(() => {
    if (tab === 'comissoes') void loadComissoes();
  }, [tab, loadComissoes]);

  const enviarRecibo = async (id: number, canal: 'email' | 'whatsapp') => {
    setSendingRecibo(id);
    try {
      const res = await CabeleireiroAPI.payments.enviarRecibo(id, canal);
      alert(res.message || (res.success ? 'Enviado' : res.error || 'Falha'));
    } catch {
      alert('Erro ao enviar recibo');
    } finally {
      setSendingRecibo(null);
    }
  };

  const baixarPdf = async () => {
    try {
      const blob = await CabeleireiroAPI.relatorios.comissoesPdf({
        data_inicio: dataInicio,
        data_fim: dataFim,
        profissional_id: comissaoProf || undefined,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `comissoes_${dataInicio}_${dataFim}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert('Erro ao baixar PDF');
    }
  };

  const mesAnoLabel = useMemo(() => {
    if (!resumo?.filter) return '';
    return `${String(resumo.filter.mes).padStart(2, '0')}/${resumo.filter.ano}`;
  }, [resumo]);

  return (
    <div>
      <SalaoPageHeader
        title="Financeiro"
        subtitle="Caixa, receitas e comissões por profissional"
        icon={DollarSign}
      >
        <button
          type="button"
          onClick={() => (tab === 'receitas' ? void loadReceitas() : void loadComissoes())}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-white rounded-lg text-sm"
          style={{ backgroundColor: SALAO_PRIMARY }}
        >
          <RefreshCw size={14} className={loading || loadingComissoes ? 'animate-spin' : ''} />
          Atualizar
        </button>
      </SalaoPageHeader>

      <div className="p-4 md:p-6 space-y-4">
        <div className="flex gap-2 border-b border-[#E8D5DC]">
          {(
            [
              ['receitas', 'Receitas / Caixa'],
              ['comissoes', 'Comissões'],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setTab(key)}
              className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
                tab === key ? 'border-current' : 'border-transparent text-gray-500'
              }`}
              style={tab === key ? { color: SALAO_PRIMARY } : undefined}
            >
              {label}
            </button>
          ))}
        </div>

        {tab === 'receitas' && (
          <>
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <ResumoCard icon={Wallet} label="Caixa hoje" value={resumo?.caixa_diario} color="text-green-700" />
              <ResumoCard
                icon={DollarSign}
                label={`Receita ${mesAnoLabel || 'mês'}`}
                value={resumo?.total_mes}
                color="text-purple-700"
              />
              <ResumoCard
                icon={Calendar}
                label="A receber"
                value={resumo?.contas_a_receber}
                color="text-amber-700"
              />
              <ResumoCard
                icon={TrendingUp}
                label="Comissões mês"
                value={resumo?.comissao_mes}
                color="text-blue-700"
                hint={resumo ? `Lucro estimado ${formatCurrency(resumo.lucro)}` : undefined}
              />
            </section>

            <div className="flex flex-wrap gap-2 items-end">
              <label className="text-xs space-y-1">
                <span className="text-gray-500">Status</span>
                <select
                  className="block border rounded-lg px-2 py-1.5 text-sm"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="">Todos</option>
                  <option value="PAID">Pago</option>
                  <option value="PENDING">Pendente</option>
                  <option value="CANCELLED">Cancelado</option>
                </select>
              </label>
              <label className="text-xs space-y-1">
                <span className="text-gray-500">Profissional</span>
                <select
                  className="block border rounded-lg px-2 py-1.5 text-sm min-w-[160px]"
                  value={profFilter}
                  onChange={(e) => setProfFilter(e.target.value)}
                >
                  <option value="">Todos</option>
                  {profissionais.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nome}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-xs space-y-1">
                <span className="text-gray-500">Data pagamento</span>
                <input
                  type="date"
                  className="block border rounded-lg px-2 py-1.5 text-sm"
                  value={dateFilter}
                  onChange={(e) => setDateFilter(e.target.value)}
                />
              </label>
            </div>

            <div className="bg-white rounded-xl border border-[#E8D5DC] overflow-hidden">
              {loading ? (
                <p className="text-sm text-gray-500 text-center py-10">Carregando...</p>
              ) : payments.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-10">Nenhum pagamento encontrado</p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-[#F7F0F3] text-left text-xs uppercase text-gray-500">
                      <th className="px-3 py-2">Cliente</th>
                      <th className="px-3 py-2 hidden sm:table-cell">Serviço</th>
                      <th className="px-3 py-2 hidden md:table-cell">Profissional</th>
                      <th className="px-3 py-2 text-right">Valor</th>
                      <th className="px-3 py-2 text-right hidden lg:table-cell">Comissão</th>
                      <th className="px-3 py-2 text-right">Recibo</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {payments.map((p) => (
                      <tr key={p.id}>
                        <td className="px-3 py-2">
                          <div className="font-medium">{p.cliente_nome || '—'}</div>
                          <div className="text-xs text-gray-500">
                            {p.payment_method_label || p.payment_method} · {p.status_display || p.status}
                          </div>
                        </td>
                        <td className="px-3 py-2 text-gray-600 hidden sm:table-cell">{p.servico_nome || '—'}</td>
                        <td className="px-3 py-2 text-gray-600 hidden md:table-cell">
                          {p.profissional_nome || '—'}
                        </td>
                        <td className="px-3 py-2 text-right tabular-nums font-medium">
                          {formatCurrency(Number(p.amount || 0))}
                        </td>
                        <td className="px-3 py-2 text-right tabular-nums text-gray-600 hidden lg:table-cell">
                          {formatCurrency(Number(p.comissao_valor || 0))}
                        </td>
                        <td className="px-3 py-2">
                          {p.status === 'PAID' ? (
                            <div className="flex justify-end gap-1">
                              <button
                                type="button"
                                title="Email"
                                disabled={sendingRecibo === p.id}
                                onClick={() => void enviarRecibo(p.id, 'email')}
                                className="p-1.5 hover:bg-gray-100 rounded"
                              >
                                <Mail size={14} />
                              </button>
                              <button
                                type="button"
                                title="WhatsApp"
                                disabled={sendingRecibo === p.id}
                                onClick={() => void enviarRecibo(p.id, 'whatsapp')}
                                className="p-1.5 hover:bg-emerald-50 rounded text-emerald-700"
                              >
                                <MessageCircle size={14} />
                              </button>
                            </div>
                          ) : (
                            <span className="text-xs text-gray-400 float-right">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}

        {tab === 'comissoes' && (
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2 items-end">
              <label className="text-xs space-y-1">
                <span className="text-gray-500">De</span>
                <input
                  type="date"
                  className="block border rounded-lg px-2 py-1.5 text-sm"
                  value={dataInicio}
                  onChange={(e) => setDataInicio(e.target.value)}
                />
              </label>
              <label className="text-xs space-y-1">
                <span className="text-gray-500">Até</span>
                <input
                  type="date"
                  className="block border rounded-lg px-2 py-1.5 text-sm"
                  value={dataFim}
                  onChange={(e) => setDataFim(e.target.value)}
                />
              </label>
              <label className="text-xs space-y-1">
                <span className="text-gray-500">Profissional</span>
                <select
                  className="block border rounded-lg px-2 py-1.5 text-sm min-w-[160px]"
                  value={comissaoProf}
                  onChange={(e) => setComissaoProf(e.target.value)}
                >
                  <option value="">Todos</option>
                  {profissionais.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nome}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                onClick={() => void loadComissoes()}
                className="px-3 py-1.5 rounded-lg text-sm text-white"
                style={{ backgroundColor: SALAO_PRIMARY }}
              >
                Filtrar
              </button>
              <button
                type="button"
                onClick={() => void baixarPdf()}
                className="inline-flex items-center gap-1 px-3 py-1.5 border rounded-lg text-sm"
              >
                <Download size={14} /> PDF
              </button>
            </div>

            {loadingComissoes ? (
              <p className="text-sm text-gray-500 text-center py-10">Carregando...</p>
            ) : !comissoes || comissoes.profissionais.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-10">
                Nenhuma comissão no período. Receba atendimentos com regras cadastradas em Profissionais.
              </p>
            ) : (
              <div className="space-y-4">
                <div className="bg-white rounded-xl border border-[#E8D5DC] p-4 text-sm flex flex-wrap gap-4">
                  <span>
                    Atendimentos: <strong>{comissoes.totais.qtd}</strong>
                  </span>
                  <span>
                    Faturado: <strong>{formatCurrency(comissoes.totais.valor_total)}</strong>
                  </span>
                  <span>
                    Comissões: <strong>{formatCurrency(comissoes.totais.comissao_total)}</strong>
                  </span>
                </div>
                {comissoes.profissionais.map((prof) => (
                  <div key={String(prof.profissional_id)} className="bg-white rounded-xl border border-[#E8D5DC] overflow-hidden">
                    <div className="px-4 py-3 bg-[#F7F0F3] flex flex-wrap justify-between gap-2 text-sm">
                      <strong>{prof.nome}</strong>
                      <span className="text-gray-600">
                        {prof.qtd} · {formatCurrency(prof.valor_total)} · comissão{' '}
                        {formatCurrency(prof.comissao_total)}
                      </span>
                    </div>
                    <table className="w-full text-sm">
                      <tbody className="divide-y divide-gray-100">
                        {prof.itens.map((it) => (
                          <tr key={it.payment_id}>
                            <td className="px-4 py-2 text-gray-500 w-28">{it.data}</td>
                            <td className="px-4 py-2">{it.cliente}</td>
                            <td className="px-4 py-2 text-gray-600 hidden sm:table-cell">{it.servico}</td>
                            <td className="px-4 py-2 text-right tabular-nums">{formatCurrency(it.valor)}</td>
                            <td className="px-4 py-2 text-right tabular-nums font-medium">
                              {formatCurrency(it.comissao)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function ResumoCard({
  icon: Icon,
  label,
  value,
  color,
  hint,
}: {
  icon: typeof Wallet;
  label: string;
  value?: number;
  color: string;
  hint?: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-[#E8D5DC] p-4">
      <div className={`flex items-center gap-2 mb-1 ${color}`}>
        <Icon size={18} />
        <span className="text-sm font-medium">{label}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{formatCurrency(value ?? 0)}</p>
      {hint ? <p className="text-xs text-gray-500 mt-1">{hint}</p> : null}
    </div>
  );
}
