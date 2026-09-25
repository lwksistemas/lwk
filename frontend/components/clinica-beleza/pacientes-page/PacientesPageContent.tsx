"use client";

/**
 * Cadastro de Clientes - Clínica da Beleza
 * Lista em tela cheia; novo/editar ocupa a página inteira (sem modal).
 */

import { useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Users } from "lucide-react";
import { useClinicaBelezaEntityList } from "@/hooks/clinica-beleza";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { LocalizarClienteButton } from "@/components/clinica-beleza/localizar-cliente/LocalizarClienteButton";
import { LocalizarClienteModal } from "@/components/clinica-beleza/localizar-cliente/LocalizarClienteModal";
import { PacienteCadastroForm } from "./components/PacienteCadastroForm";
import { PacienteListView } from "./components/PacienteListView";
import { useLojaTheme } from "@/hooks/useLojaTheme";
import { useClinicaBelezaFormRouting } from "@/hooks/clinica-beleza/useClinicaBelezaFormRouting";
import { usePacienteForm } from "@/hooks/clinica-beleza/usePacienteForm";
import { usePacientesColunas } from "@/hooks/clinica-beleza/usePacientesColunas";
import { entityActive } from "@/lib/clinica-beleza-entities";
import { buscarPacientesOffline, salvarPacientesOffline } from "@/lib/offline-db";
import { buildProntuarioPacientePath } from "@/components/clinica-beleza/prontuario/prontuario-paths";
import { useClinicaPodeVerConsulta } from "@/hooks/clinica-beleza/useClinicaPodeVerConsulta";
import type { Patient } from "./lib/paciente-form-utils";

type SituacaoClientes = "com_consulta" | "ativos" | "inativos" | "todos";

const SITUACOES_CLIENTES: { id: SituacaoClientes; label: string }[] = [
  { id: "com_consulta", label: "Consulta finalizada" },
  { id: "ativos", label: "Ativos" },
  { id: "inativos", label: "Inativos" },
  { id: "todos", label: "Todos" },
];

export function PacientesPageContent() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;
  const basePath = `/loja/${slug}/clinica-beleza/pacientes`;
  const { theme } = useLojaTheme(slug);
  const [showLocalizar, setShowLocalizar] = useState(false);
  const [situacao, setSituacao] = useState<SituacaoClientes>("com_consulta");
  const queryParams = useMemo(() => ({ situacao }), [situacao]);
  const { podeVerConsulta, loaded: meLoaded } = useClinicaPodeVerConsulta();
  const { colunasKeys } = usePacientesColunas();

  const { isNovo, editIdParam, isFormView, voltarLista, abrirNovo, abrirEditar } =
    useClinicaBelezaFormRouting(basePath);

  const { list, setList, loading, load, page, setPage, totalPages, pageSize, totalCount } =
    useClinicaBelezaEntityList<Patient>({
      path: "/patients/",
      fetchOffline: buscarPacientesOffline,
      saveOffline: salvarPacientesOffline,
      queryParams,
      reloadDeps: [situacao],
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

  const visibleList = list.filter((p) => {
    if (situacao === "todos" || situacao === "com_consulta") return true;
    const ativo = entityActive(p);
    return situacao === "inativos" ? !ativo : ativo;
  });
  const patientId = formState.editing?.id ?? (editIdParam ? Number(editIdParam) : null);
  const podeAbrirProntuario = Boolean(meLoaded && podeVerConsulta && patientId && patientId > 0);

  if (isFormView) {
    return (
      <>
        <ClinicaBelezaStandardPageHeader
          title={formState.editing ? "Editar cliente" : "Novo cliente"}
          subtitle={formState.editing ? undefined : "Cadastro de cliente da clínica"}
          onBack={voltarLista}
          icon={Users}
        />
        <ClinicaBelezaPageContent className="flex flex-col flex-1 min-h-0 !p-0 !bg-[var(--cb-page-bg,#f7f2f4)] dark:!bg-gray-950">
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
            onDelete={formState.editing ? formState.deletePaciente : undefined}
            deleting={formState.deleting}
            accentColor={theme.corPrimaria || CLINICA_BELEZA_PRIMARY}
            lojaSlug={slug}
            patientId={patientId}
            onVerProntuario={
              podeAbrirProntuario
                ? () => router.push(buildProntuarioPacientePath(slug, patientId as number))
                : undefined
            }
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
        beforeLogout={
          <LocalizarClienteButton
            onClick={() => setShowLocalizar(true)}
            title="Localizar cliente para editar"
          />
        }
      />
      <ClinicaBelezaPageContent>
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className="text-sm text-gray-600 dark:text-gray-400">Mostrar</span>
          <div className="inline-flex rounded-lg border border-gray-200 dark:border-neutral-600 overflow-hidden">
            {SITUACOES_CLIENTES.map((opcao) => {
              const selecionado = situacao === opcao.id;
              return (
                <button
                  key={opcao.id}
                  type="button"
                  onClick={() => setSituacao(opcao.id)}
                  className={`px-3 py-1.5 text-sm font-medium ${
                    selecionado
                      ? "text-white"
                      : "bg-white dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700"
                  }`}
                  style={selecionado ? { backgroundColor: theme.corPrimaria || CLINICA_BELEZA_PRIMARY } : undefined}
                >
                  {opcao.label}
                </button>
              );
            })}
          </div>
        </div>
        <PacienteListView
          list={visibleList}
          loading={loading}
          situacao={situacao}
          page={page}
          totalPages={totalPages}
          totalCount={totalCount ?? 0}
          pageSize={pageSize}
          onPageChange={setPage}
          onEdit={(p) => abrirEditar(p.id)}
          colunasVisiveis={colunasKeys}
        />
      </ClinicaBelezaPageContent>
      <LocalizarClienteModal
        open={showLocalizar}
        mode="edit"
        onClose={() => setShowLocalizar(false)}
        onSelectPatient={(p) => abrirEditar(p.id)}
      />
    </>
  );
}
