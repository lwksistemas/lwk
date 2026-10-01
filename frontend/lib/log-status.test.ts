import { describe, expect, it } from "vitest";
import {
  mensagemStatusLog,
  rotuloHttpLog,
  textoErroLegivel,
  tipoResultadoLog,
  tituloStatusLog,
} from "./log-status";

describe("textoErroLegivel", () => {
  it("extrai a frase do dict da API", () => {
    expect(
      textoErroLegivel("{'error': 'Horário já ocupado para este profissional.'}"),
    ).toBe("Horário já ocupado para este profissional.");
  });

  it("traduz o conflito da agenda mesmo com datetime no meio", () => {
    const bruto =
      "{'conflict': True, 'server': {'id': 463, " +
      "'title': 'BIANCA ORNELLAS DE ALMEIDA - TIRZEPATIDA DOSE DE 5 MG', " +
      "'start': '2026-10-01T16:50:00-03:00', " +
      "'end': datetime.datetime(2026, 10, 1, 17, 10, tzinfo=zoneinfo.ZoneInfo(key='America/Sao_Paulo')), " +
      "'backgroundColor': '#22c55e', 'borde…";
    expect(textoErroLegivel(bruto)).toBe(
      "Este agendamento foi alterado em outro dispositivo. A edição não foi salva. " +
        "Versão que permanece: BIANCA ORNELLAS DE ALMEIDA - TIRZEPATIDA DOSE DE 5 MG · 01/10/2026 16:50.",
    );
  });
});

describe("mensagemStatusLog", () => {
  it("mostra conclusão com ação e recurso", () => {
    expect(
      mensagemStatusLog({
        sucesso: true,
        acao: "criar",
        acao_display: "Criar",
        recurso: "Agenda",
      }),
    ).toBe("Criar em agenda concluído.");
  });

  it("mostra o motivo da recusa em vez de Erro vazio", () => {
    expect(
      mensagemStatusLog({
        sucesso: false,
        erro: "{'error': 'Horário já ocupado para este profissional.'}",
        acao: "criar",
        recurso: "Agenda",
      }),
    ).toBe("Horário já ocupado para este profissional.");
  });
});

describe("rotuloHttpLog", () => {
  it("não inventa GET N/A", () => {
    expect(rotuloHttpLog({ sucesso: true })).toBe("URL não registrada");
    expect(
      rotuloHttpLog({
        sucesso: false,
        metodo_http: "POST",
        url: "/api/clinica-beleza/agenda/create/",
      }),
    ).toBe("POST /api/clinica-beleza/agenda/create/");
  });
});

describe("tituloStatusLog", () => {
  it("separa recusa de falha", () => {
    expect(tituloStatusLog("sucesso")).toBe("Concluído");
    expect(tituloStatusLog("recusado")).toBe("Não concluído");
    expect(tituloStatusLog("erro")).toBe("Falhou");
    expect(
      tipoResultadoLog({
        sucesso: false,
        erro: "{'error': 'Horário já ocupado para este profissional.'}",
      }),
    ).toBe("recusado");
  });
});
