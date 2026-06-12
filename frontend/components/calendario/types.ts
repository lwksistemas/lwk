export interface Agendamento {
  id: number;
  cliente_nome: string;
  cliente_telefone: string;
  profissional_nome: string;
  procedimento_nome: string;
  data: string;
  horario: string;
  status: string;
  valor: number;
  observacoes?: string;
}

export interface BloqueioAgenda {
  id: number;
  titulo: string;
  tipo: string;
  tipo_nome?: string;
  data_inicio: string;
  data_fim: string;
  horario_inicio?: string | null;
  horario_fim?: string | null;
  profissional?: number | null;
  profissional_nome?: string | null;
  observacoes?: string;
  is_active?: boolean;
}

export interface HorarioTrabalho {
  dia_semana: number;
  hora_entrada: string;
  hora_saida: string;
  intervalo_inicio?: string | null;
  intervalo_fim?: string | null;
  ativo?: boolean;
}

export interface Profissional {
  id: number;
  nome: string;
  horarios_trabalho?: HorarioTrabalho[];
}

export interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
  cor_secundaria: string;
}

export type VisualizacaoTipo = 'dia' | 'semana' | 'mes';

export interface CalendarioAgendamentosProps {
  loja: LojaInfo;
  /** Quando true, não renderiza o bloco "📅 Calendário" + período + legenda (o pai coloca no menu superior) */
  headerInBar?: boolean;
  /** Chamado quando o título do período muda (ex: "28 - 6 de fevereiro de 2026") */
  onViewTitleChange?: (title: string) => void;
}
