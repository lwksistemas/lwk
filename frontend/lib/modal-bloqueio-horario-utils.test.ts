import { describe, expect, it } from "vitest";
import {
  buildBloqueioRequestBody,
  extractBloqueioApiError,
  resolveMotivoBloqueio,
  validateBloqueioForm,
} from "@/components/clinica-beleza/modal-bloqueio-horario/modal-bloqueio-horario-utils";

describe("resolveMotivoBloqueio", () => {
  it("usa tipo, outro ou fallback", () => {
    expect(resolveMotivoBloqueio("Manutenção", "")).toBe("Manutenção");
    expect(resolveMotivoBloqueio("", "Reunião")).toBe("Reunião");
    expect(resolveMotivoBloqueio("", "")).toBe("Bloqueio");
  });
});

describe("validateBloqueioForm", () => {
  it("valida intervalo e motivo", () => {
    expect(validateBloqueioForm("", "2026-01-02T10:00", "x")).toBeTruthy();
    expect(validateBloqueioForm("2026-01-02T12:00", "2026-01-02T10:00", "x")).toContain("depois");
    expect(validateBloqueioForm("2026-01-02T10:00", "2026-01-02T12:00", "  ")).toContain("motivo");
    expect(validateBloqueioForm("2026-01-02T10:00", "2026-01-02T12:00", "OK")).toBeNull();
  });
});

describe("buildBloqueioRequestBody", () => {
  it("monta ISO e professional opcional", () => {
    const body = buildBloqueioRequestBody({
      dataInicio: "2026-01-02T10:00",
      dataFim: "2026-01-02T12:00",
      motivo: "Férias",
      observacoes: " obs ",
      professionalId: "5",
    });
    expect(body.motivo).toBe("Férias");
    expect(body.professional).toBe(5);
    expect(body.observacoes).toBe("obs");
    expect(typeof body.data_inicio).toBe("string");
  });
});

describe("extractBloqueioApiError", () => {
  it("prioriza error do backend", () => {
    expect(extractBloqueioApiError({ error: "negado" }, 400)).toBe("negado");
  });
});
