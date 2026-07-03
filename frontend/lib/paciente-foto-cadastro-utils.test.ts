import { describe, expect, it } from "vitest";
import { isArquivoImagemValido, mensagemErroCamera } from "@/components/clinica-beleza/paciente-foto-cadastro/paciente-foto-cadastro-utils";

describe("mensagemErroCamera", () => {
  it("traduz erros comuns da DOMException", () => {
    expect(mensagemErroCamera(new DOMException("", "NotAllowedError"))).toContain("Permita");
    expect(mensagemErroCamera(new DOMException("", "NotFoundError"))).toContain("webcam");
    expect(mensagemErroCamera(new Error("x"))).toContain("Não foi possível");
  });
});

describe("isArquivoImagemValido", () => {
  it("aceita mime image ou extensão", () => {
    expect(isArquivoImagemValido({ type: "image/png", name: "x.bin" } as File)).toBe(true);
    expect(isArquivoImagemValido({ type: "application/pdf", name: "foto.jpg" } as File)).toBe(true);
    expect(isArquivoImagemValido({ type: "application/pdf", name: "doc.pdf" } as File)).toBe(false);
  });
});
