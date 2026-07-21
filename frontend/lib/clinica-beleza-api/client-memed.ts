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
  timbrado: {
    get: () => apiGet("/memed/timbrado/"),
  },

  status: () =>
    apiGet<{
      environment: string;
      credentials_configured: boolean;
      production_keys_configured: boolean;
      timbrado: { tem_timbrado: boolean; pdf_nome?: string | null };
      profissionais_com_cpf: number;
      ready_for_production: boolean;
    }>("/memed/status/"),

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

  excluirPrescricao: (consultaId: number, prescricaoId: number) =>
    clinicaBelezaFetch(`/consultas/${consultaId}/prescricoes/${prescricaoId}/`, { method: "DELETE" })
      .then((res) => { if (!res.ok) throw new Error("Erro ao excluir prescrição"); }),
};

export type MemedApi = typeof memedApi;
