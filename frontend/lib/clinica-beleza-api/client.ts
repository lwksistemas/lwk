import {
  clinicaBelezaFetch,
  getClinicaBelezaBaseUrl,
} from "./fetch";
import {
  buildClinicaBelezaListUrl,
  parseClinicaBelezaListResponse,
  parseClinicaBelezaResponseBody,
} from "./pagination";
import type {
  AgendaRetornoConfigItem,
  ConvenioDetailItem,
  ConvenioItem,
  ConvenioPrecoItem,
  ConvenioPrecoModo,
  DocumentTemplateItem,
  DocumentoClinicoItem,
  LocalAtendimentoItem,
  NomeAgendaItem,
  ProcedureConvenioPrecoItem,
  ProcedimentoConvenioPrecosMatrix,
  ProntuarioData,
  RetornoProcedimentoRegraItem,
  RetornoVerificacaoResult,
} from "./types-entities";
import type { PacienteFotoItem, PrescricaoMemedItem } from "./types-memed";

export class ClinicaBelezaAPI {
  /** GET que retorna sempre um array (compatível com paginação opcional). */
  static async getList<T = unknown>(
    path: string,
    params?: Record<string, unknown>,
    loja?: { id?: number; slug?: string } | null,
  ): Promise<T[]> {
    const data = await ClinicaBelezaAPI.get(path, params, loja);
    return parseClinicaBelezaListResponse<T>(data);
  }

  /**
   * GET request
   */
  static async get<T = any>(
    path: string,
    params?: Record<string, any>,
    loja?: { id?: number; slug?: string } | null,
  ): Promise<T> {
    const url = params ? buildClinicaBelezaListUrl(path, params) : path;
    const res = await clinicaBelezaFetch(url, {}, loja);
    const data = await parseClinicaBelezaResponseBody(res);
    if (!res.ok) throw data;
    return data as T;
  }
  
  /**
   * POST request
   */
  static async post<T = any>(
    path: string,
    data: any,
    loja?: { id?: number; slug?: string } | null,
  ): Promise<T> {
    const res = await clinicaBelezaFetch(path, {
      method: 'POST',
      body: JSON.stringify(data),
    }, loja);
    const body = await parseClinicaBelezaResponseBody(res);
    if (!res.ok) throw body;
    return body as T;
  }
  
  /**
   * PUT request
   */
  static async put<T = any>(
    path: string,
    data: any,
    loja?: { id?: number; slug?: string } | null,
  ): Promise<T> {
    const res = await clinicaBelezaFetch(path, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, loja);
    const body = await parseClinicaBelezaResponseBody(res);
    if (!res.ok) throw body;
    return body as T;
  }
  
  /**
   * PATCH request
   */
  static async patch<T = any>(
    path: string,
    data: any,
    loja?: { id?: number; slug?: string } | null,
  ): Promise<T> {
    const res = await clinicaBelezaFetch(path, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }, loja);
    const body = await parseClinicaBelezaResponseBody(res);
    if (!res.ok) throw body;
    return body as T;
  }
  
  /**
   * DELETE request
   */
  static async delete(path: string): Promise<void> {
    await clinicaBelezaFetch(path, { method: 'DELETE' });
  }

  static consultas = {
    list: (params?: { patient?: number; professional?: number; status?: string; appointment?: number }) =>
      ClinicaBelezaAPI.get('/consultas/', params),
    /** Abre uma consulta avulsa (sem agendamento na agenda) a partir do cadastro do cliente. */
    criar: (data: {
      patient: number;
      professional: number;
      procedure?: number;
      procedures_ids?: number[];
      iniciar?: boolean;
      local_atendimento?: number;
      valor_consulta?: number | string;
      convenio?: number | null;
    }) =>
      ClinicaBelezaAPI.post('/consultas/', data),
    get: (id: number) => ClinicaBelezaAPI.get(`/consultas/${id}/`),
    update: (id: number, data: Record<string, unknown>) => ClinicaBelezaAPI.patch(`/consultas/${id}/`, data),
    /** Exclui uma consulta (somente se não estiver concluída). */
    excluir: (id: number) => ClinicaBelezaAPI.delete(`/consultas/${id}/`),
    aplicarProtocolo: (id: number, protocolId: number) =>
      ClinicaBelezaAPI.post(`/consultas/${id}/aplicar-protocolo/`, { protocol_id: protocolId }),
    iniciar: (id: number, body?: { professional?: number }) => ClinicaBelezaAPI.post(`/consultas/${id}/iniciar/`, body || {}),
    finalizar: (
      id: number,
      data?: {
        payment_method?: string;
        mark_as_paid?: boolean;
        amount?: number | string;
        local_atendimento?: number;
      },
    ) => ClinicaBelezaAPI.post(`/consultas/${id}/finalizar/`, data ?? {}),
    evolucoes: {
      list: (consultaId: number) => ClinicaBelezaAPI.get(`/consultas/${consultaId}/evolucoes/`),
      create: (consultaId: number, data: Record<string, unknown>) =>
        ClinicaBelezaAPI.post(`/consultas/${consultaId}/evolucoes/`, data),
    },
    historicoCliente: (patientId: number, params?: { page?: number; page_size?: number }) =>
      ClinicaBelezaAPI.getList(`/patients/${patientId}/consultas/`, {
        page: 1,
        page_size: 100,
        ...params,
      }),
    produtos: {
      list: (consultaId: number) =>
        ClinicaBelezaAPI.get(`/consultas/${consultaId}/produtos/`),
      add: (
        consultaId: number,
        data: { produto: number; quantidade: number; lote?: string; validade?: string },
      ) => ClinicaBelezaAPI.post(`/consultas/${consultaId}/produtos/`, data),
      remove: (consultaId: number, itemId: number) =>
        ClinicaBelezaAPI.delete(`/consultas/${consultaId}/produtos/${itemId}/`),
    },
    fotos: {
      list: (consultaId: number) =>
        ClinicaBelezaAPI.get<{
          patient_id: number;
          patient_nome: string;
          fotos: PacienteFotoItem[];
        }>(`/consultas/${consultaId}/fotos/`),
      salvar: (consultaId: number, cloudinaryUrl: string, publicId?: string) =>
        ClinicaBelezaAPI.post<{ message: string; foto: PacienteFotoItem }>(
          `/consultas/${consultaId}/fotos/`,
          { cloudinary_url: cloudinaryUrl, cloudinary_public_id: publicId || '' },
        ),
      gerarQr: (consultaId: number) =>
        ClinicaBelezaAPI.post<{
          url: string;
          qr_base64: string;
          expira_em_horas: number;
        }>(`/consultas/${consultaId}/fotos/qr/`, {
          frontend_origin: typeof window !== 'undefined' ? window.location.origin : '',
        }),
      excluir: (consultaId: number, fotoId: number) =>
        ClinicaBelezaAPI.delete(`/consultas/${consultaId}/fotos/${fotoId}/`),
    },
    termoConsentimento: {
      get: (consultaId: number) =>
        ClinicaBelezaAPI.get<{
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
      enviar: (consultaId: number, procedureId?: number, canal: 'email' | 'whatsapp' = 'email') =>
        ClinicaBelezaAPI.post<{
          message: string;
          status_assinatura_termo: string;
          enviados?: string[];
        }>(
          `/consultas/${consultaId}/termo-consentimento/enviar/`,
          { ...(procedureId ? { procedure_id: procedureId } : {}), canal },
        ),
      reenviar: (consultaId: number, procedureId: number, canal: 'email' | 'whatsapp' = 'email') =>
        ClinicaBelezaAPI.post<{ message: string; procedure_nome?: string }>(
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
        if (!res.ok) throw new Error('Erro ao baixar PDF do termo.');
        return res.blob();
      },
    },
  };

  static anamnese = {
    get: (patientId: number) => ClinicaBelezaAPI.get(`/patients/${patientId}/anamnese/`),
    save: (patientId: number, data: Record<string, unknown>) =>
      ClinicaBelezaAPI.put(`/patients/${patientId}/anamnese/`, data),
  };

  static patients = {
    list: (params?: { active?: boolean; page?: number; page_size?: number }) =>
      ClinicaBelezaAPI.getList('/patients/', params),
    get: (id: number) => ClinicaBelezaAPI.get(`/patients/${id}/`),
    create: (data: Record<string, unknown>) => ClinicaBelezaAPI.post('/patients/', data),
    update: (id: number, data: Record<string, unknown>) =>
      ClinicaBelezaAPI.put(`/patients/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/patients/${id}/`),
  };

  static professionals = {
    list: (params?: { active?: boolean; with_schedule?: boolean; page?: number; page_size?: number }) =>
      ClinicaBelezaAPI.getList('/professionals/', params),
    get: (id: number) => ClinicaBelezaAPI.get(`/professionals/${id}/`),
    create: (data: Record<string, unknown>) =>
      ClinicaBelezaAPI.post('/professionals/', data),
    update: (id: number, data: Record<string, unknown>) =>
      ClinicaBelezaAPI.put(`/professionals/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/professionals/${id}/`),
    comissoes: {
      list: (id: number) => ClinicaBelezaAPI.get(`/professionals/${id}/comissoes/`),
      save: (id: number, payload: unknown[]) =>
        ClinicaBelezaAPI.post(`/professionals/${id}/comissoes/`, payload),
    },
    horarios: {
      get: (id: number) => ClinicaBelezaAPI.get(`/professionals/${id}/horarios-trabalho/`),
      save: (id: number, data: unknown) =>
        ClinicaBelezaAPI.put(`/professionals/${id}/horarios-trabalho/`, data),
    },
  };

  static loja = {
    info: () =>
      ClinicaBelezaAPI.get<{
        owner_username?: string;
        owner_email?: string;
        owner_telefone?: string;
      }>('/loja-info/'),
  };

  static financeiro = {
    resumo: (params?: { mes?: number; ano?: number }) =>
      ClinicaBelezaAPI.get('/financeiro/resumo/', params),
    despesas: {
      list: (params?: { status?: string; categoria?: number; date?: string; page?: number; page_size?: number }) =>
        ClinicaBelezaAPI.getList('/despesas/', params),
      create: (data: Record<string, unknown>) =>
        ClinicaBelezaAPI.post('/despesas/', data),
      update: (id: number, data: Record<string, unknown>) =>
        ClinicaBelezaAPI.put(`/despesas/${id}/`, data),
      delete: (id: number) => ClinicaBelezaAPI.delete(`/despesas/${id}/`),
      categorias: () => ClinicaBelezaAPI.getList<{ id: number; nome: string }>('/despesas/categorias/'),
    },
  };

  static estoque = {
    list: (
      params?: { categoria?: string; search?: string; page?: number; page_size?: number },
      loja?: { id?: number; slug?: string } | null,
    ) => ClinicaBelezaAPI.getList('/estoque/', params, loja),
    get: (id: number) => ClinicaBelezaAPI.get(`/estoque/${id}/`),
    create: (data: Record<string, unknown>, loja?: { id?: number; slug?: string } | null) =>
      ClinicaBelezaAPI.post('/estoque/', data, loja),
    update: (id: number, data: Record<string, unknown>, loja?: { id?: number; slug?: string } | null) =>
      ClinicaBelezaAPI.put(`/estoque/${id}/`, data, loja),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/estoque/${id}/`),
    resumo: (loja?: { id?: number; slug?: string } | null) =>
      ClinicaBelezaAPI.get('/estoque/resumo/', undefined, loja),
    movimentar: (id: number, data: { tipo: string; quantidade: number; motivo?: string }) =>
      ClinicaBelezaAPI.post(`/estoque/${id}/movimentar/`, data),
  };

  static memed = {
    /** Token do prescritor + URL do script da Memed (api-key/secret-key ficam no backend). */
    token: (params?: { professional?: number; prescritor?: string; uf?: string }) =>
      ClinicaBelezaAPI.get<{
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
      }>('/memed/token/', params as Record<string, string> | undefined),

    timbrado: {
      get: () => ClinicaBelezaAPI.get('/memed/timbrado/'),
    },

    /** Registra no histórico do paciente uma prescrição emitida na Memed. */
    salvarPrescricao: (
      consultaId: number,
      data: { prescricao_id?: string; resumo?: string; itens?: unknown[]; pdf_url?: string; professional?: number | null },
    ) => ClinicaBelezaAPI.post(`/consultas/${consultaId}/prescricoes/`, data),

    /** Lista prescrições Memed registradas nesta consulta. */
    listarPrescricoesConsulta: (consultaId: number) =>
      ClinicaBelezaAPI.get<PrescricaoMemedItem[]>(`/consultas/${consultaId}/prescricoes/`),

    /** Lista as prescrições registradas para um paciente (histórico). */
    listarPrescricoesPaciente: (patientId: number) =>
      ClinicaBelezaAPI.getList<PrescricaoMemedItem>(`/patients/${patientId}/prescricoes/`),

    /** Busca/salva PDF da prescrição na Memed e retorna URL para impressão. */
    obterPdf: (prescricaoId: number) =>
      ClinicaBelezaAPI.post<{ pdf_url: string }>(`/prescricoes-memed/${prescricaoId}/pdf/`, {}),
  };

  static templates = {
    list: async (params?: { tipo?: string; page?: number; page_size?: number; professional?: number }) => {
      const data = await ClinicaBelezaAPI.get<
        DocumentTemplateItem[] | { results: DocumentTemplateItem[]; count: number }
      >('/templates/', params);
      if (Array.isArray(data)) {
        return { results: data, count: data.length };
      }
      return { results: data?.results ?? [], count: data?.count ?? 0 };
    },
    get: (id: number) => ClinicaBelezaAPI.get<DocumentTemplateItem>(`/templates/${id}/`),
    create: (data: { nome: string; tipo: string; conteudo: string }) =>
      ClinicaBelezaAPI.post<DocumentTemplateItem>('/templates/', data),
    update: (id: number, data: Partial<{ nome: string; tipo: string; conteudo: string }>) =>
      ClinicaBelezaAPI.put<DocumentTemplateItem>(`/templates/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/templates/${id}/`),
  };

  static documentos = {
    list: (consultaId: number) =>
      ClinicaBelezaAPI.get<DocumentoClinicoItem[]>(`/consultas/${consultaId}/documentos/`),
    create: (consultaId: number, data: { tipo: string; conteudo?: string; template_id?: number; titulo?: string }) =>
      ClinicaBelezaAPI.post<DocumentoClinicoItem>(`/consultas/${consultaId}/documentos/`, data),
    delete: (consultaId: number, docId: number) =>
      ClinicaBelezaAPI.delete(`/consultas/${consultaId}/documentos/${docId}/`),
  };

  static prontuario = {
    get: (patientId: number, secao?: string) =>
      ClinicaBelezaAPI.get<ProntuarioData>(`/patients/${patientId}/prontuario/`, secao ? { secao } : undefined),
    pdfUrl: (patientId: number, secao?: string) => {
      const base = getClinicaBelezaBaseUrl();
      const query = secao ? `?secao=${secao}` : '';
      return `${base}/patients/${patientId}/prontuario/pdf/${query}`;
    },
    documentoPdfUrl: (docId: number) => {
      const base = getClinicaBelezaBaseUrl();
      return `${base}/documentos/${docId}/pdf/`;
    },
  };

  static locaisAtendimento = {
    list: () =>
      ClinicaBelezaAPI.get<LocalAtendimentoItem[]>('/locais-atendimento/'),
    create: (data: { nome: string; valor_consulta: number | string; tempo_consulta_minutos?: number }) =>
      ClinicaBelezaAPI.post<LocalAtendimentoItem>('/locais-atendimento/', data),
    update: (id: number, data: { nome?: string; valor_consulta?: number | string; tempo_consulta_minutos?: number; is_padrao?: boolean }) =>
      ClinicaBelezaAPI.patch<LocalAtendimentoItem>(`/locais-atendimento/${id}/`, data),
    delete: (id: number) =>
      ClinicaBelezaAPI.delete(`/locais-atendimento/${id}/`),
  };

  static nomesAgenda = {
    list: () =>
      ClinicaBelezaAPI.get<NomeAgendaItem[]>('/nomes-agenda/'),
    create: (data: { nome: string }) =>
      ClinicaBelezaAPI.post<NomeAgendaItem>('/nomes-agenda/', data),
    update: (id: number, data: { nome?: string; is_padrao?: boolean }) =>
      ClinicaBelezaAPI.patch<NomeAgendaItem>(`/nomes-agenda/${id}/`, data),
    delete: (id: number) =>
      ClinicaBelezaAPI.delete(`/nomes-agenda/${id}/`),
  };

  static retorno = {
    getConfig: () => ClinicaBelezaAPI.get<AgendaRetornoConfigItem>('/retorno/config/'),
    updateConfig: (data: Partial<Pick<AgendaRetornoConfigItem, 'retorno_procedimento_ativo' | 'retorno_consulta_ativo' | 'dias_retorno_consulta'>>) =>
      ClinicaBelezaAPI.patch<AgendaRetornoConfigItem>('/retorno/config/', data),
    listRegras: () => ClinicaBelezaAPI.get<RetornoProcedimentoRegraItem[]>('/retorno/procedimentos/'),
    createRegra: (data: { procedure: number; dias_retorno: number }) =>
      ClinicaBelezaAPI.post<RetornoProcedimentoRegraItem>('/retorno/procedimentos/', data),
    updateRegra: (id: number, data: { dias_retorno?: number; is_active?: boolean }) =>
      ClinicaBelezaAPI.patch<RetornoProcedimentoRegraItem>(`/retorno/procedimentos/${id}/`, data),
    deleteRegra: (id: number) => ClinicaBelezaAPI.delete(`/retorno/procedimentos/${id}/`),
    verificar: (params: {
      patient_id: number;
      procedure_ids?: number[];
      retorno_procedure_id?: number;
      exclude_appointment_id?: number;
    }) => {
      const qs = new URLSearchParams({ patient_id: String(params.patient_id) });
      if (params.procedure_ids?.length) {
        qs.set('procedure_ids', params.procedure_ids.join(','));
      }
      if (params.retorno_procedure_id) {
        qs.set('retorno_procedure_id', String(params.retorno_procedure_id));
      }
      if (params.exclude_appointment_id) {
        qs.set('exclude_appointment_id', String(params.exclude_appointment_id));
      }
      return ClinicaBelezaAPI.get<RetornoVerificacaoResult>(`/retorno/verificar/?${qs.toString()}`);
    },
  };

  static campanhas = {
    list: () => ClinicaBelezaAPI.get('/campanhas/'),
    get: (id: number) => ClinicaBelezaAPI.get(`/campanhas/${id}/`),
    create: (data: Record<string, unknown>) => ClinicaBelezaAPI.post('/campanhas/', data),
    update: (id: number, data: Record<string, unknown>) => ClinicaBelezaAPI.put(`/campanhas/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/campanhas/${id}/`),
    enviar: (id: number) => ClinicaBelezaAPI.post(`/campanhas/${id}/enviar/`, {}),
  };

  static protocolos = {
    list: (params?: { categoria?: string; procedure?: number; page?: number; page_size?: number }) =>
      ClinicaBelezaAPI.getList('/protocolos/', params),
    get: (id: number) => ClinicaBelezaAPI.get(`/protocolos/${id}/`),
    create: (data: Record<string, unknown>) => ClinicaBelezaAPI.post('/protocolos/', data),
    update: (id: number, data: Record<string, unknown>) =>
      ClinicaBelezaAPI.put(`/protocolos/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/protocolos/${id}/`),
  };

  static procedures = {
    list: (params?: { categoria?: string; active?: boolean; page?: number; page_size?: number }) =>
      ClinicaBelezaAPI.getList('/procedures/', params),
    get: (id: number) => ClinicaBelezaAPI.get(`/procedures/${id}/`),
    create: (data: Record<string, unknown>) => ClinicaBelezaAPI.post('/procedures/', data),
    update: (id: number, data: Record<string, unknown>) =>
      ClinicaBelezaAPI.put(`/procedures/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/procedures/${id}/`),
    convenioPrecosMatrix: () =>
      ClinicaBelezaAPI.get<ProcedimentoConvenioPrecosMatrix>('/procedures/convenio-precos-matrix/'),
    precosConvenio: (id: number) =>
      ClinicaBelezaAPI.get<ProcedureConvenioPrecoItem[]>(`/procedures/${id}/precos-convenio/`),
    savePrecosConvenio: (
      id: number,
      precos: { convenio: number; preco: number | string | null }[],
    ) =>
      ClinicaBelezaAPI.put<ConvenioPrecoItem[]>(`/procedures/${id}/precos-convenio/`, { precos }),
  };

  static convenios = {
    list: (params?: { todos?: boolean; page?: number; page_size?: number }) =>
      ClinicaBelezaAPI.getList<ConvenioItem>('/convenios/', params),
    get: (id: number) => ClinicaBelezaAPI.get<ConvenioDetailItem>(`/convenios/${id}/`),
    create: (data: { nome: string; codigo?: string }) =>
      ClinicaBelezaAPI.post<ConvenioDetailItem>('/convenios/', data),
    update: (id: number, data: { nome?: string; codigo?: string; is_active?: boolean }) =>
      ClinicaBelezaAPI.put<ConvenioDetailItem>(`/convenios/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/convenios/${id}/`),
    precos: (id: number) => ClinicaBelezaAPI.get<ConvenioPrecoItem[]>(`/convenios/${id}/precos/`),
    savePrecos: (
      id: number,
      precos: { procedure: number; modo?: ConvenioPrecoModo; preco: number | string | null }[],
    ) =>
      ClinicaBelezaAPI.put<ConvenioPrecoItem[]>(`/convenios/${id}/precos/`, { precos }),
  };
}
