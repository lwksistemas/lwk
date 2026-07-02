export interface CrmHeaderBuscaResult {
  leads: { id: number; nome: string; empresa: string; status: string; cpf_cnpj?: string }[];
  oportunidades: {
    id: number;
    titulo: string;
    valor: string;
    etapa: string;
    lead_nome: string;
    lead_empresa: string;
  }[];
  contas: { id: number; nome: string; segmento: string; cnpj?: string }[];
  propostas?: {
    id: number;
    titulo: string;
    numero: string;
    status: string;
    oportunidade_titulo: string;
    lead_nome: string;
  }[];
}

export interface CrmHeaderNotificacao {
  id: number;
  titulo: string;
  mensagem: string;
  status: string;
  created_at: string;
}

export const CRM_HEADER_SEARCH_DEBOUNCE_MS = 300;
export const CRM_HEADER_SEARCH_MIN_LEN = 2;
export const CRM_HEADER_NOTIFICATIONS_POLL_MS = 120000;

export function crmHeaderHasSearchResults(results: CrmHeaderBuscaResult | null): boolean {
  if (!results) return false;
  return (
    results.leads.length > 0 ||
    results.oportunidades.length > 0 ||
    results.contas.length > 0 ||
    (results.propostas?.length ?? 0) > 0
  );
}
