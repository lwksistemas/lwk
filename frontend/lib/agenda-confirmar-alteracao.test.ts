import { describe, expect, it } from "vitest";
import { descreverAlteracaoAgenda } from "./agenda-confirmar-alteracao";

describe("descreverAlteracaoAgenda", () => {
  const antes = new Date(2026, 8, 30, 17, 0, 0);
  const depois = new Date(2026, 8, 30, 18, 0, 0);

  it("pede confirmação ao mover o horário", () => {
    const texto = descreverAlteracaoAgenda({
      nome: "FERNANDA OLIVEIRA DE CARVALHO",
      inicioAntes: antes,
      inicioDepois: depois,
    });
    expect(texto.titulo).toBe("Confirmar alteração");
    expect(texto.linhas).toEqual([
      "Mover FERNANDA OLIVEIRA DE CARVALHO de 17:00 para 18:00.",
    ]);
  });

  it("pede confirmação ao trocar o profissional", () => {
    const texto = descreverAlteracaoAgenda({
      nome: "FERNANDA OLIVEIRA DE CARVALHO",
      inicioAntes: antes,
      inicioDepois: antes,
      profissionalAntes: "MARINA GARCIA RAMOS",
      profissionalDepois: "NAYARA DA SILVA DE SOUZA",
    });
    expect(texto.linhas).toEqual([
      "Trocar o profissional de MARINA GARCIA RAMOS para NAYARA DA SILVA DE SOUZA.",
    ]);
  });

  it("pede confirmação ao mudar a duração", () => {
    const texto = descreverAlteracaoAgenda({
      nome: "Evento interno",
      inicioAntes: antes,
      inicioDepois: antes,
      duracaoAntes: 60,
      duracaoDepois: 90,
    });
    expect(texto.linhas).toEqual([
      "Alterar a duração de 60 min para 90 min.",
    ]);
  });
});
