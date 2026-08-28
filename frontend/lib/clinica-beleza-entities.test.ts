import { describe, expect, it } from "vitest";
import { matchesPatientSearchQuery } from "@/lib/clinica-beleza-entities";

const patient = {
  name: "Maria Silva Santos",
  cpf: "123.456.789-00",
  telefone: "(11) 98888-7777",
  email: "maria@exemplo.com",
};

describe("matchesPatientSearchQuery", () => {
  it("acha por trecho do nome", () => {
    expect(matchesPatientSearchQuery(patient, "silva")).toBe(true);
    expect(matchesPatientSearchQuery(patient, "Maria")).toBe(true);
  });

  it("acha CPF com e sem pontuação", () => {
    expect(matchesPatientSearchQuery(patient, "123.456.789-00")).toBe(true);
    expect(matchesPatientSearchQuery(patient, "12345678900")).toBe(true);
    expect(matchesPatientSearchQuery(patient, "123.456")).toBe(true);
    expect(matchesPatientSearchQuery(patient, "123456")).toBe(true);
  });

  it("não confunde outro CPF", () => {
    expect(matchesPatientSearchQuery(patient, "987.654.321-00")).toBe(false);
  });
});
