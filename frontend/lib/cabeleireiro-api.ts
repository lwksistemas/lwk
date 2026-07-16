import apiClient from '@/lib/api-client';

const BASE = 'cabeleireiro';

export type SalaoCliente = {
  id: number;
  nome: string;
  name?: string;
  telefone: string;
  phone?: string;
  email?: string;
  cpf?: string;
  data_nascimento?: string | null;
  birth_date?: string | null;
  observacoes?: string;
  notes?: string;
  allow_whatsapp?: boolean;
  foto_url?: string;
  cep?: string;
  logradouro?: string;
  numero?: string;
  complemento?: string;
  bairro?: string;
  cidade?: string;
  estado?: string;
  endereco?: string;
};

export type SalaoProfissional = {
  id: number;
  nome: string;
  telefone: string;
  email?: string;
  especialidade?: string;
  cor_agenda?: string;
  is_active?: boolean;
};

export type SalaoServico = {
  id: number;
  nome: string;
  descricao?: string;
  duracao_minutos: number;
  preco: number | string;
  categoria?: string;
};

export type SalaoCategoriaServico = {
  id: number;
  nome: string;
  ordem?: number;
  is_active?: boolean;
};

export type SalaoHorarioTrabalho = {
  id?: number;
  profissional?: number;
  professional?: number;
  dia_semana: number;
  dia_semana_display?: string;
  hora_entrada: string;
  hora_saida: string;
  intervalo_inicio?: string | null;
  intervalo_fim?: string | null;
  ativo: boolean;
};

export type SalaoProfissionalComissao = {
  id?: number;
  profissional?: number;
  categoria: number;
  categoria_nome?: string;
  servico?: number | null;
  servico_nome?: string;
  modo: 'percentual' | 'fixo';
  modo_display?: string;
  valor: number | string;
  is_active?: boolean;
};

export type SalaoPayment = {
  id: number;
  agendamento: number;
  amount: number | string;
  valor_total?: number | string | null;
  valor_total_efetivo?: number;
  payment_method: string;
  payment_method_label?: string;
  status: string;
  status_display?: string;
  payment_date?: string | null;
  notes?: string;
  desconto?: number | string;
  comissao_percentual?: number | string;
  comissao_valor?: number | string;
  cliente_nome?: string;
  profissional_nome?: string;
  profissional_id?: number | null;
  servico_nome?: string;
  data_atendimento?: string;
  hora_atendimento?: string;
};

export type SalaoFinanceiroResumo = {
  caixa_diario: number;
  total_mes: number;
  contas_a_receber: number;
  comissao_mes: number;
  faturamento: number;
  despesas: number;
  lucro: number;
  filter?: { mes: number; ano: number };
};

export type SalaoComissoesRelatorio = {
  data_inicio: string;
  data_fim: string;
  profissionais: {
    profissional_id: number | null;
    nome: string;
    qtd: number;
    valor_total: number;
    comissao_total: number;
    itens: {
      payment_id: number;
      data: string;
      cliente: string;
      servico: string;
      valor: number;
      comissao: number;
      comissao_percentual: number;
      modo: string;
    }[];
  }[];
  totais: {
    qtd: number;
    valor_total: number;
    comissao_total: number;
  };
};

export type SalaoAgendamento = {
  id: number;
  cliente: number;
  cliente_nome: string;
  profissional?: number | null;
  profissional_nome?: string;
  servico?: number | null;
  servico_nome?: string;
  data: string;
  hora_inicio: string;
  hora_fim?: string | null;
  status: string;
  status_display?: string;
  valor?: number | string;
  observacoes?: string;
};

export type SalaoBloqueio = {
  id: number;
  professional?: number | null;
  profissional?: number | null;
  professional_name?: string | null;
  data_inicio: string;
  data_fim: string;
  motivo: string;
  observacoes?: string | null;
  criado_em?: string;
};

export type SalaoDashboard = {
  data: string;
  total_hoje: number;
  concluidos_hoje: number;
  proximos: SalaoAgendamento[];
};

function unwrapList<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === 'object' && Array.isArray((data as { results?: T[] }).results)) {
    return (data as { results: T[] }).results;
  }
  return [];
}

export const CabeleireiroAPI = {
  dashboard: async () => {
    const { data } = await apiClient.get<SalaoDashboard>(`${BASE}/dashboard/`);
    return data;
  },
  confirmarChegada: async (id: number) => {
    const { data } = await apiClient.post<SalaoAgendamento>(
      `${BASE}/agendamentos/${id}/confirmar-chegada/`,
      {},
    );
    return data;
  },
  receberAgendamento: async (
    id: number,
    payload: { amount: number; payment_method: string; desconto?: number },
  ) => {
    const { data } = await apiClient.post<{ payment: SalaoPayment; agendamento: SalaoAgendamento }>(
      `${BASE}/agendamentos/${id}/receber/`,
      payload,
    );
    return data;
  },
  financeiro: {
    resumo: async (params?: { mes?: number; ano?: number }) => {
      const { data } = await apiClient.get<SalaoFinanceiroResumo>(`${BASE}/financeiro/resumo/`, {
        params,
      });
      return data;
    },
  },
  payments: {
    list: async (params?: {
      status?: string;
      date?: string;
      profissional?: number | string;
      professional?: number | string;
    }) => {
      const { data } = await apiClient.get(`${BASE}/payments/`, { params });
      return unwrapList<SalaoPayment>(data);
    },
    enviarRecibo: async (id: number, canal: 'email' | 'whatsapp') => {
      const { data } = await apiClient.post<{ success?: boolean; message?: string; error?: string }>(
        `${BASE}/payments/${id}/enviar-recibo/`,
        { canal },
      );
      return data;
    },
  },
  relatorios: {
    comissoes: async (params: {
      data_inicio: string;
      data_fim: string;
      profissional_id?: number | string;
    }) => {
      const { data } = await apiClient.get<SalaoComissoesRelatorio>(`${BASE}/relatorios/comissoes/`, {
        params,
      });
      return data;
    },
    comissoesPdf: async (params: {
      data_inicio: string;
      data_fim: string;
      profissional_id?: number | string;
    }) => {
      const { data } = await apiClient.get(`${BASE}/relatorios/comissoes/pdf/`, {
        params,
        responseType: 'blob',
      });
      return data as Blob;
    },
  },
  reenviarConfirmacaoWhatsApp: async (id: number) => {
    const { data } = await apiClient.post<{ ok: boolean; detail: string }>(
      `${BASE}/agendamentos/${id}/reenviar-mensagem/`,
      {},
    );
    return data;
  },
  clientes: {
    list: async (params?: { search?: string }) => {
      const { data } = await apiClient.get(`${BASE}/clientes/`, { params });
      return unwrapList<SalaoCliente>(data);
    },
    get: async (id: number) => {
      const { data } = await apiClient.get<SalaoCliente>(`${BASE}/clientes/${id}/`);
      return data;
    },
    create: async (payload: Record<string, unknown>) => {
      const { data } = await apiClient.post<SalaoCliente>(`${BASE}/clientes/`, payload);
      return data;
    },
    update: async (id: number, payload: Record<string, unknown>) => {
      const { data } = await apiClient.patch<SalaoCliente>(`${BASE}/clientes/${id}/`, payload);
      return data;
    },
    remove: async (id: number) => {
      await apiClient.delete(`${BASE}/clientes/${id}/`);
    },
  },
  profissionais: {
    list: async () => {
      const { data } = await apiClient.get(`${BASE}/profissionais/`);
      return unwrapList<SalaoProfissional>(data);
    },
    create: async (payload: Record<string, unknown>) => {
      const { data } = await apiClient.post<SalaoProfissional>(`${BASE}/profissionais/`, payload);
      return data;
    },
    update: async (id: number, payload: Record<string, unknown>) => {
      const { data } = await apiClient.patch<SalaoProfissional>(`${BASE}/profissionais/${id}/`, payload);
      return data;
    },
    remove: async (id: number) => {
      await apiClient.delete(`${BASE}/profissionais/${id}/`);
    },
    horarios: {
      get: async (id: number) => {
        const { data } = await apiClient.get(`${BASE}/profissionais/${id}/horarios-trabalho/`);
        return unwrapList<SalaoHorarioTrabalho>(data);
      },
      save: async (id: number, payload: Record<string, unknown>[]) => {
        const { data } = await apiClient.put(`${BASE}/profissionais/${id}/horarios-trabalho/`, payload);
        return unwrapList<SalaoHorarioTrabalho>(data);
      },
    },
    comissoes: {
      list: async (id: number) => {
        const { data } = await apiClient.get(`${BASE}/profissionais/${id}/comissoes/`);
        return unwrapList<SalaoProfissionalComissao>(data);
      },
      save: async (id: number, payload: Record<string, unknown>[]) => {
        const { data } = await apiClient.post(`${BASE}/profissionais/${id}/comissoes/`, payload);
        return unwrapList<SalaoProfissionalComissao>(data);
      },
    },
  },
  categorias: {
    list: async () => {
      const { data } = await apiClient.get(`${BASE}/categorias-servico/`);
      return unwrapList<SalaoCategoriaServico>(data);
    },
    create: async (payload: Record<string, unknown>) => {
      const { data } = await apiClient.post<SalaoCategoriaServico>(`${BASE}/categorias-servico/`, payload);
      return data;
    },
    update: async (id: number, payload: Record<string, unknown>) => {
      const { data } = await apiClient.patch<SalaoCategoriaServico>(
        `${BASE}/categorias-servico/${id}/`,
        payload,
      );
      return data;
    },
    remove: async (id: number) => {
      await apiClient.delete(`${BASE}/categorias-servico/${id}/`);
    },
  },
  servicos: {
    list: async () => {
      const { data } = await apiClient.get(`${BASE}/servicos/`);
      return unwrapList<SalaoServico>(data);
    },
    create: async (payload: Record<string, unknown>) => {
      const { data } = await apiClient.post<SalaoServico>(`${BASE}/servicos/`, payload);
      return data;
    },
    update: async (id: number, payload: Record<string, unknown>) => {
      const { data } = await apiClient.patch<SalaoServico>(`${BASE}/servicos/${id}/`, payload);
      return data;
    },
    remove: async (id: number) => {
      await apiClient.delete(`${BASE}/servicos/${id}/`);
    },
  },
  agendamentos: {
    list: async (params?: {
      data?: string;
      data_inicio?: string;
      data_fim?: string;
      status?: string;
      profissional?: number | string;
    }) => {
      const { data } = await apiClient.get(`${BASE}/agendamentos/`, { params });
      return unwrapList<SalaoAgendamento>(data);
    },
    create: async (payload: Record<string, unknown>) => {
      const { data } = await apiClient.post<SalaoAgendamento>(`${BASE}/agendamentos/`, payload);
      return data;
    },
    update: async (id: number, payload: Record<string, unknown>) => {
      const { data } = await apiClient.patch<SalaoAgendamento>(`${BASE}/agendamentos/${id}/`, payload);
      return data;
    },
    remove: async (id: number) => {
      await apiClient.delete(`${BASE}/agendamentos/${id}/`);
    },
  },
  bloqueios: {
    list: async (params?: {
      start?: string;
      end?: string;
      data_inicio?: string;
      data_fim?: string;
      professional?: number | string;
    }) => {
      const { data } = await apiClient.get(`${BASE}/bloqueios/`, { params });
      return unwrapList<SalaoBloqueio>(data);
    },
    create: async (payload: Record<string, unknown>) => {
      const { data } = await apiClient.post<SalaoBloqueio>(`${BASE}/bloqueios/`, payload);
      return data;
    },
    update: async (id: number, payload: Record<string, unknown>) => {
      const { data } = await apiClient.patch<SalaoBloqueio>(`${BASE}/bloqueios/${id}/`, payload);
      return data;
    },
    remove: async (id: number) => {
      await apiClient.delete(`${BASE}/bloqueios/${id}/`);
    },
  },
};
