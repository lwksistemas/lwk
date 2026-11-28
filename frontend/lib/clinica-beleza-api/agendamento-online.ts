import axios from "axios";
import { getPrimaryApiBaseUrl } from "@/lib/api-base";
import { cbDelete, cbGet, cbPatch, cbPost, cbPut } from "./client-http";

/* ------------------------------------------------------------------ */
/* Tipos                                                               */
/* ------------------------------------------------------------------ */

export type AgendamentoOnlineConfig = {
  id: number;
  ativo: boolean;
  antecedencia_minima_horas: number;
  dias_futuros: number;
  permitir_mesmo_dia: boolean;
  intervalo_slots_minutos: number;
  modo_confirmacao: "automatico" | "secretaria";
  permitir_cancelamento_cliente: boolean;
  permitir_reagendamento_cliente: boolean;
  prazo_cancelamento_horas: number;
  reserva_pendente_minutos: number;
  enviar_confirmacao: boolean;
  enviar_lembrete: boolean;
  enviar_cancelamento: boolean;
  enviar_reagendamento: boolean;
  notificar_secretaria: boolean;
  botao_whatsapp_ativo: boolean;
  whatsapp_secretaria: string;
  nome_publico: string;
  texto_apresentacao: string;
  logo_url: string;
  banner_url: string;
  cor_primaria: string;
  cor_secundaria: string;
  endereco_publico: string;
  telefone_publico: string;
  politica_privacidade: string;
  link_publico: string;
};

export type AgendamentoOnlineHorario = {
  id?: number;
  dia_semana: number;
  hora_inicio: string;
  hora_fim: string;
  ativo: boolean;
};

export type AgendamentoOnlineProfissional = {
  professional_id: number;
  nome: string;
  especialidade: string;
  foto_url: string;
  liberado: boolean;
  bloqueado_temporariamente: boolean;
  usar_horarios_exclusivos: boolean;
  horarios: AgendamentoOnlineHorario[];
};

export type AgendamentoOnlineProcedimento = {
  id: number;
  procedure_id: number;
  nome: string;
  categoria: string;
  duracao_minutos: number;
  preco: string | null;
  liberado: boolean;
  exibir_valor: boolean;
  ordem: number;
  profissionais: number[];
  profissionais_nomes: string[];
};

export type PublicoInfo = {
  disponivel: boolean;
  error?: string;
  slug?: string;
  nome?: string;
  texto_apresentacao?: string;
  logo_url?: string;
  banner_url?: string;
  cor_primaria?: string;
  cor_secundaria?: string;
  endereco?: string;
  telefone?: string;
  politica_privacidade?: string;
  botao_whatsapp_ativo?: boolean;
  whatsapp?: string;
  modo_confirmacao?: "automatico" | "secretaria";
};

export type PublicoCategoria = {
  slug: string;
  nome: string;
  cor: string;
  quantidade: number;
  descricao?: string;
  imagem_url?: string;
};

export type PublicoProcedimento = {
  id: number;
  nome: string;
  descricao: string;
  categoria: string;
  duracao_minutos: number;
  exibir_valor: boolean;
  preco: string | null;
  preco_rotulo?: string;
};

export type PublicoProfissional = {
  id: number;
  nome: string;
  especialidade: string;
  foto_url: string;
  tempo_consulta_minutos?: number;
};

export type PublicoCriarPayload = {
  nome: string;
  telefone: string;
  email?: string;
  data_nascimento?: string;
  observacoes?: string;
  professional: number;
  procedure: number;
  date_ymd: string;
  time: string;
};

export type PublicoCriarResultado = {
  id: number;
  numero: number;
  status: string;
  pendente_aprovacao: boolean;
  mensagem: string;
  date: string;
  professional_nome: string;
  procedure_nome: string;
};

/* ------------------------------------------------------------------ */
/* Erros                                                               */
/* ------------------------------------------------------------------ */

export function mensagemErroAgendamentoOnline(err: unknown, fallback = "Não foi possível concluir a operação."): string {
  if (!err) return fallback;
  if (typeof err === "string") return err;
  if (axios.isAxiosError(err)) {
    const d = err.response?.data as { error?: string; detail?: string } | undefined;
    if (d?.error) return d.error;
    if (d?.detail) return d.detail;
    if (err.code === "ECONNABORTED") return "Tempo esgotado. Tente novamente.";
    if (!err.response) return "Sem conexão com o servidor. Verifique sua internet.";
    return fallback;
  }
  if (typeof err === "object") {
    const o = err as Record<string, unknown>;
    if (typeof o.error === "string") return o.error;
    if (typeof o.detail === "string") return o.detail;
    if (typeof o.message === "string") return o.message;
  }
  return fallback;
}

/* ------------------------------------------------------------------ */
/* Admin (autenticado)                                                 */
/* ------------------------------------------------------------------ */

export const agendamentoOnlineAdminApi = {
  getConfig: () => cbGet<AgendamentoOnlineConfig>("/agendamento-online/config/"),
  patchConfig: (data: Partial<AgendamentoOnlineConfig>) =>
    cbPatch<AgendamentoOnlineConfig>("/agendamento-online/config/", data),
  listProfissionais: () => cbGet<AgendamentoOnlineProfissional[]>("/agendamento-online/profissionais/"),
  saveProfissionais: (itens: AgendamentoOnlineProfissional[]) =>
    cbPut<AgendamentoOnlineProfissional[]>("/agendamento-online/profissionais/", itens),
  listProcedimentos: () => cbGet<AgendamentoOnlineProcedimento[]>("/agendamento-online/procedimentos/"),
  vincularProcedimento: (procedureId: number, extra?: { exibir_valor?: boolean; profissionais?: number[] }) =>
    cbPost<AgendamentoOnlineProcedimento>("/agendamento-online/procedimentos/", {
      procedure_id: procedureId,
      ...extra,
    }),
  patchProcedimento: (
    id: number,
    data: Partial<Pick<AgendamentoOnlineProcedimento, "liberado" | "exibir_valor" | "ordem" | "profissionais">>,
  ) => cbPatch<AgendamentoOnlineProcedimento>(`/agendamento-online/procedimentos/${id}/`, data),
  desvincularProcedimento: (id: number) => cbDelete(`/agendamento-online/procedimentos/${id}/`),
};

/* ------------------------------------------------------------------ */
/* Público (sem sessão)                                                */
/* ------------------------------------------------------------------ */

function publicBase(slug: string): string {
  return `${getPrimaryApiBaseUrl()}/clinica-beleza/agendamento-online/publico/${encodeURIComponent(slug)}`;
}

async function publicGet<T>(slug: string, sufixo: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const base = publicBase(slug).replace(/\/$/, "");
  const path = sufixo ? `${base}/${sufixo.replace(/^\//, "")}` : `${base}/`;
  const { data } = await axios.get<T>(path, {
    timeout: 15000,
    params: { ...params, _t: Date.now() },
  });
  return data;
}

export const agendamentoOnlinePublicoApi = {
  info: (slug: string) => publicGet<PublicoInfo>(slug, ""),
  categorias: (slug: string) => publicGet<PublicoCategoria[]>(slug, "categorias/"),
  procedimentos: (slug: string, categoria?: string) =>
    publicGet<PublicoProcedimento[]>(slug, "procedimentos/", { categoria }),
  profissionais: (slug: string, procedure: number) =>
    publicGet<PublicoProfissional[]>(slug, "profissionais/", { procedure }),
  dias: (slug: string, professional: number, procedure: number) =>
    publicGet<{ dias: string[] }>(slug, "disponibilidade/", { professional, procedure }),
  slots: (slug: string, professional: number, procedure: number, date: string) =>
    publicGet<{ date: string; slots: string[] }>(slug, "disponibilidade/", { professional, procedure, date }),
  criar: async (slug: string, payload: PublicoCriarPayload) => {
    const { data } = await axios.post<PublicoCriarResultado>(`${publicBase(slug)}/criar/`, payload, {
      timeout: 20000,
      headers: { "Content-Type": "application/json" },
    });
    return data;
  },
};
