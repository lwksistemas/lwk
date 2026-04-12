/**
 * Utilitários para o CRM Vendas.
 * Centraliza helpers de tratamento de respostas da API.
 */

/**
 * Normaliza resposta paginada ou array da API para um array de itens.
 * A API pode retornar { results: T[] } (DRF pagination) ou T[] diretamente.
 */
export function normalizeListResponse<T>(data: T[] | { results: T[] } | null | undefined): T[] {
  if (data == null) return [];
  if (Array.isArray(data)) return data;
  return (data as { results: T[] }).results ?? [];
}

/** Extrai mensagem de erro de respostas DRF/axios (uso comum em páginas CRM). */
export function getCrmApiErrorDetail(err: unknown, fallback: string): string {
  const e = err as { response?: { data?: { detail?: string } } };
  return e.response?.data?.detail ?? fallback;
}

/** Dispara download de um blob no navegador (PDF, etc.). */
export function downloadBlobAsFile(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

/** Mensagem de sucesso após enviar documento ao cliente por canal. */
export function crmMensagemEnvioCanalSucesso(canal: 'email' | 'whatsapp'): string {
  return `Enviado por ${canal === 'email' ? 'e-mail' : 'WhatsApp'} com sucesso!`;
}

/** Formata valor monetário para exibição (listagens/modais CRM).
 * @deprecated Use formatCurrency de financeiro-helpers.ts para novos componentes.
 */
export function formatCrmBrl(valor: string | number | null | undefined): string {
  if (valor == null || valor === '') return '';
  const n = typeof valor === 'string' ? parseFloat(valor) : valor;
  if (Number.isNaN(n)) return String(valor);
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}
