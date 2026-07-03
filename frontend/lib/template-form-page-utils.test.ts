import { describe, expect, it } from "vitest";
import {
  buildTemplatesListPath,
  extractTemplateLoadError,
  extractTemplateSaveError,
  parseTemplateEditId,
  validateTemplateForm,
} from "@/components/clinica-beleza/template-form-page/template-form-page-utils";
import { buildTemplateNovoPath, templateTipoLabel } from "@/components/clinica-beleza/templates-page/templates-page-utils";

describe("buildTemplatesListPath", () => {
  it("monta path da lista", () => {
    expect(buildTemplatesListPath("loja-a")).toBe("/loja/loja-a/clinica-beleza/templates");
  });
});

describe("parseTemplateEditId", () => {
  it("converte id válido", () => {
    expect(parseTemplateEditId("42")).toBe(42);
    expect(parseTemplateEditId(null)).toBeNull();
    expect(parseTemplateEditId("x")).toBeNull();
  });
});

describe("validateTemplateForm", () => {
  it("exige nome e conteúdo", () => {
    expect(validateTemplateForm({ nome: "", tipo: "receituario", conteudo: "x" })).toBe(
      "Nome é obrigatório.",
    );
    expect(validateTemplateForm({ nome: "A", tipo: "receituario", conteudo: "" })).toBe(
      "Conteúdo é obrigatório.",
    );
    expect(validateTemplateForm({ nome: "A", tipo: "receituario", conteudo: "B" })).toBeNull();
  });
});

describe("extractTemplateSaveError", () => {
  it("prioriza campo nome", () => {
    expect(extractTemplateSaveError({ nome: ["inválido"] })).toBe("inválido");
  });
});

describe("extractTemplateLoadError", () => {
  it("usa detail ou fallback", () => {
    expect(extractTemplateLoadError({ detail: "404" })).toBe("404");
  });
});

describe("buildTemplateNovoPath", () => {
  it("inclui query id na edição", () => {
    expect(buildTemplateNovoPath("x", 5)).toBe("/loja/x/clinica-beleza/templates/novo?id=5");
  });
});

describe("templateTipoLabel", () => {
  it("traduz tipo conhecido", () => {
    expect(templateTipoLabel("receituario")).toBe("Receituário");
  });
});
