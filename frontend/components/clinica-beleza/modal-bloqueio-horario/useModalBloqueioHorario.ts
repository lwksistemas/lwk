import { useCallback, useEffect, useState } from "react";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { formatDateTimeLocal } from "@/lib/clinica-beleza-datetime";
import type { BloqueioProfessional } from "./modal-bloqueio-horario-utils";
import {
  TIPOS_BLOQUEIO,
  buildBloqueioRequestBody,
  extractBloqueioApiError,
  resolveMotivoBloqueio,
  validateBloqueioForm,
} from "./modal-bloqueio-horario-utils";

interface UseModalBloqueioHorarioParams {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  dataInicioSugerida?: Date | null;
  defaultProfessionalId?: string;
}

export function useModalBloqueioHorario({
  isOpen,
  onClose,
  onSuccess,
  dataInicioSugerida,
  defaultProfessionalId,
}: UseModalBloqueioHorarioParams) {
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");
  const [tipoSelecionado, setTipoSelecionado] = useState<string>(TIPOS_BLOQUEIO[0].value);
  const [motivoOutro, setMotivoOutro] = useState("");
  const [professionalId, setProfessionalId] = useState<string>("");
  const [observacoes, setObservacoes] = useState("");
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");

  const motivoFinal = resolveMotivoBloqueio(tipoSelecionado, motivoOutro);

  useEffect(() => {
    if (!isOpen) return;
    setErro("");
    const now = new Date();
    const base = dataInicioSugerida || now;
    setTipoSelecionado(TIPOS_BLOQUEIO[0].value);
    setMotivoOutro("");
    setProfessionalId(defaultProfessionalId || "");
    setObservacoes("");
    const inicio = new Date(base);
    inicio.setMinutes(0, 0, 0);
    const fim = new Date(inicio);
    fim.setHours(fim.getHours() + 1);
    setDataInicio(formatDateTimeLocal(inicio));
    setDataFim(formatDateTimeLocal(fim));
  }, [isOpen, dataInicioSugerida, defaultProfessionalId]);

  const salvar = useCallback(async () => {
    const validationError = validateBloqueioForm(dataInicio, dataFim, motivoFinal);
    if (validationError) {
      setErro(validationError);
      return;
    }
    setLoading(true);
    setErro("");
    try {
      const body = buildBloqueioRequestBody({
        dataInicio,
        dataFim,
        motivo: motivoFinal,
        observacoes,
        professionalId,
      });
      const res = await clinicaBelezaFetch("/bloqueios/", {
        method: "POST",
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(extractBloqueioApiError(data, res.status));
      }
      onSuccess();
      onClose();
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : "Erro ao criar bloqueio.");
    } finally {
      setLoading(false);
    }
  }, [dataFim, dataInicio, motivoFinal, observacoes, onClose, onSuccess, professionalId]);

  return {
    dataInicio,
    setDataInicio,
    dataFim,
    setDataFim,
    tipoSelecionado,
    setTipoSelecionado,
    motivoOutro,
    setMotivoOutro,
    professionalId,
    setProfessionalId,
    observacoes,
    setObservacoes,
    loading,
    erro,
    salvar,
  };
}

export type { BloqueioProfessional };
