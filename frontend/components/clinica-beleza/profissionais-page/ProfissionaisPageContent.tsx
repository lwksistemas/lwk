"use client";

import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { ModalHorariosTrabalho } from "@/components/clinica-beleza/ModalHorariosTrabalho";
import { ModalTempoConsulta } from "@/components/clinica-beleza/ModalTempoConsulta";
import { ProfissionalFormPageContent } from "@/components/clinica-beleza/profissional-form/ProfissionalFormPageContent";
import { AdminProfissionalToggle } from "@/components/clinica-beleza/AdminProfissionalToggle";
import { entityName } from "@/lib/clinica-beleza-entities";
import { ProfissionaisListView } from "./ProfissionaisListView";
import { useProfissionaisPage } from "./useProfissionaisPage";

export function ProfissionaisPageContent() {
  const {
    slug,
    isNovo,
    editIdParam,
    isFormView,
    voltarLista,
    abrirNovo,
    abrirEditar,
    activeList,
    loading,
    load,
    page,
    setPage,
    totalPages,
    pageSize,
    totalCount,
    horariosProfessional,
    setHorariosProfessional,
    tempoConsultaProfessional,
    setTempoConsultaProfessional,
    exclude,
    toggleProfissional,
  } = useProfissionaisPage();

  if (isFormView) {
    return (
      <ProfissionalFormPageContent
        slug={slug}
        editId={isNovo ? null : editIdParam}
        onDone={() => {
          voltarLista();
          load();
        }}
      />
    );
  }

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Profissionais"
        subtitle="Cadastro de profissionais da clínica"
        newLabel="Novo Profissional"
        onNew={abrirNovo}
      />
      <ClinicaBelezaPageContent>
        <AdminProfissionalToggle onToggled={load} />
        <ProfissionaisListView
          rows={activeList}
          loading={loading}
          page={page}
          totalPages={totalPages}
          pageSize={pageSize}
          totalCount={totalCount ?? 0}
          onPageChange={setPage}
          onEdit={abrirEditar}
          onExclude={exclude}
          onToggleProfissional={toggleProfissional}
          onHorarios={setHorariosProfessional}
          onTempoConsulta={setTempoConsultaProfessional}
        />
      </ClinicaBelezaPageContent>

      {horariosProfessional && (
        <ModalHorariosTrabalho
          professionalId={horariosProfessional.id}
          professionalName={entityName(horariosProfessional)}
          onClose={() => setHorariosProfessional(null)}
          onSaved={() => load()}
        />
      )}

      {tempoConsultaProfessional && (
        <ModalTempoConsulta
          professionalId={tempoConsultaProfessional.id}
          professionalName={entityName(tempoConsultaProfessional)}
          onClose={() => setTempoConsultaProfessional(null)}
          onSaved={() => load()}
        />
      )}
    </>
  );
}
