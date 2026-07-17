import { useCallback, useEffect, useMemo, useState } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { entityName } from "@/lib/clinica-beleza-entities";
import type { CampanhaResumo, ModoEnvioCampanha, PacienteCampanha } from "./campanha-enviar-modal-types";
import { pacienteCampanhaElegivel } from "./campanha-enviar-modal-types";

interface ToastApi {
  error: (msg: string) => void;
  warning: (msg: string) => void;
  success: (msg: string) => void;
}

interface UseCampanhaEnviarModalParams {
  open: boolean;
  campanha: CampanhaResumo | null;
  onClose: () => void;
  onSent: () => void;
  toast: ToastApi;
}

export function useCampanhaEnviarModal({ open, campanha, onClose, onSent, toast }: UseCampanhaEnviarModalParams) {
  const [mounted, setMounted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [modo, setModo] = useState<ModoEnvioCampanha>("todos");
  const [pacientes, setPacientes] = useState<PacienteCampanha[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [busca, setBusca] = useState("");

  useEffect(() => setMounted(true), []);

  const elegiveis = useMemo(() => pacientes.filter(pacienteCampanhaElegivel), [pacientes]);

  const filtrados = useMemo(() => {
    const q = busca.trim().toLowerCase();
    if (!q) return elegiveis;
    return elegiveis.filter((p) => entityName(p).toLowerCase().includes(q));
  }, [busca, elegiveis]);

  const loadPacientes = useCallback(async () => {
    setLoading(true);
    try {
      const data = await ClinicaBelezaAPI.patients.list({ page_size: 200, active: true });
      const list = Array.isArray(data) ? data : [];
      setPacientes(list);
    } catch (e: unknown) {
      if (e instanceof Error && e.message === "SESSION_ENDED") return;
      toast.error("Não foi possível carregar pacientes para segmentação.");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    if (!open) {
      setModo("todos");
      setSelectedIds([]);
      setBusca("");
      return;
    }
    void loadPacientes();
  }, [open, loadPacientes]);

  const toggleId = useCallback((id: number) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }, []);

  const handleEnviar = useCallback(async () => {
    if (!campanha) return;
    if (modo === "segmentacao" && selectedIds.length === 0) {
      toast.warning("Selecione ao menos um paciente.");
      return;
    }
    setSending(true);
    try {
      const body = modo === "segmentacao" ? { patient_ids: selectedIds } : {};
      const data = (await ClinicaBelezaAPI.campanhas.enviar(campanha.id, body)) as {
        sent?: number;
        message?: string;
        error?: string;
      };
      if (data.sent !== undefined) {
        toast.success(data.message || `Enviado para ${data.sent} paciente(s).`);
        onSent();
        onClose();
      } else {
        toast.error(data.error || "Não foi possível enviar. Verifique o WhatsApp em Configurações.");
      }
    } catch (e: unknown) {
      if (e instanceof Error && e.message === "SESSION_ENDED") return;
      toast.error("Erro ao enviar campanha.");
    } finally {
      setSending(false);
    }
  }, [campanha, modo, onClose, onSent, selectedIds, toast]);

  return {
    mounted,
    loading,
    sending,
    modo,
    setModo,
    selectedIds,
    busca,
    setBusca,
    filtrados,
    elegiveis,
    toggleId,
    handleEnviar,
  };
}
