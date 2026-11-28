"use client";

import { useEffect, useState } from "react";
import { workHoursRejectionMessage, type HorarioTrabalho } from "@/lib/clinica-beleza-work-hours";
import { isBrowserOffline } from "@/lib/clinica-beleza-offline";
import { buildAppointmentDate } from "./criar-agendamento-builders";
import { verificarDisponibilidadeAgendamento } from "./criar-agendamento-disponibilidade-api";

type Args = {
  open: boolean;
  professionalId: number | "";
  dateInput: string;
  time: string;
  selectedDate: Date | null;
  durationMinutes: number;
  procedureIds: number[];
  localAtendimentoId: number | "";
  horariosProfissional: HorarioTrabalho[];
  setCreateError?: (msg: string) => void;
};

export function useCriarAgendamentoDisponibilidade(args: Args) {
  const {
    open,
    professionalId,
    dateInput,
    time,
    selectedDate,
    durationMinutes,
    procedureIds,
    localAtendimentoId,
    horariosProfissional,
    setCreateError,
  } = args;

  const [disponibilidadeError, setDisponibilidadeError] = useState("");
  const [verificandoDisponibilidade, setVerificandoDisponibilidade] = useState(false);
  const procedureIdsKey = procedureIds.join(",");

  useEffect(() => {
    setCreateError?.("");
    if (!open || !professionalId || !dateInput || !time || durationMinutes <= 0) {
      setDisponibilidadeError("");
      setVerificandoDisponibilidade(false);
      return;
    }

    const date = buildAppointmentDate(dateInput, time, selectedDate);
    if (!date) {
      setDisponibilidadeError("");
      setVerificandoDisponibilidade(false);
      return;
    }

    const horarioMsg = workHoursRejectionMessage(date, durationMinutes, horariosProfissional);
    if (horarioMsg) {
      setDisponibilidadeError(horarioMsg);
      setVerificandoDisponibilidade(false);
      return;
    }

    if (isBrowserOffline()) {
      setDisponibilidadeError("");
      setVerificandoDisponibilidade(false);
      return;
    }

    const ids = procedureIdsKey
      ? procedureIdsKey.split(",").map((id) => Number(id)).filter((id) => id > 0)
      : [];

    let cancelled = false;
    setVerificandoDisponibilidade(true);
    const timer = setTimeout(() => {
      void (async () => {
        try {
          const result = await verificarDisponibilidadeAgendamento({
            professionalId: Number(professionalId),
            date,
            durationMinutes,
            procedureIds: ids,
            localAtendimentoId,
          });
          if (cancelled) return;
          setDisponibilidadeError(result.disponivel ? "" : result.error || "Horário indisponível.");
        } catch {
          if (!cancelled) setDisponibilidadeError("");
        } finally {
          if (!cancelled) setVerificandoDisponibilidade(false);
        }
      })();
    }, 350);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [
    open,
    professionalId,
    dateInput,
    time,
    selectedDate,
    durationMinutes,
    procedureIdsKey,
    localAtendimentoId,
    horariosProfissional,
    setCreateError,
  ]);
  return { disponibilidadeError, verificandoDisponibilidade };
}
