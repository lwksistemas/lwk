"use client";

import type { ReactNode } from "react";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import { parseEventDate } from "@/lib/clinica-beleza-datetime";
import {
  ehAgendamentoCliente,
  eventProfessionalId,
  tituloCardAgenda,
} from "./agenda-dia-colunas-utils";

type FcEventLike = {
  id?: string | number;
  title: string;
  start: Date | null;
  end: Date | null;
  extendedProps?: Record<string, unknown>;
};

/** IDs de agendamentos do mesmo profissional com horário sobreposto (só sinal visual). */
export function idsEventosSobrepostosMesmoProf(eventos: AgendaEventData[]): Set<string> {
  const items = eventos.filter((e) => ehAgendamentoCliente(e));
  const out = new Set<string>();
  for (let i = 0; i < items.length; i++) {
    for (let j = i + 1; j < items.length; j++) {
      const a = items[i];
      const b = items[j];
      if (eventProfessionalId(a) !== eventProfessionalId(b)) continue;
      if (eventProfessionalId(a) == null) continue;
      const as = parseEventDate(a.start);
      const ae = parseEventDate(a.end) || as;
      const bs = parseEventDate(b.start);
      const be = parseEventDate(b.end) || bs;
      if (!as || !ae || !bs || !be) continue;
      if (as < be && bs < ae) {
        out.add(String(a.id));
        out.add(String(b.id));
      }
    }
  }
  return out;
}

function nomeCurtoEvento(event: FcEventLike, max = 28): string {
  const p = event.extendedProps || {};
  const raw = tituloCardAgenda({
    id: String(event.id ?? ""),
    title: event.title,
    start: event.start?.toISOString() || "",
    end: event.end?.toISOString() || "",
    backgroundColor: "",
    borderColor: "",
    textColor: "",
    extendedProps: p as AgendaEventData["extendedProps"],
  });
  const t = raw.trim();
  if (t.length <= max) return t;
  return `${t.slice(0, Math.max(1, max - 1))}…`;
}

/** Conteúdo compacto do FullCalendar (Semana/Mês/Dia filtrado). */
export function renderAgendaFcEventContent(arg: {
  event: FcEventLike;
  timeText: string;
  view: { type: string };
}): ReactNode {
  const isMonth = (arg.view?.type || "").startsWith("dayGrid");
  const hora = (arg.timeText || "").trim();
  const nome = nomeCurtoEvento(arg.event, isMonth ? 18 : 26);
  const p = arg.event.extendedProps || {};
  const isBloq = Boolean(p.isBloqueio);
  const isInt = Boolean(p.isIntervalo);

  if (isMonth) {
    return (
      <div className={`agenda-fc-event-inner agenda-fc-event-month${isBloq ? " is-bloqueio" : ""}`}>
        {hora ? <span className="agenda-fc-event-time">{hora}</span> : null}
        <span className="agenda-fc-event-title">{nome}</span>
      </div>
    );
  }

  return (
    <div
      className={`agenda-fc-event-inner${isBloq ? " is-bloqueio" : ""}${isInt ? " is-intervalo" : ""}`}
    >
      {hora ? <div className="agenda-fc-event-time">{hora}</div> : null}
      <div className="agenda-fc-event-title">{nome}</div>
    </div>
  );
}
