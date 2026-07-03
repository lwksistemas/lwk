import { useState } from "react";
import { useParams } from "next/navigation";
import {
  CLINICA_BELEZA_ONLINE_ONLY,
  useClinicaBelezaEntityList,
} from "@/lib/clinica-beleza-crud";
import { useClinicaBelezaFormRouting } from "@/hooks/clinica-beleza/useClinicaBelezaFormRouting";
import type { Campanha } from "./campanhas-page-types";
import { useCampanhasExclusao, useCampanhasForm } from "./useCampanhasForm";

export function useCampanhasPage() {
  const slug = useParams().slug as string;
  const basePath = `/loja/${slug}/clinica-beleza/campanhas`;

  const { isNovo, editId, editIdParam, isFormView, voltarLista, abrirNovo, abrirEditar } =
    useClinicaBelezaFormRouting(basePath);

  const { list, loading, load, page, setPage, totalPages, pageSize, totalCount } =
    useClinicaBelezaEntityList<Campanha>({
      path: "/campanhas/",
      ...CLINICA_BELEZA_ONLINE_ONLY,
    });

  const [enviarCampanha, setEnviarCampanha] = useState<Campanha | null>(null);

  const form = useCampanhasForm({
    isNovo,
    editIdParam,
    editId,
    list,
    voltarLista,
    load,
  });

  const exclusao = useCampanhasExclusao({ editId, voltarLista, load });

  return {
    basePath,
    isFormView,
    loading,
    list,
    page,
    setPage,
    totalPages,
    pageSize,
    totalCount,
    abrirNovo,
    abrirEditar,
    voltarLista,
    load,
    enviarCampanha,
    setEnviarCampanha,
    form,
    exclusao,
  };
}
