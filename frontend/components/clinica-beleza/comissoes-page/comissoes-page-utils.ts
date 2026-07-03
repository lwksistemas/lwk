import type { DetalheComissao, ProfissionalComissao, RelatorioComissoesData } from "./comissoes-page-types";

export const LABEL_LINHA_CONSULTA = "Consulta";

export function isLinhaConsulta(d: DetalheComissao): boolean {
  return d.tipo_linha === "consulta" || d.procedimento_nome === LABEL_LINHA_CONSULTA;
}

export function buildComissoesCsv(data: RelatorioComissoesData, dataInicio: string, dataFim: string): string {
  const BOM = "\ufeff";
  let csv = "Profissional;Tipo;Item;Convênio;Local;Qtd;Valor (R$);Regra;Comissão (R$)\n";
  for (const p of data.profissionais) {
    for (const d of p.detalhes.filter(isLinhaConsulta)) {
      csv +=
        `${p.nome};Consulta;${d.local_nome || "Consulta"};;${d.local_nome || ""};${d.qtd};` +
        `${d.valor_consulta.toFixed(2)};${d.regra_consulta || ""};${d.comissao_consulta.toFixed(2)}\n`;
    }
    for (const d of p.detalhes.filter((x) => !isLinhaConsulta(x))) {
      csv +=
        `${p.nome};Procedimento;${d.procedimento_nome};${d.convenio_nome || ""};${d.local_nome || ""};${d.qtd};` +
        `${d.valor_procedimento.toFixed(2)};${d.regra_procedimento};${d.comissao_procedimento.toFixed(2)}\n`;
    }
    csv +=
      `${p.nome};Resumo consulta;;;${p.total_atendimentos};${p.valor_consulta.toFixed(2)};;${p.comissao_consulta.toFixed(2)}\n`;
    csv +=
      `${p.nome};Resumo procedimentos;;;;${p.valor_procedimento.toFixed(2)};;${p.comissao_procedimento.toFixed(2)}\n`;
    csv += `${p.nome};Total;;;;${p.valor_total.toFixed(2)};;${p.comissao_total.toFixed(2)}\n`;
  }
  csv +=
    `TOTAIS;Valor consulta;;;;${data.totais.valor_consulta.toFixed(2)};;${data.totais.comissao_consulta.toFixed(2)}\n`;
  csv +=
    `TOTAIS;Valor procedimentos;;;;${data.totais.valor_procedimento.toFixed(2)};;${data.totais.comissao_procedimento.toFixed(2)}\n`;
  csv +=
    `TOTAIS;Geral;;;;${data.totais.valor_total.toFixed(2)};;${data.totais.comissao_total.toFixed(2)}\n`;
  return BOM + csv;
}

export function downloadComissoesCsv(data: RelatorioComissoesData, dataInicio: string, dataFim: string): void {
  const blob = new Blob([buildComissoesCsv(data, dataInicio, dataFim)], {
    type: "text/csv;charset=utf-8;",
  });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `comissoes_${dataInicio}_${dataFim}.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
}

export function ensureComissoesPrintStyles(): void {
  if (typeof window === "undefined") return;
  if (document.getElementById("comissoes-print-styles")) return;
  const style = document.createElement("style");
  style.id = "comissoes-print-styles";
  style.textContent = `
    @media print {
      body * { visibility: hidden; }
      .print-area, .print-area * { visibility: visible; }
      .print-area { position: absolute; left: 0; top: 0; width: 100%; }
      .no-print { display: none !important; }
      nav, aside, header { display: none !important; }
    }
  `;
  document.head.appendChild(style);
}

export function calcOutrosProcedimentos(p: ProfissionalComissao, valorProcedimentosVisivel: number): number {
  return p.valor_procedimento > valorProcedimentosVisivel + 0.009
    ? p.valor_procedimento - valorProcedimentosVisivel
    : 0;
}
