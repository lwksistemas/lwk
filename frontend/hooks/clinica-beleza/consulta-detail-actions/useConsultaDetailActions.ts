"use client";

import { useMemo } from "react";
import type { UseConsultaDetailActionsArgs } from "./consulta-detail-actions-types";
import {
  buildConsultaPrintMeta,
  computeConsultaFlags,
  consultaProcedimentos,
  formatConsultaData,
  valorPagamentoConsulta,
} from "./consulta-detail-actions-utils";
import { useConsultaAtendimentoHandlers } from "./useConsultaAtendimentoHandlers";
import { useConsultaDetailUiState } from "./useConsultaDetailUiState";
import { useConsultaLifecycleHandlers } from "./useConsultaLifecycleHandlers";

export function useConsultaDetailActions(loader: UseConsultaDetailActionsArgs) {
  const {
    selected,
    historico,
    anamnese,
    anamneseDraft,
    setAnamneseDraft,
    observacoes,
    observacoesDraft,
    setObservacoesDraft,
    recarregarPrescricoes,
  } = loader;

  const ui = useConsultaDetailUiState(recarregarPrescricoes);
  const atendimento = useConsultaAtendimentoHandlers(loader, ui);
  const lifecycle = useConsultaLifecycleHandlers(loader, ui);

  const flags = useMemo(() => computeConsultaFlags(selected, historico), [selected, historico]);
  const printMeta = useMemo(() => buildConsultaPrintMeta(selected), [selected]);
  const procedimentosRealizados = useMemo(() => consultaProcedimentos(selected), [selected]);

  return {
    ...ui,
    ...atendimento,
    ...lifecycle,
    ...flags,
    formatData: formatConsultaData,
    printMeta,
    procedimentosRealizados,
    valorPagamentoConsulta,
    anamnese,
    anamneseDraft,
    setAnamneseDraft,
    observacoes,
    observacoesDraft,
    setObservacoesDraft,
  };
}
