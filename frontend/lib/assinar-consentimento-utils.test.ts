import { describe, expect, it } from "vitest";
import {
  buildAssinaturaConsentimentoUrls,
  decodeAssinaturaToken,
  podeAssinarTermo,
} from "@/components/assinar-consentimento/assinar-consentimento-utils";

describe("decodeAssinaturaToken", () => {
  it("decodifica token URL-encoded", () => {
    expect(decodeAssinaturaToken("abc%2F123")).toBe("abc/123");
  });

  it("retorna token bruto se decode falhar", () => {
    expect(decodeAssinaturaToken("%E0%A4%A")).toBe("%E0%A4%A");
  });
});

describe("buildAssinaturaConsentimentoUrls", () => {
  it("monta endpoints do termo e PDF", () => {
    expect(buildAssinaturaConsentimentoUrls("tok%2Fen")).toEqual({
      termo: "/clinica-beleza/assinar-consentimento/tok%2Fen/",
      pdf: "/clinica-beleza/assinar-consentimento/tok%2Fen/pdf/",
    });
  });
});

describe("podeAssinarTermo", () => {
  it("exige PDF pronto, interação e declaração", () => {
    expect(podeAssinarTermo(true, true, true)).toBe(true);
    expect(podeAssinarTermo(false, true, true)).toBe(false);
    expect(podeAssinarTermo(true, false, true)).toBe(false);
    expect(podeAssinarTermo(true, true, false)).toBe(false);
  });
});
