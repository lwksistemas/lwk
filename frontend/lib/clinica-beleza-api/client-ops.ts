import type {
  AgendaRetornoConfigItem,
  LocalAtendimentoItem,
  NomeAgendaItem,
  RetornoProcedimentoRegraItem,
  RetornoVerificacaoResult,
} from "./types-entities";
import { cbDelete, cbGet, cbGetList, cbPatch, cbPost, cbPut } from "./client-http";

export const lojaApi = {
  info: () =>
    cbGet<{
      owner_username?: string;
      owner_email?: string;
      owner_telefone?: string;
    }>("/loja-info/"),
};

export const financeiroApi = {
  resumo: (params?: { mes?: number; ano?: number }) => cbGet("/financeiro/resumo/", params),
  despesas: {
    list: (params?: { status?: string; categoria?: number; date?: string; page?: number; page_size?: number }) =>
      cbGetList("/despesas/", params),
    create: (data: Record<string, unknown>) => cbPost("/despesas/", data),
    update: (id: number, data: Record<string, unknown>) => cbPut(`/despesas/${id}/`, data),
    delete: (id: number) => cbDelete(`/despesas/${id}/`),
    categorias: () => cbGetList<{ id: number; nome: string }>("/despesas/categorias/"),
  },
};

export const estoqueApi = {
  list: (
    params?: { categoria?: string; search?: string; page?: number; page_size?: number },
    loja?: { id?: number; slug?: string } | null,
  ) => cbGetList("/estoque/", params, loja),
  get: (id: number) => cbGet(`/estoque/${id}/`),
  create: (data: Record<string, unknown>, loja?: { id?: number; slug?: string } | null) =>
    cbPost("/estoque/", data, loja),
  update: (id: number, data: Record<string, unknown>, loja?: { id?: number; slug?: string } | null) =>
    cbPut(`/estoque/${id}/`, data, loja),
  delete: (id: number) => cbDelete(`/estoque/${id}/`),
  resumo: (loja?: { id?: number; slug?: string } | null) => cbGet("/estoque/resumo/", undefined, loja),
  movimentar: (id: number, data: { tipo: string; quantidade: number; motivo?: string }) =>
    cbPost(`/estoque/${id}/movimentar/`, data),
};

export const locaisAtendimentoApi = {
  list: () => cbGet<LocalAtendimentoItem[]>("/locais-atendimento/"),
  create: (data: { nome: string; valor_consulta: number | string; tempo_consulta_minutos?: number }) =>
    cbPost<LocalAtendimentoItem>("/locais-atendimento/", data),
  update: (
    id: number,
    data: { nome?: string; valor_consulta?: number | string; tempo_consulta_minutos?: number; is_padrao?: boolean },
  ) => cbPatch<LocalAtendimentoItem>(`/locais-atendimento/${id}/`, data),
  delete: (id: number) => cbDelete(`/locais-atendimento/${id}/`),
};

export const nomesAgendaApi = {
  list: () => cbGet<NomeAgendaItem[]>("/nomes-agenda/"),
  create: (data: { nome: string }) => cbPost<NomeAgendaItem>("/nomes-agenda/", data),
  update: (id: number, data: { nome?: string; is_padrao?: boolean }) =>
    cbPatch<NomeAgendaItem>(`/nomes-agenda/${id}/`, data),
  delete: (id: number) => cbDelete(`/nomes-agenda/${id}/`),
};

export const retornoApi = {
  getConfig: () => cbGet<AgendaRetornoConfigItem>("/retorno/config/"),
  updateConfig: (
    data: Partial<Pick<AgendaRetornoConfigItem, "retorno_procedimento_ativo" | "retorno_consulta_ativo" | "dias_retorno_consulta">>,
  ) => cbPatch<AgendaRetornoConfigItem>("/retorno/config/", data),
  listRegras: () => cbGet<RetornoProcedimentoRegraItem[]>("/retorno/procedimentos/"),
  createRegra: (data: { procedure: number; dias_retorno: number }) =>
    cbPost<RetornoProcedimentoRegraItem>("/retorno/procedimentos/", data),
  updateRegra: (id: number, data: { dias_retorno?: number; is_active?: boolean }) =>
    cbPatch<RetornoProcedimentoRegraItem>(`/retorno/procedimentos/${id}/`, data),
  deleteRegra: (id: number) => cbDelete(`/retorno/procedimentos/${id}/`),
  verificar: (params: {
    patient_id: number;
    procedure_ids?: number[];
    retorno_procedure_id?: number;
    exclude_appointment_id?: number;
  }) => {
    const qs = new URLSearchParams({ patient_id: String(params.patient_id) });
    if (params.procedure_ids?.length) qs.set("procedure_ids", params.procedure_ids.join(","));
    if (params.retorno_procedure_id) qs.set("retorno_procedure_id", String(params.retorno_procedure_id));
    if (params.exclude_appointment_id) qs.set("exclude_appointment_id", String(params.exclude_appointment_id));
    return cbGet<RetornoVerificacaoResult>(`/retorno/verificar/?${qs.toString()}`);
  },
};
