import { describe, expect, it } from "vitest";
import {
  cepSomenteDigitos,
  isCepCompleto,
} from "@/components/clinica-beleza/paciente-cadastro/paciente-cadastro-utils";

describe("cepSomenteDigitos", () => {
  it("remove formatação", () => {
    expect(cepSomenteDigitos("01310-100")).toBe("01310100");
  });
});

describe("isCepCompleto", () => {
  it("exige 8 dígitos", () => {
    expect(isCepCompleto("01310-100")).toBe(true);
    expect(isCepCompleto("01310")).toBe(false);
  });
});
