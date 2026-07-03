"use client";

import dynamic from "next/dynamic";
import { CalendarCog } from "lucide-react";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { ConsultasListTable } from "@/components/clinica-beleza/consultas/ConsultasListTable";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import { formatConsultaListDate } from "./consultas-page-utils";

interface ConsultasListViewProps {
  consultas: Consulta[];
  loading: boolean;
  deepLinkError: string | null;
  page: number;
  totalPages: number;
  totalCount: number;
  pageSize: number;
  onNovaConsulta: () => void;
  onOpenConfigAgenda: () => void;
  onSelectConsulta: (c: Consulta) => void;
  onPageChange: (page: number) => void;
  onLimparDeepLinkError: () => void;
}

export function ConsultasListView({
  consultas,
  loading,
  deepLinkError,
  page,
  totalPages,
  totalCount,
  pageSize,
  onNovaConsulta,
  onOpenConfigAgenda,
  onSelectConsulta,
  onPageChange,
  onLimparDeepLinkError,
}: ConsultasListViewProps) {
  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Consultas"
        subtitle="Confirme na Agenda · inicie e finalize aqui"
        onNew={onNovaConsulta}
        newLabel="Nova consulta"
        extraActions={
          <button
            type="button"
            onClick={onOpenConfigAgenda}
            className="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-800 transition-colors"
            title="Configuração da Agenda"
          >
            <CalendarCog className="w-4 h-4 shrink-0" style={{ color: CLINICA_BELEZA_PRIMARY }} />
            <span className="hidden sm:inline text-gray-700 dark:text-gray-300">Configuração da Agenda</span>
          </button>
        }
      />
      <ClinicaBelezaPageContent>
        {deepLinkError && (
          <div
            role="alert"
            className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-100"
          >
            {deepLinkError}
            <button
              type="button"
              onClick={onLimparDeepLinkError}
              className="ml-2 font-medium underline hover:no-underline"
            >
              Voltar à lista
            </button>
          </div>
        )}
        {loading ? (
          <div className="text-center py-16 text-gray-500">Carregando...</div>
        ) : consultas.length === 0 ? (
          <ClinicaBelezaPanel className="p-12 text-center text-gray-500 text-sm">
            Nenhuma consulta ainda. Confirme um agendamento na Agenda ou clique em{" "}
            <strong>Nova consulta</strong> para abrir um atendimento direto pelo cadastro do cliente.
          </ClinicaBelezaPanel>
        ) : (
          <ClinicaBelezaPanel>
            <ConsultasListTable
              consultas={consultas}
              onSelect={onSelectConsulta}
              formatData={formatConsultaListDate}
            />
            <EntityListLoadMore
              page={page}
              totalPages={totalPages}
              totalCount={totalCount}
              pageSize={pageSize}
              loading={loading}
              onPageChange={onPageChange}
              itemLabel="consultas"
            />
          </ClinicaBelezaPanel>
        )}
      </ClinicaBelezaPageContent>
    </>
  );
}

const ConsultaDetailShell = dynamic(
  () =>
    import("@/components/clinica-beleza/consultas/ConsultaDetailShell").then((m) => ({
      default: m.ConsultaDetailShell,
    })),
  {
    ssr: false,
    loading: () => <div className="text-center py-16 text-gray-500">Carregando consulta...</div>,
  },
);

interface ConsultaDetailViewProps {
  consulta: Consulta;
  detailPreloaded: boolean;
  onBack: () => void;
  onSelectConsulta: (c: Consulta) => void;
  onListRefresh: () => void;
}

export function ConsultaDetailView({
  consulta,
  detailPreloaded,
  onBack,
  onSelectConsulta,
  onListRefresh,
}: ConsultaDetailViewProps) {
  return (
    <ConsultaDetailShell
      consulta={consulta}
      detailPreloaded={detailPreloaded}
      onBack={onBack}
      onSelectConsulta={onSelectConsulta}
      onListRefresh={onListRefresh}
    />
  );
}
