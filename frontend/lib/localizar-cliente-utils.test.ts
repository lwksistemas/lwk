import { describe, expect, it } from "vitest";
import {
  patientSearchRank,
  sortPatientSearchResults,
  splitPatientMatch,
} from "@/components/clinica-beleza/localizar-cliente/localizar-cliente-utils";

describe("patientSearchRank", () => {
  it("coloca quem começa com o termo na frente", () => {
    expect(patientSearchRank("RENATA AMICCI", "renata")).toBe(0);
    expect(patientSearchRank("ELISETE PRIMA RENATA CLIENTE", "renata")).toBe(1);
    expect(patientSearchRank("LUIZ BOM", "luiz")).toBe(0);
    expect(patientSearchRank("ANA LUIZA JUSTINO", "luiz")).toBe(1);
  });
});

describe("sortPatientSearchResults", () => {
  it("ordena Luiz antes de Ana Luiza", () => {
    const sorted = sortPatientSearchResults(
      [{ nome: "ANA LUIZA JUSTINO" }, { nome: "LUIZ BOM" }, { nome: "DENIS LUIZ FERRAZ" }],
      "luiz",
    );
    expect(sorted.map((r) => r.nome)).toEqual([
      "LUIZ BOM",
      "ANA LUIZA JUSTINO",
      "DENIS LUIZ FERRAZ",
    ]);
  });
});

describe("splitPatientMatch", () => {
  it("marca o trecho buscado", () => {
    const parts = splitPatientMatch("RENATA AMICCI", "rena");
    expect(parts.some((p) => p.hit && p.text.toLowerCase() === "rena")).toBe(true);
  });
});
