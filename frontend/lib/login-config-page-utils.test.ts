import { describe, expect, it } from "vitest";
import {
  buildLoginConfigSaveBody,
  extractLoginConfigSaveError,
  isColorPresetSelected,
  loginConfigDataToForm,
  normalizeHexColor,
} from "@/components/clinica-beleza/login-config-page/login-config-page-utils";

describe("normalizeHexColor", () => {
  it("adiciona # quando ausente", () => {
    expect(normalizeHexColor("8B3D52")).toBe("#8B3D52");
    expect(normalizeHexColor("#8B3D52")).toBe("#8B3D52");
  });
});

describe("loginConfigDataToForm", () => {
  it("aplica defaults quando cor ausente", () => {
    const form = loginConfigDataToForm(
      {
        logo: "",
        login_background: "",
        login_logo: "",
        cor_primaria: null as unknown as string,
        cor_secundaria: null as unknown as string,
      },
      "#111111",
      "#222222",
    );
    expect(form.corPrimaria).toBe("#111111");
    expect(form.corSecundaria).toBe("#222222");
  });
});

describe("buildLoginConfigSaveBody", () => {
  it("trim e normaliza cores", () => {
    const body = buildLoginConfigSaveBody({
      logo: "  url ",
      loginBackground: "",
      loginLogo: " logo ",
      corPrimaria: "8B3D52",
      corSecundaria: "#6B2F40",
    });
    expect(body.logo).toBe("url");
    expect(body.cor_primaria).toBe("#8B3D52");
    expect(body.login_logo).toBe("logo");
  });
});

describe("extractLoginConfigSaveError", () => {
  it("prioriza error da API", () => {
    expect(extractLoginConfigSaveError({ response: { data: { error: "Falha" } } })).toBe("Falha");
    expect(extractLoginConfigSaveError({})).toBe("Erro ao salvar. Tente novamente.");
  });
});

describe("isColorPresetSelected", () => {
  it("compara cor primária", () => {
    expect(isColorPresetSelected("#8B3D52", "#8B3D52")).toBe(true);
    expect(isColorPresetSelected("#111111", "#8B3D52")).toBe(false);
  });
});
