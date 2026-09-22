import { describe, expect, it } from "vitest";
import {
  buildBloqueioRequestBody,
  buildBloqueiosPorDia,
  enumerarDiasInclusivo,
  extractBloqueioApiError,
  modoSugeridoParaTipo,
  resolveMotivoBloqueio,
  toggleDiaIso,
  validateBloqueioForm,
} from "@/components/clinica-beleza/modal-bloqueio-horario/modal-bloqueio-horario-utils";

describe("resolveMotivoBloqueio", () => {
  it("usa tipo, outro ou fallback", () => {
    expect(resolveMotivoBloqueio("Manutenção", "")).toBe("Manutenção");
    expect(resolveMotivoBloqueio("", "Reunião")).toBe("Reunião");
    expect(resolveMotivoBloqueio("", "")).toBe("Bloqueio");
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

describe("extractBloqueioApiError", () => {
  it("prioriza error do backend", () => {
    expect(extractBloqueioApiError({ error: "negado" }, 400)).toBe("negado");
  });
});
