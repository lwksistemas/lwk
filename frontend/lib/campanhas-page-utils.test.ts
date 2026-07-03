import { describe, expect, it } from "vitest";
import {
  buildCampanhaSaveBody,
  campanhaFoiEnviada,
  campanhaToForm,
  extractCampanhaSaveError,
  validateCampanhaForm,
} from "@/components/clinica-beleza/campanhas-page/campanhas-page-utils";
import {
  EMPTY_CAMPANHA_FORM,
  type Campanha,
} from "@/components/clinica-beleza/campanhas-page/campanhas-page-types";

const campanha = (overrides: Partial<Campanha> = {}): Campanha => ({
  id: 1,
  titulo: "Promo",
  mensagem: "Texto",
  data_inicio: "2026-01-01",
  data_fim: null,
  ativa: true,
  enviada_em: null,
  total_enviados: 0,
  created_at: "2026-01-01",
  ...overrides,
});

describe("campanhaToForm", () => {
  it("corta datas para input date", () => {
    const form = campanhaToForm(campanha({ data_inicio: "2026-06-15T00:00:00Z" }));
    expect(form.data_inicio).toBe("2026-06-15");
  });
});

describe("validateCampanhaForm", () => {
  it("exige título e mensagem", () => {
    expect(validateCampanhaForm(EMPTY_CAMPANHA_FORM)).toBe("Título e mensagem são obrigatórios.");
    expect(
      validateCampanhaForm({ ...EMPTY_CAMPANHA_FORM, titulo: "A", mensagem: "B" }),
    ).toBeNull();
  });
});

describe("buildCampanhaSaveBody", () => {
  it("trim e null em datas vazias", () => {
    const body = buildCampanhaSaveBody({
      ...EMPTY_CAMPANHA_FORM,
      titulo: "  Promo  ",
      mensagem: " Olá ",
      data_inicio: "",
      data_fim: "2026-12-31",
    });
    expect(body.titulo).toBe("Promo");
    expect(body.data_inicio).toBeNull();
    expect(body.data_fim).toBe("2026-12-31");
  });
});

describe("extractCampanhaSaveError", () => {
  it("detecta SESSION_ENDED", () => {
    expect(extractCampanhaSaveError(new Error("SESSION_ENDED"), "x")).toBe("SESSION_ENDED");
  });
});

describe("campanhaFoiEnviada", () => {
  it("verifica enviada_em", () => {
    expect(campanhaFoiEnviada(campanha())).toBe(false);
    expect(campanhaFoiEnviada(campanha({ enviada_em: "2026-01-02" }))).toBe(true);
  });
});
