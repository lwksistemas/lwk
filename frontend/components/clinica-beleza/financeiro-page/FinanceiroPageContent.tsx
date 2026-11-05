"use client";

import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { useFinanceiroPage } from "@/hooks/clinica-beleza/useFinanceiroPage";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { formatApiErrorBody } from "@/lib/api-errors";
import { useToast } from "@/components/ui/Toast";
import { DespesaFormModal } from "./DespesaFormModal";
import { FinanceiroDespesasTab } from "./components/FinanceiroDespesasTab";
import { FinanceiroReceitasTab } from "./components/FinanceiroReceitasTab";
import { FinanceiroResumoCards } from "./components/FinanceiroResumoCards";
import { FinanceiroTabBar } from "./components/FinanceiroTabBar";
import { ModalReceberConsulta } from "@/components/clinica-beleza/consultas/ModalReceberConsulta";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import { ModalBaixaPayment } from "./components/ModalBaixaPayment";
import { ModalReceberProcedimentoAnterior } from "./components/ModalReceberProcedimentoAnterior";
import { ModalCorrigirForma } from "./components/ModalCorrigirForma";
import type { FinanceiroPayment } from "./types";

export function FinanceiroPageContent() {
  const f = useFinanceiroPage();
  const toast = useToast();
  const [baixaPayment, setBaixaPayment] = useState<FinanceiroPayment | null>(null);
  const [receberAnterior, setReceberAnterior] = useState<FinanceiroPayment | null>(null);
  const [formaPayment, setFormaPayment] = useState<FinanceiroPayment | null>(null);
  const [cobrandoId, setCobrandoId] = useState<number | null>(null);
  const [reciboId, setReciboId] = useState<number | null>(null);
  const [receberConsulta, setReceberConsulta] = useState<Consulta | null>(null);
  const [resumoVisivel, setResumoVisivel] = useState(true);

  useEffect(() => {
    setResumoVisivel(window.localStorage.getItem("lwk-financeiro-resumo") !== "0");
  }, []);

  const alternarResumo = () => {
    setResumoVisivel((atual) => {
      const proximo = !atual;
      window.localStorage.setItem("lwk-financeiro-resumo", proximo ? "1" : "0");
      return proximo;
    });
  };

  const handleAbrirRecibo = async (payment: FinanceiroPayment) => {
    if (!payment.consulta_id) {
      toast.error("Consulta não encontrada para este lançamento.");
      return;
    }
    setReciboId(payment.id);
    try {
      const fresh = await ClinicaBelezaAPI.consultas.get(payment.consulta_id);
      setReceberConsulta(fresh);
    } catch (e) {
      toast.error(formatApiErrorBody(e) || "Erro ao abrir o recibo.");
    } finally {
      setReciboId(null);
    }
  };

  const handleCobrar = async (payment: FinanceiroPayment, canal: "whatsapp" | "email") => {
    setCobrandoId(payment.id);
    try {
      const res = await ClinicaBelezaAPI.financeiro.payments.cobrar(payment.id, canal);
      toast.success(res.message || "Cobrança enviada.");
    } catch (e) {
      toast.error(formatApiErrorBody(e) || "Erro ao enviar cobrança.");
    } finally {
      setCobrandoId(null);
    }
  };

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Financeiro da Clínica"
        subtitle="Receitas, despesas e comissões"
        extraActions={
          <button
            type="button"
            onClick={() => f.loadAll()}
            disabled={f.loading}
            className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 text-white rounded-lg hover:opacity-90 disabled:opacity-50 text-xs sm:text-sm font-medium"
            style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
          >
            <RefreshCw size={16} className={f.loading ? "animate-spin" : ""} />
            <span className="hidden sm:inline">Atualizar</span>
          </button>
        }
      />
      <ClinicaBelezaPageContent>
        {f.loadingResumo && !f.resumo ? (
          <div className="flex justify-center py-12">
            <div className="w-10 h-10 border-4 border-purple-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <>
            <div className="mb-3 flex justify-end">
              <button type="button" onClick={alternarResumo} className="text-sm font-medium text-gray-600 dark:text-gray-300">
                {resumoVisivel ? "Ocultar resumo" : "Mostrar resumo"}
              </button>
            </div>
            {resumoVisivel && <FinanceiroResumoCards resumo={f.resumo} />}
            <FinanceiroTabBar
              tab={f.tab}
              onTabChange={f.setTab}
              onNovaDespesa={f.abrirNovaDespesa}
              periodo={f.periodo}
              inicio={f.periodoInicio}
              fim={f.periodoFim}
              onPeriodoChange={f.setPeriodo}
              onInicioChange={f.setPeriodoInicio}
              onFimChange={f.setPeriodoFim}
            />
            {f.tab === "receitas" ? (
              <FinanceiroReceitasTab
                payments={f.payments}
                professionals={f.professionals}
                loading={f.loadingPayments}
                page={f.paymentsPage}
                totalPages={f.paymentsTotalPages}
                totalCount={f.totalPayments ?? 0}
                pageSize={f.paymentsPageSize}
                totalLista={f.totalListaReceitas}
                statusFilter={f.statusFilter}
                professionalFilter={f.professionalFilter}
                operadorFilter={f.operadorFilter}
                operadores={f.resumo?.operadores ?? []}
                formaFilter={f.formaFilter}
                clienteFilter={f.clienteFilter}
                tipoFilter={f.tipoFilter}
                itemFilter={f.itemFilter}
                onStatusFilterChange={f.setStatusFilter}
                onProfessionalFilterChange={f.setProfessionalFilter}
                onOperadorFilterChange={f.setOperadorFilter}
                onFormaFilterChange={f.setFormaFilter}
                onClienteFilterChange={f.setClienteFilter}
                onTipoFilterChange={f.setTipoFilter}
                onItemFilterChange={f.setItemFilter}
                onLimparFiltros={f.limparFiltrosReceita}
                onPageChange={f.setPaymentsPage}
                onBaixa={(p) => {
                  if (p.origem === "procedimento_anterior") setReceberAnterior(p);
                  else setBaixaPayment(p);
                }}
                onCorrigirForma={(p) => setFormaPayment(p)}
                cobrandoId={cobrandoId}
                onCobrar={handleCobrar}
                onAbrirRecibo={(p) => { void handleAbrirRecibo(p); }}
                reciboId={reciboId}
              />
            ) : (
              <FinanceiroDespesasTab
                despesas={f.despesas}
                loading={f.loadingDespesas}
                page={f.despesasPage}
                totalPages={f.despesasTotalPages}
                totalCount={f.totalDespesas ?? 0}
                pageSize={f.despesasPageSize}
                totalLista={f.totalListaDespesas}
                statusFilter={f.despesaStatusFilter}
                onStatusFilterChange={f.setDespesaStatusFilter}
                onPageChange={f.setDespesasPage}
                onEdit={f.editarDespesa}
                onRemove={f.removerDespesa}
              />
            )}
          </>
        )}
      </ClinicaBelezaPageContent>

      {receberConsulta && (
        <ModalReceberConsulta
          open
          consulta={receberConsulta}
          onClose={() => setReceberConsulta(null)}
          onSuccess={(c) => setReceberConsulta((prev) => (prev ? { ...prev, ...c } : prev))}
        />
      )}
      <ModalReceberProcedimentoAnterior
        payment={receberAnterior}
        onClose={() => setReceberAnterior(null)}
        onSuccess={() => {
          toast.success("Recebimento registrado.");
          void f.loadAll();
        }}
      />
      <ModalBaixaPayment
        payment={baixaPayment}
        onClose={() => setBaixaPayment(null)}
        onSuccess={() => { void f.loadAll(); }}
      />
      <ModalCorrigirForma
        payment={formaPayment}
        onClose={() => setFormaPayment(null)}
        onSuccess={() => {
          toast.success("Forma de pagamento corrigida.");
          void f.loadAll();
        }}
      />
      <DespesaFormModal
        open={f.showDespesaModal}
        editing={f.editingDespesa}
        saving={f.savingDespesa}
        onClose={() => f.setShowDespesaModal(false)}
        onSaved={f.onDespesaSalva}
      />
    </>
  );
}
