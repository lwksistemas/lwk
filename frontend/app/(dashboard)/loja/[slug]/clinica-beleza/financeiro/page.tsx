"use client";

/**
 * Financeiro da Clínica - Clínica da Beleza
 * Caixa diário, contas a receber, formas de pagamento, comissão por profissional
 * Integrado com Pacientes, Procedimentos, Agendamentos, Profissionais
 */

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, DollarSign, Calendar, TrendingUp, Wallet, RefreshCw } from "lucide-react";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { useClinicaBelezaDark } from "@/hooks/useClinicaBelezaDark";
import { OfflineIndicator } from "@/components/clinica-beleza/OfflineIndicator";

const FORMA_PAGAMENTO: Record<string, string> = {
  CASH: "Dinheiro",
  CREDIT_CARD: "Crédito",
  DEBIT_CARD: "Débito",
  PIX: "PIX",
  TRANSFER: "Transferência",
};

const STATUS_LABEL: Record<string, string> = {
  PENDING: "Pendente",
  PAID: "Pago",
  CANCELLED: "Cancelado",
};

interface Resumo {
  caixa_diario: number;
  total_mes: number;
  contas_a_receber: number;
  comissao_mes: number;
}

interface Payment {
  id: number;
  appointment: number;
  amount: string;
  payment_method: string;
  status: string;
  payment_date: string | null;
  comissao_percentual: number;
  comissao_valor: string;
  paciente_nome: string;
  profissional_nome: string;
  procedimento_nome: string;
  data_atendimento: string;
  created_at: string;
}

interface Professional {
  id: number;
  name: string;
  specialty: string;
}

export default function FinanceiroClinicaPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;
  const [resumo, setResumo] = useState<Resumo | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [professionals, setProfessionals] = useState<Professional[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [professionalFilter, setProfessionalFilter] = useState<string>("");
  const [dateFilter, setDateFilter] = useState<string>("");
  useClinicaBelezaDark();

  const loadResumo = async () => {
    try {
      const res = await clinicaBelezaFetch("/financeiro/resumo/");
      if (res.ok) {
        const data = await res.json();
        setResumo(data);
      }
    } catch {
      setResumo(null);
    }
  };

  const loadPayments = async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      if (professionalFilter) params.set("professional", professionalFilter);
      if (dateFilter) params.set("date", dateFilter);
      const qs = params.toString();
      const res = await clinicaBelezaFetch(`/payments${qs ? `?${qs}` : ""}`);
      if (res.ok) {
        const data = await res.json();
        setPayments(Array.isArray(data) ? data : []);
      } else {
        setPayments([]);
      }
    } catch {
      setPayments([]);
    }
  };

  const loadProfessionals = async () => {
    try {
      const res = await clinicaBelezaFetch("/professionals/");
      if (res.ok) {
        const data = await res.json();
        setProfessionals(Array.isArray(data) ? data : []);
      }
    } catch {
      setProfessionals([]);
    }
  };

  const loadAll = async () => {
    setLoading(true);
    await Promise.all([loadResumo(), loadPayments(), loadProfessionals()]);
    setLoading(false);
  };

  useEffect(() => {
    loadAll();
    // loadAll/loadPayments omitidos: execução única ao montar e ao mudar filtros
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadPayments();
    // loadPayments omitido: depende de vários estados; reexecutar só quando filtros mudam
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, professionalFilter, dateFilter]);

  const totalLista = payments.reduce((s, p) => s + (p.status === "PAID" ? Number(p.amount) : 0), 0);

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 via-purple-50 to-white dark:from-neutral-900 dark:via-neutral-800 dark:to-neutral-900 text-gray-800 dark:text-gray-100 p-4 md:p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push(`/loja/${slug}/dashboard`)}
              className="p-2 hover:bg-white/80 dark:hover:bg-neutral-700 rounded-lg transition-colors"
              aria-label="Voltar"
            >
              <ArrowLeft size={24} className="text-gray-800 dark:text-gray-200" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Financeiro da Clínica</h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">Caixa, contas a receber e comissões</p>
            </div>
            <OfflineIndicator />
          </div>
          <button
            onClick={() => loadAll()}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
            Atualizar
          </button>
        </div>

        {loading && !resumo ? (
          <div className="flex justify-center py-12">
            <div className="w-10 h-10 border-4 border-purple-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <>
            {/* Cards resumo */}
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-green-100 dark:border-green-900/50">
                <div className="flex items-center gap-2 text-green-700 dark:text-green-400 mb-1">
                  <Wallet size={20} />
                  <span className="text-sm font-medium">Caixa hoje</span>
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {formatCurrency(resumo?.caixa_diario ?? 0)}
                </p>
              </div>
              <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-purple-100 dark:border-purple-900/50">
                <div className="flex items-center gap-2 text-purple-700 dark:text-purple-400 mb-1">
                  <DollarSign size={20} />
                  <span className="text-sm font-medium">Total mês</span>
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {formatCurrency(resumo?.total_mes ?? 0)}
                </p>
              </div>
              <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-amber-100 dark:border-amber-900/50">
                <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400 mb-1">
                  <Calendar size={20} />
                  <span className="text-sm font-medium">A receber</span>
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {formatCurrency(resumo?.contas_a_receber ?? 0)}
                </p>
              </div>
              <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-blue-100 dark:border-blue-900/50">
                <div className="flex items-center gap-2 text-blue-700 dark:text-blue-400 mb-1">
                  <TrendingUp size={20} />
                  <span className="text-sm font-medium">Comissão mês</span>
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {formatCurrency(resumo?.comissao_mes ?? 0)}
                </p>
              </div>
            </section>

            {/* Filtros */}
            <div className="flex flex-wrap gap-3 mb-4">
              <input
                type="date"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm"
                title="Filtrar por data do pagamento"
              />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm"
              >
                <option value="">Todos os status</option>
                <option value="PAID">Pago</option>
                <option value="PENDING">Pendente</option>
                <option value="CANCELLED">Cancelado</option>
              </select>
              <select
                value={professionalFilter}
                onChange={(e) => setProfessionalFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm"
              >
                <option value="">Todos os profissionais</option>
                {professionals.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Tabela */}
            <section className="bg-white dark:bg-neutral-800 rounded-xl shadow-md overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-neutral-700 border-b border-gray-200 dark:border-neutral-600">
                    <tr>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Data</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Paciente</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Profissional</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Procedimento</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Valor</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Pagamento</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Status</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Comissão</th>
                    </tr>
                  </thead>
                  <tbody>
                    {payments.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="py-8 text-center text-gray-500 dark:text-gray-400">
                          Nenhum lançamento encontrado
                        </td>
                      </tr>
                    ) : (
                      payments.map((p) => (
                        <tr
                          key={p.id}
                          className="border-b border-gray-100 dark:border-neutral-700 hover:bg-gray-50/50 dark:hover:bg-neutral-700/50"
                        >
                          <td className="py-3 px-4 text-gray-600 dark:text-gray-300 whitespace-nowrap">
                            {p.data_atendimento
                              ? new Date(p.data_atendimento).toLocaleDateString("pt-BR", {
                                  day: "2-digit",
                                  month: "2-digit",
                                  year: "numeric",
                                  hour: "2-digit",
                                  minute: "2-digit",
                                })
                              : "—"}
                          </td>
                          <td className="py-3 px-4 text-gray-800 dark:text-gray-200">{p.paciente_nome || "—"}</td>
                          <td className="py-3 px-4 text-gray-800 dark:text-gray-200">{p.profissional_nome || "—"}</td>
                          <td className="py-3 px-4 text-gray-800 dark:text-gray-200">{p.procedimento_nome || "—"}</td>
                          <td className="py-3 px-4 text-right font-medium text-gray-900 dark:text-gray-100">
                            {formatCurrency(p.amount)}
                          </td>
                          <td className="py-3 px-4 text-gray-700 dark:text-gray-300">
                            {FORMA_PAGAMENTO[p.payment_method] || p.payment_method}
                          </td>
                          <td className="py-3 px-4">
                            <span
                              className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                                p.status === "PAID"
                                  ? "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300"
                                  : p.status === "PENDING"
                                    ? "bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300"
                                    : "bg-gray-100 dark:bg-neutral-600 text-gray-600 dark:text-gray-300"
                              }`}
                            >
                              {STATUS_LABEL[p.status] || p.status}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-300">
                            {formatCurrency(p.comissao_valor || 0)}
                            {p.comissao_percentual ? ` (${p.comissao_percentual}%)` : ""}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            {payments.length > 0 && (
              <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">
                Total na lista (pagos): {formatCurrency(totalLista)} • {payments.length} lançamento(s)
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
