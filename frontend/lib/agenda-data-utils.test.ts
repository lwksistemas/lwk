import { describe, expect, it } from "vitest";
import {
  agendaEventsEqual,
  formatarAgendaEvento,
  temExpedienteProfissional,
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
});

describe("temExpedienteProfissional", () => {
  it("exige profissional e horário ativo", () => {
    expect(temExpedienteProfissional("3", [{ ativo: true } as never])).toBe(true);
    expect(temExpedienteProfissional("", [{ ativo: true } as never])).toBe(false);
  });
});
