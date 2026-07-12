import { describe, expect, it } from "vitest";
import {
  buildComissoesSavePayload,
  buildProfissionalSaveBody,
  locaisDisponiveisParaConsulta,
  mapComissoesConsultaFromApi,
  mapComissoesProcedimentoFromApi,
  suggestUsernameFromName,
  validateProfissionalForm,
} from "@/components/clinica-beleza/profissional-form/profissional-form-utils";
import { DEFAULT_PROFISSIONAL_FORM } from "@/components/clinica-beleza/profissional-form/profissional-form-types";

describe("mapComissoesProcedimentoFromApi", () => {
  it("filtra apenas tipo procedimento", () => {
    const result = mapComissoesProcedimentoFromApi([
      { id: 1, tipo: "procedimento", modo: "fixo", valor: 100, procedure: 5, convenio: 2 },
      { id: 2, tipo: "consulta", modo: "percentual", valor: 30 },
    ]);
    expect(result).toHaveLength(1);
    expect(result[0].procedure).toBe(5);
    expect(result[0].valor).toBe("100");
  });
});

describe("mapComissoesConsultaFromApi", () => {
  it("expande comissão geral para todos os locais", () => {
    const locais = [
      { id: 1, nome: "Moema", is_active: true, valor_consulta: "100", created_at: "", updated_at: "" },
      { id: 2, nome: "Centro", is_active: true, valor_consulta: "100", created_at: "", updated_at: "" },
    ];
    const result = mapComissoesConsultaFromApi(
      [{ tipo: "consulta", modo: "percentual", valor: 35 }],
      locais,
    );
    expect(result).toHaveLength(2);
    expect(result[0].local_atendimento).toBe(1);
    expect(result[1].valor).toBe("35");
  });

  it("prioriza comissões por local", () => {
    const locais = [{ id: 1, nome: "Moema", is_active: true, valor_consulta: "100", created_at: "", updated_at: "" }];
    const result = mapComissoesConsultaFromApi(
      [{ tipo: "consulta", modo: "fixo", valor: 140, local_atendimento: 1, local_atendimento_nome: "Moema" }],
      locais,
    );
    expect(result).toHaveLength(1);
    expect(result[0].modo).toBe("fixo");
  });
});

describe("locaisDisponiveisParaConsulta", () => {
  it("exclui locais já usados em outras linhas", () => {
    const locais = [
      { id: 1, nome: "A", is_active: true, valor_consulta: "100", created_at: "", updated_at: "" },
      { id: 2, nome: "B", is_active: true, valor_consulta: "100", created_at: "", updated_at: "" },
    ];
    const comissoes = [
      { tipo: "consulta", modo: "percentual", valor: "30", local_atendimento: 1 },
      { tipo: "consulta", modo: "percentual", valor: "", local_atendimento: null },
    ];
    const disponiveis = locaisDisponiveisParaConsulta(locais, comissoes, 1);
    expect(disponiveis.map((l) => l.id)).toEqual([2]);
  });
});

describe("validateProfissionalForm", () => {
  it("exige nome e especialidade", () => {
    expect(validateProfissionalForm(DEFAULT_PROFISSIONAL_FORM, [], [], false)).toBe("Nome é obrigatório.");
    expect(
      validateProfissionalForm({ ...DEFAULT_PROFISSIONAL_FORM, name: "Ana" }, [], [], false),
    ).toBe("Especialidade é obrigatória.");
  });

  it("detecta local duplicado na comissão de consulta", () => {
    const form = { ...DEFAULT_PROFISSIONAL_FORM, name: "Ana", specialty: "Esteticista" };
    const comissoesConsulta = [
      { tipo: "consulta", modo: "percentual", valor: "30", local_atendimento: 1 },
      { tipo: "consulta", modo: "percentual", valor: "20", local_atendimento: 1 },
    ];
    expect(validateProfissionalForm(form, [], comissoesConsulta, false)).toBe(
      "Não repita o mesmo local na comissão de consulta.",
    );
  });
});

describe("buildProfissionalSaveBody", () => {
  it("inclui dados de acesso apenas em criação com flag", () => {
    const form = {
      ...DEFAULT_PROFISSIONAL_FORM,
      name: "Ana Silva",
      specialty: "Esteticista",
      criar_acesso: true,
      perfil: "profissional" as const,
      username: "ana",
      email: "ana@test.com",
    };
    const body = buildProfissionalSaveBody(form, null);
    expect(body.criar_acesso).toBe(true);
    expect(body.username).toBe("ana");
    expect(body.name).toBe("Ana Silva");
  });
});

describe("buildComissoesSavePayload", () => {
  it("monta payload de consulta e procedimento", () => {
    const payload = buildComissoesSavePayload(
      [{ tipo: "procedimento", modo: "fixo", valor: "200", procedure: 3, convenio: 1 }],
      [{ tipo: "consulta", modo: "percentual", valor: "35", local_atendimento: 2 }],
    );
    expect(payload).toHaveLength(2);
    expect(payload[0]).toMatchObject({ tipo: "consulta", local_atendimento: 2 });
    expect(payload[1]).toMatchObject({ tipo: "procedimento", procedure: 3, convenio: 1 });
  });
});

describe("suggestUsernameFromName", () => {
  it("normaliza acentos e usa primeiro nome", () => {
    expect(suggestUsernameFromName("José da Silva")).toBe("jose");
  });
});
