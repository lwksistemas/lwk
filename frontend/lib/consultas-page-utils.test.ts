import { describe, expect, it } from "vitest";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import {
  buildConsultaDetailHref,
  buildConsultasBasePath,
  buildConsultasListQueryParams,
  extractConsultaDeepLinkError,
  findConsultaInList,
  formatConsultaListDate,
  isNovaConsultaQuery,
} from "@/components/clinica-beleza/consultas-page/consultas-page-utils";

const consulta = (id: number): Consulta =>
  ({
    id,
    status: "agendada",
  }) as Consulta;

describe("buildConsultasBasePath", () => {
  it("monta path da loja", () => {
    expect(buildConsultasBasePath("novaimagem")).toBe("/loja/novaimagem/clinica-beleza/consultas");
  });
});

describe("buildConsultaDetailHref", () => {
  it("inclui query id", () => {
    expect(buildConsultaDetailHref("loja-a", 42)).toBe("/loja/loja-a/clinica-beleza/consultas?id=42");
  });
});

describe("findConsultaInList", () => {
  it("encontra por id string", () => {
    const list = [consulta(1), consulta(2)];
    expect(findConsultaInList(list, "2")?.id).toBe(2);
    expect(findConsultaInList(list, "9")).toBeUndefined();
  });
});

describe("isNovaConsultaQuery", () => {
  it("detecta ?novo=1", () => {
    expect(isNovaConsultaQuery(new URLSearchParams("novo=1"))).toBe(true);
    expect(isNovaConsultaQuery(new URLSearchParams())).toBe(false);
  });
});

describe("formatConsultaListDate", () => {
  it("retorna traço quando vazio", () => {
    expect(formatConsultaListDate(null)).toBe("—");
  });
});

describe("extractConsultaDeepLinkError", () => {
  it("usa fallback quando erro sem corpo", () => {
    expect(extractConsultaDeepLinkError(new Error("x"))).toBe(
      "Consulta não encontrada ou sem permissão para visualizá-la.",
    );
  });
});

describe("buildConsultasListQueryParams", () => {
  it("usa a fila quando não há paciente", () => {
    expect(buildConsultasListQueryParams({})).toEqual({ fila: "iniciar" });
  });

  it("filtra histórico do paciente sem a fila", () => {
    expect(buildConsultasListQueryParams({ patientId: 12 })).toEqual({ patient: 12 });
  });

  it("combina profissional com a fila", () => {
    expect(buildConsultasListQueryParams({ professionalId: 7 })).toEqual({
      fila: "iniciar",
      professional: 7,
    });
  });

  it("combina profissional com o paciente", () => {
    expect(buildConsultasListQueryParams({ patientId: 12, professionalId: 7 })).toEqual({
      patient: 12,
      professional: 7,
    });
  });
});
