/**
 * Namespace lazy-loaded da API de prontuário (PDF).
 */
import type { ProntuarioData } from "./types-entities";
import { clinicaBelezaFetch } from "./fetch";
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
};

export type ProntuarioApi = typeof prontuarioApi;
