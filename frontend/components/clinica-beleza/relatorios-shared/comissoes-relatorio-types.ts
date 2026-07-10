export interface DetalheComissao {
  local_nome: string;
  forma_pagamento?: string;
  procedimento_nome: string;
  tipo_linha?: "consulta" | "procedimento";
  qtd: number;
  valor_consulta: number;
  valor_procedimento: number;
  comissao_consulta: number;
  comissao_procedimento: number;
  comissao: number;
  modo_consulta: string;
  regra_consulta: string;
  modo_procedimento: string;
  regra_procedimento: string;
  convenio_nome?: string;
}

export interface ProfissionalComissao {
  professional_id: number;
  nome: string;
  total_atendimentos: number;
  valor_consulta: number;
  valor_procedimento: number;
  valor_total: number;
  comissao_consulta: number;
  comissao_procedimento: number;
  comissao_total: number;
  detalhes: DetalheComissao[];
}

export interface RelatorioComissoesData {
  profissionais: ProfissionalComissao[];
  totais: {
    total_atendimentos: number;
    valor_consulta: number;
    valor_procedimento: number;
    valor_total: number;
    comissao_consulta: number;
    comissao_procedimento: number;
    comissao_total: number;
  };
}
