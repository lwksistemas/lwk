import { describe, expect, it } from "vitest";
import { juntarTextoFalado } from "@/lib/ditado-texto";

describe("juntarTextoFalado", () => {
  it("escreve a fala quando o campo está vazio", () => {
    expect(juntarTextoFalado("", "dor de cabeça", "")).toBe("dor de cabeça");
  });

  it("continua o texto que a profissional já tinha digitado", () => {
    expect(juntarTextoFalado("Paciente relata", "dor na testa", "")).toBe(
      "Paciente relata dor na testa",
    );
  });

  it("mostra o trecho ainda incompleto sem gravar duas vezes", () => {
    expect(juntarTextoFalado("Queixa:", "acne", " no rosto")).toBe("Queixa: acne no rosto");
  });

  it("mantém o texto quando ainda não houve fala", () => {
    expect(juntarTextoFalado("Alergia a dipirona", "  ", "")).toBe("Alergia a dipirona");
  });
});
