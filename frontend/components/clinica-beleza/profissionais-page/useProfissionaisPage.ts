import { useCallback, useState } from "react";
import { useParams } from "next/navigation";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { deleteClinicaBelezaEntity, useClinicaBelezaEntityList } from "@/hooks/clinica-beleza";
import { useClinicaBelezaFormRouting } from "@/hooks/clinica-beleza/useClinicaBelezaFormRouting";
import { entityActive, entityName, type ClinicaProfessional } from "@/lib/clinica-beleza-entities";
import { buscarProfissionaisOffline, salvarProfissionaisOffline } from "@/lib/offline-db";
import { useToast } from "@/components/ui/Toast";
import { buildProfissionaisBasePath, extractProfissionalToggleError } from "./profissionais-page-utils";

export function useProfissionaisPage() {
  const toast = useToast();
  const slug = useParams().slug as string;
  const basePath = buildProfissionaisBasePath(slug);
  const { isNovo, editIdParam, isFormView, voltarLista, abrirNovo, abrirEditar } =
    useClinicaBelezaFormRouting(basePath);

  const { list, loading, load, page, setPage, totalPages, pageSize, totalCount } =
    useClinicaBelezaEntityList<ClinicaProfessional>({
      path: "/professionals/",
      fetchOffline: buscarProfissionaisOffline,
      saveOffline: salvarProfissionaisOffline,
    });

  const [horariosProfessional, setHorariosProfessional] = useState<ClinicaProfessional | null>(null);
  const [tempoConsultaProfessional, setTempoConsultaProfessional] = useState<ClinicaProfessional | null>(
    null,
  );

  const exclude = useCallback(
    async (p: ClinicaProfessional) => {
      if (!confirm(`Desativar o profissional "${entityName(p)}"?`)) return;
      try {
        await deleteClinicaBelezaEntity(`/professionals/${p.id}/`);
        load();
      } catch {
        toast.error("Erro ao desativar.");
      }
    },
    [load, toast],
  );

  const toggleProfissional = useCallback(
    async (p: ClinicaProfessional) => {
      const novoValor = !(p.is_profissional ?? true);
      try {
        await ClinicaBelezaAPI.patch(`/professionals/${p.id}/`, { is_profissional: novoValor });
        load();
      } catch (err: unknown) {
        toast.error(extractProfissionalToggleError(err));
      }
    },
    [load, toast],
  );

  const activeList = list.filter((p) => entityActive(p));

  return {
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
  };
}
