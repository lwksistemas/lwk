/**
 * Rótulos de domínio da Clínica da Beleza (financeiro, agenda, etc.).
 */

export const CLINICA_FORMA_PAGAMENTO_LABEL: Record<string, string> = {
  CASH: 'Dinheiro',
  CREDIT_CARD: 'Crédito',
  DEBIT_CARD: 'Débito',
  PIX: 'PIX',
  TRANSFER: 'Transferência',
};

export const CLINICA_PAGAMENTO_STATUS_LABEL: Record<string, string> = {
  PENDING: 'Pendente',
  PAID: 'Pago',
  CANCELLED: 'Cancelado',
};

/** Status de agendamento (conflito offline / modal de agenda). */
export const CLINICA_AGENDA_STATUS_LABEL: Record<string, string> = {
  SCHEDULED: 'Agendado',
  CONFIRMED: 'Confirmado',
  PENDING: 'Pendente',
  IN_PROGRESS: 'Em Atendimento',
  COMPLETED: 'Concluído',
  CANCELLED: 'Cancelado',
  NO_SHOW: 'Faltou',
};
