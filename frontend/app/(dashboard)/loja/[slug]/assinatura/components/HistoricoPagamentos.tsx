'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Download,
  ExternalLink,
  FileText,
  Loader2,
  CreditCard,
  Copy,
} from 'lucide-react';
import { formatCurrency, formatDate } from '@/lib/financeiro-helpers';
import apiClient from '@/lib/api-client';
import { hexToRgba } from '@/lib/loja-theme';

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

export interface CobrancaAberta {
  valor: number;
  data_vencimento: string;
  referencia_mes?: string | null;
  boleto_url?: string;
  pix_copy_paste?: string;
  pagamento_id?: number;
}

interface Props {
  itens: HistoricoPagamentoItem[];
  slug: string;
  proximaCobranca?: string;
  valorMensalidade?: number;
  cobrancaAberta?: CobrancaAberta | null;
  onGerarCobranca?: () => void;
  gerandoCobranca?: boolean;
  onCopiarPix?: () => void;
  corPrimaria?: string;
}

function StatusBadge({ item }: { item: HistoricoPagamentoItem }) {
  if (item.is_paid) {
    return (
      <Badge className="bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300">
        Pago
      </Badge>
    );
  }
  if (item.is_overdue) {
    return <Badge variant="destructive">Vencido</Badge>;
  }
  return <Badge variant="secondary">Pendente</Badge>;
}

export function HistoricoPagamentos({
  itens,
  slug,
  proximaCobranca,
  valorMensalidade,
  cobrancaAberta,
  onGerarCobranca,
  gerandoCobranca,
  onCopiarPix,
  corPrimaria = '#10B981',
}: Props) {
  const softBg = hexToRgba(corPrimaria, 0.08);
  const softBorder = hexToRgba(corPrimaria, 0.22);
  const headerBg = hexToRgba(corPrimaria, 0.14);
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
      const ax = err as { response?: { data?: { error?: string } } };
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

  const baixarBoletoPorId = async (pagamentoId: number, boletoUrl?: string) => {
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
    } catch {
      if (boletoUrl) window.open(boletoUrl, '_blank');
      else alert('Erro ao baixar boleto.');
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

  const renderAcoesBoleto = (item: HistoricoPagamentoItem) => {
    const pid = item.pagamento_loja_id || item.id;
    const podeBoleto =
      item.pode_baixar_boleto !== false &&
      (pid > 0 ||
        Boolean(item.boleto_url) ||
        Boolean(item.asaas_id) ||
        Boolean(item.mercadopago_payment_id));
    const showBaixarPdf = pid > 0 || Boolean(item.asaas_id);

    if (!podeBoleto) return <span className="text-xs text-muted-foreground">—</span>;

    return (
      <div className="flex flex-wrap gap-1 justify-end">
        {item.boleto_url && (
          <Button type="button" variant="outline" size="sm" onClick={() => window.open(item.boleto_url, '_blank')}>
            <ExternalLink className="w-3.5 h-3.5 mr-1" />
            Ver
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
              <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
            ) : (
              <Download className="w-3.5 h-3.5 mr-1" />
            )}
            Baixar
          </Button>
        )}
      </div>
    );
  };

  const renderAcoesNf = (item: HistoricoPagamentoItem) => {
    const pid = item.pagamento_loja_id || item.id;
    const podeNf = item.tem_nota_fiscal || item.is_paid;
    if (!podeNf) {
      return <span className="text-xs text-muted-foreground">Após pagamento</span>;
    }
    return (
      <Button
        type="button"
        variant="outline"
        size="sm"
        disabled={loadingNf === pid}
        onClick={() => abrirNotaFiscal(item)}
      >
        {loadingNf === pid ? (
          <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
        ) : (
          <FileText className="w-3.5 h-3.5 mr-1" />
        )}
        NFS-e
      </Button>
    );
  };

  const temCobrancaAbertaNaLista = cobrancaAberta
    ? itens.some(
        (i) =>
          i.is_pending &&
          i.data_vencimento === cobrancaAberta.data_vencimento &&
          Math.abs(i.valor - cobrancaAberta.valor) < 0.01
      )
    : false;

  const mostrarProximaLinha = !cobrancaAberta && !temCobrancaAbertaNaLista && proximaCobranca;

  return (
    <div
      className="overflow-x-auto rounded-lg dark:bg-slate-900/60"
      style={{ border: `1px solid ${softBorder}`, backgroundColor: softBg }}
    >
      <table className="w-full text-sm">
        <thead>
          <tr
            className="border-b dark:border-slate-600"
            style={{ borderColor: softBorder, backgroundColor: headerBg }}
          >
            <th className="text-left py-3 px-3 font-medium text-muted-foreground">Referência</th>
            <th className="text-left py-3 px-3 font-medium text-muted-foreground">Vencimento</th>
            <th className="text-left py-3 px-3 font-medium text-muted-foreground">Valor</th>
            <th className="text-left py-3 px-3 font-medium text-muted-foreground">Status</th>
            <th className="text-right py-3 px-3 font-medium text-muted-foreground">Boleto</th>
            <th className="text-right py-3 px-3 font-medium text-muted-foreground">Nota fiscal</th>
          </tr>
        </thead>
        <tbody>
          {cobrancaAberta && !temCobrancaAbertaNaLista && (
            <tr className="border-b border-gray-100 dark:border-neutral-800 bg-amber-50/50 dark:bg-amber-950/20">
              <td className="py-3 px-3 font-medium dark:text-gray-100">
                {cobrancaAberta.referencia_mes || 'Cobrança em aberto'}
              </td>
              <td className="py-3 px-3 dark:text-gray-200">{formatDate(cobrancaAberta.data_vencimento)}</td>
              <td className="py-3 px-3 font-semibold dark:text-gray-100">
                {formatCurrency(cobrancaAberta.valor)}
              </td>
              <td className="py-3 px-3">
                <Badge variant="secondary">Pendente</Badge>
              </td>
              <td className="py-3 px-3">
                <div className="flex flex-wrap gap-1 justify-end">
                  {cobrancaAberta.boleto_url && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => window.open(cobrancaAberta.boleto_url, '_blank')}
                    >
                      <ExternalLink className="w-3.5 h-3.5 mr-1" />
                      Ver
                    </Button>
                  )}
                  {cobrancaAberta.pagamento_id && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={loadingBoleto === cobrancaAberta.pagamento_id}
                      onClick={() =>
                        baixarBoletoPorId(cobrancaAberta.pagamento_id!, cobrancaAberta.boleto_url)
                      }
                    >
                      {loadingBoleto === cobrancaAberta.pagamento_id ? (
                        <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
                      ) : (
                        <Download className="w-3.5 h-3.5 mr-1" />
                      )}
                      Baixar
                    </Button>
                  )}
                  {cobrancaAberta.pix_copy_paste && onCopiarPix && (
                    <Button type="button" variant="outline" size="sm" onClick={onCopiarPix}>
                      <Copy className="w-3.5 h-3.5 mr-1" />
                      PIX
                    </Button>
                  )}
                </div>
              </td>
              <td className="py-3 px-3 text-right text-xs text-muted-foreground">Após pagamento</td>
            </tr>
          )}

          {mostrarProximaLinha && (
            <tr className="border-b border-gray-100 dark:border-neutral-800">
              <td className="py-3 px-3 font-medium dark:text-gray-100">Próxima mensalidade</td>
              <td className="py-3 px-3 dark:text-gray-200">{formatDate(proximaCobranca)}</td>
              <td className="py-3 px-3 font-semibold dark:text-gray-100">
                {valorMensalidade != null ? formatCurrency(valorMensalidade) : '—'}
              </td>
              <td className="py-3 px-3">
                <Badge variant="outline">Aguardando</Badge>
              </td>
              <td className="py-3 px-3 text-right">
                {onGerarCobranca && (
                  <Button type="button" size="sm" disabled={gerandoCobranca} onClick={onGerarCobranca}>
                    {gerandoCobranca ? (
                      <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                    ) : (
                      <CreditCard className="w-4 h-4 mr-1" />
                    )}
                    Gerar boleto
                  </Button>
                )}
              </td>
              <td className="py-3 px-3 text-right text-xs text-muted-foreground">—</td>
            </tr>
          )}

          {itens.map((item, index) => {
            const pid = item.pagamento_loja_id || item.id;
            return (
              <tr
                key={`${pid}-${item.asaas_id || index}`}
                className="border-b border-gray-100 dark:border-neutral-800 last:border-0 hover:bg-muted/30"
              >
                <td className="py-3 px-3 dark:text-gray-200">
                  {item.referencia_mes || item.status_display || 'Mensalidade'}
                  {item.numero_nf ? (
                    <span className="block text-xs text-muted-foreground">NF {item.numero_nf}</span>
                  ) : null}
                </td>
                <td className="py-3 px-3 dark:text-gray-200">
                  {formatDate(item.data_vencimento)}
                  {item.data_pagamento ? (
                    <span className="block text-xs text-green-700 dark:text-green-400">
                      Pago {formatDate(item.data_pagamento)}
                    </span>
                  ) : null}
                </td>
                <td className="py-3 px-3 font-semibold dark:text-gray-100">{formatCurrency(item.valor)}</td>
                <td className="py-3 px-3">
                  <StatusBadge item={item} />
                </td>
                <td className="py-3 px-3 text-right">{renderAcoesBoleto(item)}</td>
                <td className="py-3 px-3 text-right">{renderAcoesNf(item)}</td>
              </tr>
            );
          })}

          {!itens.length && !cobrancaAberta && !mostrarProximaLinha && (
            <tr>
              <td colSpan={6} className="py-10 px-4 text-center text-muted-foreground dark:text-gray-400">
                Nenhum pagamento no histórico. Use &quot;Gerar boleto&quot; para antecipar a mensalidade.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
