import { describe, expect, it } from "vitest";
import type { DetalheComissao } from "@/components/clinica-beleza/comissoes-page/comissoes-page-types";
import {
  buildComissoesCsv,
  calcOutrosProcedimentos,
  isLinhaConsulta,
  LABEL_LINHA_CONSULTA,
} from "@/components/clinica-beleza/comissoes-page/comissoes-page-utils";

describe("isLinhaConsulta", () => {
  it("detecta tipo_linha consulta", () => {
    const d = { tipo_linha: "consulta", procedimento_nome: "X" } as DetalheComissao;
    expect(isLinhaConsulta(d)).toBe(true);
  });

  it("detecta label Consulta no procedimento_nome", () => {
    const d = { procedimento_nome: LABEL_LINHA_CONSULTA } as DetalheComissao;
    expect(isLinhaConsulta(d)).toBe(true);
  });

  it("rejeita procedimento comum", () => {
    const d = { tipo_linha: "procedimento", procedimento_nome: "Botox" } as DetalheComissao;
    expect(isLinhaConsulta(d)).toBe(false);
  });
});

describe("buildComissoesCsv", () => {
  it("inclui BOM e cabeçalho", () => {
    const csv = buildComissoesCsv(
      {
        profissionais: [],
        totais: {
          total_atendimentos: 0,
          valor_consulta: 0,
          valor_procedimento: 0,
          valor_total: 0,
          comissao_consulta: 0,
          comissao_procedimento: 0,
          comissao_total: 0,
        },
      },
      "2026-01-01",
      "2026-01-31",
    );
    expect(csv.startsWith("\ufeff")).toBe(true);
    expect(csv).toContain("Profissional;Tipo;Item");
    expect(csv).toContain("TOTAIS;Geral");
  });
});

describe("calcOutrosProcedimentos", () => {
  it("retorna diferença quando valor visível é menor", () => {
    expect(
      calcOutrosProcedimentos(
        { valor_procedimento: 100 } as Parameters<typeof calcOutrosProcedimentos>[0],
        40,
      ),
    ).toBe(60);
  });

  it("retorna zero quando diferença é insignificante", () => {
    expect(
      calcOutrosProcedimentos(
        { valor_procedimento: 100 } as Parameters<typeof calcOutrosProcedimentos>[0],
        99.995,
      ),
    ).toBe(0);
  });
});
