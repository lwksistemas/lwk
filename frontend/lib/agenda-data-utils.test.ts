import { describe, expect, it } from "vitest";
import {
  agendaEventsEqual,
  agendaGradeAindaCarregando,
  aplicarHorarioAgendaEvento,
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

  it("repassa a categoria dos procedimentos da agenda", () => {
    const ev = formatarAgendaEvento(
      {
        id: 2,
        start: "2026-08-31T16:00:00",
        end: "2026-08-31T16:35:00",
        status: "CONFIRMED",
        patient_name: "Luiz",
        procedure_name: "Botox",
        procedures_list: [{ id: 8, nome: "BOTOX — TESTA E GLABELA", categoria: "injetavel" }],
      },
      false,
    );
    expect(ev.extendedProps.procedures_list).toEqual([
      { id: 8, nome: "BOTOX — TESTA E GLABELA", categoria: "injetavel" },
    ]);
    expect(ev.extendedProps.patient).toBeUndefined();
  });

  it("repassa o id do paciente para abrir o prontuário", () => {
    const ev = formatarAgendaEvento(
      {
        id: 3,
        start: "2026-08-31T16:00:00",
        end: "2026-08-31T16:35:00",
        status: "CONFIRMED",
        patient: 9,
        patient_name: "Marcia",
      },
      false,
    );
    expect(ev.extendedProps.patient).toBe(9);
  });

  it("calcula o fim pela duração para não misturar fuso de start/end", () => {
    const ev = formatarAgendaEvento(
      {
        id: 82,
        start: "2026-08-27T16:20:00-03:00",
        end: "2026-08-27T20:25:00+00:00",
        status: "SCHEDULED",
        duracao_minutos: 65,
        patient_name: "Luiz",
        procedure_name: "Drenagem",
      },
      false,
    );
    const inicio = new Date(ev.start).getTime();
    const fim = new Date(ev.end).getTime();
    expect(Math.round((fim - inicio) / 60000)).toBe(65);
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

describe("aplicarHorarioAgendaEvento", () => {
  it("atualiza start/end só do evento arrastado", () => {
    const base: AgendaEventData = {
      id: "1",
      title: "A",
      start: "s1",
      end: "e1",
      backgroundColor: "#fff",
      borderColor: "#000",
      textColor: "#fff",
      extendedProps: { status: "SCHEDULED" },
    };
    const other = { ...base, id: "2", start: "s2", end: "e2" };
    const next = aplicarHorarioAgendaEvento([base, other], "1", "s3", "e3");
    expect(next[0].start).toBe("s3");
    expect(next[0].end).toBe("e3");
    expect(next[1].start).toBe("s2");
  });
});

describe("versaoAgenda", () => {
  it("normaliza number e string", () => {
    expect(versaoAgenda(5)).toBe(5);
    expect(versaoAgenda("5")).toBe(5);
    expect(versaoAgenda(undefined)).toBeUndefined();
  });
});

describe("agendaGradeAindaCarregando", () => {
  it("não espera o catálogo de procedimentos para mostrar a grade", () => {
    expect(
      agendaGradeAindaCarregando({
        isOnline: true,
        offlineLoading: false,
        professionalsLoading: false,
        eventsLoading: false,
        eventosCount: 0,
      }),
    ).toBe(false);
    expect(
      agendaGradeAindaCarregando({
        isOnline: true,
        offlineLoading: false,
        professionalsLoading: false,
        eventsLoading: true,
        eventosCount: 0,
      }),
    ).toBe(true);
    expect(
      agendaGradeAindaCarregando({
        isOnline: true,
        offlineLoading: false,
        professionalsLoading: false,
        eventsLoading: true,
        eventosCount: 3,
      }),
    ).toBe(false);
  });
});

describe("temExpedienteProfissional", () => {
  it("exige profissional e horário ativo", () => {
    expect(temExpedienteProfissional("3", [{ ativo: true } as never])).toBe(true);
    expect(temExpedienteProfissional("", [{ ativo: true } as never])).toBe(false);
  });
});
