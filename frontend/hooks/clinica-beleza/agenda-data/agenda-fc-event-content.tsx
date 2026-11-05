"use client";

import type { ReactNode } from "react";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import { parseEventDate } from "@/lib/clinica-beleza-datetime";
import {
  ehAgendamentoCliente,
  eventProfessionalId,
  primeiroNomeProfissional,
  procedimentoCardAgenda,
  tituloCardAgenda,
} from "./agenda-dia-colunas-utils";

type FcEventLike = {
  id?: string | number;
  title: string;
  start: Date | null;
  end: Date | null;
  extendedProps?: Record<string, unknown>;
};

/** Conflito real: mesmo profissional, horários cruzados (sinal vermelho). */
export function idsEventosSobrepostosMesmoProf(eventos: AgendaEventData[]): Set<string> {
  const items = eventos.filter((e) => ehAgendamentoCliente(e));
  const out = new Set<string>();
  for (let i = 0; i < items.length; i++) {
    for (let j = i + 1; j < items.length; j++) {
      const a = items[i];
      const b = items[j];
      const pa = eventProfessionalId(a);
      const pb = eventProfessionalId(b);
      if (pa == null || pb == null || pa !== pb) continue;
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

/**
 * Simultâneos de profissionais diferentes (só quando a grade mostra “todos”).
 * Não é conflito — classe visual distinta do vermelho.
 */
export function idsEventosSimultaneosOutrosProf(eventos: AgendaEventData[]): Set<string> {
  const items = eventos.filter((e) => ehAgendamentoCliente(e));
  const out = new Set<string>();
  for (let i = 0; i < items.length; i++) {
    for (let j = i + 1; j < items.length; j++) {
      const a = items[i];
      const b = items[j];
      const pa = eventProfessionalId(a);
      const pb = eventProfessionalId(b);
      if (pa == null || pb == null || pa === pb) continue;
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

function duracaoMinutos(event: FcEventLike): number {
  if (!event.start || !event.end) return 60;
  return Math.max(0, (event.end.getTime() - event.start.getTime()) / 60000);
}

export function makeAgendaFcEventContent(opts: { showProfessional: boolean }) {
  return function renderAgendaFcEventContent(arg: {
    event: FcEventLike;
    timeText: string;
    view: { type: string };
  }): ReactNode {
    const isMonth = (arg.view?.type || "").startsWith("dayGrid");
    const hora = (arg.timeText || "").trim();
    const p = arg.event.extendedProps || {};
    const isBloq = Boolean(p.isBloqueio);
    const isInt = Boolean(p.isIntervalo);
    const mins = duracaoMinutos(arg.event);
    const compact = !isMonth && mins > 0 && mins <= 25;
    const showProf =
      opts.showProfessional && !isBloq && !isInt && !compact && mins >= 45;
    const nome = nomeCurtoEvento(
      arg.event,
      isMonth ? 16 : 80,
    );
    const procedimento = !isBloq && !isInt
      ? procedimentoCardAgenda({
          id: String(arg.event.id ?? ""),
          title: arg.event.title,
          start: arg.event.start?.toISOString() || "",
          end: arg.event.end?.toISOString() || "",
          backgroundColor: "",
          borderColor: "",
          textColor: "",
          extendedProps: p as AgendaEventData["extendedProps"],
        })
      : "";
    const prof = showProf ? primeiroNomeProfissional(String(p.professional_name || "")) : "";

    if (isMonth) {
      return (
        <div className={`agenda-fc-event-inner agenda-fc-event-month${isBloq ? " is-bloqueio" : ""}`}>
          {hora ? <span className="agenda-fc-event-time">{hora}</span> : null}
          <span className="agenda-fc-event-title">{nome}</span>
        </div>
      );
    }

    if (compact) {
      return (
        <div
          className={`agenda-fc-event-inner is-compact${isBloq ? " is-bloqueio" : ""}${isInt ? " is-intervalo" : ""}`}
          title={procedimento ? `${nome} · ${procedimento}` : nome}
        >
          <span className="agenda-fc-event-line">
            {hora ? <span className="agenda-fc-event-time">{hora}</span> : null}
            <span className="agenda-fc-event-title">{nome}</span>
          </span>
          {procedimento ? <span className="agenda-fc-event-proc">{procedimento}</span> : null}
        </div>
      );
    }

    return (
      <div
        className={`agenda-fc-event-inner${isBloq ? " is-bloqueio" : ""}${isInt ? " is-intervalo" : ""}`}
      >
        {hora ? <div className="agenda-fc-event-time">{hora}</div> : null}
        {prof ? <div className="agenda-fc-event-prof">{prof}</div> : null}
        <div className="agenda-fc-event-title">{nome}</div>
        {procedimento ? <div className="agenda-fc-event-proc" title={procedimento}>{procedimento}</div> : null}
      </div>
    );
  };
}

/** @deprecated use makeAgendaFcEventContent — mantido para imports antigos */
export const renderAgendaFcEventContent = makeAgendaFcEventContent({ showProfessional: false });
