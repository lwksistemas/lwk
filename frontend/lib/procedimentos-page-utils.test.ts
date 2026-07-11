import { describe, expect, it } from "vitest";
import {
  buildPrecosConvenioPayload,
  buildPrecosMapFromMatrix,
  buildProcedimentoSaveBody,
  filterProcedimentosList,
  formatPrecoCelula,
  mapPrecosConvenioFromApi,
  validateProcedimentoForm,
} from "@/components/clinica-beleza/procedimentos-page/procedimentos-page-utils";
import { EMPTY_PROCEDIMENTO_FORM } from "@/components/clinica-beleza/procedimentos-page/procedimentos-page-types";

describe("buildPrecosMapFromMatrix", () => {
  it("indexa por procedure:convenio", () => {
    const map = buildPrecosMapFromMatrix([
      { procedure: 1, convenio: 2, preco: "150.00" },
      { procedure: 1, convenio: 3, preco: "200.00" },
    ]);
    expect(map["1:2"]).toBe("150.00");
    expect(map["1:3"]).toBe("200.00");
  });
});

describe("formatPrecoCelula", () => {
  it("formata valor existente", () => {
    const text = formatPrecoCelula({ "5:1": "100" }, 5, 1);
    expect(text).toMatch(/R\$/);
  });

  it("retorna traço quando vazio", () => {
    expect(formatPrecoCelula({}, 1, 1)).toBe("—");
  });
});

describe("buildPrecosConvenioPayload", () => {
  it("normaliza vírgula decimal", () => {
    const payload = buildPrecosConvenioPayload(
      [{ id: 1, nome: "Unimed", is_active: true, created_at: "", updated_at: "" }],
      { 1: "150,50" },
    );
    expect(payload[0].preco).toBe("150.50");
  });
});

describe("validateProcedimentoForm", () => {
  it("exige nome e categoria", () => {
    expect(validateProcedimentoForm(EMPTY_PROCEDIMENTO_FORM, [], {}, "")).toBe("Nome é obrigatório.");
    expect(
      validateProcedimentoForm({ ...EMPTY_PROCEDIMENTO_FORM, name: "Botox" }, [], {}, ""),
    ).toBe("Categoria é obrigatória.");
  });

  it("exige preço em pelo menos um convênio", () => {
    const form = { ...EMPTY_PROCEDIMENTO_FORM, name: "Botox", categoria: "estetica" };
    const convenios = [{ id: 1, nome: "Unimed", is_active: true, created_at: "", updated_at: "" }];
    expect(validateProcedimentoForm(form, convenios, {}, "estetica")).toBe(
      "Informe o valor praticado em pelo menos um convênio.",
    );
  });
});

describe("buildProcedimentoSaveBody", () => {
  it("monta body com categoria e termo", () => {
    const body = buildProcedimentoSaveBody(
      {
        ...EMPTY_PROCEDIMENTO_FORM,
        name: "Botox",
        categoria: "estetica",
        duration: "45",
        termo_consentimento_ativo: true,
        termo_consentimento: "Texto do termo",
      },
      "estetica",
    );
    expect(body.name).toBe("Botox");
    expect(body.duration).toBe(45);
    expect(body.termo_consentimento).toBe("Texto do termo");
  });
});

describe("filterProcedimentosList", () => {
  it("filtra por módulo quando showAllCategories é false", () => {
    const list = [
      { id: 1, nome: "A", categoria: "estetica", is_active: true },
      { id: 2, nome: "B", categoria: "soroterapia", is_active: true },
    ];
    const { filteredList, hiddenByCategoryCount } = filterProcedimentosList(list, "estetica", false);
    expect(filteredList).toHaveLength(1);
    expect(hiddenByCategoryCount).toBe(1);
  });

  it("filtra por slug de categoria na lista", () => {
    const list = [
      { id: 1, nome: "A", categoria: "facial", is_active: true },
      { id: 2, nome: "B", categoria: "corporal", is_active: true },
    ];
    const { filteredList } = filterProcedimentosList(list, "", false, "facial");
    expect(filteredList).toHaveLength(1);
    expect(filteredList[0].id).toBe(1);
  });
});

describe("mapPrecosConvenioFromApi", () => {
  it("ignora preços vazios", () => {
    const map = mapPrecosConvenioFromApi([
      { convenio: 1, preco: "100" },
      { convenio: 2, preco: "" },
      { convenio: 3, preco: null },
    ]);
    expect(map).toEqual({ 1: "100" });
  });
});
