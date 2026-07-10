import { fetchAllPaginatedResults } from '@/lib/crm-utils';

export interface CrmContaExportRow {
  nome: string;
  cnpj?: string;
  razao_social?: string;
  segmento?: string;
  email?: string;
  telefone?: string;
}

function downloadContasCsv(contas: CrmContaExportRow[], filename: string) {
  const headers = ['Nome', 'CNPJ', 'Razão Social', 'Segmento', 'Email', 'Telefone'];
  const rows = contas.map((c) => [
    c.nome,
    c.cnpj || '',
    c.razao_social || '',
    c.segmento || '',
    c.email || '',
    c.telefone || '',
  ]);
  const csv = [headers.join(';'), ...rows.map((r) => r.map((v) => `"${(v || '').replace(/"/g, '""')}"`).join(';'))].join('\n');
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export async function exportAllContasCsv(busca = ''): Promise<number> {
  const params: Record<string, string | number> = {};
  if (busca.trim().length >= 2) params.q = busca.trim();
  const contas = await fetchAllPaginatedResults<CrmContaExportRow>('/crm-vendas/contas/', params);
  downloadContasCsv(contas, `contas_${new Date().toISOString().slice(0, 10)}.csv`);
  return contas.length;
}
