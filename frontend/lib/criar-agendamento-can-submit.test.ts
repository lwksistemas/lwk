import { describe, expect, it } from "vitest";
import { canSubmitCriarAgendamento } from "@/hooks/clinica-beleza/criar-agendamento/criar-agendamento-can-submit";

const base = {
  createLoading: false,
  patientId: 1 as number | "",
  professionalId: 2 as number | "",
  dateInput: "2026-11-28",
  time: "10:00",
  nomeAgendaId: 3 as number | "",
  agendaEhProtocolo: false,
  protocoloClienteId: "" as number | "",
  protocoloModeloId: "" as number | "",
  disponibilidadeError: "",
};

describe("canSubmitCriarAgendamento", () => {
  it("habilita quando os campos obrigatórios estão ok", () => {
    expect(canSubmitCriarAgendamento(base)).toBe(true);
  });

  it("desabilita sem paciente, profissional, data, hora ou tipo", () => {
    expect(canSubmitCriarAgendamento({ ...base, patientId: "" })).toBe(false);
    expect(canSubmitCriarAgendamento({ ...base, professionalId: "" })).toBe(false);
    expect(canSubmitCriarAgendamento({ ...base, dateInput: "" })).toBe(false);
    expect(canSubmitCriarAgendamento({ ...base, time: "" })).toBe(false);
    expect(canSubmitCriarAgendamento({ ...base, nomeAgendaId: "" })).toBe(false);
  });

  it("desabilita com conflito de disponibilidade ou loading", () => {
    expect(canSubmitCriarAgendamento({ ...base, disponibilidadeError: "Horário ocupado" })).toBe(false);
    expect(canSubmitCriarAgendamento({ ...base, createLoading: true })).toBe(false);
  });

  it("exige protocolo quando o tipo de agenda é protocolo", () => {
    expect(
      canSubmitCriarAgendamento({
        ...base,
        agendaEhProtocolo: true,
        protocoloClienteId: "",
        protocoloModeloId: "",
      }),
    ).toBe(false);
    expect(
      canSubmitCriarAgendamento({
        ...base,
        agendaEhProtocolo: true,
        protocoloModeloId: 9,
      }),
    ).toBe(true);
  });
});
