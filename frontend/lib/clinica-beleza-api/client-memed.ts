/**
 * Namespace lazy-loaded da API Memed (prescrições).
 */
import type { PrescricaoMemedItem } from "./types-memed";
import { clinicaBelezaFetch } from "./fetch";
import { buildClinicaBelezaListUrl, parseClinicaBelezaListResponse, parseClinicaBelezaResponseBody } from "./pagination";

async function apiGet<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = params ? buildClinicaBelezaListUrl(path, params) : path;
  const res = await clinicaBelezaFetch(url);
  const data = await parseClinicaBelezaResponseBody(res);
  if (!res.ok) throw data;
  return data as T;
}

async function apiPost<T>(path: string, body: unknown = {}): Promise<T> {
  const res = await clinicaBelezaFetch(path, { method: "POST", body: JSON.stringify(body) });
  const data = await parseClinicaBelezaResponseBody(res);
  if (!res.ok) throw data;
  return data as T;
}

async function apiGetList<T>(path: string): Promise<T[]> {
  const data = await apiGet<T[] | { results: T[] }>(path);
  return parseClinicaBelezaListResponse<T>(data);
}

export const memedApi = {
  token: (params?: { professional?: number; prescritor?: string; uf?: string }) =>
    apiGet<{
      token: string;
      script_url: string;
      environment: string;
      prescritor?: { nome?: string; sobrenome?: string; crm?: string; uf?: string };
      clinica?: {
        local_name?: string;
        address?: string;
        city?: string;
        state?: string;
        phone?: string;
      };
    }>("/memed/token/", params as Record<string, string> | undefined),

  timbrado: {
    get: () => apiGet("/memed/timbrado/"),
  },

  salvarPrescricao: (
    consultaId: number,
    data: {
      prescricao_id?: string;
      resumo?: string;
      itens?: unknown[];
      pdf_url?: string;
      professional?: number | null;
    },
  ) => apiPost(`/consultas/${consultaId}/prescricoes/`, data),

  listarPrescricoesConsulta: (consultaId: number) =>
    apiGet<PrescricaoMemedItem[]>(`/consultas/${consultaId}/prescricoes/`),

  listarPrescricoesPaciente: (patientId: number) =>
    apiGetList<PrescricaoMemedItem>(`/patients/${patientId}/prescricoes/`),

  obterPdf: (prescricaoId: number) =>
    apiPost<{ pdf_url: string }>(`/prescricoes-memed/${prescricaoId}/pdf/`, {}),
};

export type MemedApi = typeof memedApi;
