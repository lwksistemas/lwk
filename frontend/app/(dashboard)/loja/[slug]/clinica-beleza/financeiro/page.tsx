"use client";

import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { useFinanceiroPage } from "@/hooks/clinica-beleza/useFinanceiroPage";
import { DespesaFormModal } from "./DespesaFormModal";
import { FinanceiroDespesasTab } from "./components/FinanceiroDespesasTab";
import { FinanceiroReceitasTab } from "./components/FinanceiroReceitasTab";
import { FinanceiroResumoCards } from "./components/FinanceiroResumoCards";
import { FinanceiroTabBar } from "./components/FinanceiroTabBar";
import { ModalBaixaPayment } from "./components/ModalBaixaPayment";
import type { FinanceiroPayment } from "./types";

export default function FinanceiroClinicaPage() {
  const f = useFinanceiroPage();
  const [baixaPayment, setBaixaPayment] = useState<FinanceiroPayment | null>(null);

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
            style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
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
            <FinanceiroResumoCards resumo={f.resumo} />
            <FinanceiroTabBar
              tab={f.tab}
              onTabChange={f.setTab}
              onNovaDespesa={f.abrirNovaDespesa}
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
                dateFilter={f.dateFilter}
                onStatusFilterChange={f.setStatusFilter}
                onProfessionalFilterChange={f.setProfessionalFilter}
                onDateFilterChange={f.setDateFilter}
                onPageChange={f.setPaymentsPage}
                onBaixa={(p) => setBaixaPayment(p)}
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
                dateFilter={f.despesaDateFilter}
                onStatusFilterChange={f.setDespesaStatusFilter}
                onDateFilterChange={f.setDespesaDateFilter}
                onPageChange={f.setDespesasPage}
                onEdit={f.editarDespesa}
                onRemove={f.removerDespesa}
              />
            )}
          </>
        )}
      </ClinicaBelezaPageContent>

      <ModalBaixaPayment
        payment={baixaPayment}
        onClose={() => setBaixaPayment(null)}
        onSuccess={() => { setBaixaPayment(null); void f.loadAll(); }}
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
