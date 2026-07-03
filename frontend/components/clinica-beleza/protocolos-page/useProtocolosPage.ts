import { useMemo } from "react";
import { useParams } from "next/navigation";
import {
  CLINICA_BELEZA_ONLINE_ONLY,
  useClinicaBelezaEntityList,
} from "@/hooks/clinica-beleza";
import { useClinicaBelezaFormRouting } from "@/hooks/clinica-beleza/useClinicaBelezaFormRouting";
import { useLojaTheme } from "@/hooks/useLojaTheme";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { buildProtocolosListPath } from "./protocolos-page-utils";
import type { Protocol, ProtocolosPageContentProps } from "./protocolos-page-types";
import { useProtocolosForm } from "./useProtocolosForm";
import { useProtocolosProcedures } from "./useProtocolosProcedures";

export function useProtocolosPage({
  defaultCategoria = "",
}: Pick<ProtocolosPageContentProps, "defaultCategoria">) {
  const params = useParams();
  const slug = params.slug as string;
  const { theme } = useLojaTheme(slug);
  const accentColor = theme.corPrimaria || CLINICA_BELEZA_PRIMARY;

  const { isNovo, editIdParam, isFormView, voltarLista, abrirNovo, abrirEditar } =
    useClinicaBelezaFormRouting();

  const protocolosPath = useMemo(
    () => buildProtocolosListPath(defaultCategoria),
    [defaultCategoria],
  );

  const { list, loading, load, page, setPage, totalPages, pageSize, totalCount } =
    useClinicaBelezaEntityList<Protocol>({
      path: protocolosPath,
      ...CLINICA_BELEZA_ONLINE_ONLY,
      reloadDeps: [defaultCategoria],
    });

  const { procedures } = useProtocolosProcedures(defaultCategoria);

  const form = useProtocolosForm({
    isFormView,
    isNovo,
    editIdParam,
    list,
    voltarLista,
    load,
  });

  return {
    slug,
    accentColor,
    isFormView,
    loading,
    list,
    page,
    setPage,
    totalPages,
    pageSize,
    totalCount,
    procedures,
    abrirNovo,
    abrirEditar,
    voltarLista,
    form,
  };
}
