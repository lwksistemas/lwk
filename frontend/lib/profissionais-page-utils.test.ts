import { describe, expect, it } from "vitest";
import {
  buildProfissionaisBasePath,
  extractProfissionalToggleError,
} from "@/components/clinica-beleza/profissionais-page/profissionais-page-utils";

describe("buildProfissionaisBasePath", () => {
  it("monta path da loja", () => {
    expect(buildProfissionaisBasePath("novaimagem")).toBe(
      "/loja/novaimagem/clinica-beleza/profissionais",
    );
  });
});

describe("extractProfissionalToggleError", () => {
  it("extrai error ou detail", () => {
    expect(extractProfissionalToggleError({ error: "negado" })).toBe("negado");
    expect(extractProfissionalToggleError({ detail: "falhou" })).toBe("falhou");
    expect(extractProfissionalToggleError({})).toBe("Erro ao alterar status.");
  });
});
