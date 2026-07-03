import { useCallback, useEffect, useRef, useState } from "react";
import { ClinicaBelezaAPI, type LocalAtendimentoItem } from "@/lib/clinica-beleza-api";
import type { MemedPrescricaoHandle } from "@/components/clinica-beleza/consultas/MemedPrescricao";
import { logger } from "@/lib/logger";
import {
  EMPTY_EVOLUCAO_FORM,
  type FinalizarFormState,
} from "./consulta-detail-actions-types";
import type { Protocolo } from "@/components/clinica-beleza/consultas/consultas-types";

export function useConsultaDetailUiState(recarregarPrescricoesBase: () => Promise<void>) {
  const [saving, setSaving] = useState(false);
  const [editAtendimento, setEditAtendimento] = useState(false);
  const [editAnamnese, setEditAnamnese] = useState(false);
  const [editEvolucao, setEditEvolucao] = useState(false);
  const [protocoloPreview, setProtocoloPreview] = useState<Protocolo | null>(null);
  const [protocoloPendingId, setProtocoloPendingId] = useState<number | null>(null);
  const [showFinalizarModal, setShowFinalizarModal] = useState(false);
  const [finalizando, setFinalizando] = useState(false);
  const [iniciando, setIniciando] = useState(false);
  const [showProfessionalModal, setShowProfessionalModal] = useState(false);
  const [profissionaisDisponiveis, setProfissionaisDisponiveis] = useState<
    { id: number; nome?: string; name?: string }[]
  >([]);
  const [memedBusy, setMemedBusy] = useState(false);
  const [locaisAtendimento, setLocaisAtendimento] = useState<LocalAtendimentoItem[]>([]);
  const [finalizarForm, setFinalizarForm] = useState<FinalizarFormState>({
    payment_method: "CASH",
    mark_as_paid: false,
    amount: "",
    local_atendimento: "",
  });
  const [prescricoesRefresh, setPrescricoesRefresh] = useState(0);
  const [evolucaoForm, setEvolucaoForm] = useState(EMPTY_EVOLUCAO_FORM);

  const memedRef = useRef<MemedPrescricaoHandle>(null);

  const recarregarPrescricoes = useCallback(async () => {
    await recarregarPrescricoesBase();
    setPrescricoesRefresh((n) => n + 1);
  }, [recarregarPrescricoesBase]);

  useEffect(() => {
    ClinicaBelezaAPI.locaisAtendimento
      .list()
      .then(setLocaisAtendimento)
      .catch((e) => logger.warn("Erro ao carregar locais de atendimento:", e));
  }, []);

  const resetEditsOnLoad = () => {
    setEditAtendimento(false);
    setEditAnamnese(false);
    setEditEvolucao(false);
    setProtocoloPreview(null);
    setProtocoloPendingId(null);
  };

  return {
    saving,
    setSaving,
    editAtendimento,
    setEditAtendimento,
    editAnamnese,
    setEditAnamnese,
    editEvolucao,
    setEditEvolucao,
    protocoloPreview,
    setProtocoloPreview,
    protocoloPendingId,
    setProtocoloPendingId,
    showFinalizarModal,
    setShowFinalizarModal,
    finalizando,
    setFinalizando,
    iniciando,
    setIniciando,
    showProfessionalModal,
    setShowProfessionalModal,
    profissionaisDisponiveis,
    setProfissionaisDisponiveis,
    memedBusy,
    setMemedBusy,
    memedRef,
    locaisAtendimento,
    finalizarForm,
    setFinalizarForm,
    prescricoesRefresh,
    evolucaoForm,
    setEvolucaoForm,
    recarregarPrescricoes,
    resetEditsOnLoad,
  };
}
