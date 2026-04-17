/**
 * Tipos compartilhados do módulo Hotel / Pousada.
 */

export interface Hospede {
  id: number;
  nome: string;
  documento: string;
  telefone: string;
  email: string;
  observacoes: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Quarto {
  id: number;
  numero: string;
  nome: string;
  tipo: string;
  capacidade: number;
  status: 'disponivel' | 'ocupado' | 'limpeza' | 'manutencao';
  observacoes: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Tarifa {
  id: number;
  nome: string;
  tipo_quarto: string;
  valor_diaria: string | number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Reserva {
  id: number;
  hospede: number;
  hospede_nome?: string;
  quarto: number;
  quarto_numero?: string;
  quarto_nome?: string | null;
  tarifa: number | null;
  tarifa_nome?: string | null;
  data_checkin: string;
  data_checkout: string;
  adultos: number;
  criancas: number;
  canal: string;
  status: 'pendente' | 'confirmada' | 'checkin' | 'checkout' | 'cancelada' | 'no_show';
  valor_diaria: string | number;
  valor_total: string | number;
  observacoes: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface GovernancaTarefa {
  id: number;
  quarto: number;
  quarto_numero?: string;
  tipo: 'limpeza' | 'manutencao' | 'enxoval' | 'outros';
  status: 'aberta' | 'em_andamento' | 'concluida';
  descricao: string;
  prioridade: number;
  concluido_em: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export const QUARTO_STATUS_LABEL: Record<Quarto['status'], string> = {
  disponivel: 'Disponível',
  ocupado: 'Ocupado',
  limpeza: 'Limpeza',
  manutencao: 'Manutenção',
};

export const RESERVA_STATUS_LABEL: Record<Reserva['status'], string> = {
  pendente: 'Pendente',
  confirmada: 'Confirmada',
  checkin: 'Check-in',
  checkout: 'Check-out',
  cancelada: 'Cancelada',
  no_show: 'No-show',
};

export const GOVERNANCA_TIPO_LABEL: Record<GovernancaTarefa['tipo'], string> = {
  limpeza: 'Limpeza',
  manutencao: 'Manutenção',
  enxoval: 'Enxoval',
  outros: 'Outros',
};

export const GOVERNANCA_STATUS_LABEL: Record<GovernancaTarefa['status'], string> = {
  aberta: 'Aberta',
  em_andamento: 'Em andamento',
  concluida: 'Concluída',
};
