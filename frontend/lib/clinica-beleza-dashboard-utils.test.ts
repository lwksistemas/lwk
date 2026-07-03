import { describe, expect, it } from "vitest";
import {
  currentDashboardMesAno,
  parseDashboardMesAno,
  pctChangeDashboard,
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
