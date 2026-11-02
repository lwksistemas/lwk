import { describe, expect, it } from "vitest";
import {
  buildBloqueioRequestBody,
  buildBloqueiosHorarioPorDia,
  buildBloqueiosPorDia,
  enumerarDiasDaSemana,
  enumerarDiasInclusivo,
  extractBloqueioApiError,
  modoSugeridoParaTipo,
  resolveMotivoBloqueio,
  rotuloDiasSelecionados,
  selecionarSomenteMes,
  removerDiasDoMes,
  toggleDiaIso,
  validateBloqueioForm,
  weekdaySegundaZero,
} from "@/components/clinica-beleza/modal-bloqueio-horario/modal-bloqueio-horario-utils";

describe("resolveMotivoBloqueio", () => {
  it("usa tipo, outro ou fallback", () => {
    expect(resolveMotivoBloqueio("Manutenção", "")).toBe("Manutenção");
    expect(resolveMotivoBloqueio("", "Reunião")).toBe("Reunião");
    expect(resolveMotivoBloqueio("", "")).toBe("Bloqueio");
  });
});

describe("diasDoMes", () => {
  it("marca outubro inteiro e limpa só esse mês", () => {
    const outubro = selecionarSomenteMes("2026-10-01");
    expect(outubro).toHaveLength(31);
    expect(outubro[0]).toBe("2026-10-01");
    expect(outubro[30]).toBe("2026-10-31");
    expect(rotuloDiasSelecionados(outubro)).toContain("Outubro de 2026");
    expect(rotuloDiasSelecionados(outubro)).toContain("(31 dias)");
    expect(removerDiasDoMes(["2026-09-29", ...outubro], "2026-10-01")).toEqual(["2026-09-29"]);
  });
});

describe("modoSugeridoParaTipo", () => {
  it("sugere dias para férias e horario para os demais", () => {
    expect(modoSugeridoParaTipo("Férias do profissional")).toBe("dias");
    expect(modoSugeridoParaTipo("Manutenção")).toBe("horario");
    expect(modoSugeridoParaTipo("")).toBe("horario");
  });
});

describe("validateBloqueioForm", () => {
  it("valida modo dias", () => {
    expect(
      validateBloqueioForm({
        modo: "dias",
        motivoFinal: "Férias",
        dataInicioDia: "",
        dataFimDia: "2026-07-25",
      }),
    ).toContain("data");
    expect(
      validateBloqueioForm({
        modo: "dias",
        motivoFinal: "Férias",
        dataInicioDia: "2026-07-25",
        dataFimDia: "2026-07-17",
      }),
    ).toContain("depois");
    expect(
      validateBloqueioForm({
        modo: "dias",
        motivoFinal: "Férias",
        dataInicioDia: "2026-07-17",
        dataFimDia: "2026-07-25",
      }),
    ).toBeNull();
    expect(
      validateBloqueioForm({
        modo: "dias",
        motivoFinal: "Férias",
        dataInicioDia: "2026-07-17",
        dataFimDia: "2026-07-17",
      }),
    ).toBeNull();
    expect(
      validateBloqueioForm({
        modo: "dias",
        motivoFinal: "Férias",
        diasSelecionados: [],
      }),
    ).toContain("calendário");
    expect(
      validateBloqueioForm({
        modo: "dias",
        motivoFinal: "Férias",
        diasSelecionados: ["2026-09-03", "2026-09-22"],
      }),
    ).toBeNull();
  });

  it("valida modo horario", () => {
    expect(
      validateBloqueioForm({
        modo: "horario",
        motivoFinal: "x",
        dataHorario: "2026-07-25",
        horaInicio: "13:00",
        horaFim: "12:00",
      }),
    ).toContain("depois");
    expect(
      validateBloqueioForm({
        modo: "horario",
        motivoFinal: "  ",
        dataHorario: "2026-07-25",
        horaInicio: "13:00",
        horaFim: "17:00",
      }),
    ).toContain("motivo");
    expect(
      validateBloqueioForm({
        modo: "horario",
        motivoFinal: "OK",
        dataHorario: "2026-07-25",
        horaInicio: "13:00",
        horaFim: "17:00",
      }),
    ).toBeNull();
  });
});

describe("buildBloqueioRequestBody", () => {
  it("modo dias envia dia_inteiro e datas", () => {
    const body = buildBloqueioRequestBody({
      modo: "dias",
      dataInicioDia: "2026-07-17",
      dataFimDia: "2026-07-25",
      motivo: "Férias",
      observacoes: " obs ",
      professionalId: "5",
    });
    expect(body.motivo).toBe("Férias");
    expect(body.professional).toBe(5);
    expect(body.observacoes).toBe("obs");
    expect(body.dia_inteiro).toBe(true);
    expect(typeof body.data_inicio).toBe("string");
    expect(typeof body.data_fim).toBe("string");
  });

  it("modo horario envia intervalo no mesmo dia sem dia_inteiro", () => {
    const body = buildBloqueioRequestBody({
      modo: "horario",
      dataHorario: "2026-07-25",
      horaInicio: "13:00",
      horaFim: "17:00",
      motivo: "Manutenção",
      observacoes: "",
      professionalId: "",
    });
    expect(body.motivo).toBe("Manutenção");
    expect(body.dia_inteiro).toBeUndefined();
    expect(body.professional).toBeUndefined();
    expect(typeof body.data_inicio).toBe("string");
    expect(typeof body.data_fim).toBe("string");
  });
});

describe("dias soltos do mês", () => {
  it("enumera o intervalo e aceita dias fora de sequência", () => {
    expect(enumerarDiasInclusivo("2026-09-21", "2026-09-23")).toEqual([
      "2026-09-21",
      "2026-09-22",
      "2026-09-23",
    ]);
    expect(enumerarDiasInclusivo("2026-09-23", "2026-09-21")).toEqual([]);
    expect(toggleDiaIso(["2026-09-03", "2026-09-22"], "2026-09-10")).toEqual([
      "2026-09-03",
      "2026-09-10",
      "2026-09-22",
    ]);
    expect(toggleDiaIso(["2026-09-03", "2026-09-22"], "2026-09-03")).toEqual(["2026-09-22"]);
  });

  it("gera um bloqueio de dia inteiro por data", () => {
    const bodies = buildBloqueiosPorDia({
      dias: ["2026-09-22", "2026-09-03"],
      motivo: "Férias",
      observacoes: "",
      professionalId: "",
    });
    expect(bodies).toHaveLength(2);
    expect(bodies.every((b) => b.dia_inteiro === true && b.motivo === "Férias")).toBe(true);
    expect(bodies[0].data_inicio).not.toBe(bodies[1].data_inicio);
  });
});

describe("repetir dia da semana", () => {
  it("enumera as terças do mês", () => {
    expect(weekdaySegundaZero("2026-11-02")).toBe(0);
    expect(weekdaySegundaZero("2026-11-03")).toBe(1);
    expect(enumerarDiasDaSemana("2026-11-02", "2026-11-30", 1)).toEqual([
      "2026-11-03",
      "2026-11-10",
      "2026-11-17",
      "2026-11-24",
    ]);
  });

  it("valida a repetição e gera horários iguais", () => {
    expect(
      validateBloqueioForm({
        modo: "horario",
        motivoFinal: "Reunião",
        dataHorario: "2026-11-03",
        horaInicio: "13:00",
        horaFim: "18:00",
        repetir: true,
        dataFimRepeticao: "2026-11-24",
        weekdayRepeticao: 1,
      }),
    ).toBeNull();
    expect(
      validateBloqueioForm({
        modo: "dias",
        motivoFinal: "Férias",
        dataInicioDia: "2026-11-03",
        repetir: true,
        dataFimRepeticao: "2026-10-01",
        weekdayRepeticao: 1,
      }),
    ).toContain("depois");
    const bodies = buildBloqueiosHorarioPorDia({
      dias: ["2026-11-03", "2026-11-10"],
      motivo: "Reunião",
      observacoes: "",
      professionalId: "12",
      horaInicio: "13:00",
      horaFim: "18:00",
    });
    expect(bodies).toHaveLength(2);
    expect(bodies.every((b) => b.professional === 12 && b.motivo === "Reunião")).toBe(true);
  });
});

describe("extractBloqueioApiError", () => {
  it("prioriza error do backend", () => {
    expect(extractBloqueioApiError({ error: "negado" }, 400)).toBe("negado");
  });
});
