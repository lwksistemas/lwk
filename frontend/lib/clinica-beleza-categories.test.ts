import {
  describe,
  expect,
  it,
} from "vitest";
import {
  groupProceduresByCategoria,
  labelTipoAgendamento,
  procedureSelectLabel,
  stripCategoriaPrefixFromNome,
} from "@/lib/clinica-beleza-categories";

describe("stripCategoriaPrefixFromNome", () => {
  it("remove SOROTERAPIA — do nome", () => {
    expect(stripCategoriaPrefixFromNome("SOROTERAPIA — ANTI-AGING", "soroterapia")).toBe(
      "ANTI-AGING",
    );
  });

  it("mantém nome sem prefixo", () => {
    expect(stripCategoriaPrefixFromNome("PREENCHIMENTO LABIAL", "facial")).toBe(
      "PREENCHIMENTO LABIAL",
    );
  });
});

describe("procedureSelectLabel", () => {
  it("não repete categoria no sufixo", () => {
    expect(
      procedureSelectLabel("SOROTERAPIA — GLUTAMINA E REPOSIÇÃO", "soroterapia", {
        includeCategorySuffix: true,
      }),
    ).toBe("GLUTAMINA E REPOSIÇÃO · Soroterapia");
  });

  it("acrescenta categoria em procedimento facial", () => {
    expect(
      procedureSelectLabel("PREENCHIMENTO LABIAL", "facial", { includeCategorySuffix: true }),
    ).toBe("PREENCHIMENTO LABIAL · Facial");
  });

  it("omite sufixo quando o filtro de categoria já está ativo", () => {
    expect(
      procedureSelectLabel("SOROTERAPIA — DETOX", "soroterapia", { includeCategorySuffix: false }),
    ).toBe("DETOX");
  });
});

describe("groupProceduresByCategoria", () => {
  it("separa procedimentos por categoria cadastrada", () => {
    const grupos = groupProceduresByCategoria([
      { id: 1, nome: "BOTOX", categoria: "injetavel" },
      { id: 2, nome: "AXILAS", categoria: "depilacao" },
      { id: 3, nome: "GLABELA", categoria: "injetavel" },
    ]);
    expect(grupos.map((g) => g.slug)).toEqual(["depilacao", "injetavel"]);
    expect(grupos.find((g) => g.slug === "injetavel")?.items.map((i) => i.id)).toEqual([1, 3]);
    expect(grupos.find((g) => g.slug === "depilacao")?.label).toBe("Depilação");
  });

  it("coloca sem categoria em Outro", () => {
    const grupos = groupProceduresByCategoria([{ id: 9, nome: "AVULSO" }]);
    expect(grupos).toHaveLength(1);
    expect(grupos[0].slug).toBe("outro");
    expect(grupos[0].label).toBe("Outro");
  });
});

describe("labelTipoAgendamento", () => {
  it("distingue só consulta de consulta com procedimentos", () => {
    expect(labelTipoAgendamento(0)).toBe("Somente consulta");
    expect(labelTipoAgendamento(1)).toBe("Consulta + 1 procedimento");
    expect(labelTipoAgendamento(3)).toBe("Consulta + 3 procedimentos");
  });
});
