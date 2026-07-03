import type { AgrupamentoFaturamento, FaturamentoData } from "./faturamento-page-types";

export const AGRUPAMENTO_LABELS: Record<AgrupamentoFaturamento, string> = {
  profissional: "Profissional",
  procedimento: "Procedimento",
  local: "Local de Atendimento",
  convenio: "Convênio",
};

export const AGRUPAMENTO_TITULOS: Record<AgrupamentoFaturamento, string> = {
  profissional: "Faturamento por Profissional",
  procedimento: "Faturamento por Procedimento",
  local: "Faturamento por Local de Atendimento",
  convenio: "Faturamento por Convênio",
};

export function parseAgrupamentoFaturamento(value: string | null): AgrupamentoFaturamento {
  if (value === "procedimento" || value === "local" || value === "convenio") return value;
  return "profissional";
}

export function buildFaturamentoRelatorioPath(slug: string): string {
  return `/loja/${slug}/relatorios`;
}

export function buildFaturamentoCsv(
  data: FaturamentoData,
  agrupamento: AgrupamentoFaturamento,
): string {
  const BOM = "\ufeff";
  const label = AGRUPAMENTO_LABELS[agrupamento];
  let csv = `${label};Atendimentos;Valor Consultas (R$);Valor Procedimentos (R$);Valor Total (R$)\n`;
  for (const linha of data.linhas) {
    csv +=
      `${linha.nome};${linha.total_atendimentos};${linha.valor_consulta.toFixed(2)};` +
      `${linha.valor_procedimento.toFixed(2)};${linha.valor_total.toFixed(2)}\n`;
  }
  csv +=
    `TOTAL;${data.totais.total_atendimentos};${data.totais.valor_consulta.toFixed(2)};` +
    `${data.totais.valor_procedimento.toFixed(2)};${data.totais.valor_total.toFixed(2)}\n`;
  return BOM + csv;
}

export function downloadFaturamentoCsv(
  data: FaturamentoData,
  agrupamento: AgrupamentoFaturamento,
  dataInicio: string,
  dataFim: string,
): void {
  const blob = new Blob([buildFaturamentoCsv(data, agrupamento)], {
    type: "text/csv;charset=utf-8;",
  });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `faturamento_${agrupamento}_${dataInicio}_${dataFim}.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
}
