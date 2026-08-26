import { describe, expect, it } from "vitest";
import {
  celulasCalendarioMes,
  colunasProfissionaisDia,
  corProfissionalAgenda,
  eventProfessionalId,
  eventosDoDia,
  eventosDoDiaNaColuna,
  iniciaisProfissional,
  snapMinutos,
} from "@/hooks/clinica-beleza/agenda-data/agenda-dia-colunas-utils";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";

function evt(partial: Partial<AgendaEventData> & { id: string; start: string }): AgendaEventData {
  return {
    title: "A",
    end: partial.end || partial.start,
    backgroundColor: "#fff",
    borderColor: "#000",
    textColor: "#fff",
    extendedProps: {},
    ...partial,
  };
}

describe("iniciaisProfissional", () => {
  it("usa as duas primeiras palavras relevantes", () => {
    expect(iniciaisProfissional("Bruna Tucci Martins")).toBe("BT");
    expect(iniciaisProfissional("Dra. Marina Garcia Ramos")).toBe("MG");
    expect(iniciaisProfissional("Nayara da Silva")).toBe("NS");
  });
});

describe("colunasProfissionaisDia", () => {
  const profs = [
    { id: 1, nome: "Bruna Tucci", especialidade: "Fisioterapia" },
    { id: 2, nome: "Marina Garcia", especialidade: "Dermatologia" },
  ];

  it("mostra todos quando o filtro está vazio", () => {
    expect(colunasProfissionaisDia(profs, "").map((c) => c.id)).toEqual([1, 2]);
  });

  it("filtra um profissional", () => {
    expect(colunasProfissionaisDia(profs, "2").map((c) => c.id)).toEqual([2]);
  });
});

describe("eventosDoDiaNaColuna", () => {
  it("agrupa pelo profissional e pelo dia", () => {
    const lista = [
      evt({
        id: "1",
        start: "2026-08-26T10:00:00-03:00",
        end: "2026-08-26T11:00:00-03:00",
        extendedProps: { professional: 1, patient_name: "Ana" },
      }),
      evt({
        id: "2",
        start: "2026-08-26T11:00:00-03:00",
        extendedProps: { professional: 2 },
      }),
      evt({
        id: "3",
        start: "2026-08-27T10:00:00-03:00",
        extendedProps: { professional: 1 },
      }),
    ];
    expect(eventosDoDiaNaColuna(lista, "2026-08-26", 1).map((x) => x.evt.id)).toEqual(["1"]);
    expect(eventProfessionalId(lista[0])).toBe(1);
  });
});

describe("corProfissionalAgenda / snapMinutos", () => {
  it("é estável por id", () => {
    expect(corProfissionalAgenda(1)).toBe(corProfissionalAgenda(1));
    expect(snapMinutos(17)).toBe(15);
    expect(snapMinutos(18)).toBe(20);
  });
});

describe("eventosDoDia", () => {
  it("lista o dia e ignora intervalo e bloqueio", () => {
    const lista = [
      evt({
        id: "1",
        start: "2026-08-26T09:00:00-03:00",
        extendedProps: { professional: 1, patient_name: "Ana" },
      }),
      evt({
        id: "2",
        start: "2026-08-26T12:00:00-03:00",
        extendedProps: { isIntervalo: true },
      }),
      evt({
        id: "3",
        start: "2026-08-26T18:00:00-03:00",
        extendedProps: { isBloqueio: true },
      }),
      evt({
        id: "4",
        start: "2026-08-27T09:00:00-03:00",
        extendedProps: { professional: 1 },
      }),
    ];
    expect(eventosDoDia(lista, "2026-08-26").map((x) => x.evt.id)).toEqual(["1"]);
  });
});

describe("celulasCalendarioMes", () => {
  it("preenche 6 semanas começando no domingo", () => {
    const cells = celulasCalendarioMes("2026-08-26");
    expect(cells).toHaveLength(42);
    expect(cells[0].iso).toBe("2026-07-26");
    expect(cells.find((c) => c.iso === "2026-08-26")?.inMonth).toBe(true);
  });
});

describe("formatarAgendaEvento / professional", () => {
  it("expõe o id do profissional para as colunas do dia", async () => {
    const { formatarAgendaEvento } = await import(
      "@/hooks/clinica-beleza/agenda-data/agenda-event-mappers"
    );
    const e = formatarAgendaEvento(
      {
        id: 9,
        start: "2026-08-26T10:00:00-03:00",
        patient_name: "Ana",
        professional: 3,
        professional_id: 3,
        status: "SCHEDULED",
      },
      false,
    );
    expect(eventProfessionalId(e)).toBe(3);
  });
});
