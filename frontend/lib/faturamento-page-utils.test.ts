import { describe, expect, it } from "vitest";
import {
  AGRUPAMENTO_TITULOS,
  buildFaturamentoCsv,
  buildFaturamentoRelatorioPath,
  parseAgrupamentoFaturamento,
} from "@/components/clinica-beleza/relatorios-shared/faturamento-relatorio-utils";

describe("parseAgrupamentoFaturamento", () => {
  it("aceita valores válidos e usa profissional como padrão", () => {
    expect(parseAgrupamentoFaturamento("local")).toBe("local");
    expect(parseAgrupamentoFaturamento(null)).toBe("profissional");
    expect(parseAgrupamentoFaturamento("invalido")).toBe("profissional");
  });
});

describe("buildFaturamentoRelatorioPath", () => {
  it("monta path de relatórios", () => {
    expect(buildFaturamentoRelatorioPath("x")).toBe("/loja/x/relatorios");
  });
});

describe("buildFaturamentoCsv", () => {
  it("inclui BOM e linha total", () => {
    const csv = buildFaturamentoCsv(
      {
        linhas: [{ nome: "Ana", total_atendimentos: 1, valor_consulta: 100, valor_procedimento: 50, valor_total: 150 }],
        totais: { total_atendimentos: 1, valor_consulta: 100, valor_procedimento: 50, valor_total: 150 },
        agrupamento: "profissional",
      },
      "profissional",
    );
    expect(csv.startsWith("\ufeff")).toBe(true);
    expect(csv).toContain("TOTAL;1");
    expect(AGRUPAMENTO_TITULOS.profissional).toContain("Profissional");
  });
});
