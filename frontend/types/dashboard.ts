/**
 * Types compartilhados entre os dashboards
 */

export interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  atalho?: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
  logo?: string;
  /** Overrides de cores dos status da agenda (bg/border). Vazio = padrão LWK. */
  agenda_status_colors?: Record<string, { bg?: string; border?: string }> | null;
  /** Fundo das páginas internas. Vazio = tom claro da cor primária. */
  cor_fundo_pagina?: string | null;
}

export interface BaseEstatisticas {
  receita_mensal?: number;
}

export interface EstatisticasClinica extends BaseEstatisticas {
  agendamentos_hoje: number;
  agendamentos_mes: number;
  clientes_ativos: number;
  procedimentos_ativos: number;
  receita_mensal: number;
}

export interface EstatisticasCRM extends BaseEstatisticas {
  leads_ativos: number;
  negociacoes: number;
  vendas_mes: number;
  receita: number;
}

export interface EstatisticasServicos extends BaseEstatisticas {
  agendamentos_hoje: number;
  ordens_abertas: number;
  orcamentos_pendentes: number;
  receita_mensal: number;
}

export interface EstatisticasRestaurante extends BaseEstatisticas {
  pedidos_hoje: number;
  mesas_ocupadas: string;
  cardapio: number;
  faturamento: number;
}

export interface Agendamento {
  id: number;
  cliente_nome: string;
  cliente_telefone?: string;
  profissional_nome: string;
  procedimento_nome?: string;
  servico_nome?: string;
  data: string;
  horario: string;
  status: string;
  valor?: number;
}

export interface Lead {
  id: number;
  nome: string;
  empresa: string;
  status: string;
  valor_estimado: number | string;
  created_at?: string;
}
