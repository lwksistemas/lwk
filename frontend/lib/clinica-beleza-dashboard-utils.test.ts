import { describe, expect, it } from "vitest";
import {
  currentDashboardMesAno,
  parseDashboardMesAno,
  pctChangeDashboard,
  percentualDashboard,
  primeiroNomeDashboard,
  rotuloPeriodoDashboard,
  saudacaoDashboard,
} from "@/components/clinica-beleza/clinica-beleza-dashboard/clinica-beleza-dashboard-utils";

describe("currentDashboardMesAno", () => {
  it("retorna YYYY-MM", () => {
    expect(currentDashboardMesAno()).toMatch(/^\d{4}-\d{2}$/);
  });
});

describe("parseDashboardMesAno", () => {
  it("extrai mês e ano", () => {
    expect(parseDashboardMesAno("2026-06")).toEqual({ ano: 2026, mes: 6 });
  });
});

describe("pctChangeDashboard", () => {
  it("calcula variação percentual", () => {
    expect(pctChangeDashboard(120, 100)).toBe("+20%");
    expect(pctChangeDashboard(80, 100)).toBe("-20%");
    expect(pctChangeDashboard(10, 0)).toBeNull();
  });
});

describe("rótulos do dashboard", () => {
  it("formata o período e a saudação", () => {
    expect(rotuloPeriodoDashboard("2026-11")).toBe("Novembro / 2026");
    expect(saudacaoDashboard(8)).toBe("Bom dia");
    expect(saudacaoDashboard(15)).toBe("Boa tarde");
    expect(saudacaoDashboard(20)).toBe("Boa noite");
    expect(primeiroNomeDashboard("FABIO CRISTIANO FELIX")).toBe("FABIO");
    expect(primeiroNomeDashboard("  ")).toBe("");
  });

  it("calcula o percentual do gráfico sem inventar total", () => {
    expect(percentualDashboard(7, 20)).toBe(35);
    expect(percentualDashboard(4, 0)).toBe(0);
  });
});
