"use client";

import { ArrowLeft, FileText } from "lucide-react";
import { ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { ProntuarioTabBar } from "./ProntuarioTabBar";
import { ProntuarioTabContent } from "./ProntuarioTabContent";
import { useProntuarioPage } from "./useProntuarioPage";

export function ProntuarioPageContent() {
  const {
    slug,
    activeTab,
    data,
    loading,
    patientName,
    handleTabChange,
    voltarPacientes,
    handlePrintSecao,
    handlePrintCompleto,
  } = useProntuarioPage();

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={`Prontuário — ${patientName}`}
        subtitle="Histórico clínico completo do paciente"
        backHref={`/loja/${slug}/clinica-beleza/pacientes`}
        icon={FileText}
      />

      <div className="min-h-full bg-[#f7f2f4] dark:bg-gray-950 flex flex-col">
        <div className="px-4 md:px-6 pt-2 pb-4 border-b border-gray-200 dark:border-neutral-800 bg-white/80 dark:bg-neutral-900/80">
          <button
            type="button"
            onClick={voltarPacientes}
            className="inline-flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-3"
          >
            <ArrowLeft size={16} />
            Voltar aos clientes
          </button>

          <ProntuarioTabBar
            activeTab={activeTab}
            onTabChange={handleTabChange}
            onPrintSecao={handlePrintSecao}
            onPrintCompleto={handlePrintCompleto}
          />
        </div>

        <div className="flex-1 p-4 md:p-6 lg:p-8 w-full">
          {loading ? (
            <div className="text-center py-16 text-gray-500 dark:text-gray-400">
              Carregando prontuário...
            </div>
          ) : !data ? (
            <ClinicaBelezaPanel className="p-12 text-center text-gray-500 dark:text-gray-400 text-sm">
              Não foi possível carregar o prontuário. Tente novamente.
            </ClinicaBelezaPanel>
          ) : (
            <ProntuarioTabContent data={data} activeTab={activeTab} />
          )}
        </div>
      </div>
    </>
  );
}
