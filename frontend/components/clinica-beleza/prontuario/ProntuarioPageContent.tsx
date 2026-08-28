"use client";

import { ArrowLeft, BookOpen } from "lucide-react";
import { ConsultaProfessionalSelectModal } from "@/components/clinica-beleza/consultas/ConsultaProfessionalSelectModal";
import { ModalReceberConsulta } from "@/components/clinica-beleza/consultas/ModalReceberConsulta";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { isProntuarioLocalTab } from "./prontuario-utils";
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
    consultas,
    consultasLoading,
    consultaParaFotosId,
    printando,
    iniciandoId,
    excluindoId,
    receberConsulta,
    abrindoReceberId,
    showProfessionalModal,
    profissionaisDisponiveis,
    handleTabChange,
    voltarHub,
    abrirConsulta,
    handlePrintSecao,
    handlePrintCompleto,
    iniciarConsulta,
    confirmarProfissional,
    fecharProfessionalModal,
    abrirReceber,
    fecharReceber,
    aposRecebimento,
    excluirConsulta,
  } = useProntuarioPage();

  const showDocsLoading = loading && !isProntuarioLocalTab(activeTab);

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={`Prontuário — ${patientName || "Paciente"}`}
        subtitle="Resumo, consultas, fotos e evolução. Inclusões só dentro da consulta."
        backHref={`/loja/${slug}/clinica-beleza/prontuario`}
        icon={BookOpen}
      />

      <div className="min-h-full bg-[var(--cb-page-bg,#f7f2f4)] dark:bg-gray-950 flex flex-col">
        <div className="px-4 md:px-6 pt-2 pb-4 border-b border-gray-200 dark:border-neutral-800 bg-white/80 dark:bg-neutral-900/80">
          <button
            type="button"
            onClick={voltarHub}
            className="inline-flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-3"
          >
            <ArrowLeft size={16} />
            Buscar outro paciente
          </button>

          <ProntuarioTabBar
            activeTab={activeTab}
            onTabChange={handleTabChange}
            onPrintSecao={() => void handlePrintSecao()}
            onPrintCompleto={() => void handlePrintCompleto()}
            printando={printando}
          />
        </div>

        <div className="flex-1 p-4 md:p-6 lg:p-8 w-full">
          {showDocsLoading ? (
            <div className="text-center py-16 text-gray-500 dark:text-gray-400">
              Carregando prontuário...
            </div>
          ) : (
            <ProntuarioTabContent
              data={data}
              activeTab={activeTab}
              consultas={consultas}
              consultasLoading={consultasLoading}
              consultaParaFotosId={consultaParaFotosId}
              iniciandoId={iniciandoId}
              excluindoId={excluindoId}
              recebendoId={abrindoReceberId}
              onAbrirConsulta={abrirConsulta}
              onIniciarConsulta={(c) => void iniciarConsulta(c)}
              onReceberConsulta={(c) => void abrirReceber(c)}
              onExcluirConsulta={(c) => void excluirConsulta(c)}
            />
          )}
        </div>
      </div>

      {receberConsulta && (
        <ModalReceberConsulta
          open
          consulta={receberConsulta}
          onClose={fecharReceber}
          onSuccess={(c) => void aposRecebimento(c)}
        />
      )}

      <ConsultaProfessionalSelectModal
        open={showProfessionalModal}
        profissionais={profissionaisDisponiveis}
        onSelect={confirmarProfissional}
        onClose={fecharProfessionalModal}
      />
    </>
  );
}
