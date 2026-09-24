import { useEffect, useMemo, useState } from "react";
import { clinicaBelezaFetch, parseClinicaBelezaListResponse, parseClinicaBelezaResponseBody } from "@/lib/clinica-beleza-api";
import { useParams } from "next/navigation";
import {
  CLINICA_BELEZA_ONLINE_ONLY,
  useClinicaBelezaEntityList,
} from "@/hooks/clinica-beleza";
import { useClinicaBelezaFormRouting } from "@/hooks/clinica-beleza/useClinicaBelezaFormRouting";
import { useLojaTheme } from "@/hooks/useLojaTheme";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { buildProtocolosListPath } from "./protocolos-page-utils";
import type { Protocol, ProtocoloProdutoOption, ProtocolosPageContentProps } from "./protocolos-page-types";
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
  const [produtos, setProdutos] = useState<ProtocoloProdutoOption[]>([]);
  const [agendando, setAgendando] = useState<Protocol | null>(null);

  useEffect(() => {
    let ativo = true;
    void (async () => {
      const res = await clinicaBelezaFetch("/protocolos/produtos/");
      const dados = await parseClinicaBelezaResponseBody(res);
      if (!ativo) return;
      setProdutos(parseClinicaBelezaListResponse<ProtocoloProdutoOption>(dados));
    })();
    return () => {
      ativo = false;
    };
  }, []);

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
    produtos,
    agendando,
    setAgendando,
    abrirNovo,
    abrirEditar,
    voltarLista,
    form,
  };
}
