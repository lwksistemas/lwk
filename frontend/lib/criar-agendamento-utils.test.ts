import { describe, expect, it } from "vitest";
import {
  buildAppointmentDate,
  buildCriarAgendamentoPayload,
  computeCriarAgendamentoPricing,
} from "@/hooks/clinica-beleza/criar-agendamento/criar-agendamento-builders";
import {
  buildQuickPatientBody,
  extractCriarAgendamentoSubmitError,
  mapSubmitValidationError,
} from "@/hooks/clinica-beleza/criar-agendamento/criar-agendamento-submit-utils";

describe("buildAppointmentDate", () => {
  it("combina data e hora", () => {
    const date = buildAppointmentDate("2026-06-15", "14:30", null);
    expect(date?.getFullYear()).toBe(2026);
    expect(date?.getMonth()).toBe(5);
    expect(date?.getDate()).toBe(15);
    expect(date?.getHours()).toBe(14);
    expect(date?.getMinutes()).toBe(30);
  });
});

describe("buildCriarAgendamentoPayload", () => {
  it("monta payload com múltiplos procedimentos", () => {
    const date = new Date("2026-06-15T14:30:00");
    const payload = buildCriarAgendamentoPayload({
      patientId: 1,
      agendaId: 2,
      notes: "teste",
      date,
      professionalId: 3,
      localId: 4,
      convenioId: "",
      selectedProcedures: [10, 11],
      retornoProcedureId: "",
    });
    expect(payload.patient).toBe(1);
    expect(payload.procedures_ids).toEqual([10, 11]);
    expect(payload.procedure).toBe(10);
  });
});

describe("computeCriarAgendamentoPricing", () => {
  it("isenta taxa quando retorno elegível", () => {
    const result = computeCriarAgendamentoPricing(
      1,
      [{ id: 1, nome: "Consultório", valor_consulta: 100, is_active: true, created_at: "", updated_at: "" }],
      { elegivel: true } as never,
      50,
    );
    expect(result.totalEstimado).toBe(50);
  });
});

describe("buildQuickPatientBody", () => {
  it("normaliza telefone e cpf", () => {
    const body = buildQuickPatientBody({
      nome: "Ana",
      telefone: "(11) 99999-0000",
      cpf: "123.456.789-00",
    });
    expect(body.telefone).toBe("11999990000");
    expect(body.cpf).toBe("12345678900");
  });
});

describe("mapSubmitValidationError", () => {
  it("troca cliente por paciente", () => {
    expect(mapSubmitValidationError("Selecione o cliente.")).toBe("Selecione o paciente.");
  });
});

describe("extractCriarAgendamentoSubmitError", () => {
  it("usa mensagem de Error", () => {
    expect(extractCriarAgendamentoSubmitError(new Error("Falha rede"), false)).toBe("Falha rede");
  });
});
