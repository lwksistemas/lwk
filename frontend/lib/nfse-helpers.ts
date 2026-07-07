/**
 * Helpers compartilhados entre páginas NFS-e (loja CRM e superadmin).
 * Evita duplicar motivos de cancelamento, detecção de provedor e download de blobs.
 */

import { downloadBlobFile } from '@/lib/download-blob';

export { downloadBlobFile };

/** Opções de motivo de cancelamento (subset alinhado ao backend ISSNet). */
export const NFSE_CANCELAMENTO_OPCOES: Record<string, string> = {
  '1': 'Erro na emissão',
  '2': 'Serviço não prestado',
  '4': 'Duplicidade da nota',
};

export const NFSE_ISSNET_ERRO_EMISSAO_AVISO =
  'A prefeitura/ISSNet costuma recusar cancelamento por "Erro na emissão" (E206) e exigir substituição.\n\n' +
  'Recomendado: usar "2 - Serviço não prestado" ou "4 - Duplicidade".\n\nDeseja continuar mesmo assim?';

export function nfseIdentificador(nf: {
  numero_nf?: string | null;
  numero_rps?: number | null;
  id?: number;
}): string {
  if (nf.numero_nf) return nf.numero_nf;
  if (nf.numero_rps != null) return `RPS ${nf.numero_rps}`;
  return String(nf.id ?? '');
}

export function buildCancelamentoPromptText(identificador: string): string {
  const linhas = Object.entries(NFSE_CANCELAMENTO_OPCOES)
    .map(([cod, label]) => `${cod} - ${label}`)
    .join('\n');
  return `CANCELAR NFS-e ${identificador}?\n\nEscolha o motivo:\n${linhas}\n\nDigite o número (1, 2 ou 4):`;
}

/** Monta texto do motivo enviado à API (descrição opcional ou label padrão). */
export function montarMotivoCancelamento(codigo: string, textoOpcional?: string): string {
  const trim = (textoOpcional || '').trim();
  return trim || NFSE_CANCELAMENTO_OPCOES[codigo] || '';
}

export function isIssnetProvedor(provedor?: string | null): boolean {
  return (provedor || '').toLowerCase() === 'issnet';
}

export type NfseProvedorRef = {
  provedor?: string | null;
  provedor_display?: string | null;
};

export function nfUsaIssnet(nf: NfseProvedorRef, lojaProvedor?: string): boolean {
  const p = (nf.provedor || '').toLowerCase();
  const d = (nf.provedor_display || '').toLowerCase();
  const loja = (lojaProvedor || '').toLowerCase();
  if (p === 'issnet' || d.includes('issnet')) return true;
  return loja === 'issnet';
}

export function nfseSyncEndpoint(
  nf: NfseProvedorRef,
  lojaProvedor?: string,
): 'sincronizar-issnet' | 'sincronizar-asaas' | null {
  if (nfUsaIssnet(nf, lojaProvedor)) return 'sincronizar-issnet';
  if ((nf.provedor || '').toLowerCase() === 'asaas' || (lojaProvedor || '').toLowerCase() === 'asaas') {
    return 'sincronizar-asaas';
  }
  return null;
}

export type NfseCancelamentoEscolha = { codigo: string; motivo: string };

export function openBlobInNewTab(blob: Blob, mime = 'application/pdf'): void {
  const typed = blob.type ? blob : new Blob([blob], { type: mime });
  const url = window.URL.createObjectURL(typed);
  window.open(url, '_blank');
  setTimeout(() => window.URL.revokeObjectURL(url), 10000);
}

type ApiBlobResponse = { data: unknown; headers?: Record<string, string | undefined> };

/** Abre PDF: JSON com URL (Asaas/ISSNet DANFE) ou blob inline. */
export async function openPdfFromApiBlobResponse(res: ApiBlobResponse): Promise<void> {
  const contentType = res.headers?.['content-type'] || '';
  if (contentType.includes('application/json')) {
    const text = await (res.data as Blob).text();
    const json = JSON.parse(text) as { url?: string };
    if (json.url) {
      window.open(json.url, '_blank');
      return;
    }
  }
  const blob =
    res.data instanceof Blob ? res.data : new Blob([res.data as BlobPart], { type: 'application/pdf' });
  openBlobInNewTab(blob);
}

/** Resposta JSON com campo url (DANFE ISSNet / link Asaas). */
export function openPdfFromJsonUrl(data: unknown): boolean {
  if (data && typeof data === 'object' && 'url' in data && typeof (data as { url: unknown }).url === 'string') {
    window.open((data as { url: string }).url, '_blank');
    return true;
  }
  return false;
}

/** Classes Tailwind para badge de status na listagem NFS-e (loja CRM). */
export const NFSE_STATUS_TAILWIND: Record<string, string> = {
  emitida: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
  cancelada: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
  erro: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
};

const NFSE_STATUS_TAILWIND_FALLBACK =
  'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';

export function nfseStatusTailwindClass(status: string): string {
  return NFSE_STATUS_TAILWIND[status] || NFSE_STATUS_TAILWIND_FALLBACK;
}

export function nfsePodeBaixar(status: string): boolean {
  return status === 'emitida' || status === 'cancelada';
}

export function nfsePodeSincronizar(
  status: string,
  nf?: NfseProvedorRef,
  lojaProvedor?: string,
): boolean {
  if (status === 'erro' || status === 'pendente') return true;
  if (status === 'cancelada' && nf && nfUsaIssnet(nf, lojaProvedor)) return true;
  return false;
}

export function nfsePodeEnviarWhatsapp(status: string): boolean {
  return status === 'emitida';
}

export function nfsePodeCancelar(status: string): boolean {
  return status === 'emitida';
}

/** Superadmin: excluir registro com erro ou pendente. */
export function nfsePodeExcluirSuperadmin(status: string): boolean {
  return status === 'erro' || status === 'pendente';
}

/** Loja CRM: excluir quando ainda não emitida/cancelada. */
export function nfsePodeExcluirLoja(status: string): boolean {
  return status !== 'emitida' && status !== 'cancelada';
}

export function nfseProvedorLabel(provedor: string): string {
  switch (provedor) {
    case 'nacional':
      return '🇧🇷 Nacional';
    case 'issnet':
      return '🏛️ ISSNet';
    case 'asaas':
      return '🔵 Asaas';
    default:
      return provedor;
  }
}

export function blobFromApiData(data: unknown, mime?: string): Blob {
  if (data instanceof Blob) return data;
  return new Blob([data as BlobPart], mime ? { type: mime } : undefined);
}

/** Filtra listagem NFS-e por número, tomador ou CPF/CNPJ (busca local na loja). */
export function filtrarNfsesPorBusca<T extends {
  numero_nf?: string | null;
  tomador_nome?: string | null;
  tomador_cpf_cnpj?: string | null;
}>(nfses: T[], busca: string): T[] {
  if (!busca.trim()) return nfses;
  const q = busca.toLowerCase();
  return nfses.filter(
    (nf) =>
      (nf.numero_nf ?? '').toLowerCase().includes(q) ||
      (nf.tomador_nome ?? '').toLowerCase().includes(q) ||
      (nf.tomador_cpf_cnpj ?? '').includes(busca),
  );
}

export async function downloadNfseXmlBlob(
  fetchBlob: () => Promise<{ data: unknown }>,
  filename: string,
): Promise<void> {
  const res = await fetchBlob();
  downloadBlobFile(blobFromApiData(res.data), filename);
}

export type NfseEmitirResponse = {
  success?: boolean;
  queued?: boolean;
  message?: string;
  error?: string;
};

export type NfseEmissaoResult = {
  queued: boolean;
  message: string;
};

/** Interpreta resposta de POST /nfse/emitir/ (201 imediato ou 202 enfileirado). */
export function parseNfseEmissaoResult(status: number, data: NfseEmitirResponse): NfseEmissaoResult {
  const queued = Boolean(data.queued) || status === 202;
  if (queued) {
    return {
      queued: true,
      message: data.message || 'Nota enfileirada. Aguardando emissão…',
    };
  }
  return {
    queued: false,
    message: data.message || 'NFS-e emitida com sucesso.',
  };
}
