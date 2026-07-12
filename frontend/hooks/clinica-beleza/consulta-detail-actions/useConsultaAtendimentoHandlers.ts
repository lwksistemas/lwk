import { useCallback, type Dispatch, type SetStateAction } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import type { EvolucaoFormState } from "@/components/clinica-beleza/consultas/tab-panels/tab-panels-types";
import { useToast } from "@/components/ui/Toast";
import { EMPTY_EVOLUCAO_FORM, type ConsultaDetailLoaderSlice } from "./consulta-detail-actions-types";
import type { Protocolo, Consulta } from "@/components/clinica-beleza/consultas/consultas-types";

type AtendimentoUiSlice = {
  setSaving: (v: boolean) => void;
  protocoloPendingId: number | null;
  setProtocoloPreview: (p: Protocolo | null) => void;
  setProtocoloPendingId: (id: number | null) => void;
  setEditAtendimento: (v: boolean) => void;
  setEditAnamnese: (v: boolean) => void;
  setEditEvolucao: (v: boolean) => void;
  evolucaoForm: EvolucaoFormState;
  setEvolucaoForm: Dispatch<SetStateAction<EvolucaoFormState>>;
};

export function useConsultaAtendimentoHandlers(
  loader: ConsultaDetailLoaderSlice & { onListRefresh: () => void | Promise<void> },
  ui: AtendimentoUiSlice,
) {
  const toast = useToast();
  const {
    selected,
    setSelected,
    protocolos,
    anamneseDraft,
    setAnamnese,
    setEvolucoes,
    observacoes,
    observacoesDraft,
    setObservacoes,
    setObservacoesDraft,
    onListRefresh,
  } = loader;

  const {
    setSaving,
    protocoloPendingId,
    setProtocoloPreview,
    setProtocoloPendingId,
    setEditAtendimento,
    setEditAnamnese,
    setEditEvolucao,
    evolucaoForm,
    setEvolucaoForm,
  } = ui;

  const salvarObservacoes = useCallback(async () => {
    setSaving(true);
    try {
      const updated = await ClinicaBelezaAPI.consultas.update(selected.id, {
        observacoes_gerais: observacoesDraft,
      });
      setSelected({ ...selected, ...(updated as Partial<Consulta>) });
      setObservacoes(observacoesDraft);
      setEditAtendimento(false);
      await onListRefresh();
    } catch {
      toast.error("Erro ao salvar atendimento.");
    } finally {
      setSaving(false);
    }
  }, [
    observacoesDraft,
    onListRefresh,
    selected,
    setEditAtendimento,
    setObservacoes,
    setSaving,
    setSelected,
    toast,
  ]);

  const selecionarProtocolo = useCallback(
    (protocolId: number) => {
      const p = protocolos.find((x) => x.id === protocolId);
      if (!p) return;
      setProtocoloPendingId(protocolId);
      setProtocoloPreview(p);
    },
    [protocolos, setProtocoloPendingId, setProtocoloPreview],
  );

  const confirmarProtocolo = useCallback(async () => {
    if (!protocoloPendingId) return;
    setSaving(true);
    try {
      const updated = await ClinicaBelezaAPI.consultas.aplicarProtocolo(
        selected.id,
        protocoloPendingId,
      );
      const notas = (updated as Partial<Consulta>).protocolo_notas || observacoes;
      setSelected({ ...selected, ...(updated as Partial<Consulta>) });
      setObservacoes(notas);
      setObservacoesDraft(notas);
      setProtocoloPreview(null);
      setProtocoloPendingId(null);
      await onListRefresh();
    } catch {
      toast.error("Erro ao aplicar protocolo.");
    } finally {
      setSaving(false);
    }
  }, [
    observacoes,
    onListRefresh,
    protocoloPendingId,
    selected,
    setObservacoes,
    setObservacoesDraft,
    setProtocoloPendingId,
    setProtocoloPreview,
    setSaving,
    setSelected,
    toast,
  ]);

  const salvarAnamnese = useCallback(async () => {
    setSaving(true);
    try {
      const payload: Record<string, unknown> = { ...anamneseDraft };
      for (const key of ["peso", "altura"] as const) {
        if (payload[key] === "" || payload[key] == null) payload[key] = null;
      }
      await ClinicaBelezaAPI.anamnese.save(selected.patient, payload);
      setAnamnese(anamneseDraft);
      setEditAnamnese(false);
    } catch {
      toast.error("Erro ao salvar anamnese.");
    } finally {
      setSaving(false);
    }
  }, [anamneseDraft, selected.patient, setAnamnese, setEditAnamnese, setSaving, toast]);

  const salvarEvolucao = useCallback(async () => {
    if (!evolucaoForm.descricao.trim() && !evolucaoForm.procedimento_realizado.trim()) {
      toast.warning("Preencha a evolução ou o procedimento realizado.");
      return;
    }
    setSaving(true);
    try {
      const payload: Record<string, unknown> = { ...evolucaoForm };
      if (selected.protocolo_notas) payload.protocolo_snapshot = selected.protocolo_notas;
      if (evolucaoForm.satisfacao) payload.satisfacao = Number(evolucaoForm.satisfacao);
      await ClinicaBelezaAPI.consultas.evolucoes.create(selected.id, payload);
      const evol = await ClinicaBelezaAPI.consultas.evolucoes.list(selected.id);
      setEvolucoes(Array.isArray(evol) ? evol : []);
      setEvolucaoForm(EMPTY_EVOLUCAO_FORM);
      setEditEvolucao(false);
    } catch {
      toast.error("Erro ao registrar evolução.");
    } finally {
      setSaving(false);
    }
  }, [
    evolucaoForm,
    selected.id,
    selected.protocolo_notas,
    setEditEvolucao,
    setEvolucaoForm,
    setEvolucoes,
    setSaving,
    toast,
  ]);

  return {
    salvarObservacoes,
    selecionarProtocolo,
    confirmarProtocolo,
    salvarAnamnese,
    salvarEvolucao,
  };
}
