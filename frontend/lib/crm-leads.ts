import { fetchAllPaginatedResults, fetchCrmPaginatedPage, getCrmApiErrorDetail } from '@/lib/crm-utils';
import { formatDate } from '@/lib/financeiro-helpers';
import type { Lead } from '@/components/crm-vendas/LeadsTable';

export const LEADS_PAGE_SIZE = 50;

export function formatarDataLead(s: string) {
  if (!s) return '–';
  const formatted = formatDate(s, '');
  return formatted || s;
}

function buildLeadsCsv(leads: Lead[]) {
  const headers = ['Nome', 'Empresa', 'Email', 'Telefone', 'CPF/CNPJ', 'Status'];
  const rows = leads.map((l) => [
    l.nome,
    l.empresa || '',
    l.email || '',
    l.telefone || '',
    l.cpf_cnpj || '',
    l.status,
  ]);
  return [headers.join(';'), ...rows.map((r) => r.map((c) => `"${(c || '').replace(/"/g, '""')}"`).join(';'))].join('\n');
}

function downloadCsv(csv: string, filename: string) {
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function loadLeadsPage(
  page: number,
  setLeads: (l: Lead[]) => void,
  setTotalCount: (n: number) => void,
  setTotalPages: (n: number) => void,
  setError: (e: string | null) => void,
  setLoading: (v: boolean) => void,
  busca = '',
) {
  setLoading(true);
  const params: Record<string, string | number> = { _t: Date.now() };
  if (busca.trim().length >= 2) params.q = busca.trim();

  fetchCrmPaginatedPage<Lead>('/crm-vendas/leads/', page, LEADS_PAGE_SIZE, params)
    .then((data) => {
      setLeads(data.results);
      setTotalCount(data.count);
      setTotalPages(data.totalPages);
      setError(null);
    })
    .catch((err) => {
      setError(getCrmApiErrorDetail(err, 'Erro ao carregar leads.'));
    })
    .finally(() => setLoading(false));
}

export async function exportAllLeadsCsv(busca = ''): Promise<number> {
  const params: Record<string, string | number> = { _t: Date.now() };
  if (busca.trim().length >= 2) params.q = busca.trim();
  const leads = await fetchAllPaginatedResults<Lead>('/crm-vendas/leads/', params);
  downloadCsv(buildLeadsCsv(leads), `leads_${new Date().toISOString().slice(0, 10)}.csv`);
  return leads.length;
}
