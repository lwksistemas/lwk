/**
 * Helpers para o sistema financeiro
 * Funções reutilizáveis seguindo DRY (Don't Repeat Yourself)
 */

/**
 * Formata valor para moeda brasileira (aceita number ou string)
 */
export const formatCurrency = (value: number | string): string => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (Number.isNaN(num)) return 'R$ 0,00';
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(num);
};

/**
 * Formata data para padrão brasileiro (dd/mm/yyyy).
 * Usa apenas a parte da data (split T) para evitar problemas de timezone.
 * @param fallback - texto quando date é null/undefined/vazio (default '-')
 */
export const formatDate = (date: string | null | undefined, fallback = '-'): string => {
  if (date == null || date === '') return fallback;
  const part = String(date).split('T')[0];
  const [year, month, day] = part.split('-');
  if (!year || !month || !day) return fallback;
  return `${day}/${month}/${year}`;
};

/**
 * Formata data e hora para padrão brasileiro (dd/mm/yyyy, hh:mm)
 */
export const formatDateTime = (date: string | null | undefined, fallback = '-'): string => {
  if (date == null || date === '') return fallback;
  try {
    return new Date(date).toLocaleString('pt-BR');
  } catch {
    return fallback;
  }
};

/**
 * Retorna classe CSS para badge de status
 */
export const getStatusBadgeClass = (status: string): string => {
  const badges: Record<string, string> = {
    pago: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300',
    pendente: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300',
    atrasado: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300',
    cancelado: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
  };
  return badges[status] || badges.pendente;
};

/**
 * Retorna ícone para tipo de transação
 */
export const getTipoIcon = (tipo: string): string => {
  return tipo === 'receita' ? '💰' : '💸';
};

/**
 * Retorna cor para tipo de transação
 */
export const getTipoColor = (tipo: string): string => {
  return tipo === 'receita' ? '#10B981' : '#EF4444';
};

/**
 * Opções de forma de pagamento
 */
export const FORMAS_PAGAMENTO = [
  { value: 'dinheiro', label: 'Dinheiro' },
  { value: 'pix', label: 'PIX' },
  { value: 'cartao_credito', label: 'Cartão de Crédito' },
  { value: 'cartao_debito', label: 'Cartão de Débito' },
  { value: 'transferencia', label: 'Transferência' },
  { value: 'boleto', label: 'Boleto' },
  { value: 'cheque', label: 'Cheque' },
  { value: 'outros', label: 'Outros' }
];

/**
 * Opções de status
 */
export const STATUS_OPTIONS = [
  { value: 'pendente', label: 'Pendente' },
  { value: 'pago', label: 'Pago' },
  { value: 'cancelado', label: 'Cancelado' }
];
