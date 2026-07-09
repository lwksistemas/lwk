import { useCallback, type Dispatch, type RefObject, type SetStateAction } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { fetchClinicaSchedulingProfessionals, fetchHistoricoPaciente } from "@/lib/clinica-beleza-cadastros-api";
import { formatApiErrorBody } from "@/lib/api-errors";
import { logger } from "@/lib/logger";
import { consultaEstaConcluida, type Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import type { ConsultaDetailLoaderSlice, FinalizarFormState } from "./consulta-detail-actions-types";
import { valorPagamentoConsulta } from "./consulta-detail-actions-utils";
import type { MemedPrescricaoHandle } from "@/components/clinica-beleza/consultas/MemedPrescricao";

type LifecycleUiSlice = {
  setIniciando: (v: boolean) => void;
  setShowProfessionalModal: (v: boolean) => void;
  setProfissionaisDisponiveis: (p: { id: number; nome?: string; name?: string }[]) => void;
  setShowReceberModal: (v: boolean) => void;
  setRecebendo: (v: boolean) => void;
  setShowFinalizarModal: (v: boolean) => void;
  setFinalizando: (v: boolean) => void;
  setFinalizarForm: Dispatch<SetStateAction<FinalizarFormState>>;
  finalizarForm: FinalizarFormState;
  memedRef: RefObject<MemedPrescricaoHandle | null>;
  memedBusy: boolean;
  setMemedBusy: (v: boolean) => void;
};

export function useConsultaLifecycleHandlers(
  loader: ConsultaDetailLoaderSlice & {
    onBack: () => void;
    onListRefresh: () => void | Promise<void>;
  },
  ui: LifecycleUiSlice,
) {
  const {
    selected,
    setSelected,
    setTab,
    setHistorico,
    loadDetalhes,
    onBack,
    onListRefresh,
  } = loader;

  const {
    setIniciando,
    setShowProfessionalModal,
    setProfissionaisDisponiveis,
    setShowReceberModal,
    setRecebendo,
    setShowFinalizarModal,
    setFinalizando,
    setFinalizarForm,
    finalizarForm,
    memedRef,
    memedBusy,
    setMemedBusy,
  } = ui;

  const iniciarConsulta = useCallback(
    async (professionalId?: number) => {
      if (!selected.professional && !professionalId) {
        try {
          const profs = await fetchClinicaSchedulingProfessionals();
          setProfissionaisDisponiveis(Array.isArray(profs) ? profs : []);
        } catch {
          /* fallback empty */
        }
        setShowProfessionalModal(true);
        return;
      }

      if (!confirm("Iniciar atendimento? A agenda será marcada como Em atendimento.")) return;
      setIniciando(true);
      try {
        const body = professionalId ? { professional: professionalId } : undefined;
        const data = await ClinicaBelezaAPI.consultas.iniciar(selected.id, body);
        setSelected({ ...selected, ...data });
        await onListRefresh();
        const hist = await fetchHistoricoPaciente(selected.patient).catch(() => []);
        setHistorico(Array.isArray(hist) ? (hist as Consulta[]) : []);
      } catch (e: unknown) {
        alert(formatApiErrorBody(e) || "Erro ao iniciar consulta.");
      } finally {
        setIniciando(false);
      }
    },
    [
      onListRefresh,
      selected,
      setHistorico,
      setIniciando,
      setProfissionaisDisponiveis,
      setSelected,
      setShowProfessionalModal,
    ],
  );

  const abrirReceberModal = useCallback(() => {
    setShowReceberModal(true);
  }, [setShowReceberModal]);

  const aposRecebimento = useCallback(
    async (consultaAtualizada: Consulta) => {
      setRecebendo(true);
      try {
        setSelected({ ...selected, ...consultaAtualizada });
        await loadDetalhes(consultaAtualizada);
        await onListRefresh();
        // NÃO fechar o modal aqui — mostra tela de recibo para o usuário imprimir/enviar.
      } finally {
        setRecebendo(false);
      }
    },
    [
      loadDetalhes,
      onListRefresh,
      selected,
      setRecebendo,
      setSelected,
      setShowReceberModal,
    ],
  );

  const abrirFinalizarModal = useCallback(async () => {
    if (!confirm("Finalizar consulta? A agenda será marcada como Concluída.")) return;
    setFinalizando(true);
    try {
      const updated = (await ClinicaBelezaAPI.consultas.finalizar(selected.id, {})) as Consulta & { error?: string };
      if (updated?.error) throw new Error(updated.error);
      const consultaAtualizada = { ...selected, ...updated };
      setSelected(consultaAtualizada);
      setTab("atendimento");
      await loadDetalhes(consultaAtualizada);
      await onListRefresh();
      alert("Consulta finalizada. Agenda marcada como Concluída.");
    } catch (e: unknown) {
      alert(formatApiErrorBody(e) || "Erro ao finalizar consulta.");
    } finally {
      setFinalizando(false);
    }
  }, [selected, setSelected, setTab, loadDetalhes, onListRefresh, setFinalizando]);

  const finalizarConsulta = useCallback(async () => {
    // Mantido para retrocompatibilidade — chamado se o modal ainda estiver aberto
    setFinalizando(true);
    try {
      const updated = (await ClinicaBelezaAPI.consultas.finalizar(selected.id, {})) as Consulta & { error?: string };
      if (updated?.error) throw new Error(updated.error);
      const consultaAtualizada = { ...selected, ...updated };
      setSelected(consultaAtualizada);
      setShowFinalizarModal(false);
      setTab("atendimento");
      await loadDetalhes(consultaAtualizada);
      await onListRefresh();
      alert("Consulta finalizada. Agenda marcada como Concluída.");
    } catch (e: unknown) {
      alert(formatApiErrorBody(e) || "Erro ao finalizar consulta.");
    } finally {
      setFinalizando(false);
    }
  }, [
    loadDetalhes,
    onListRefresh,
    selected,
    setFinalizando,
    setSelected,
    setShowFinalizarModal,
    setTab,
  ]);

  const abrirMemed = useCallback(async () => {
    if (!memedRef.current || memedBusy) return;
    setMemedBusy(true);
    try {
      await memedRef.current.abrir();
    } catch (e: unknown) {
      logger.warn("Erro ao abrir a Memed:", e);
      alert(e instanceof Error ? e.message : "Erro ao abrir a prescrição da Memed.");
    } finally {
      setMemedBusy(false);
    }
  }, [memedBusy, memedRef, setMemedBusy]);

  const excluirConsulta = useCallback(async () => {
    if (consultaEstaConcluida(selected)) {
      alert("Consultas concluídas não podem ser excluídas.");
      return;
    }
    if (!confirm("Excluir esta consulta? O agendamento vinculado será cancelado.")) return;
    try {
      await ClinicaBelezaAPI.consultas.excluir(selected.id);
      await onListRefresh();
      onBack();
    } catch (e: unknown) {
      alert(formatApiErrorBody(e) || "Erro ao excluir consulta.");
    }
  }, [onBack, onListRefresh, selected]);

  return {
    iniciarConsulta,
    abrirReceberModal,
    aposRecebimento,
    abrirFinalizarModal,
    finalizarConsulta,
    abrirMemed,
    excluirConsulta,
  };
}
