"use client";

import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { CLINICA_FORMA_PAGAMENTO_LABEL, CLINICA_PAGAMENTO_STATUS_LABEL } from "@/lib/clinica-beleza-constants";
import { entityName } from "@/lib/clinica-beleza-entities";
import { formatCurrency } from "@/lib/financeiro-helpers";
import type { FinanceiroPayment, FinanceiroProfessional } from "../types";
import {
  rotuloDataLancamentoReceita,
  rotuloFormaPagamentoReceita,
  rotuloVencimentoPrazo,
  podeCorrigirFormaPagamento,
  statusPagamentoReceita,
} from "../payment-status";

interface FinanceiroReceitasTabProps {
  payments: FinanceiroPayment[];
  professionals: FinanceiroProfessional[];
  loading: boolean;
  page: number;
  totalPages: number;
  totalCount: number;
  pageSize: number;
  totalLista: number;
  statusFilter: string;
  professionalFilter: string;
  operadorFilter: string;
  operadores: string[];
  formaFilter: string;
  clienteFilter: string;
  tipoFilter: string;
  itemFilter: string;
  cobrandoId: number | null;
  onStatusFilterChange: (value: string) => void;
  onProfessionalFilterChange: (value: string) => void;
  onOperadorFilterChange: (value: string) => void;
  onFormaFilterChange: (value: string) => void;
  onClienteFilterChange: (value: string) => void;
  onTipoFilterChange: (value: string) => void;
  onItemFilterChange: (value: string) => void;
  onLimparFiltros: () => void;
  onPageChange: (page: number) => void;
  onBaixa: (payment: FinanceiroPayment) => void;
  onCorrigirForma: (payment: FinanceiroPayment) => void;
  onCobrar: (payment: FinanceiroPayment, canal: "whatsapp" | "email") => void;
  onAbrirRecibo: (payment: FinanceiroPayment) => void;
  reciboId: number | null;
}

export function FinanceiroReceitasTab({
  payments,
  professionals,
  loading,
  page,
  totalPages,
  totalCount,
  pageSize,
  totalLista,
  statusFilter,
  professionalFilter,
  operadorFilter,
  operadores,
  formaFilter,
  clienteFilter,
  tipoFilter,
  itemFilter,
  cobrandoId,
  onStatusFilterChange,
  onProfessionalFilterChange,
  onOperadorFilterChange,
  onFormaFilterChange,
  onClienteFilterChange,
  onTipoFilterChange,
  onItemFilterChange,
  onLimparFiltros,
  onPageChange,
  onBaixa,
  onCorrigirForma,
  onCobrar,
  onAbrirRecibo,
  reciboId,
}: FinanceiroReceitasTabProps) {
  const campo = "px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm";
  const mostrarOperador = payments.some((p) => Boolean(p.operador_nome?.trim())) || Boolean(operadorFilter);
  const temFiltro = Boolean(statusFilter || professionalFilter || operadorFilter || formaFilter || clienteFilter || tipoFilter || itemFilter);
  const operadoresLista = operadores.includes(operadorFilter) || !operadorFilter ? operadores : [operadorFilter, ...operadores];

  return (
    <>
      <div className="flex flex-wrap gap-3 mb-4">
        <select
          value={statusFilter}
          onChange={(e) => onStatusFilterChange(e.target.value)}
          className={campo}
          aria-label="Status"
        >
          <option value="">Todos os status</option>
          <option value="PAID">Pago</option>
          <option value="PENDING">Pendente</option>
          <option value="PARTIAL">Parcial</option>
          <option value="CANCELLED">Cancelado</option>
        </select>
        <select
          value={professionalFilter}
          onChange={(e) => onProfessionalFilterChange(e.target.value)}
          className={campo}
          aria-label="Profissional"
        >
          <option value="">Todos os profissionais</option>
          {professionals.map((p) => (
            <option key={p.id} value={p.id}>
              {entityName(p)}
            </option>
          ))}
        </select>
        {mostrarOperador && (
          <select
            value={operadorFilter}
            onChange={(e) => onOperadorFilterChange(e.target.value)}
            className={campo}
            aria-label="Operador do caixa"
          >
            <option value="">Todos os operadores</option>
            {operadoresLista.map((nome) => (
              <option key={nome} value={nome}>{nome}</option>
            ))}
          </select>
        )}
        <select
          value={formaFilter}
          onChange={(e) => onFormaFilterChange(e.target.value)}
          className={campo}
          aria-label="Forma de pagamento"
        >
          <option value="">Todas as formas</option>
          {Object.entries(CLINICA_FORMA_PAGAMENTO_LABEL).map(([id, rotulo]) => (
            <option key={id} value={id}>{rotulo}</option>
          ))}
        </select>
        <input
          type="search"
          value={clienteFilter}
          onChange={(e) => onClienteFilterChange(e.target.value)}
          placeholder="Cliente"
          aria-label="Cliente"
          className={campo}
        />
        <select
          value={tipoFilter}
          onChange={(e) => onTipoFilterChange(e.target.value)}
          className={campo}
          aria-label="Produtos ou procedimentos"
        >
          <option value="">Produtos e procedimentos</option>
          <option value="produto">Só produtos</option>
          <option value="procedimento">Só procedimentos</option>
        </select>
        <input
          type="search"
          value={itemFilter}
          onChange={(e) => onItemFilterChange(e.target.value)}
          placeholder="Nome do produto ou procedimento"
          aria-label="Nome do produto ou procedimento"
          className={`${campo} min-w-[16rem]`}
        />
        {temFiltro && (
          <button type="button" onClick={onLimparFiltros} className="px-3 py-2 text-sm text-gray-600 dark:text-gray-300">
            Limpar filtros
          </button>
        )}
      </div>
      <section className="bg-white dark:bg-neutral-800 rounded-xl shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="text-sm">
            <thead className="bg-gray-50 dark:bg-neutral-700 border-b border-gray-200 dark:border-neutral-600">
              <tr>
                <th className="text-left py-3 px-4 font-semibold">Cliente</th>
                <th className="text-left py-3 px-4 font-semibold">Profissional</th>
                {mostrarOperador && <th className="text-left py-3 px-4 font-semibold">Operador</th>}
                <th className="text-left py-3 px-4 font-semibold">Procedimentos</th>
                <th className="text-right py-3 px-4 font-semibold">Valor</th>
                <th className="text-left py-3 px-4 font-semibold">Pagamento</th>
                <th className="text-left py-3 px-4 font-semibold whitespace-nowrap">Recebido em</th>
                <th className="text-left py-3 px-4 font-semibold">Status</th>
                <th className="text-right py-3 px-4 font-semibold whitespace-nowrap min-w-[8.5rem]">
                  Comissão
                </th>
                <th className="py-3 px-3 min-w-[9rem]"></th>
              </tr>
            </thead>
            <tbody>
              {payments.length === 0 ? (
                <tr>
                  <td colSpan={mostrarOperador ? 10 : 9} className="py-8 text-center text-gray-500">
                    Nenhum lançamento. Receitas são criadas ao finalizar consultas.
                  </td>
                </tr>
              ) : (
                payments.map((p) => {
                  const status = statusPagamentoReceita(p);
                  const vencimentoPrazo = rotuloVencimentoPrazo(p);
                  const anterior = p.origem === "procedimento_anterior";
                  const falta = anterior && p.saldo_devedor > 0 ? ` · falta ${formatCurrency(p.saldo_devedor)}` : "";
                  return (
                  <tr key={anterior ? `anterior-${p.id}` : `pagamento-${p.id}`} className="border-b border-gray-100 dark:border-neutral-700">
                    <td className="py-3 px-4">{p.paciente_nome || "—"}</td>
                    <td className="py-3 px-4">{p.profissional_nome || "—"}</td>
                    {mostrarOperador && <td className="py-3 px-4">{p.operador_nome || "—"}</td>}
                    <td className="py-3 px-4 max-w-[220px] text-sm leading-snug col-allow-wrap">
                      {p.procedimento_nome || "Consulta"}
                      {anterior && (
                        <span className="block text-xs text-gray-500">Antes do sistema</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right font-medium">
                      {formatCurrency(p.valor_total_efetivo ?? p.amount)}
                    </td>
                    <td className="py-3 px-4">
                      {rotuloFormaPagamentoReceita(p)}
                      {vencimentoPrazo && (
                        <span className={`block text-xs mt-0.5 ${p.vencido ? "text-red-600 dark:text-red-400 font-medium" : "text-gray-500 dark:text-gray-400"}`}>
                          Venc. {vencimentoPrazo}
                          {p.vencido && p.dias_atraso > 0 ? ` · ${p.dias_atraso} dia(s) em atraso` : ""}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-gray-600 dark:text-gray-400">
                      {rotuloDataLancamentoReceita(p)}
                    </td>
                    <td className="py-3 px-4 col-allow-wrap">
                      {p.retorno_gratuito ? (
                        <button
                          type="button"
                          onClick={() => onAbrirRecibo(p)}
                          disabled={reciboId === p.id}
                          title="Clique para imprimir ou enviar o recibo"
                          className="inline-block px-2 py-1 rounded-full text-xs font-medium bg-sky-100 text-sky-800 hover:bg-sky-200 dark:bg-sky-900/30 dark:text-sky-300 disabled:opacity-50"
                        >
                          Retorno
                        </button>
                      ) : (status === "PAID" || status === "PARTIAL") && !anterior ? (
                        <button
                          type="button"
                          onClick={() => onAbrirRecibo(p)}
                          disabled={reciboId === p.id}
                          title="Clique para imprimir ou enviar o recibo"
                          className={`inline-block px-2 py-1 rounded-full text-xs font-medium disabled:opacity-50 ${
                            status === "PAID"
                              ? "bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-300"
                              : "bg-orange-100 text-orange-800 hover:bg-orange-200 dark:bg-orange-900/30 dark:text-orange-300"
                          }`}
                        >
                          {CLINICA_PAGAMENTO_STATUS_LABEL[status] || status}
                          {status === "PARTIAL" && p.saldo_devedor > 0
                            ? ` · falta ${formatCurrency(p.saldo_devedor)}`
                            : ""}
                        </button>
                      ) : (
                        <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                          status === "PENDING" || status === "PARTIAL"
                            ? "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300"
                            : status === "PAID"
                              ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
                              : "bg-gray-100 dark:bg-neutral-600"
                        }`}>
                          {CLINICA_PAGAMENTO_STATUS_LABEL[status] || status}
                          {falta}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right col-allow-wrap">
                      {anterior ? "—" : formatCurrency(p.comissao_valor || 0)}
                      {!anterior && p.comissao_percentual ? (
                        <span className="block text-xs text-gray-500 font-normal">
                          ref. {p.comissao_percentual}% do total
                        </span>
                      ) : null}
                    </td>
                    <td className="py-3 px-3 text-center">
                      <div className="flex flex-col items-stretch gap-1">
                        {!p.retorno_gratuito && (status === "PENDING" || status === "PARTIAL") && (
                          <button
                            type="button"
                            onClick={() => onBaixa(p)}
                            className="text-xs px-2 py-1 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-medium whitespace-nowrap"
                          >
                            {anterior ? "Receber" : status === "PARTIAL" ? "Complementar" : "Dar Baixa"}
                          </button>
                        )}
                        {!anterior && podeCorrigirFormaPagamento(p) && (
                          <button
                            type="button"
                            onClick={() => onCorrigirForma(p)}
                            className="text-xs px-2 py-1 rounded-lg border border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-200 font-medium whitespace-nowrap hover:bg-gray-50 dark:hover:bg-neutral-700"
                          >
                            Corrigir forma
                          </button>
                        )}
                        {!anterior && p.vencido && (
                          <div className="flex items-center justify-center gap-1">
                            <button
                              type="button"
                              onClick={() => onCobrar(p, "whatsapp")}
                              disabled={cobrandoId === p.id}
                              title="Cobrar por WhatsApp"
                              className="text-xs px-2 py-1 rounded-lg bg-green-600 hover:bg-green-700 text-white font-medium disabled:opacity-50"
                            >
                              Zap
                            </button>
                            <button
                              type="button"
                              onClick={() => onCobrar(p, "email")}
                              disabled={cobrandoId === p.id}
                              title="Cobrar por e-mail"
                              className="text-xs px-2 py-1 rounded-lg border border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-200 font-medium disabled:opacity-50"
                            >
                              E-mail
                            </button>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
        <EntityListLoadMore
          page={page}
          totalPages={totalPages}
          totalCount={totalCount}
          pageSize={pageSize}
          loading={loading}
          onPageChange={onPageChange}
          itemLabel="pagamentos"
        />
      </section>
      {payments.length > 0 && (
        <p className="mt-3 text-sm text-gray-500">
          Total na lista (pagos): {formatCurrency(totalLista)}
        </p>
      )}
    </>
  );
}
