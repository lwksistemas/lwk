import { useCallback, useEffect, useState } from "react";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import type { BloqueioProfessional, ModoBloqueioIntervalo } from "./modal-bloqueio-horario-utils";
import {
  TIPOS_BLOQUEIO,
  buildBloqueioRequestBody,
  extractBloqueioApiError,
  formatDateInput,
  formatTimeInput,
  modoSugeridoParaTipo,
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
  const [modo, setModo] = useState<ModoBloqueioIntervalo>("horario");
  const [dataInicioDia, setDataInicioDia] = useState("");
  const [dataFimDia, setDataFimDia] = useState("");
  const [dataHorario, setDataHorario] = useState("");
  const [horaInicio, setHoraInicio] = useState("");
  const [horaFim, setHoraFim] = useState("");
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
    // Default do modal: horário no dia; Férias só muda o modo quando o usuário troca o tipo.
    setModo("horario");
    setMotivoOutro("");
    setProfessionalId(defaultProfessionalId || "");
    setObservacoes("");

    const dia = formatDateInput(base);
    setDataInicioDia(dia);
    setDataFimDia(dia);
    setDataHorario(dia);

    const inicio = new Date(base);
    inicio.setMinutes(0, 0, 0);
    const fim = new Date(inicio);
    fim.setHours(fim.getHours() + 1);
    setHoraInicio(formatTimeInput(inicio));
    setHoraFim(formatTimeInput(fim));
  }, [isOpen, dataInicioSugerida, defaultProfessionalId]);

  const onTipoChange = useCallback((tipo: string) => {
    setTipoSelecionado(tipo);
    setModo(modoSugeridoParaTipo(tipo));
  }, []);

  const salvar = useCallback(async () => {
    const validationError = validateBloqueioForm({
      modo,
      motivoFinal,
      dataInicioDia,
      dataFimDia,
      dataHorario,
      horaInicio,
      horaFim,
    });
    if (validationError) {
      setErro(validationError);
      return;
    }
    setLoading(true);
    setErro("");
    try {
      const body = buildBloqueioRequestBody({
        modo,
        motivo: motivoFinal,
        observacoes,
        professionalId,
        dataInicioDia,
        dataFimDia,
        dataHorario,
        horaInicio,
        horaFim,
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
  }, [
    dataFimDia,
    dataHorario,
    dataInicioDia,
    horaFim,
    horaInicio,
    modo,
    motivoFinal,
    observacoes,
    onClose,
    onSuccess,
    professionalId,
  ]);

  return {
    modo,
    setModo,
    dataInicioDia,
    setDataInicioDia,
    dataFimDia,
    setDataFimDia,
    dataHorario,
    setDataHorario,
    horaInicio,
    setHoraInicio,
    horaFim,
    setHoraFim,
    tipoSelecionado,
    onTipoChange,
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
