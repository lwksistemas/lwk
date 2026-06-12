/**
 * Utilitários para o CRM Vendas.
 * Centraliza helpers de tratamento de respostas da API.
 */
import apiClient from '@/lib/api-client';
import { formatApiErrorBody } from '@/lib/api-errors';
import { applyTelefoneInternacionalPayload } from '@/lib/format-br';

export type CrmLeadFormPayloadInput = {
  nome: string;
  empresa: string;
  cpf_cnpj: string;
  email: string;
  telefone: string;
  origem: string;
  status: string;
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  cidade: string;
  uf: string;
  observacoes: string;
};

/** Monta payload JSON para POST/PATCH de leads (telefone em 55...). */
export function buildCrmLeadPayload(form: CrmLeadFormPayloadInput): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    nome: form.nome.trim(),
    origem: form.origem,
    status: form.status,
    empresa: form.empresa.trim() || undefined,
    cpf_cnpj: form.cpf_cnpj.trim() || undefined,
    email: form.email.trim() || undefined,
    cep: form.cep.trim() || undefined,
    logradouro: form.logradouro.trim() || undefined,
    numero: form.numero.trim() || undefined,
    complemento: form.complemento.trim() || undefined,
    bairro: form.bairro.trim() || undefined,
    cidade: form.cidade.trim() || undefined,
    uf: form.uf.trim().toUpperCase() || undefined,
    observacoes: form.observacoes.trim() || undefined,
  };
  if (form.telefone.trim()) {
    payload.telefone = form.telefone.trim();
  }
  return applyTelefoneInternacionalPayload(payload);
}

/**
 * Normaliza resposta paginada ou array da API para um array de itens.
 * A API pode retornar { results: T[] } (DRF pagination) ou T[] diretamente.
 */
export function normalizeListResponse<T>(data: T[] | { results: T[] } | null | undefined): T[] {
  if (data == null) return [];
  if (Array.isArray(data)) return data;
  return (data as { results: T[] }).results ?? [];
}

export type CrmPaginatedResponse<T> = {
  results: T[];
  count: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
  hasPrevious: boolean;
  totalPages: number;
};

/** Uma página de listagem paginada do DRF. */
export async function fetchCrmPaginatedPage<T>(
  path: string,
  page: number,
  pageSize = 50,
  params: Record<string, string | number> = {},
): Promise<CrmPaginatedResponse<T>> {
  const res = await apiClient.get<
    T[] | { results: T[]; count: number; next: string | null; previous: string | null }
  >(path, {
    params: { ...params, page, page_size: pageSize },
  });
  const data = res.data;
  if (Array.isArray(data)) {
    return {
      results: data,
      count: data.length,
      page: 1,
      pageSize: data.length || pageSize,
      hasNext: false,
      hasPrevious: false,
      totalPages: 1,
    };
  }
  const count = data.count ?? (data.results?.length ?? 0);
  const totalPages = Math.max(1, Math.ceil(count / pageSize));
  return {
    results: data.results ?? [],
    count,
    page,
    pageSize,
    hasNext: Boolean(data.next),
    hasPrevious: Boolean(data.previous),
    totalPages,
  };
}

/** Busca todas as páginas de um endpoint paginado do DRF (até maxPages). */
export async function fetchAllPaginatedResults<T>(
  path: string,
  params: Record<string, string | number> = {},
  pageSize = 100,
  maxPages = 20,
): Promise<T[]> {
  const items: T[] = [];
  for (let page = 1; page <= maxPages; page += 1) {
    const res = await apiClient.get<T[] | { results: T[]; next: string | null }>(path, {
      params: { ...params, page, page_size: pageSize },
    });
    const data = res.data;
    if (Array.isArray(data)) return data;
    items.push(...(data.results ?? []));
    if (!data.next) break;
  }
  return items;
}

/** Extrai mensagem de erro de respostas DRF/axios (uso comum em páginas CRM). */
export function getCrmApiErrorDetail(err: unknown, fallback: string): string {
  const e = err as { response?: { data?: unknown }; code?: string; message?: string };
  const fromBody = formatApiErrorBody(e.response?.data);
  if (fromBody) return fromBody;
  if (e.code === 'ECONNABORTED') {
    return 'Tempo esgotado. Verifique sua conexão e tente novamente.';
  }
  if (e.message && !e.response) {
    return e.message;
  }
  return fallback;
}

import { downloadBlobAsFile } from '@/lib/download-blob';

export { downloadBlobAsFile };

/** Mensagem de sucesso após enviar documento ao cliente por canal. */
export function crmMensagemEnvioCanalSucesso(canal: 'email' | 'whatsapp'): string {
  return `Enviado por ${canal === 'email' ? 'e-mail' : 'WhatsApp'} com sucesso!`;
}

/** Formata valor monetário para exibição (listagens/modais CRM).
 * @deprecated Use formatCurrency de financeiro-helpers.ts para novos componentes.
 */
export type CrmDocumentoTipo = 'propostas' | 'contratos';

function crmSanitizeTituloArquivo(titulo: string): string {
  return titulo.replace(/\s+/g, '_');
}

export function crmDocumentoDownloadFilename(
  tipo: CrmDocumentoTipo,
  id: number,
  titulo: string,
  ext: 'pdf' | 'docx',
): string {
  const prefix = tipo === 'propostas' ? 'proposta' : 'contrato';
  return `${prefix}_${id}_${crmSanitizeTituloArquivo(titulo)}.${ext}`;
}

/** Baixa PDF ou DOCX de proposta/contrato (mesma lógica das páginas de listagem). */
export async function downloadCrmDocumento(
  tipo: CrmDocumentoTipo,
  id: number,
  titulo: string,
  formato: 'pdf' | 'docx',
): Promise<void> {
  const endpoint = formato === 'pdf' ? 'download_pdf' : 'download_docx';
  const response = await apiClient.get(`/crm-vendas/${tipo}/${id}/${endpoint}/`, {
    responseType: 'blob',
  });
  const blob = response.data instanceof Blob ? response.data : new Blob([response.data]);
  downloadBlobAsFile(blob, crmDocumentoDownloadFilename(tipo, id, titulo, formato));
}

/** Título padrão da oportunidade: nome do lead (cliente), não da prestadora. */
export function gerarTituloOportunidade(lead: { nome: string; empresa?: string | null }): string {
  const nome = (lead.nome || '').trim();
  const empresa = (lead.empresa || '').trim();
  if (!nome) return 'Oportunidade';
  if (empresa && empresa.toLowerCase() !== nome.toLowerCase()) {
    return `${nome} — ${empresa}`;
  }
  return nome;
}

/** Rótulo no quadro Kanban — pessoa (lead) em destaque, senão título legível. */
export function rotuloExibicaoOportunidade(o: {
  titulo: string;
  lead_nome?: string;
  empresa_prestadora_nome?: string | null;
}): string {
  const lead = (o.lead_nome || '').trim();
  if (lead) return lead;
  const titulo = (o.titulo || '').trim();
  const prestadora = (o.empresa_prestadora_nome || '').trim();
  if (titulo && titulo !== prestadora) return titulo;
  return titulo || '—';
}

export function formatCrmBrl(valor: string | number | null | undefined): string {
  if (valor == null || valor === '') return '';
  const n = typeof valor === 'string' ? parseFloat(valor) : valor;
  if (Number.isNaN(n)) return String(valor);
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}
