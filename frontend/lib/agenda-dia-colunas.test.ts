import { describe, expect, it } from "vitest";
import {
  celulasCalendarioMes,
  clampLarguraColuna,
  clampMinutosInicio,
  colunasProfissionaisDia,
  combinarDiaEHorario,
  corProfissionalAgenda,
  diasSemanaIso,
  duracaoResizeNaGrade,
  eventProfessionalId,
  eventosDoDia,
  eventosDoDiaNaColuna,
  faixasSobrepostas,
  iniciaisProfissional,
  inicioSemanaIso,
  minutosArrastoNaGrade,
  movimentoGradeAlterou,
  snapMinutos,
  toAgendaDiaIso,
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

describe("movimento e resize da grade", () => {
  const base = evt({
    id: "1",
    start: "2026-08-26T08:10:00",
    end: "2026-08-26T09:40:00",
    extendedProps: { professional: 3, duracao_minutos: 90 },
  });

  it("combina o horário com outro dia", () => {
    const origem = new Date(2026, 7, 26, 8, 10);
    const dest = combinarDiaEHorario("2026-08-28", origem);
    expect(toAgendaDiaIso(dest)).toBe("2026-08-28");
    expect(dest.getHours()).toBe(8);
    expect(dest.getMinutes()).toBe(10);
  });

  it("detecta troca de horário ou profissional", () => {
    expect(movimentoGradeAlterou(base, new Date(2026, 7, 26, 8, 10), 3)).toBe(false);
    expect(movimentoGradeAlterou(base, new Date(2026, 7, 26, 10, 0), 3)).toBe(true);
    expect(movimentoGradeAlterou(base, new Date(2026, 7, 26, 8, 10), 1)).toBe(true);
  });

  it("calcula minutos e duração com snap", () => {
    expect(minutosArrastoNaGrade(72, 0, 420, 1.2, 0)).toBe(480);
    expect(duracaoResizeNaGrade(480, 144, 0, 420, 1140, 1.2)).toBe(60);
    expect(clampMinutosInicio(400, 420, 1140, 40)).toBe(420);
  });
});

describe("semana", () => {
  it("começa na segunda e omite domingo", () => {
    expect(inicioSemanaIso("2026-08-26")).toBe("2026-08-24");
    expect(diasSemanaIso("2026-08-26", [0])).toEqual([
      "2026-08-24",
      "2026-08-25",
      "2026-08-26",
      "2026-08-27",
      "2026-08-28",
      "2026-08-29",
    ]);
  });

  it("separa eventos que se sobrepõem em faixas", () => {
    const a = {
      evt: evt({ id: "a", start: "2026-08-26T09:00:00", end: "2026-08-26T10:00:00" }),
      start: new Date(2026, 7, 26, 9, 0),
      end: new Date(2026, 7, 26, 10, 0),
    };
    const b = {
      evt: evt({ id: "b", start: "2026-08-26T09:30:00", end: "2026-08-26T10:30:00" }),
      start: new Date(2026, 7, 26, 9, 30),
      end: new Date(2026, 7, 26, 10, 30),
    };
    const faixas = faixasSobrepostas([a, b]);
    expect(faixas.map((f) => f.lane)).toEqual([0, 1]);
    expect(faixas[0].lanes).toBe(2);
  });
});

describe("clampLarguraColuna", () => {
  it("respeita o mínimo, o máximo e arredonda", () => {
    expect(clampLarguraColuna(80)).toBe(160);
    expect(clampLarguraColuna(900)).toBe(560);
    expect(clampLarguraColuna(280.4)).toBe(280);
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
