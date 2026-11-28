import axios from "axios";
import { getPrimaryApiBaseUrl } from "@/lib/api-base";
import { cbDelete, cbGet, cbPatch, cbPost } from "./client-http";

export type NovidadeConfig = {
  id: number;
  ativo: boolean;
  intervalo_carrossel: number;
};

export type Novidade = {
  id: number;
  titulo: string;
  descricao: string;
  imagem_url: string;
  selo: string;
  condicao_especial: string;
  preco_de: string | null;
  preco_por: string | null;
  botao_texto: string;
  botao_url: string;
  beneficios: string[];
  ordem: number;
  ativo: boolean;
  data_inicio: string | null;
  data_fim: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type NovidadePayload = Partial<
  Omit<Novidade, "id" | "created_at" | "updated_at">
>;

export type NovidadesPublico = {
  ativo: boolean;
  intervalo_carrossel: number;
  itens: Novidade[];
};

export const novidadesAdminApi = {
  getConfig: () => cbGet<NovidadeConfig>("/novidades/config/"),
  patchConfig: (data: Partial<NovidadeConfig>) =>
    cbPatch<NovidadeConfig>("/novidades/config/", data),
  list: (params?: { q?: string; ativo?: string }) => {
    const qs = new URLSearchParams();
    if (params?.q) qs.set("q", params.q);
    if (params?.ativo) qs.set("ativo", params.ativo);
    const suffix = qs.toString() ? `?${qs}` : "";
    return cbGet<Novidade[]>(`/novidades/${suffix}`);
  },
  create: (data: NovidadePayload) => cbPost<Novidade>("/novidades/", data),
  update: (id: number, data: NovidadePayload) =>
    cbPatch<Novidade>(`/novidades/${id}/`, data),
  remove: (id: number) => cbDelete(`/novidades/${id}/`),
  bulk: (action: "ativar" | "desativar" | "excluir", ids: number[]) =>
    cbPost<{ ok: boolean }>("/novidades/bulk/", { action, ids }),
};

export async function novidadesPublico(slug: string): Promise<NovidadesPublico> {
  const base = getPrimaryApiBaseUrl();
  const { data } = await axios.get<NovidadesPublico>(
    `${base}/clinica-beleza/novidades/publico/${encodeURIComponent(slug)}/`,
  );
  return data;
}

export function mensagemErroNovidade(err: unknown, fallback: string): string {
  const e = err as { response?: { data?: { error?: string; detail?: string } } };
  return e.response?.data?.error || e.response?.data?.detail || fallback;
}
