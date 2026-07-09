"use client";

import { useCallback } from "react";
import { parseEventDate } from "@/lib/clinica-beleza-datetime";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import type { BloqueioHorario } from "@/lib/clinica-beleza-entities";
import {
  type HorarioTrabalho,
  workHoursRejectionMessage,
} from "@/lib/clinica-beleza-work-hours";
import { useToast } from "@/components/ui/Toast";

type AgendaEventClickInfo = {
  event: {
    id: string;
    title: string;
    start: Date | null;
    end: Date | null;
    backgroundColor: string;
    borderColor: string;
    textColor: string;
    extendedProps: AgendaEventData["extendedProps"] & {
      isIntervalo?: boolean;
      isBloqueio?: boolean;
      bloqueioId?: number;
      motivo?: string;
      professional_name?: string;
    };
  };
};

export function useAgendaPageHandlers({
  selectedProfessional,
  horariosTrabalho,
  bloqueios,
  setSelectedEvent,
  setShowModal,
  setSelectedBloqueio,
  setSelectedDate,
  setShowCreateModal,
}: {
  selectedProfessional: string;
  horariosTrabalho: HorarioTrabalho[];
  bloqueios: BloqueioHorario[];
  setSelectedEvent: (event: AgendaEventData | null) => void;
  setShowModal: (open: boolean) => void;
  setSelectedBloqueio: (
    bloqueio: { id: number; motivo: string; professional_name: string } | null,
  ) => void;
  setSelectedDate: (date: Date | null) => void;
  setShowCreateModal: (open: boolean) => void;
}) {
  const toast = useToast();

  const conflitoComBloqueio = useCallback(
    (date: Date, durationMin = 30) => {
      const apptEnd = new Date(date.getTime() + durationMin * 60000);
      return bloqueios.some((b) => {
        const profMatch = !b.professional || selectedProfessional === String(b.professional);
        if (!profMatch) return false;
        const bStart = new Date(b.data_inicio);
        const bEnd = new Date(b.data_fim);
        if (Number.isNaN(bStart.getTime()) || Number.isNaN(bEnd.getTime())) return false;
        return date < bEnd && apptEnd > bStart;
      });
    },
    [bloqueios, selectedProfessional],
  );

  const handleEventClick = useCallback(
    (info: AgendaEventClickInfo) => {
      if (info.event.extendedProps?.isIntervalo) return;
      if (info.event.extendedProps?.isBloqueio) {
        setSelectedBloqueio({
          id: info.event.extendedProps.bloqueioId!,
          motivo: info.event.extendedProps.motivo || info.event.title,
          professional_name: info.event.extendedProps.professional_name || "Todos",
        });
        return;
      }
      setSelectedEvent({
        id: info.event.id,
        title: info.event.title,
        start: info.event.start!,
        end: info.event.end!,
        backgroundColor: info.event.backgroundColor,
        borderColor: info.event.borderColor,
        textColor: info.event.textColor,
        extendedProps: info.event.extendedProps,
      });
      setShowModal(true);
    },
    [setSelectedBloqueio, setSelectedEvent, setShowModal],
  );

  const abrirEventoDaLista = useCallback(
    (evt: AgendaEventData) => {
      handleEventClick({
        event: {
          id: evt.id,
          title: evt.title,
          start: parseEventDate(evt.start),
          end: parseEventDate(evt.end),
          backgroundColor: evt.backgroundColor,
          borderColor: evt.borderColor,
          textColor: evt.textColor,
          extendedProps: evt.extendedProps,
        },
      });
    },
    [handleEventClick],
  );

  const handleDateClick = useCallback(
    (info: { date: Date }) => {
      const date = info.date;
      if (selectedProfessional) {
        const msg = workHoursRejectionMessage(date, 30, horariosTrabalho);
        if (msg) {
          toast.warning(msg);
          return;
        }
        if (conflitoComBloqueio(date)) {
          toast.warning(
            'Horário bloqueado. Escolha outro horário ou gerencie bloqueios no botão "Bloquear horário".',
          );
          return;
        }
      }
      setSelectedDate(date);
      setShowCreateModal(true);
    },
    [
      conflitoComBloqueio,
      horariosTrabalho,
      selectedProfessional,
      setSelectedDate,
      setShowCreateModal,
      toast,
    ],
  );

  return {
    handleEventClick,
    abrirEventoDaLista,
    handleDateClick,
  };
}
