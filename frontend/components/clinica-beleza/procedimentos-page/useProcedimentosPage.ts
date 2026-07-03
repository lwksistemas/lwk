import { useState } from "react";
import { useParams } from "next/navigation";
import { buscarProcedimentosOffline, salvarProcedimentosOffline } from "@/lib/offline-db";
import { useClinicaBelezaEntityList } from "@/hooks/clinica-beleza";
import { defaultCategoriaForModule } from "@/lib/clinica-beleza-categories";
import { useClinicaBelezaFormRouting } from "@/hooks/clinica-beleza/useClinicaBelezaFormRouting";
import { useLojaTheme } from "@/hooks/useLojaTheme";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { filterProcedimentosList } from "./procedimentos-page-utils";
import type { Procedure } from "./procedimentos-page-types";
import { useProcedimentosForm } from "./useProcedimentosForm";
import { useProcedimentosMatrix } from "./useProcedimentosMatrix";
import type { ProcedimentosPageContentProps } from "./procedimentos-page-types";

export function useProcedimentosPage({
  defaultCategoria = "",
}: Pick<ProcedimentosPageContentProps, "defaultCategoria">) {
  const params = useParams();
  const slug = params.slug as string;
  const { theme } = useLojaTheme(slug);
  const accentColor = theme.corPrimaria || CLINICA_BELEZA_PRIMARY;

  const { isNovo, editIdParam, isFormView, voltarLista, abrirNovo, abrirEditar } =
    useClinicaBelezaFormRouting();

  const [showAllCategories, setShowAllCategories] = useState(false);
  const moduleKey = defaultCategoria || "";
  const presetCategoria = defaultCategoriaForModule(moduleKey) || defaultCategoria;

  const { list, setList, loading, load, page, setPage, totalPages, pageSize, totalCount } =
    useClinicaBelezaEntityList<Procedure>({
      path: "/procedures/",
      fetchOffline: buscarProcedimentosOffline,
      saveOffline: salvarProcedimentosOffline,
      reloadDeps: [moduleKey, showAllCategories],
    });

  const matrix = useProcedimentosMatrix(list.length);

  const form = useProcedimentosForm({
    isFormView,
    isNovo,
    editIdParam,
    list,
    presetCategoria,
    defaultCategoria,
    convenios: matrix.convenios,
    setList,
    voltarLista,
    load,
    carregarMatrix: matrix.carregarMatrix,
  });

  const { activeList, filteredList, hiddenByCategoryCount } = filterProcedimentosList(
    list,
    moduleKey,
    showAllCategories,
  );

  return {
    slug,
    accentColor,
    isFormView,
    moduleKey,
    showAllCategories,
    setShowAllCategories,
    activeList,
    filteredList,
    hiddenByCategoryCount,
    loading,
    page,
    setPage,
    totalPages,
    pageSize,
    totalCount,
    abrirNovo,
    abrirEditar,
    voltarLista,
    matrix,
    form,
  };
}
