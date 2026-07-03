export interface ProcedimentoAtendimento {
  nome: string;
  valor: number;
  comissao: number;
  regra: string;
}

export interface AtendimentoRepasse {
  appointment_id: number;
  data_atendimento: string;
  hora_atendimento: string;
  paciente_nome: string;
  local_nome: string;
  forma_pagamento: string;
  valor_consulta: number;
  comissao_consulta: number;
  regra_consulta: string;
  procedimentos: ProcedimentoAtendimento[];
  valor_procedimentos: number;
  comissao_procedimentos: number;
  valor_atendimento: number;
  comissao_atendimento: number;
}

export interface ProfissionalRepasse {
  professional_id: number;
  nome: string;
  total_atendimentos: number;
  comissao_total: number;
  atendimentos: AtendimentoRepasse[];
}

export interface RelatorioRepasseData {
  profissionais: ProfissionalRepasse[];
  totais: {
    total_atendimentos: number;
    comissao_total: number;
  };
}
