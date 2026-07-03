import { describe, expect, it } from "vitest";
import {
  deveExibirAguardandoInicio,
  loadingConsultaLabel,
  temHistoricoAnterior,
} from "@/components/clinica-beleza/consultas/consulta-detail-shell/consulta-detail-shell-utils";

describe("temHistoricoAnterior", () => {
  it("exige mais de um item", () => {
    expect(temHistoricoAnterior([{ id: 1 }])).toBe(false);
    expect(temHistoricoAnterior([{ id: 1 }, { id: 2 }])).toBe(true);
  });
});

describe("deveExibirAguardandoInicio", () => {
  it("oculta quando consulta ativa ou finalizada ou aba histórico", () => {
    expect(deveExibirAguardandoInicio(true, false, "atendimento")).toBe(false);
    expect(deveExibirAguardandoInicio(false, true, "atendimento")).toBe(false);
    expect(deveExibirAguardandoInicio(false, false, "historico")).toBe(false);
    expect(deveExibirAguardandoInicio(false, false, "atendimento")).toBe(true);
  });
});

describe("loadingConsultaLabel", () => {
  it("diferencia carregamento inicial e de aba", () => {
    expect(loadingConsultaLabel(true)).toBe("Carregando consulta...");
    expect(loadingConsultaLabel(false)).toBe("Carregando aba...");
  });
});
