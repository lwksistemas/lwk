"use client";

/**
 * Cadastro de Clientes - Clínica da Beleza
 * Lista em tela cheia; novo/editar ocupa a página inteira (sem modal).
 */

import { useParams } from "next/navigation";
import { Users } from "lucide-react";
import {
  deleteClinicaBelezaEntity,
  useClinicaBelezaEntityList,
} from "@/hooks/clinica-beleza";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { useToast } from "@/components/ui/Toast";
import { PacienteCadastroForm } from "./components/PacienteCadastroForm";
import { PacienteListView } from "./components/PacienteListView";
import { useLojaTheme } from "@/hooks/useLojaTheme";
import { useClinicaBelezaFormRouting } from "@/hooks/clinica-beleza/useClinicaBelezaFormRouting";
import { usePacienteForm } from "@/hooks/clinica-beleza/usePacienteForm";
import { entityActive, entityName } from "@/lib/clinica-beleza-entities";
import { buscarPacientesOffline, salvarPacientesOffline } from "@/lib/offline-db";
import type { Patient } from "./lib/paciente-form-utils";

export function PacientesPageContent() {
  const params = useParams();
  const slug = params.slug as string;
  const basePath = `/loja/${slug}/clinica-beleza/pacientes`;
  const { theme } = useLojaTheme(slug);
  const toast = useToast();

  const { isNovo, editIdParam, isFormView, voltarLista, abrirNovo, abrirEditar } =
    useClinicaBelezaFormRouting(basePath);

  const { list, setList, loading, load, page, setPage, totalPages, pageSize, totalCount } =
    useClinicaBelezaEntityList<Patient>({
      path: "/patients/",
      fetchOffline: buscarPacientesOffline,
      saveOffline: salvarPacientesOffline,
    });

  const formState = usePacienteForm({
    isNovo,
    editIdParam,
    isFormView,
    list,
    setList,
    load,
    voltarLista,
  });

  const exclude = async (p: Patient) => {
    if (!confirm(`Desativar o cliente "${entityName(p)}"?`)) return;
    try {
      await deleteClinicaBelezaEntity(`/patients/${p.id}/`);
      load();
    } catch {
      toast.error("Erro ao desativar.");
    }
  };

  const activeList = list.filter((p) => entityActive(p));

  if (isFormView) {
    return (
      <>
        <ClinicaBelezaStandardPageHeader
          title={formState.editing ? "Editar cliente" : "Novo cliente"}
          subtitle={formState.editing ? undefined : "Cadastro de cliente da clínica"}
          onBack={voltarLista}
          icon={Users}
        />
        <ClinicaBelezaPageContent className="flex flex-col flex-1 min-h-0 !p-0 !bg-[#f7f2f4] dark:!bg-gray-950">
          <PacienteCadastroForm
            showHeader={false}
            editing={Boolean(formState.editing)}
            form={formState.form}
            setForm={formState.setForm}
            error={formState.error}
            saving={formState.saving}
            convenios={formState.convenios}
            buscarCepLoading={formState.buscarCepLoading}
            onCepChange={formState.handleCepChange}
            onBuscarCep={formState.handleBuscarCep}
            onSave={formState.save}
            onCancel={voltarLista}
            accentColor={theme.corPrimaria || CLINICA_BELEZA_PRIMARY}
            lojaSlug={slug}
          />
        </ClinicaBelezaPageContent>
      </>
    );
  }

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Clientes"
        subtitle="Cadastro de clientes da clínica"
        newLabel="Novo Cliente"
        onNew={abrirNovo}
        icon={Users}
      />
      <ClinicaBelezaPageContent>
        <PacienteListView
          list={activeList}
          loading={loading}
          page={page}
          totalPages={totalPages}
          totalCount={totalCount ?? 0}
          pageSize={pageSize}
          onPageChange={setPage}
          onEdit={(p) => abrirEditar(p.id)}
          onExclude={exclude}
        />
      </ClinicaBelezaPageContent>
    </>
  );
}
