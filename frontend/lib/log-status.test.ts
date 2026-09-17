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
