import { describe, expect, it } from "vitest";
import { periodoFinanceiro } from "@/components/clinica-beleza/financeiro-page/periodo";

describe("periodoFinanceiro", () => {
  const hoje = new Date(2026, 10, 5);

  it("mês atual e mês passado", () => {
    expect(periodoFinanceiro("atual", hoje, "", "")).toEqual({ inicio: "2026-11-01", fim: "2026-11-30" });
    expect(periodoFinanceiro("passado", hoje, "", "")).toEqual({ inicio: "2026-10-01", fim: "2026-10-31" });
  });

  it("personalizado usa as datas escolhidas", () => {
    expect(periodoFinanceiro("personalizado", hoje, "2026-08-01", "2026-08-15")).toEqual({
      inicio: "2026-08-01",
      fim: "2026-08-15",
    });
    expect(periodoFinanceiro("", hoje, "2026-08-01", "2026-08-15")).toEqual({ inicio: "", fim: "" });
  });
});
