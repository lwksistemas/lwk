import { describe, expect, it } from "vitest";
import {
  formatDuracaoPrevista,
  formatRetornoResumoCompact,
  formatTerminoPrevisto,
} from "@/components/clinica-beleza/criar-agendamento/agendamento-resumo-format";
import { iconeTipoAgenda } from "@/components/clinica-beleza/criar-agendamento/TipoAgendaButtons";
import {
  estadoAposAdicionarProcedimento,
  estadoFecharListaDisponiveis,
  estadoToggleCategoria,
  mostrarListaDisponiveis,
} from "@/components/clinica-beleza/procedure-picker-state";
import { Layers, Stethoscope, RefreshCw } from "lucide-react";
import { buildAgendaPatientSearchQuery } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-utils";

describe("formatDuracaoPrevista", () => {
  it("formata horas e minutos", () => {
    expect(formatDuracaoPrevista(0)).toBe("Não definida");
    expect(formatDuracaoPrevista(45)).toBe("45min");
    expect(formatDuracaoPrevista(60)).toBe("1h");
    expect(formatDuracaoPrevista(150)).toBe("2h 30min");
  });
});

describe("formatRetornoResumoCompact", () => {
  it("compacta retorno gratuito com dias restantes", () => {
    expect(formatRetornoResumoCompact(null)).toBe("Não informado");
    expect(formatRetornoResumoCompact({ elegivel: false })).toBe("Não informado");
    expect(
      formatRetornoResumoCompact({
        elegivel: true,
        dias_restantes: 26,
        mensagem: "Retorno da avaliação (26 dia(s) restantes no prazo de 30). Taxa de avaliação isenta.",
      }),
    ).toBe("Retorno gratuito · 26 dias restantes");
    expect(formatRetornoResumoCompact({ elegivel: true, dias_restantes: 1 })).toBe(
      "Retorno gratuito · 1 dia restante",
    );
    expect(formatRetornoResumoCompact({ elegivel: true })).toBe("Retorno gratuito");
  });
});

describe("formatTerminoPrevisto", () => {
  it("soma horário de início com a duração", () => {
    expect(formatTerminoPrevisto("17:05", 120)).toBe("19:05");
    expect(formatTerminoPrevisto("17:30", 150)).toBe("20:00");
    expect(formatTerminoPrevisto("23:30", 60)).toBe("00:30");
    expect(formatTerminoPrevisto("17:05", 0)).toBeNull();
    expect(formatTerminoPrevisto("", 60)).toBeNull();
  });
});

describe("iconeTipoAgenda", () => {
  it("mapeia tipos conhecidos", () => {
    expect(iconeTipoAgenda("Consulta")).toBe(Stethoscope);
    expect(iconeTipoAgenda("RETORNO")).toBe(RefreshCw);
    expect(iconeTipoAgenda("Protocolo")).toBe(Layers);
  });
});

describe("buildAgendaPatientSearchQuery", () => {
  it("usa dígitos para telefone/CPF e texto para nome", () => {
    expect(buildAgendaPatientSearchQuery("  ")).toBe("");
    expect(buildAgendaPatientSearchQuery("Maria Silva")).toBe("Maria Silva");
    expect(buildAgendaPatientSearchQuery("(11) 99999-0000")).toBe("11999990000");
    expect(buildAgendaPatientSearchQuery("123.456.789-00")).toBe("12345678900");
  });
});

describe("procedure picker — lista disponível", () => {
  it("começa fechada sem categoria nem busca", () => {
    expect(mostrarListaDisponiveis({ categoriaAtiva: "", busca: "", listaAberta: false })).toBe(false);
  });

  it("abre ao ativar categoria ou buscar", () => {
    expect(
      mostrarListaDisponiveis(estadoToggleCategoria({ categoriaAtiva: "", busca: "", listaAberta: false }, "facial")),
    ).toBe(true);
    expect(mostrarListaDisponiveis({ categoriaAtiva: "", busca: "botox", listaAberta: false })).toBe(true);
  });

  it("fecha e limpa após adicionar", () => {
    expect(estadoAposAdicionarProcedimento()).toEqual({
      categoriaAtiva: "",
      busca: "",
      listaAberta: false,
    });
  });

  it("permite fechar sem selecionar e reabrir a mesma categoria", () => {
    const aberto = estadoToggleCategoria({ categoriaAtiva: "", busca: "", listaAberta: false }, "facial");
    expect(aberto).toEqual({ categoriaAtiva: "facial", busca: "", listaAberta: true });
    expect(estadoFecharListaDisponiveis({ ...aberto, busca: "x" })).toEqual({
      categoriaAtiva: "",
      busca: "",
      listaAberta: false,
    });
    const deNovo = estadoToggleCategoria({ categoriaAtiva: "", busca: "", listaAberta: false }, "facial");
    expect(deNovo.listaAberta).toBe(true);
    expect(estadoToggleCategoria(deNovo, "facial").listaAberta).toBe(false);
  });
});
