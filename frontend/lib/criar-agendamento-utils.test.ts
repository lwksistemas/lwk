import { describe, expect, it } from "vitest";
import {
  buildAppointmentDate,
  buildCriarAgendamentoPayload,
  classificarSelecaoProtocolo,
  computeCriarAgendamentoPricing,
  type ProtocoloAgendaResumo,
} from "@/hooks/clinica-beleza/criar-agendamento/criar-agendamento-builders";
import {
  buildQuickPatientBody,
  extractCriarAgendamentoSubmitError,
  mapSubmitValidationError,
} from "@/hooks/clinica-beleza/criar-agendamento/criar-agendamento-submit-utils";
import {
  resolveDefaultNomeAgendaId,
  resolveNomeAgendaIdParaRetorno,
} from "@/components/clinica-beleza/criar-agendamento/criar-agendamento-utils";

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
    expect(payload.professional).toBe(3);
    expect(payload.procedures_ids).toEqual([10, 11]);
    expect(payload.procedure).toBe(10);
  });
});

const protocolo = (overrides: Partial<ProtocoloAgendaResumo> = {}): ProtocoloAgendaResumo => ({
  id: 1,
  nome: "Tirzepatida",
  procedure: 4,
  sessoes: 4,
  tempo_estimado: 40,
  intervalo_quantidade: 7,
  intervalo_unidade: "dias",
  ...overrides,
});

describe("classificarSelecaoProtocolo", () => {
  it("agenda o protocolo quando só ele está selecionado", () => {
    const item = protocolo();
    const selecao = classificarSelecaoProtocolo(
      [{ id: 4, categoria: "protocolo" }],
      [4],
      [item],
    );
    expect(selecao).toEqual({ tipo: "agendar", protocolo: item });
  });

  it("pede o cadastro quando a categoria Protocolo ainda não tem protocolo", () => {
    expect(
      classificarSelecaoProtocolo([{ id: 4, categoria: "protocolo" }], [4], []),
    ).toEqual({
      tipo: "erro",
      mensagem: "Cadastre o protocolo deste procedimento em Protocolos antes de agendar.",
    });
  });

  it("recusa misturar o protocolo com outro procedimento", () => {
    expect(
      classificarSelecaoProtocolo(
        [
          { id: 4, categoria: "protocolo" },
          { id: 5, categoria: "facial" },
        ],
        [4, 5],
        [protocolo()],
      ),
    ).toEqual({ tipo: "erro", mensagem: "O protocolo é agendado sozinho." });
  });
});

describe("buildCriarAgendamentoPayload forma do protocolo", () => {
  it("envia a forma de cobrança e não marca retorno", () => {
    const payload = buildCriarAgendamentoPayload({
      patientId: 1,
      agendaId: 2,
      notes: "",
      date: new Date("2026-06-15T14:30:00"),
      professionalId: 3,
      localId: 4,
      convenioId: 8,
      selectedProcedures: [4],
      retornoProcedureId: 9,
      formaCobranca: "POR_CONSULTA",
    });
    expect(payload.forma_cobranca).toBe("POR_CONSULTA");
    expect(payload.retorno_procedure).toBeUndefined();
    expect(payload.convenio).toBe(8);
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

  it("mantém mensagem de profissional obrigatório", () => {
    expect(mapSubmitValidationError("Selecione o profissional.")).toBe("Selecione o profissional.");
  });
});

describe("extractCriarAgendamentoSubmitError", () => {
  it("usa mensagem de Error", () => {
    expect(extractCriarAgendamentoSubmitError(new Error("Falha rede"), false)).toBe("Falha rede");
  });
});

describe("tipo de agenda no retorno", () => {
  const consulta = {
    id: 1,
    nome: "CONSULTA",
    is_padrao: true,
    is_active: true,
    created_at: "",
    updated_at: "",
  };
  const retorno = {
    id: 2,
    nome: "Retorno",
    is_padrao: false,
    is_active: true,
    created_at: "",
    updated_at: "",
  };
  const estetica = {
    id: 3,
    nome: "Estética",
    is_padrao: false,
    is_active: true,
    created_at: "",
    updated_at: "",
  };

  it("escolhe Consulta como padrão mesmo se is_padrao estiver em outro", () => {
    expect(resolveDefaultNomeAgendaId([retorno, consulta])).toBe(1);
  });

  it("muda para Retorno quando o paciente está no prazo", () => {
    expect(resolveNomeAgendaIdParaRetorno([consulta, retorno], 1, true)).toBe(2);
  });

  it("volta para Consulta quando sai do prazo", () => {
    expect(resolveNomeAgendaIdParaRetorno([consulta, retorno], 2, false)).toBe(1);
  });

  it("não sobrescreve tipo cadastrado pelo cliente", () => {
    expect(resolveNomeAgendaIdParaRetorno([consulta, retorno, estetica], 3, true)).toBe(3);
  });
});
