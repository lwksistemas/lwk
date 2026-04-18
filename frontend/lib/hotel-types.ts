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
  hospede_email?: string;
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
  status_assinatura?: 'rascunho' | 'aguardando_hospede' | 'aguardando_funcionario' | 'concluido';
  conteudo_confirmacao?: string;
  nome_hospede_assinatura?: string;
  nome_funcionario_assinatura?: string;
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

/** Formata data ISO (YYYY-MM-DD) para DD/MM/YYYY */
export function formatDateBR(dateStr: string | null | undefined): string {
  if (!dateStr) return '—';
  const parts = dateStr.split('-');
  if (parts.length !== 3) return dateStr;
  return `${parts[2]}/${parts[1]}/${parts[0]}`;
}

/** Classes CSS para badge de status de reserva */
export const RESERVA_STATUS_BADGE: Record<string, string> = {
  pendente: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  confirmada: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  checkin: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  checkout: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  cancelada: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  no_show: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
};

export const ASSINATURA_STATUS_LABEL: Record<string, string> = {
  rascunho: 'Não enviada',
  aguardando_hospede: 'Aguardando Hóspede',
  aguardando_funcionario: 'Aguardando Funcionário',
  concluido: 'Assinada',
};

export const ASSINATURA_STATUS_BADGE: Record<string, string> = {
  rascunho: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
  aguardando_hospede: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  aguardando_funcionario: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  concluido: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
};

/** Classes CSS para badge de status de quarto */
export const QUARTO_STATUS_BADGE: Record<string, string> = {
  disponivel: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  ocupado: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  limpeza: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  manutencao: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
};

/** Classes CSS para badge de status de governança */
export const GOVERNANCA_STATUS_BADGE: Record<string, string> = {
  aberta: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  em_andamento: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  concluida: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
};

/** Classes CSS para badge de tipo de governança */
export const GOVERNANCA_TIPO_BADGE: Record<string, string> = {
  limpeza: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-300',
  manutencao: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
  enxoval: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  outros: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
};
