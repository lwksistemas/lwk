import { describe, expect, it } from "vitest";
import { resolveColunasPacientes } from "@/lib/clinica-pacientes-colunas-config";

describe("resolveColunasPacientes", () => {
  it("usa o padrão sem Ações quando a clínica ainda não salvou", () => {
    const keys = resolveColunasPacientes(null).map((c) => c.key);
    expect(keys).toEqual(["nome", "telefone", "email", "cpf", "convenio"]);
    expect(keys).not.toContain("acoes");
  });

  it("respeita a lista salva e a ordem", () => {
    const keys = resolveColunasPacientes(["telefone", "nome", "convenio"]).map((c) => c.key);
    expect(keys).toEqual(["telefone", "nome", "convenio"]);
  });
});
