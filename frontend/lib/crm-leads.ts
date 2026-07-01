import { fetchCrmPaginatedPage, getCrmApiErrorDetail } from '@/lib/crm-utils';
import type { Lead } from '@/components/crm-vendas/LeadsTable';

export const LEADS_PAGE_SIZE = 50;

export function formatarDataLead(s: string) {
  if (!s) return '–';
  try {
    const d = new Date(s);
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return s;
  }
}

export function loadLeadsPage(
  page: number,
  setLeads: (l: Lead[]) => void,
  setTotalCount: (n: number) => void,
  setTotalPages: (n: number) => void,
  setError: (e: string | null) => void,
  setLoading: (v: boolean) => void,
) {
  setLoading(true);
  fetchCrmPaginatedPage<Lead>('/crm-vendas/leads/', page, LEADS_PAGE_SIZE, { _t: Date.now() })
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

export function exportLeadsCsv(leads: Lead[]) {
  const headers = ['Nome', 'Empresa', 'Email', 'Telefone', 'CPF/CNPJ', 'Status'];
  const rows = leads.map((l) => [
    l.nome,
    l.empresa || '',
    l.email || '',
    l.telefone || '',
    l.cpf_cnpj || '',
    l.status,
  ]);
  const csv = [headers.join(';'), ...rows.map((r) => r.map((c) => `"${(c || '').replace(/"/g, '""')}"`).join(';'))].join('\n');
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `leads_${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}
