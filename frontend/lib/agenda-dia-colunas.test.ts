import { describe, expect, it } from "vitest";
import {
  agendamentoEmAndamento,
  celulasCalendarioMes,
  arrastoMoveuDesdeOrigem,
  clampLarguraColuna,
  snapshotLargurasColunas,
  templateLarguraColuna,
  clampMinutosInicio,
  colunasProfissionaisDia,
  combinarDiaEHorario,
  corProfissionalAgenda,
  diasSemanaIso,
  duracaoResizeNaGrade,
  deveIgnorarClickGradeAgenda,
  marcarIgnorarClickGradeAgenda,
  eventProfessionalId,
  eventosDoDia,
  eventosDoDiaNaColuna,
  faixasSobrepostas,
  iniciaisProfissional,
  inicioSemanaIso,
  horasGradeAgenda,
  minutesToHm,
  minutosArrastoNaGrade,
  movimentoGradeAlterou,
  primeiroNomeProfissional,
  proximosAgendamentosAgenda,
  corBloqueioAgenda,
  estiloCardStatusAgenda,
  familiaBloqueioAgenda,
  rotuloTipoBloqueioAgenda,
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

  it("leva a foto para o cabeçalho da coluna", () => {
    const comFoto = [
      { id: 1, nome: "Bruna Tucci", especialidade: "Esteticista", foto_url: "https://media.example/b.jpg" },
    ];
    expect(colunasProfissionaisDia(comFoto, "")[0].foto_url).toBe("https://media.example/b.jpg");
    expect(colunasProfissionaisDia(profs, "")[0].foto_url).toBeNull();
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
  it("lista o dia incluindo intervalo e bloqueio", () => {
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
    expect(eventosDoDia(lista, "2026-08-26").map((x) => x.evt.id)).toEqual(["1", "2", "3"]);
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

describe("arrasto da duração vs clique fantasma", () => {
  it("soma o deslocamento desde o pointerdown, não entre pointermoves", () => {
    expect(arrastoMoveuDesdeOrigem(100, 100, 102, 102)).toBe(false);
    expect(arrastoMoveuDesdeOrigem(100, 100, 104, 104)).toBe(false);
    expect(arrastoMoveuDesdeOrigem(100, 100, 100, 107)).toBe(true);
    expect(arrastoMoveuDesdeOrigem(100, 200, 100, 160)).toBe(true);
  });

  it("marca a janela em que o slot vazio não deve abrir novo agendamento", () => {
    marcarIgnorarClickGradeAgenda(400);
    expect(deveIgnorarClickGradeAgenda()).toBe(true);
    marcarIgnorarClickGradeAgenda(0);
    expect(deveIgnorarClickGradeAgenda()).toBe(false);
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

describe("templateLarguraColuna", () => {
  it("distribui o espaço enquanto nenhuma coluna foi arrastada", () => {
    expect(templateLarguraColuna(undefined, 280, false)).toBe("minmax(280px, 1fr)");
  });

  it("trava todas em px para o calendário lateral crescer", () => {
    expect(templateLarguraColuna(undefined, 280, true)).toBe("280px");
    expect(templateLarguraColuna(220, 280, true)).toBe("220px");
  });
});

describe("snapshotLargurasColunas", () => {
  it("lê data-agenda-col-id e a largura medida", () => {
    const grid = {
      querySelectorAll: () => [
        { dataset: { agendaColId: "prof-1" }, getBoundingClientRect: () => ({ width: 310.4 }) },
        { dataset: { agendaColId: "prof-2" }, getBoundingClientRect: () => ({ width: 90 }) },
      ],
    } as unknown as HTMLElement;
    expect(snapshotLargurasColunas(grid)).toEqual({ "prof-1": 310, "prof-2": 160 });
    expect(snapshotLargurasColunas(null)).toEqual({});
  });
});

describe("horasGradeAgenda", () => {
  it("mostra 22:00 quando o expediente vai até 22:00, não para no 21:00", () => {
    const horas = horasGradeAgenda(7 * 60, 22 * 60);
    expect(horas[0]).toBe(7 * 60);
    expect(horas.at(-1)).toBe(22 * 60);
    expect(horas).toContain(21 * 60);
    expect(minutesToHm(horas.at(-1)!)).toBe("22:00");
  });
});

describe("proximosAgendamentosAgenda", () => {
  const agora = new Date("2026-08-27T10:45:00-03:00");

  function fila(partial: Partial<AgendaEventData> & { id: string; start: string; end?: string }) {
    return evt({
      end: partial.end || "2026-08-27T11:00:00-03:00",
      extendedProps: { professional: 1, patient_name: "Ana", ...partial.extendedProps },
      ...partial,
    });
  }

  it("na Harmonis às 10h45 mostra o em andamento e os próximos de todos", () => {
    const lista = [
      fila({
        id: "passou",
        start: "2026-08-27T09:00:00-03:00",
        end: "2026-08-27T10:00:00-03:00",
        extendedProps: { professional: 1, patient_name: "Bruna paciente", status: "SCHEDULED" },
      }),
      fila({
        id: "agora",
        start: "2026-08-27T10:00:00-03:00",
        end: "2026-08-27T11:00:00-03:00",
        extendedProps: {
          professional: 3,
          patient_name: "Patrícia G. De Barros Martins",
          procedure_name: "Eletroestimulação",
          professional_name: "Dra. Nayara da Silva de Souza",
          status: "CLIENT_CONFIRMED",
        },
      }),
      fila({
        id: "tarde",
        start: "2026-08-27T14:30:00-03:00",
        end: "2026-08-27T15:10:00-03:00",
        extendedProps: {
          professional: 2,
          patient_name: "Maria Antonia da Cunha Carvalho",
          professional_name: "Dra. Marina Garcia Ramos",
          status: "CLIENT_CONFIRMED",
        },
      }),
      fila({
        id: "almoco",
        start: "2026-08-27T12:00:00-03:00",
        end: "2026-08-27T13:00:00-03:00",
        extendedProps: { isIntervalo: true },
      }),
      fila({
        id: "cancelado",
        start: "2026-08-27T16:00:00-03:00",
        end: "2026-08-27T16:40:00-03:00",
        extendedProps: { professional: 2, status: "CANCELLED" },
      }),
    ];
    const ids = proximosAgendamentosAgenda(lista, "2026-08-27", agora, "").map((x) => x.evt.id);
    expect(ids).toEqual(["agora", "tarde"]);
    expect(
      agendamentoEmAndamento(
        {
          evt: lista[1],
          start: new Date("2026-08-27T10:00:00-03:00"),
          end: new Date("2026-08-27T11:00:00-03:00"),
        },
        agora,
      ),
    ).toBe(true);
  });

  it("respeita o filtro de um profissional", () => {
    const lista = [
      fila({
        id: "n1",
        start: "2026-08-27T14:00:00-03:00",
        end: "2026-08-27T15:00:00-03:00",
        extendedProps: { professional: 3, status: "SCHEDULED" },
      }),
      fila({
        id: "m1",
        start: "2026-08-27T14:30:00-03:00",
        end: "2026-08-27T15:10:00-03:00",
        extendedProps: { professional: 2, status: "SCHEDULED" },
      }),
    ];
    expect(proximosAgendamentosAgenda(lista, "2026-08-27", agora, "2").map((x) => x.evt.id)).toEqual([
      "m1",
    ]);
  });

  it("em outro dia lista a fila inteira, sem cortar pelo relógio", () => {
    const lista = [
      fila({
        id: "cedo",
        start: "2026-08-28T08:00:00-03:00",
        end: "2026-08-28T09:00:00-03:00",
        extendedProps: { professional: 1, status: "SCHEDULED" },
      }),
    ];
    expect(proximosAgendamentosAgenda(lista, "2026-08-28", agora, "").map((x) => x.evt.id)).toEqual([
      "cedo",
    ]);
  });

  it("primeiro nome ignora Dr/Dra", () => {
    expect(primeiroNomeProfissional("Dra. Nayara da Silva de Souza")).toBe("Nayara");
    expect(primeiroNomeProfissional("Bruna Tucci Martins")).toBe("Bruna");
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

describe("visual do bloqueio", () => {
  it("não usa o roxo do Aguardando e listra o fundo", () => {
    expect(familiaBloqueioAgenda("REUNIÃO VÍDEOMAKER")).toBe("reuniao");
    expect(familiaBloqueioAgenda("Férias do profissional")).toBe("ferias");
    expect(rotuloTipoBloqueioAgenda("REUNIÃO VÍDEOMAKER")).toBe("Reunião");
    expect(corBloqueioAgenda("REUNIÃO")).not.toBe("#a855f7");
    expect(corBloqueioAgenda("REUNIÃO")).not.toBe("#4f46e5");
    const estilo = estiloCardStatusAgenda(
      evt({
        id: "b1",
        start: "2026-08-27T16:00:00-03:00",
        extendedProps: { isBloqueio: true, motivo: "REUNIÃO VÍDEOMAKER" },
      }),
    );
    expect(estilo.borderLeft).toContain("dashed");
    expect(estilo.backgroundImage).toContain("repeating-linear-gradient");
    const aguardando = estiloCardStatusAgenda(
      evt({
        id: "a1",
        start: "2026-08-27T16:30:00-03:00",
        backgroundColor: "#a855f7",
        extendedProps: { status: "SCHEDULED", patient_name: "Tania" },
      }),
    );
    expect(aguardando.borderLeft).toContain("solid");
    expect(aguardando.backgroundImage).toBeUndefined();
    expect(estilo.cor).not.toBe(aguardando.cor);
  });
});
