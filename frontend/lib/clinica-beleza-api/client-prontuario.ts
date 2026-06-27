/**
 * Namespace lazy-loaded da API de prontuário (PDF).
 */
import type { ProntuarioData } from "./types-entities";
import { clinicaBelezaFetch, getClinicaBelezaBaseUrl } from "./fetch";
import { buildClinicaBelezaListUrl, parseClinicaBelezaResponseBody } from "./pagination";

async function apiGet<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = params ? buildClinicaBelezaListUrl(path, params) : path;
  const res = await clinicaBelezaFetch(url);
  const data = await parseClinicaBelezaResponseBody(res);
  if (!res.ok) throw data;
  return data as T;
}

export const prontuarioApi = {
  get: (patientId: number, secao?: string) =>
    apiGet<ProntuarioData>(
      `/patients/${patientId}/prontuario/`,
      secao ? { secao } : undefined,
    ),
  pdfUrl: (patientId: number, secao?: string) => {
    const base = getClinicaBelezaBaseUrl();
    const query = secao ? `?secao=${secao}` : "";
    return `${base}/patients/${patientId}/prontuario/pdf/${query}`;
  },
  documentoPdfUrl: (docId: number) => {
    const base = getClinicaBelezaBaseUrl();
    return `${base}/documentos/${docId}/pdf/`;
  },
};

export type ProntuarioApi = typeof prontuarioApi;
