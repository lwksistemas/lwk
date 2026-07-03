export type AgrupamentoFaturamento = "profissional" | "procedimento" | "local" | "convenio";

export interface LinhaFaturamento {
  nome: string;
  total_atendimentos: number;
  valor_consulta: number;
  valor_procedimento: number;
  valor_total: number;
}

export interface FaturamentoData {
  linhas: LinhaFaturamento[];
  totais: {
    total_atendimentos: number;
    valor_consulta: number;
    valor_procedimento: number;
    valor_total: number;
  };
  agrupamento: string;
}
