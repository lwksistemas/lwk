import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, usePathname, useRouter, useSearchParams } from "next/navigation";
import { buscarProcedimentosOffline, salvarProcedimentosOffline } from "@/lib/offline-db";
import { useClinicaBelezaEntityList } from "@/hooks/clinica-beleza";
import {
  defaultCategoriaForModule,
  procedureCategoriaLabel,
} from "@/lib/clinica-beleza-categories";
import { useClinicaBelezaFormRouting } from "@/hooks/clinica-beleza/useClinicaBelezaFormRouting";
import { useLojaTheme } from "@/hooks/useLojaTheme";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import {
  buildProcedimentoCategoriaCards,
  filterProcedimentosList,
} from "./procedimentos-page-utils";
import type { Procedure } from "./procedimentos-page-types";
import { useProcedimentosForm } from "./useProcedimentosForm";
import { useProcedimentosMatrix } from "./useProcedimentosMatrix";
import type { ProcedimentosPageContentProps } from "./procedimentos-page-types";
import type { ProcedimentoCategoriaCard } from "./ProcedimentosCategoriasGrid";

export type ProcedimentosViewMode = "categorias" | "lista";

export function useProcedimentosPage({
  defaultCategoria = "",
}: Pick<ProcedimentosPageContentProps, "defaultCategoria">) {
  const params = useParams();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const { theme } = useLojaTheme(slug);
  const accentColor = theme.corPrimaria || CLINICA_BELEZA_PRIMARY;

  const { isNovo, editIdParam, isFormView } = useClinicaBelezaFormRouting();

  const moduleKey = defaultCategoria || "";
  const [showAllCategories, setShowAllCategories] = useState(false);
  const [viewMode, setViewMode] = useState<ProcedimentosViewMode>("categorias");
  const [categoriaFilter, setCategoriaFilter] = useState("");

  const presetCategoria =
    categoriaFilter ||
    defaultCategoriaForModule(moduleKey) ||
    defaultCategoria;

  useEffect(() => {
    const cat = searchParams.get("categoria") || "";
    setCategoriaFilter(cat);
    if (cat || searchParams.get("todos") === "1") {
      setViewMode("lista");
    } else if (!searchParams.get("novo") && !searchParams.get("id")) {
      setViewMode("categorias");
    }
  }, [searchParams]);

  const replaceQuery = useCallback(
    (mutate: (qp: URLSearchParams) => void) => {
      const qp = new URLSearchParams(searchParams.toString());
      mutate(qp);
      const qs = qp.toString();
      router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
    },
    [pathname, router, searchParams],
  );

  const setCategoriaFilterAndUrl = useCallback(
    (value: string, opts?: { todos?: boolean }) => {
      setCategoriaFilter(value);
      if (value || opts?.todos) setViewMode("lista");
      replaceQuery((qp) => {
        qp.delete("novo");
        qp.delete("id");
        if (value) {
          qp.set("categoria", value);
          qp.delete("todos");
        } else {
          qp.delete("categoria");
          if (opts?.todos) qp.set("todos", "1");
          else qp.delete("todos");
        }
      });
    },
    [replaceQuery],
  );

  const selecionarCategoria = (cat: ProcedimentoCategoriaCard) => {
    setViewMode("lista");
    setCategoriaFilterAndUrl(cat.value);
  };

  const verTodos = () => {
    setViewMode("lista");
    setCategoriaFilterAndUrl("", { todos: true });
  };

  const voltarCategorias = () => {
    setViewMode("categorias");
    setCategoriaFilterAndUrl("");
  };

  const voltarLista = () => {
    replaceQuery((qp) => {
      qp.delete("novo");
      qp.delete("id");
    });
  };

  const abrirNovo = () => {
    replaceQuery((qp) => {
      qp.delete("id");
      qp.set("novo", "1");
      if (categoriaFilter) qp.set("categoria", categoriaFilter);
    });
  };

  const abrirEditar = (id: number) => {
    replaceQuery((qp) => {
      qp.delete("novo");
      qp.set("id", String(id));
      if (categoriaFilter) qp.set("categoria", categoriaFilter);
    });
  };

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
    viewMode === "lista" ? categoriaFilter : "",
  );

  const categoriaCards = useMemo(
    () => buildProcedimentoCategoriaCards(list, moduleKey && !showAllCategories ? moduleKey : ""),
    [list, moduleKey, showAllCategories],
  );

  const categoriaAtualLabel = categoriaFilter
    ? procedureCategoriaLabel(categoriaFilter) || categoriaFilter
    : "";

  return {
    slug,
    accentColor,
    isFormView,
    moduleKey,
    showAllCategories,
    setShowAllCategories,
    viewMode,
    categoriaFilter,
    categoriaAtualLabel,
    categoriaCards,
    selecionarCategoria,
    verTodos,
    voltarCategorias,
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
