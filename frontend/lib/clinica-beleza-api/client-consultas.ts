import { clinicaBelezaFetch, getClinicaBelezaBaseUrl } from "./fetch";
import type { PacienteFotoItem } from "./types-memed";
import { cbDelete, cbGet, cbGetList, cbPatch, cbPost } from "./client-http";

export const consultasApi = {
  list: (params?: { patient?: number; professional?: number; status?: string; appointment?: number }) =>
    cbGet("/consultas/", params),
  criar: (data: {
    patient: number;
    professional: number;
    procedure?: number;
    procedures_ids?: number[];
    iniciar?: boolean;
    local_atendimento?: number;
    valor_consulta?: number | string;
    convenio?: number | null;
  }) => cbPost("/consultas/", data),
  get: (id: number) => cbGet(`/consultas/${id}/`),
  update: (id: number, data: Record<string, unknown>) => cbPatch(`/consultas/${id}/`, data),
  excluir: (id: number) => cbDelete(`/consultas/${id}/`),
  aplicarProtocolo: (id: number, protocolId: number) =>
    cbPost(`/consultas/${id}/aplicar-protocolo/`, { protocol_id: protocolId }),
  iniciar: (id: number, body?: { professional?: number }) =>
    cbPost(`/consultas/${id}/iniciar/`, body || {}),
  receber: (
    id: number,
    data: {
      payment_method?: string;
      mark_as_paid?: boolean;
      amount?: number | string;
      desconto?: number | string;
      entradas?: Array<{ payment_method: string; valor: number | string }>;
    },
  ) => cbPost(`/consultas/${id}/receber/`, data),
  estornarPagamento: (id: number) =>
    cbPost<{ consulta: Record<string, unknown>; payment: Record<string, unknown>; message?: string }>(
      `/consultas/${id}/estornar-pagamento/`,
      {},
    ),
  finalizar: (
    id: number,
    data?: {
      payment_method?: string;
      mark_as_paid?: boolean;
      amount?: number | string;
      local_atendimento?: number;
    },
  ) => cbPost(`/consultas/${id}/finalizar/`, data ?? {}),
  evolucoes: {
    list: (consultaId: number) => cbGet(`/consultas/${consultaId}/evolucoes/`),
    create: (consultaId: number, data: Record<string, unknown>) =>
      cbPost(`/consultas/${consultaId}/evolucoes/`, data),
  },
  historicoCliente: (patientId: number, params?: { page?: number; page_size?: number }) =>
    cbGetList(`/patients/${patientId}/consultas/`, { page: 1, page_size: 100, ...params }),
  produtos: {
    list: (consultaId: number) => cbGet(`/consultas/${consultaId}/produtos/`),
    add: (
      consultaId: number,
      data: { produto: number; quantidade: number; lote?: string; validade?: string },
    ) => cbPost(`/consultas/${consultaId}/produtos/`, data),
    remove: (consultaId: number, itemId: number) =>
      cbDelete(`/consultas/${consultaId}/produtos/${itemId}/`),
  },
  procedimentos: {
    list: (consultaId: number) =>
      cbGet<
        Array<{
          id: number;
          procedure: number;
          procedure_name: string;
          valor: number | null;
          valor_efetivo: number;
          ordem: number;
        }>
      >(`/consultas/${consultaId}/procedimentos/`),
    add: (consultaId: number, procedureId: number) =>
      cbPost<{ item: unknown; consulta: Record<string, unknown> }>(
        `/consultas/${consultaId}/procedimentos/`,
        { procedure: procedureId },
      ),
    remove: async (consultaId: number, appointmentProcedureId: number) => {
      await cbDelete(`/consultas/${consultaId}/procedimentos/${appointmentProcedureId}/`);
      return cbGet<Record<string, unknown>>(`/consultas/${consultaId}/`);
    },
  },
  fotos: {
    list: (consultaId: number) =>
      cbGet<{ patient_id: number; patient_nome: string; fotos: PacienteFotoItem[] }>(
        `/consultas/${consultaId}/fotos/`,
      ),
    salvar: (consultaId: number, cloudinaryUrl: string, publicId?: string) =>
      cbPost<{ message: string; foto: PacienteFotoItem }>(`/consultas/${consultaId}/fotos/`, {
        cloudinary_url: cloudinaryUrl,
        cloudinary_public_id: publicId || "",
      }),
    gerarQr: (consultaId: number) =>
      cbPost<{ url: string; qr_base64: string; expira_em_horas: number }>(
        `/consultas/${consultaId}/fotos/qr/`,
        { frontend_origin: typeof window !== "undefined" ? window.location.origin : "" },
      ),
    excluir: (consultaId: number, fotoId: number) =>
      cbDelete(`/consultas/${consultaId}/fotos/${fotoId}/`),
  },
  termoConsentimento: {
    get: (consultaId: number) =>
      cbGet<{
        exige_termo: boolean;
        status_assinatura_termo: string;
        tem_conteudo: boolean;
        termos_procedimentos: Array<{
          id: number;
          procedure_id: number;
          procedure_nome: string;
          status: string;
          status_display: string;
          tem_conteudo: boolean;
        }>;
      }>(`/consultas/${consultaId}/termo-consentimento/`),
    enviar: (consultaId: number, procedureId?: number, canal: "email" | "whatsapp" = "email") =>
      cbPost<{ message: string; status_assinatura_termo: string; enviados?: string[] }>(
        `/consultas/${consultaId}/termo-consentimento/enviar/`,
        { ...(procedureId ? { procedure_id: procedureId } : {}), canal },
      ),
    reenviar: (consultaId: number, procedureId: number, canal: "email" | "whatsapp" = "email") =>
      cbPost<{ message: string; procedure_nome?: string }>(
        `/consultas/${consultaId}/termo-consentimento/reenviar/`,
        { procedure_id: procedureId, canal },
      ),
    pdfUrl: (consultaId: number, procedureId: number) => {
      const base = getClinicaBelezaBaseUrl();
      return `${base}/consultas/${consultaId}/termo-consentimento/pdf/?procedure_id=${procedureId}`;
    },
    downloadPdf: async (consultaId: number, procedureId: number) => {
      const res = await clinicaBelezaFetch(
        `/consultas/${consultaId}/termo-consentimento/pdf/?procedure_id=${procedureId}`,
      );
      if (!res.ok) throw new Error("Erro ao baixar PDF do termo.");
      return res.blob();
    },
  },
};
