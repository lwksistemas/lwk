import { describe, expect, it } from "vitest";
import { deveReportarErroApiParaSuporte } from "./erro-api-suporte";

describe("deveReportarErroApiParaSuporte", () => {
  it("não reporta recusa de negócio 400/422", () => {
    expect(deveReportarErroApiParaSuporte(400, "/agenda/create/")).toBe(false);
    expect(deveReportarErroApiParaSuporte(422, "/agenda/create/")).toBe(false);
  });

  it("reporta falha interna 500", () => {
    expect(deveReportarErroApiParaSuporte(500, "/agenda/create/")).toBe(true);
  });

  it("não reporta estados esperados da Memed", () => {
    expect(deveReportarErroApiParaSuporte(404, "/memed/token")).toBe(false);
    expect(deveReportarErroApiParaSuporte(409, "/memed/token")).toBe(false);
  });
});
