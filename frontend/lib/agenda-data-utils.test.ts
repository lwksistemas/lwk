import { describe, expect, it } from "vitest";
import {
  agendaEventsEqual,
  formatarAgendaEvento,
  mergeRawAgendaEvent,
  temExpedienteProfissional,
  versaoAgenda,
} from "@/hooks/clinica-beleza/agenda-data/agenda-event-mappers";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";

describe("formatarAgendaEvento", () => {
  it("monta título a partir de paciente e procedimento", () => {
    const ev = formatarAgendaEvento(
      {
        id: 1,
        start: "2026-06-15T10:00:00",
        end: "2026-06-15T11:00:00",
        status: "SCHEDULED",
        patient_name: "Maria",
        procedure_name: "Botox",
      },
      false,
    );
    expect(ev.title).toBe("Maria • Botox");
    expect(ev.id).toBe("1");
  });
});

describe("agendaEventsEqual", () => {
  it("detecta diferença de status", () => {
    const base: AgendaEventData = {
      id: "1",
      title: "A",
      start: "s",
      end: "e",
      backgroundColor: "#fff",
      borderColor: "#000",
      textColor: "#fff",
      extendedProps: { status: "SCHEDULED" },
    };
    const other = { ...base, extendedProps: { status: "COMPLETED" } };
    expect(agendaEventsEqual([base], [other])).toBe(false);
  });

  it("detecta diferença de version após um PATCH", () => {
    const base: AgendaEventData = {
      id: "1",
      title: "A",
      start: "s",
      end: "e",
      backgroundColor: "#fff",
      borderColor: "#000",
      textColor: "#fff",
      extendedProps: { status: "SCHEDULED", version: 4 },
    };
    const other = { ...base, extendedProps: { ...base.extendedProps, version: 5 } };
    expect(agendaEventsEqual([base], [other])).toBe(false);
    expect(agendaEventsEqual([base], [{ ...base, extendedProps: { ...base.extendedProps, version: "4" as unknown as number } }])).toBe(true);
  });
});

describe("mergeRawAgendaEvent", () => {
  it("substitui o agendamento salvo mantendo os demais", () => {
    const next = mergeRawAgendaEvent(
      [
        { id: 1, start: "a", version: 4 },
        { id: 2, start: "b", version: 1 },
      ],
      { id: 1, start: "c", version: 5 },
    );
    expect(next).toEqual([
      { id: 1, start: "c", version: 5 },
      { id: 2, start: "b", version: 1 },
    ]);
  });
});

describe("versaoAgenda", () => {
  it("normaliza number e string", () => {
    expect(versaoAgenda(5)).toBe(5);
    expect(versaoAgenda("5")).toBe(5);
    expect(versaoAgenda(undefined)).toBeUndefined();
  });
});

describe("temExpedienteProfissional", () => {
  it("exige profissional e horário ativo", () => {
    expect(temExpedienteProfissional("3", [{ ativo: true } as never])).toBe(true);
    expect(temExpedienteProfissional("", [{ ativo: true } as never])).toBe(false);
  });
});
