import { describe, expect, it } from "vitest";
import type { ProntuarioData } from "@/lib/clinica-beleza-api";
import {
  documentoCardKey,
  extractAnamneseDisplayFields,
  extractEvolucaoDisplayFields,
  getProntuarioDocsForTab,
  isProntuarioDocTab,
  prontuarioTipoLabel,
  resolvePatientDisplayName,
} from "@/components/clinica-beleza/prontuario/prontuario-utils";

const emptyProntuario = (): ProntuarioData => ({
  receituario: [],
  pedido_exame: [],
  atestado: [],
  documento_personalizado: [],
  evolucao: [],
  anamnese: null,
});

describe("isProntuarioDocTab", () => {
  it("identifica abas de documentos", () => {
    expect(isProntuarioDocTab("receituario")).toBe(true);
    expect(isProntuarioDocTab("anamnese")).toBe(false);
  });
});

describe("getProntuarioDocsForTab", () => {
  it("retorna documentos da seção", () => {
    const data = emptyProntuario();
    data.receituario = [
      {
        id: 1,
        tipo: "receituario",
        titulo: "Rx",
        conteudo: "texto",
        professional_name: null,
        consulta_id: null,
        created_at: null,
        source: "documento_clinico",
      },
    ];
    expect(getProntuarioDocsForTab(data, "receituario")).toHaveLength(1);
  });
});

describe("prontuarioTipoLabel", () => {
  it("traduz tipos conhecidos", () => {
    expect(prontuarioTipoLabel("atestado")).toBe("Atestado");
    expect(prontuarioTipoLabel("outro")).toBe("outro");
  });
});

describe("resolvePatientDisplayName", () => {
  it("prioriza name e depois nome", () => {
    expect(resolvePatientDisplayName({ name: "Ana" })).toBe("Ana");
    expect(resolvePatientDisplayName({ nome: "Maria" })).toBe("Maria");
    expect(resolvePatientDisplayName({})).toBe("Paciente");
  });
});

describe("extractAnamneseDisplayFields", () => {
  it("filtra campos vazios", () => {
    const fields = extractAnamneseDisplayFields({
      id: 1,
      queixa_principal: "Dor",
      historico_medico: "",
      medicamentos_uso: "",
      alergias: "",
      tipo_pele: "",
      observacoes: "",
      created_at: null,
      updated_at: null,
    });
    expect(fields).toHaveLength(1);
    expect(fields[0].label).toBe("Queixa Principal");
  });
});

describe("extractEvolucaoDisplayFields", () => {
  it("retorna apenas campos preenchidos", () => {
    const fields = extractEvolucaoDisplayFields({
      id: 1,
      descricao: "Evoluiu bem",
      procedimento_realizado: "",
      produtos_utilizados: "",
      orientacoes: "",
      professional_name: null,
      consulta_id: null,
      created_at: null,
    });
    expect(fields).toHaveLength(1);
  });
});

describe("documentoCardKey", () => {
  it("combina source e id", () => {
    expect(
      documentoCardKey({
        id: 5,
        source: "memed",
        tipo: "receituario",
        titulo: "",
        conteudo: "",
        professional_name: null,
        consulta_id: null,
        created_at: null,
      }),
    ).toBe("memed-5");
  });
});
