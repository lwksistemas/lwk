import { describe, expect, it } from "vitest";
import { resolveColunasConsultas } from "@/lib/clinica-consultas-colunas-config";

describe("resolveColunasConsultas", () => {
  it("respeita a lista salva sem Nº", () => {
    const keys = resolveColunasConsultas([
      "patient",
      "procedure",
      "date",
      "pagamento",
      "status",
    ]).map((c) => c.key);
    expect(keys).toEqual(["patient", "procedure", "date", "pagamento", "status"]);
    expect(keys).not.toContain("numero");
  });

  it("mantém Nº quando a clínica marcou a coluna", () => {
    const keys = resolveColunasConsultas(["numero", "patient", "status"]).map((c) => c.key);
    expect(keys[0]).toBe("numero");
  });
});
