import { USE_JWT_HTTPONLY_COOKIES } from "@/lib/auth-cookies";
import {
  clearSessionAndRedirect,
  getLoginUrlForRedirect,
  tryRefreshAccessToken,
} from "@/lib/api-client";
import {
  getApiBaseUrl,
  getClinicaBelezaHeadersWithLoja,
  handle401SessionResponse,
} from "@/lib/clinica-beleza-api/fetch";

export type PainelSalao = "operacao" | "gestao" | "semana";

export type ClienteSalao = {
  id: number;
  nome: string;
  telefone: string;
  email?: string | null;
  data_nascimento?: string | null;
};

export type ProfissionalSalao = {
  id: number;
  nome: string;
  telefone: string;
  especialidade: string;
  comissao_percentual: string;
};

export type ServicoSalao = {
  id: number;
  nome: string;
  descricao?: string | null;
  categoria: string;
  duracao_minutos: number;
  preco: string;
};

export type JornadaDia = {
  dia_semana: number;
  ativo: boolean;
  hora_entrada: string;
  hora_saida: string;
  intervalo_inicio: string;
  intervalo_fim: string;
};

export type BloqueioSalao = {
  id: number;
  titulo: string;
  tipo: string;
  data_inicio: string;
  data_fim: string;
  horario_inicio: string | null;
  horario_fim: string | null;
  profissional: number | null;
  profissional_nome: string;
};

export type AgendamentoSalao = {
  id: number;
  inicio: string;
  fim: string;
  duracao_minutos: number;
  status: string;
  status_label: string;
  cliente: number;
  cliente_nome: string;
  profissional: number;
  profissional_nome: string;
  servico: number;
  servico_nome: string;
  preco: string;
  observacoes: string;
  aviso?: string;
  recebido?: {
    id: number;
    valor: string;
    desconto: string;
    forma: string;
    forma_label: string;
    comissao_valor: string;
  } | null;
};

export type ComunicacaoSalao = {
  confirmacao: boolean;
  lembrete: boolean;
  lembrete_horas: number;
  reagendamento: boolean;
  cancelamento: boolean;
  whatsapp_pronto: boolean;
  pode_gravar: boolean;
};

export type CaixaSalao = {
  total: string;
  quantidade: number;
  por_forma: { forma: string; nome: string; total: string }[];
  comissoes: { nome: string; quantidade: number; recebido: string; comissao: string }[];
  recebimentos: {
    id: number;
    quando: string;
    cliente: string;
    servico: string;
    profissional: string;
    forma: string;
    forma_label: string;
    desconto: string;
    valor: string;
    comissao: string;
    agendamento: number;
  }[];
};

async function salaoFetch<T>(path: string, options: RequestInit = {}, retried = false): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}/salao-cabeleireiro${path}`, {
    ...options,
    credentials: USE_JWT_HTTPONLY_COOKIES ? "include" : options.credentials,
    headers: { ...getClinicaBelezaHeadersWithLoja(), ...(options.headers || {}) },
  });
  if (response.status === 401) {
    if (await handle401SessionResponse(response)) throw new Error("Sessão encerrada.");
    if (!retried && (await tryRefreshAccessToken())) return salaoFetch(path, options, true);
    clearSessionAndRedirect(getLoginUrlForRedirect(), "Sessão expirada. Faça login novamente.");
    throw new Error("Sessão expirada.");
  }
  if (response.status === 204) return null as T;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detalhe = typeof data.detail === "string" ? data.detail : "";
    const mensagem = typeof data.error === "string"
      ? data.error
      : response.status === 429
        ? "Muitas consultas em seguida. Aguarde um instante e atualize a página."
        : detalhe || "Não foi possível concluir.";
    throw new Error(mensagem);
  }
  return data as T;
}

export const SalaoAPI = {
  config: () => salaoFetch<{ painel: PainelSalao; pode_trocar: boolean; paineis: { id: PainelSalao; nome: string }[] }>("/config/"),
  comunicacao: () => salaoFetch<ComunicacaoSalao>("/comunicacao/"),
  salvarComunicacao: (corpo: Pick<ComunicacaoSalao, "confirmacao" | "lembrete" | "lembrete_horas" | "reagendamento" | "cancelamento">) =>
    salaoFetch<ComunicacaoSalao>("/comunicacao/", { method: "PUT", body: JSON.stringify(corpo) }),
  enviarWhatsapp: (id: number, evento: "confirmacao" | "lembrete" | "reagendamento" | "cancelamento") =>
    salaoFetch<{ enviado: boolean }>(`/agendamentos/${id}/whatsapp/`, { method: "POST", body: JSON.stringify({ evento }) }),
  salvarPainel: (painel: PainelSalao) =>
    salaoFetch("/config/", { method: "PUT", body: JSON.stringify({ painel }) }),
  resumo: () => salaoFetch<ResumoSalao>("/resumo/"),
  agenda: (start: string, end: string) =>
    salaoFetch<AgendamentoSalao[]>(`/agenda/?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`),
  criarAgendamento: (corpo: Record<string, unknown>) =>
    salaoFetch<AgendamentoSalao>("/agenda/", { method: "POST", body: JSON.stringify(corpo) }),
  atualizarAgendamento: (id: number, corpo: Record<string, unknown>) =>
    salaoFetch<AgendamentoSalao>(`/agendamentos/${id}/`, { method: "PATCH", body: JSON.stringify(corpo) }),
  receber: (id: number, corpo: { desconto: string; forma: string }) =>
    salaoFetch<AgendamentoSalao>(`/agendamentos/${id}/receber/`, { method: "POST", body: JSON.stringify(corpo) }),
  estornarRecebimento: (id: number) => salaoFetch(`/recebimentos/${id}/`, { method: "DELETE" }),
  caixa: (start: string, end: string) =>
    salaoFetch<CaixaSalao>(`/caixa/?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`),
  clientes: () => salaoFetch<ClienteSalao[]>("/clientes/"),
  salvarCliente: (corpo: Record<string, unknown>, id?: number) =>
    salaoFetch<ClienteSalao>(id ? `/clientes/${id}/` : "/clientes/", {
      method: id ? "PATCH" : "POST",
      body: JSON.stringify(corpo),
    }),
  profissionais: () => salaoFetch<ProfissionalSalao[]>("/profissionais/"),
  salvarProfissional: (corpo: Record<string, unknown>, id?: number) =>
    salaoFetch<ProfissionalSalao>(id ? `/profissionais/${id}/` : "/profissionais/", {
      method: id ? "PATCH" : "POST",
      body: JSON.stringify(corpo),
    }),
  servicos: () => salaoFetch<ServicoSalao[]>("/servicos/"),
  salvarServico: (corpo: Record<string, unknown>, id?: number) =>
    salaoFetch<ServicoSalao>(id ? `/servicos/${id}/` : "/servicos/", {
      method: id ? "PATCH" : "POST",
      body: JSON.stringify(corpo),
    }),
  jornada: (profissionalId: number) => salaoFetch<JornadaDia[]>(`/profissionais/${profissionalId}/jornada/`),
  salvarJornada: (profissionalId: number, dias: JornadaDia[]) =>
    salaoFetch<JornadaDia[]>(`/profissionais/${profissionalId}/jornada/`, { method: "PUT", body: JSON.stringify(dias) }),
  bloqueios: () => salaoFetch<BloqueioSalao[]>("/bloqueios/"),
  bloquear: (corpo: Record<string, unknown>) =>
    salaoFetch("/bloqueios/", { method: "POST", body: JSON.stringify(corpo) }),
  removerBloqueio: (id: number) => salaoFetch(`/bloqueios/${id}/`, { method: "DELETE" }),
  arquivar: (caminho: string) => salaoFetch(caminho, { method: "DELETE" }),
};

export type ResumoSalao = {
  painel: PainelSalao;
  pode_trocar: boolean;
  hoje: { agendamentos: number; em_andamento: number; concluidos: number; faturamento: string; ocupacao: number };
  mes: { receita: string; novos_clientes: number; ticket: string; clientes_ativos: number };
  semana: { data: string; rotulo: string; total: number }[];
  serie_mes: { dia: number; valor: number }[];
  servicos: { nome: string; quantidade: number; receita: string }[];
  comissoes?: { nome: string; quantidade: number; comissao: string }[];
  aniversariantes: { nome: string; dia: string }[];
  agenda_hoje: { id: number; hora: string; cliente: string; servico: string; profissional: string; status: string; status_label: string }[];
};
