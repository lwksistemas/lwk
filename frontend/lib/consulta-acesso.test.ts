import { describe, expect, it } from "vitest";
import {
  passoInicioConsulta,
  podeReabrirConsulta,
  textoModalProfissional,
} from "@/components/clinica-beleza/consultas/consulta-acesso";

describe("passoInicioConsulta", () => {
  it("inicia quando o login é o profissional da agenda", () => {
    expect(passoInicioConsulta({ professional: 4 }, 4)).toEqual({ tipo: "iniciar" });
  });

  it("pede troca quando outro profissional está na agenda", () => {
    expect(passoInicioConsulta({ professional: 4 }, 9)).toEqual({ tipo: "modal" });
  });

  it("troca e inicia só se a pessoa escolhida for quem está logado", () => {
    expect(passoInicioConsulta({ professional: 4 }, 9, 9)).toEqual({
      tipo: "trocar",
      professionalId: 9,
      iniciarDepois: true,
    });
    expect(passoInicioConsulta({ professional: 4 }, 9, 7)).toEqual({
      tipo: "trocar",
      professionalId: 7,
      iniciarDepois: false,
    });
  });
});

describe("reabrir e texto do modal", () => {
  it("reabre só quem fez a consulta finalizada", () => {
    expect(podeReabrirConsulta({ status: "COMPLETED", professional: 3 }, 3)).toBe(true);
    expect(podeReabrirConsulta({ status: "COMPLETED", professional: 3 }, 8)).toBe(false);
  });

  it("explica a troca quando já há profissional", () => {
    expect(textoModalProfissional({ professional: 2, professional_name: "Ana" }).titulo).toBe(
      "Trocar profissional",
    );
  });
});
