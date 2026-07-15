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
};
