import type {
  ConvenioDetailItem,
  ConvenioItem,
  ConvenioPrecoItem,
  ConvenioPrecoModo,
  DocumentTemplateItem,
  DocumentoClinicoItem,
  ProcedureConvenioPrecoItem,
  ProcedimentoConvenioPrecosMatrix,
} from "./types-entities";
import { cbDelete, cbGet, cbGetList, cbPost, cbPut } from "./client-http";

export const anamneseApi = {
  get: (patientId: number) => cbGet(`/patients/${patientId}/anamnese/`),
  save: (patientId: number, data: Record<string, unknown>) =>
    cbPut(`/patients/${patientId}/anamnese/`, data),
};

export const patientsApi = {
  list: (params?: { active?: boolean; page?: number; page_size?: number }) =>
    cbGetList("/patients/", params),
  get: (id: number) => cbGet(`/patients/${id}/`),
  create: (data: Record<string, unknown>) => cbPost("/patients/", data),
  update: (id: number, data: Record<string, unknown>) => cbPut(`/patients/${id}/`, data),
  delete: (id: number) => cbDelete(`/patients/${id}/`),
};

export const professionalsApi = {
  list: (params?: { active?: boolean; with_schedule?: boolean; page?: number; page_size?: number }) =>
    cbGetList("/professionals/", params),
  get: (id: number) => cbGet(`/professionals/${id}/`),
  create: (data: Record<string, unknown>) => cbPost("/professionals/", data),
  update: (id: number, data: Record<string, unknown>) => cbPut(`/professionals/${id}/`, data),
  delete: (id: number) => cbDelete(`/professionals/${id}/`),
  comissoes: {
    list: (id: number) => cbGet(`/professionals/${id}/comissoes/`),
    save: (id: number, payload: unknown[]) => cbPost(`/professionals/${id}/comissoes/`, payload),
  },
  horarios: {
    get: (id: number) => cbGet(`/professionals/${id}/horarios-trabalho/`),
    save: (id: number, data: unknown) => cbPut(`/professionals/${id}/horarios-trabalho/`, data),
  },
  adminStatus: () =>
    cbGet<{ is_enabled: boolean; professional_id: number | null }>("/professionals/admin-status/"),
  toggleAdmin: (enable: boolean) => cbPost("/professionals/toggle-admin/", { enable }),
};

export const templatesApi = {
  list: async (params?: { tipo?: string; page?: number; page_size?: number; professional?: number }) => {
    const data = await cbGet<DocumentTemplateItem[] | { results: DocumentTemplateItem[]; count: number }>(
      "/templates/",
      params,
    );
    if (Array.isArray(data)) return { results: data, count: data.length };
    return { results: data?.results ?? [], count: data?.count ?? 0 };
  },
  get: (id: number) => cbGet<DocumentTemplateItem>(`/templates/${id}/`),
  create: (data: { nome: string; tipo: string; conteudo: string }) =>
    cbPost<DocumentTemplateItem>("/templates/", data),
  update: (id: number, data: Partial<{ nome: string; tipo: string; conteudo: string }>) =>
    cbPut<DocumentTemplateItem>(`/templates/${id}/`, data),
  delete: (id: number) => cbDelete(`/templates/${id}/`),
};

export const documentosApi = {
  list: (consultaId: number) => cbGet<DocumentoClinicoItem[]>(`/consultas/${consultaId}/documentos/`),
  create: (
    consultaId: number,
    data: { tipo: string; conteudo?: string; template_id?: number; titulo?: string },
  ) => cbPost<DocumentoClinicoItem>(`/consultas/${consultaId}/documentos/`, data),
  delete: (consultaId: number, docId: number) =>
    cbDelete(`/consultas/${consultaId}/documentos/${docId}/`),
};

export const campanhasApi = {
  list: () => cbGet("/campanhas/"),
  get: (id: number) => cbGet(`/campanhas/${id}/`),
  create: (data: Record<string, unknown>) => cbPost("/campanhas/", data),
  update: (id: number, data: Record<string, unknown>) => cbPut(`/campanhas/${id}/`, data),
  delete: (id: number) => cbDelete(`/campanhas/${id}/`),
  enviar: (id: number, body?: { patient_ids?: number[] }) =>
    cbPost(`/campanhas/${id}/enviar/`, body ?? {}),
};

export const protocolosApi = {
  list: (params?: { categoria?: string; procedure?: number; page?: number; page_size?: number }) =>
    cbGetList("/protocolos/", params),
  get: (id: number) => cbGet(`/protocolos/${id}/`),
  create: (data: Record<string, unknown>) => cbPost("/protocolos/", data),
  update: (id: number, data: Record<string, unknown>) => cbPut(`/protocolos/${id}/`, data),
  delete: (id: number) => cbDelete(`/protocolos/${id}/`),
};

export const proceduresApi = {
  list: (params?: { categoria?: string; active?: boolean; page?: number; page_size?: number }) =>
    cbGetList("/procedures/", params),
  get: (id: number) => cbGet(`/procedures/${id}/`),
  create: (data: Record<string, unknown>) => cbPost("/procedures/", data),
  update: (id: number, data: Record<string, unknown>) => cbPut(`/procedures/${id}/`, data),
  delete: (id: number) => cbDelete(`/procedures/${id}/`),
  convenioPrecosMatrix: () => cbGet<ProcedimentoConvenioPrecosMatrix>("/procedures/convenio-precos-matrix/"),
  precosConvenio: (id: number) => cbGet<ProcedureConvenioPrecoItem[]>(`/procedures/${id}/precos-convenio/`),
  savePrecosConvenio: (id: number, precos: { convenio: number; preco: number | string | null }[]) =>
    cbPut<ConvenioPrecoItem[]>(`/procedures/${id}/precos-convenio/`, { precos }),
};

export const conveniosApi = {
  list: (params?: { todos?: boolean; page?: number; page_size?: number }) =>
    cbGetList<ConvenioItem>("/convenios/", params),
  get: (id: number) => cbGet<ConvenioDetailItem>(`/convenios/${id}/`),
  create: (data: { nome: string; codigo?: string }) => cbPost<ConvenioDetailItem>("/convenios/", data),
  update: (id: number, data: { nome?: string; codigo?: string; is_active?: boolean }) =>
    cbPut<ConvenioDetailItem>(`/convenios/${id}/`, data),
  delete: (id: number) => cbDelete(`/convenios/${id}/`),
  precos: (id: number) => cbGet<ConvenioPrecoItem[]>(`/convenios/${id}/precos/`),
  savePrecos: (
    id: number,
    precos: { procedure: number; modo?: ConvenioPrecoModo; preco: number | string | null }[],
  ) => cbPut<ConvenioPrecoItem[]>(`/convenios/${id}/precos/`, { precos }),
};
