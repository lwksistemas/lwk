export interface CrmRelatorioVendedor {
  id: number;
  nome: string;
  email: string;
}

export interface CrmRelatorioEmpresaPrestadora {
  id: number;
  nome: string;
  cnpj?: string;
}

export interface CrmRelatorioDashboardData {
  receita: number;
  comissao_total_mes: number;
  performance_vendedores: Array<{ id: number; nome: string; receita_mes: number; comissao_mes: number }>;
}

export interface CrmRelatorioComissao {
  id: number;
  numero: string;
  titulo: string;
  status: string;
  status_display: string;
  empresa_prestadora_nome: string;
  vendedor_nome: string;
  periodo_descricao: string;
  valor_total_vendas: string;
  valor_total_comissao: string;
  quantidade_vendas: number;
  boleto_url: string;
  nfse_numero: string;
  created_at: string | null;
}

export const CRM_RELATORIO_COMISSAO_STATUS_COLORS: Record<string, string> = {
  pendente_aprovacao: 'bg-yellow-100 text-yellow-800',
  reprovado: 'bg-red-100 text-red-800',
  aprovado: 'bg-blue-100 text-blue-800',
  aguardando_pagamento: 'bg-orange-100 text-orange-800',
  pago: 'bg-green-100 text-green-800',
  nfse_emitida: 'bg-emerald-100 text-emerald-800',
  concluido: 'bg-gray-100 text-gray-800',
  cancelado: 'bg-gray-100 text-gray-500',
};

export function downloadBlobPdf(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export async function parseBlobErrorDetail(data: unknown, fallback: string): Promise<string> {
  if (data instanceof Blob) {
    try {
      const parsed = JSON.parse(await data.text()) as { detail?: string };
      return parsed.detail || fallback;
    } catch {
      return fallback;
    }
  }
  return fallback;
}
