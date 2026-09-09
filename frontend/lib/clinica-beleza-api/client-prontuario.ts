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

/**
 * Normaliza um item de documento do prontuário. O backend serializa com
 * `tipo_fonte`/`profissional_nome`/`data`, mas o app usa `source`/
 * `professional_name`/`created_at`. Sem este mapeamento, `doc.source` fica
 * undefined e o botão "Visualizar" não sabe se é Memed (não abre o PDF).
 */
export function normalizarDocItem(raw: Record<string, unknown>): Record<string, unknown> {
  const tipoFonte = raw.tipo_fonte ?? raw.source;
  const source = tipoFonte === "prescricao_memed" || tipoFonte === "memed" ? "memed" : "documento_clinico";
  return {
    ...raw,
    source,
    professional_name: raw.professional_name ?? raw.profissional_nome ?? null,
    created_at: raw.created_at ?? raw.data ?? null,
  };
}

function normalizarProntuario(data: ProntuarioData): ProntuarioData {
  const secoesDoc: Array<keyof ProntuarioData> = [
    "receituario",
    "pedido_exame",
    "atestado",
    "documento_personalizado",
  ];
  const out = { ...data } as Record<string, unknown>;
  for (const secao of secoesDoc) {
    const lista = data[secao];
    if (Array.isArray(lista)) {
      out[secao] = lista.map((item) =>
        normalizarDocItem(item as unknown as Record<string, unknown>),
      );
    }
  }
  return out as unknown as ProntuarioData;
}

export const prontuarioApi = {
  get: async (patientId: number, secao?: string) => {
    const data = await apiGet<ProntuarioData>(
      `/patients/${patientId}/prontuario/`,
      secao ? { secao } : undefined,
    );
    return normalizarProntuario(data);
  },
};

export type ProntuarioApi = typeof prontuarioApi;
