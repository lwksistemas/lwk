import { describe, expect, it } from "vitest";
import { procedureSelectLabel, stripCategoriaPrefixFromNome } from "@/lib/clinica-beleza-categories";

describe("stripCategoriaPrefixFromNome", () => {
  it("remove SOROTERAPIA — do nome", () => {
    expect(stripCategoriaPrefixFromNome("SOROTERAPIA — ANTI-AGING", "soroterapia")).toBe(
      "ANTI-AGING",
    );
  });

  it("mantém nome sem prefixo", () => {
    expect(stripCategoriaPrefixFromNome("PREENCHIMENTO LABIAL", "facial")).toBe(
      "PREENCHIMENTO LABIAL",
    );
  });
});

describe("procedureSelectLabel", () => {
  it("não repete categoria no sufixo", () => {
    expect(
      procedureSelectLabel("SOROTERAPIA — GLUTAMINA E REPOSIÇÃO", "soroterapia", {
        includeCategorySuffix: true,
      }),
    ).toBe("GLUTAMINA E REPOSIÇÃO · Soroterapia");
  });

  it("acrescenta categoria em procedimento facial", () => {
    expect(
      procedureSelectLabel("PREENCHIMENTO LABIAL", "facial", { includeCategorySuffix: true }),
    ).toBe("PREENCHIMENTO LABIAL · Facial");
  });

  it("omite sufixo quando o filtro de categoria já está ativo", () => {
    expect(
      procedureSelectLabel("SOROTERAPIA — DETOX", "soroterapia", { includeCategorySuffix: false }),
    ).toBe("DETOX");
  });
});
