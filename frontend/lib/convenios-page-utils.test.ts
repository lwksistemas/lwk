import { describe, expect, it } from "vitest";
import {
  buildConveniosBasePath,
  extractConvenioSaveError,
  isNovaConvenioQuery,
} from "@/components/clinica-beleza/convenios-page/convenios-page-utils";

describe("buildConveniosBasePath", () => {
  it("monta path da loja", () => {
    expect(buildConveniosBasePath("novaimagem")).toBe("/loja/novaimagem/clinica-beleza/convenios");
  });
});

describe("isNovaConvenioQuery", () => {
  it("detecta ?novo=1", () => {
    expect(isNovaConvenioQuery(new URLSearchParams("novo=1"))).toBe(true);
    expect(isNovaConvenioQuery(new URLSearchParams())).toBe(false);
  });
});

describe("extractConvenioSaveError", () => {
  it("extrai mensagem de Error", () => {
    expect(extractConvenioSaveError(new Error("falhou"))).toBe("falhou");
  });

  it("usa fallback genérico", () => {
    expect(extractConvenioSaveError("x")).toBe("Erro ao criar convênio.");
  });
});
