'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Download, ExternalLink, FileText, Loader2 } from 'lucide-react';
import { formatCurrency, formatDate } from '@/lib/financeiro-helpers';
import apiClient from '@/lib/api-client';

export interface HistoricoPagamentoItem {
  pagamento_loja_id: number;
  id: number;
  asaas_id?: string;
  mercadopago_payment_id?: string;
  provedor_boleto?: string;
  valor: number;
  status: string;
  status_display: string;
  data_vencimento: string | null;
  data_pagamento?: string | null;
  boleto_url?: string;
  is_paid: boolean;
  is_pending: boolean;
  is_overdue: boolean;
  tem_nota_fiscal?: boolean;
  numero_nf?: string;
  nf_pdf_url?: string;
  pode_baixar_boleto?: boolean;
  referencia_mes?: string | null;
}

interface Props {
  itens: HistoricoPagamentoItem[];
  slug: string;
}

function statusBadge(item: HistoricoPagamentoItem) {
  if (item.is_paid) {
    return <Badge className="bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300">Pago</Badge>;
  }
  if (item.is_overdue) {
    return <Badge variant="destructive">Vencido</Badge>;
  }
  return <Badge variant="secondary">Pendente</Badge>;
}

export function HistoricoPagamentos({ itens, slug }: Props) {
  const [loadingBoleto, setLoadingBoleto] = useState<number | null>(null);
  const [loadingNf, setLoadingNf] = useState<number | null>(null);

  const baixarBoleto = async (item: HistoricoPagamentoItem) => {
    const pagamentoId = item.pagamento_loja_id || item.id;
    const mpId = (item.mercadopago_payment_id || '').trim();

    if (!pagamentoId && mpId) {
      setLoadingBoleto(-1);
      try {
        const { data } = await apiClient.get<{ boleto_url?: string; error?: string }>(
          `/superadmin/loja-pagamentos/baixar_boleto_mercadopago/?payment_id=${encodeURIComponent(mpId)}`
        );
        if (data?.boleto_url) window.open(data.boleto_url, '_blank');
        else alert(data?.error || 'Boleto indisponível.');
      } catch {
        if (item.boleto_url) window.open(item.boleto_url, '_blank');
        else alert('Erro ao obter boleto.');
      } finally {
        setLoadingBoleto(null);
      }
      return;
    }

    if (!pagamentoId) {
      if (item.boleto_url) {
        window.open(item.boleto_url, '_blank');
        return;
      }
      alert('Boleto indisponível para este lançamento.');
      return;
    }
    setLoadingBoleto(pagamentoId);
    try {
      const res = await apiClient.get(
        `/superadmin/loja-pagamentos/${pagamentoId}/baixar_boleto_pdf/`,
        { responseType: 'blob' }
      );
      const blob = res.data as Blob;
      const ct = res.headers?.['content-type'] || blob.type || '';
      if (ct.includes('json') || blob.type?.includes('json')) {
        const d = JSON.parse(await blob.text());
        if (d?.error) {
          alert(d.error);
          return;
        }
        if (d?.boleto_url) {
          window.open(d.boleto_url, '_blank');
          return;
        }
      }
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `boleto_${slug}_${pagamentoId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: string }; status?: number } };
      if (item.boleto_url) {
        window.open(item.boleto_url, '_blank');
      } else {
        let msg = 'Erro ao baixar boleto';
        if (ax?.response?.data && typeof ax.response.data === 'object' && 'error' in ax.response.data) {
          msg = String((ax.response.data as { error: string }).error);
        }
        alert(msg);
      }
    } finally {
      setLoadingBoleto(null);
    }
  };

  const abrirNotaFiscal = async (item: HistoricoPagamentoItem) => {
    if (item.nf_pdf_url) {
      window.open(item.nf_pdf_url, '_blank');
      return;
    }
    const pagamentoId = item.pagamento_loja_id || item.id;
    if (!pagamentoId) {
      alert('Nota fiscal não disponível para este pagamento.');
      return;
    }
    setLoadingNf(pagamentoId);
    try {
      const { data } = await apiClient.get<{
        success: boolean;
        pdf_url?: string;
        numero_nf?: string;
        error?: string;
      }>(`/superadmin/loja-pagamentos/${pagamentoId}/nota-fiscal/`);
      if (data?.success && data.pdf_url) {
        window.open(data.pdf_url, '_blank');
        return;
      }
      const res = await apiClient.get(
        `/superadmin/loja-pagamentos/${pagamentoId}/nota-fiscal-arquivo/`,
        { responseType: 'blob' }
      );
      const blob = res.data as Blob;
      const ct = res.headers?.['content-type'] || blob.type || '';
      if (ct.includes('json') || blob.type?.includes('json')) {
        const d = JSON.parse(await blob.text());
        if (d?.pdf_url) {
          window.open(d.pdf_url, '_blank');
          return;
        }
        alert(d?.error || 'Nota fiscal não encontrada.');
        return;
      }
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
      setTimeout(() => window.URL.revokeObjectURL(url), 60_000);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: string } } };
      alert(ax?.response?.data?.error || 'Nota fiscal não disponível.');
    } finally {
      setLoadingNf(null);
    }
  };

  if (!itens.length) {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 dark:border-neutral-600 p-8 text-center text-sm text-muted-foreground dark:text-gray-400">
        Nenhum pagamento no histórico. Quando houver cobranças, elas aparecerão aqui com boleto e nota fiscal.
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 dark:border-neutral-700 overflow-hidden">
      <div className="hidden sm:grid sm:grid-cols-[1fr_auto] gap-2 px-4 py-3 bg-gray-50 dark:bg-neutral-800/80 border-b border-gray-200 dark:border-neutral-700 text-xs font-medium text-gray-600 dark:text-gray-400">
        <span>Pagamento</span>
        <span>Ações</span>
      </div>
      <ul className="divide-y divide-gray-200 dark:divide-neutral-700">
        {itens.map((item, index) => {
          const pid = item.pagamento_loja_id || item.id;
          const podeBoleto =
            item.pode_baixar_boleto !== false &&
            (pid > 0 ||
              Boolean(item.boleto_url) ||
              Boolean(item.asaas_id) ||
              Boolean(item.mercadopago_payment_id));
          const showBaixarPdf = pid > 0 || Boolean(item.asaas_id);
          const podeNf = item.tem_nota_fiscal || item.is_paid;

          return (
            <li key={`${pid}-${item.asaas_id || index}`} className="px-4 py-4 hover:bg-gray-50/80 dark:hover:bg-neutral-800/50">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    {statusBadge(item)}
                    <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      {formatCurrency(item.valor)}
                    </span>
                    {item.numero_nf ? (
                      <span className="text-xs text-gray-500 dark:text-gray-400">NF {item.numero_nf}</span>
                    ) : null}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Vencimento: {formatDate(item.data_vencimento)}
                    {item.data_pagamento ? (
                      <span className="text-green-700 dark:text-green-400"> · Pago em {formatDate(item.data_pagamento)}</span>
                    ) : null}
                  </p>
                  {item.referencia_mes ? (
                    <p className="text-xs text-gray-500 dark:text-gray-500 mt-0.5">
                      Referência: {formatDate(item.referencia_mes)}
                    </p>
                  ) : null}
                </div>

                <div className="flex flex-wrap gap-2 shrink-0">
                  {podeBoleto && (
                    <>
                      {item.boleto_url && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => window.open(item.boleto_url, '_blank')}
                        >
                          <ExternalLink className="w-4 h-4 mr-1" />
                          Ver boleto
                        </Button>
                      )}
                      {(showBaixarPdf || item.mercadopago_payment_id) && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          disabled={loadingBoleto === pid || loadingBoleto === -1}
                          onClick={() => baixarBoleto(item)}
                        >
                          {loadingBoleto === pid || (loadingBoleto === -1 && !pid) ? (
                            <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                          ) : (
                            <Download className="w-4 h-4 mr-1" />
                          )}
                          Baixar boleto
                        </Button>
                      )}
                    </>
                  )}
                  {podeNf && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={loadingNf === pid}
                      onClick={() => abrirNotaFiscal(item)}
                    >
                      {loadingNf === pid ? (
                        <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                      ) : (
                        <FileText className="w-4 h-4 mr-1" />
                      )}
                      Nota fiscal
                    </Button>
                  )}
                  {item.is_paid && !item.tem_nota_fiscal && !item.nf_pdf_url && (
                    <span className="text-xs text-amber-600 dark:text-amber-400 self-center px-1">
                      Clique em Nota fiscal para baixar
                    </span>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
