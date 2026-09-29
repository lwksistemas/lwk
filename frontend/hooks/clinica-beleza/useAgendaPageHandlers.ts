"use client";

import { useCallback } from "react";
import { parseEventDate } from "@/lib/clinica-beleza-datetime";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import type { BloqueioHorario } from "@/lib/clinica-beleza-entities";
import {
  type HorarioTrabalho,
  workHoursRejectionMessage,
} from "@/lib/clinica-beleza-work-hours";
import { deveIgnorarClickGradeAgenda } from "@/hooks/clinica-beleza/agenda-data/agenda-dia-colunas-utils";
import {
  type BloqueioSelecionado,
  ehBloqueioDiaInteiro,
  formatarDiaBloqueio,
  serieBloqueioDiaInteiro,
} from "@/lib/bloqueio-serie";
import { useToast } from "@/components/ui/Toast";
import type { DateClickArg } from "@fullcalendar/interaction";
import type { EventClickArg } from "@fullcalendar/core";

export type AgendaEventClickInfo = {
  event: {
    id: string;
    title: string;
    start: Date | null;
    end: Date | null;
    backgroundColor?: string;
    borderColor?: string;
    textColor?: string;
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
  setSelectedBloqueio: (bloqueio: BloqueioSelecionado | null) => void;
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
      const ext = info.event.extendedProps;
      if (ext?.isIntervalo) return;
      if (ext?.isBloqueio) {
        const id = ext.bloqueioId!;
        const serie = serieBloqueioDiaInteiro(bloqueios, id);
        const primeiro = serie[0];
        const ultimo = serie[serie.length - 1];
        setSelectedBloqueio({
          id,
          motivo: ext.motivo || info.event.title,
          professional_name: ext.professional_name || "Todos",
          diaInteiro: ehBloqueioDiaInteiro(
            primeiro?.data_inicio || info.event.start?.toISOString() || "",
            ultimo?.data_fim || info.event.end?.toISOString() || "",
          ),
          idsSerie: serie.map((b) => b.id),
          de: formatarDiaBloqueio(primeiro?.data_inicio || ""),
          ate: formatarDiaBloqueio(ultimo?.data_inicio || ""),
        });
        return;
      }
      setSelectedEvent({
        id: info.event.id,
        title: info.event.title,
        start: info.event.start ? info.event.start.toISOString() : '',
        end: info.event.end ? info.event.end.toISOString() : '',
        backgroundColor: info.event.backgroundColor || "",
        borderColor: info.event.borderColor || "",
        textColor: info.event.textColor || "",
        extendedProps: ext,
      });
      setShowModal(true);
    },
    [bloqueios, setSelectedBloqueio, setSelectedEvent, setShowModal],
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
    (info: DateClickArg) => {
      if (deveIgnorarClickGradeAgenda()) return;
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

  const handleEventClickArg = useCallback(
    (info: EventClickArg) => {
      handleEventClick({
        event: {
          id: info.event.id,
          title: info.event.title,
          start: info.event.start,
          end: info.event.end,
          backgroundColor: info.event.backgroundColor || "",
          borderColor: info.event.borderColor || "",
          textColor: info.event.textColor || "",
          extendedProps: info.event.extendedProps as AgendaEventData["extendedProps"] & {
            isIntervalo?: boolean;
            isBloqueio?: boolean;
            bloqueioId?: number;
            motivo?: string;
            professional_name?: string;
          },
        },
      });
    },
    [handleEventClick],
  );

  return {
    handleEventClick,
    handleEventClickArg,
    abrirEventoDaLista,
    handleDateClick,
  };
}
