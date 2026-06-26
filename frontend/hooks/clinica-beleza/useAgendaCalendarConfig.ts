"use client";

import { useMemo } from "react";
import type { HorarioTrabalhoRow } from "@/lib/clinica-beleza-entities";
import {
  businessHoursFromHorarios,
  type HorarioTrabalho,
} from "@/lib/clinica-beleza-work-hours";

export function useAgendaCalendarConfig(
  selectedProfessional: string,
  horariosTrabalho: HorarioTrabalhoRow[],
) {
  const temHorarioExpediente = Boolean(
    selectedProfessional && horariosTrabalho.some((h) => h.ativo),
  );

  const businessHours = useMemo(
    () => businessHoursFromHorarios(horariosTrabalho as HorarioTrabalho[]),
    [horariosTrabalho],
  );

  const hiddenDays = useMemo(() => {
    if (!selectedProfessional || horariosTrabalho.length === 0) return [0];
    const diasAtivos = horariosTrabalho
      .filter((h) => h.ativo)
      .map((h) => (h.dia_semana === 6 ? 0 : h.dia_semana + 1));
    return [0, 1, 2, 3, 4, 5, 6].filter((d) => !diasAtivos.includes(d));
  }, [selectedProfessional, horariosTrabalho]);

  const slotMinTime = useMemo(() => {
    if (!selectedProfessional || horariosTrabalho.length === 0) return "07:00:00";
    const ativos = horariosTrabalho.filter((h) => h.ativo);
    if (!ativos.length) return "07:00:00";
    return (
      ativos.reduce((min, h) => {
        const t = (h.hora_entrada || "07:00").slice(0, 5);
        return t < min ? t : min;
      }, "23:59") + ":00"
    );
  }, [selectedProfessional, horariosTrabalho]);

  const slotMaxTime = useMemo(() => {
    if (!selectedProfessional || horariosTrabalho.length === 0) return "20:00:00";
    const ativos = horariosTrabalho.filter((h) => h.ativo);
    if (!ativos.length) return "20:00:00";
    return (
      ativos.reduce((max, h) => {
        const t = (h.hora_saida || "20:00").slice(0, 5);
        return t > max ? t : max;
      }, "00:00") + ":00"
    );
  }, [selectedProfessional, horariosTrabalho]);

  return {
    temHorarioExpediente,
    businessHours,
    hiddenDays,
    slotMinTime,
    slotMaxTime,
  };
}
