import { describe, expect, it } from "vitest";
import {
  buildProtocoloSaveBody,
  buildProtocolosListPath,
  extractProtocoloSaveError,
  protocolToForm,
  validateProtocoloForm,
} from "@/components/clinica-beleza/protocolos-page/protocolos-page-utils";
import {
  EMPTY_PROTOCOLO_FORM,
  type Protocol,
} from "@/components/clinica-beleza/protocolos-page/protocolos-page-types";

const protocolo = (overrides: Partial<Protocol> = {}): Protocol => ({
  id: 1,
  nome: "Protocolo A",
  procedure: 5,
  tempo_estimado: 45,
  descricao: "Descrição",
  ...overrides,
});

describe("buildProtocolosListPath", () => {
  it("inclui categoria na query quando informada", () => {
    expect(buildProtocolosListPath("estetica")).toBe("/protocolos?categoria=estetica");
    expect(buildProtocolosListPath("")).toBe("/protocolos");
  });
});

describe("protocolToForm", () => {
  it("mapeia protocolo para estado do formulário", () => {
    const form = protocolToForm(protocolo({ tempo_estimado: 60, execucao: "Passo 1" }));
    expect(form.nome).toBe("Protocolo A");
    expect(form.procedure).toBe("5");
    expect(form.tempo_estimado).toBe("60");
    expect(form.execucao).toBe("Passo 1");
  });
});

describe("validateProtocoloForm", () => {
  it("exige nome e procedimento", () => {
    expect(validateProtocoloForm(EMPTY_PROTOCOLO_FORM)).toBe("Nome e procedimento são obrigatórios.");
    expect(
      validateProtocoloForm({ ...EMPTY_PROTOCOLO_FORM, nome: "Teste", procedure: "1" }),
    ).toBeNull();
  });
});

describe("buildProtocoloSaveBody", () => {
  it("monta payload com campos trimados", () => {
    const body = buildProtocoloSaveBody({
      ...EMPTY_PROTOCOLO_FORM,
      nome: "  Protocolo  ",
      procedure: "3",
      tempo_estimado: "40",
      execucao: " Passos ",
    });
    expect(body.nome).toBe("Protocolo");
    expect(body.procedure).toBe(3);
    expect(body.tempo_estimado).toBe(40);
    expect(body.execucao).toBe("Passos");
  });
});

describe("extractProtocoloSaveError", () => {
  it("detecta SESSION_ENDED", () => {
    expect(extractProtocoloSaveError(new Error("SESSION_ENDED"))).toBe("SESSION_ENDED");
  });

  it("extrai mensagem da API", () => {
    expect(extractProtocoloSaveError({ error: "Duplicado" })).toBe("Duplicado");
  });
});
