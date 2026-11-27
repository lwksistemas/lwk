import { describe, expect, it } from "vitest";
import { formatDuracaoPrevista } from "@/components/clinica-beleza/criar-agendamento/AgendamentoResumoCard";
import { iconeTipoAgenda } from "@/components/clinica-beleza/criar-agendamento/TipoAgendaButtons";
import { Stethoscope, RefreshCw, Package } from "lucide-react";
import { buildAgendaPatientSearchQuery } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-utils";

describe("formatDuracaoPrevista", () => {
  it("formata horas e minutos", () => {
    expect(formatDuracaoPrevista(0)).toBe("Não definida");
    expect(formatDuracaoPrevista(45)).toBe("45min");
    expect(formatDuracaoPrevista(60)).toBe("1h");
    expect(formatDuracaoPrevista(150)).toBe("2h 30min");
  });
});

describe("iconeTipoAgenda", () => {
  it("mapeia tipos conhecidos", () => {
    expect(iconeTipoAgenda("Consulta")).toBe(Stethoscope);
    expect(iconeTipoAgenda("RETORNO")).toBe(RefreshCw);
    expect(iconeTipoAgenda("Protocolo")).toBe(Package);
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
