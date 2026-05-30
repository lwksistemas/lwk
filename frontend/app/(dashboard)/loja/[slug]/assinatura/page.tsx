'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  CreditCard,
  RefreshCw,
  CheckCircle,
  Clock,
  AlertTriangle,
  ArrowLeft,
  CalendarDays,
  Receipt,
  FileText,
} from 'lucide-react';
import apiClient from '@/lib/api-client';
import { resolveLojaApiSlug } from '@/lib/resolve-loja-slug';
import { formatCurrency, formatDate } from '@/lib/financeiro-helpers';
import { PaymentTabs } from './components/PaymentTabs';
import { NovaCobrancaModal } from './components/NovaCobrancaModal';
import { HistoricoPagamentos, type HistoricoPagamentoItem } from './components/HistoricoPagamentos';

interface AssinaturaData {
  loja: { id: number; nome: string; slug: string; plano: string; tipo_assinatura: string };
  financeiro: {
    id?: number;
    status_pagamento: string;
    valor_mensalidade: number;
    data_proxima_cobranca: string;
    dia_vencimento: number;
    tem_asaas: boolean;
    tem_mercadopago?: boolean;
    provedor_boleto?: 'asaas' | 'mercadopago';
    boleto_url: string;
    pix_qr_code: string;
    pix_copy_paste: string;
  };
  proximo_pagamento: {
    id: number;
    valor: number;
    data_vencimento: string;
    referencia_mes: string;
    boleto_url?: string;
    asaas_payment_id?: string;
  } | null;
  historico_pagamentos?: HistoricoPagamentoItem[];
}

const STATUS_BADGE: Record<string, 'default' | 'secondary' | 'destructive'> = {
  ativo: 'default',
  pendente: 'secondary',
  atrasado: 'destructive',
  suspenso: 'destructive',
};

const STATUS_ICON: Record<string, React.ReactNode> = {
  ativo: <CheckCircle className="w-4 h-4" />,
  pendente: <Clock className="w-4 h-4" />,
  atrasado: <AlertTriangle className="w-4 h-4" />,
  suspenso: <AlertTriangle className="w-4 h-4" />,
};

const STEPS = [
  { n: 1, title: 'Gerar cobrança', desc: 'Clique em Gerar boleto agora' },
  { n: 2, title: 'Pagar', desc: 'Boleto ou PIX (vence em até 3 dias)' },
  { n: 3, title: 'Nota fiscal', desc: 'Emitida após confirmação do pagamento' },
];

const shell = 'min-h-screen bg-white dark:bg-[#0d1117] text-gray-800 dark:text-gray-100';
const cardCls = 'dark:bg-neutral-800 dark:border-neutral-700';

export default function AssinaturaLojaPage() {
  const params = useParams();
  const slug = params.slug as string;

  useEffect(() => {
    const theme = localStorage.getItem('theme');
    if (theme === 'dark') document.documentElement.classList.add('dark');
  }, []);

  const [data, setData] = useState<AssinaturaData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [atualizandoStatus, setAtualizandoStatus] = useState(false);
  const [gerandoCobranca, setGerandoCobranca] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [novaCobranca, setNovaCobranca] = useState<any>(null);

  const carregarDados = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const apiSlug = await resolveLojaApiSlug(slug);
      const { data: d } = await apiClient.get(`/superadmin/loja/${apiSlug}/financeiro/`);
      setData(d);
    } catch (err: any) {
      const ax = err?.response;
      const detail = ax?.data?.error ?? ax?.data?.detail;
      const detailStr = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.join(', ') : '';
      if (ax?.status === 403) setError('Sem permissão. Apenas o responsável pode acessar.');
      else if (detailStr) setError(detailStr);
      else if (ax?.status === 404) setError('Financeiro não encontrado para esta loja.');
      else if (ax?.status && ax.status >= 500) setError('Erro no servidor. Aguarde um momento e tente novamente.');
      else if (!ax && (err?.code === 'ERR_NETWORK' || err?.message?.includes('Network')))
        setError('Erro de conexão com o servidor. Verifique sua internet e tente novamente.');
      else setError('Não foi possível carregar os dados. Faça login novamente se o problema continuar.');
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    carregarDados();
  }, [carregarDados]);

  const baixarBoleto = async (pagamentoId: number) => {
    try {
      const res = await apiClient.get(`/superadmin/loja-pagamentos/${pagamentoId}/baixar_boleto_pdf/`, {
        responseType: 'blob',
      });
      const blob = res.data as Blob;
      const ct = res.headers?.['content-type'] || blob.type || '';
      if (ct.includes('json') || blob.type?.includes('json')) {
        const d = JSON.parse(await blob.text());
        if (d?.error) {
          alert(d.error);
          return;
        }
        if (d?.boleto_url && d.provedor === 'mercadopago') {
          window.open(d.boleto_url, '_blank');
          return;
        }
      }
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `boleto_${slug}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      let msg = 'Erro ao baixar boleto';
      const ax = err?.response;
      if (ax?.status === 400 && ax.data instanceof Blob) {
        try {
          msg = JSON.parse(await ax.data.text()).error || msg;
        } catch {}
      } else if (ax?.data?.error) msg = ax.data.error;
      alert(msg);
    }
  };

  const atualizarStatus = async () => {
    if (!data?.financeiro.tem_asaas) return;
    try {
      setAtualizandoStatus(true);
      await apiClient.post(`/superadmin/loja-financeiro/${data.loja.id}/atualizar_status_asaas/`);
      await carregarDados();
      alert('Status atualizado!');
    } catch {
      alert('Erro ao atualizar status');
    } finally {
      setAtualizandoStatus(false);
    }
  };

  const gerarNovaCobranca = async () => {
    const financeiroId = data?.financeiro?.id;
    if (!financeiroId) {
      alert('Dados do financeiro não carregados. Recarregue a página e tente novamente.');
      return;
    }
    const body = { antecipado: true };
    const apiSlug = await resolveLojaApiSlug(slug);
    const endpoints = [
      `/superadmin/loja/${apiSlug}/financeiro/`,
      `/superadmin/loja/${slug}/financeiro/`,
      `/superadmin/loja-financeiro/${financeiroId}/renovar/`,
      `/superadmin/loja/${apiSlug}/financeiro/renovar/`,
    ];
    try {
      setGerandoCobranca(true);
      let lastErr: unknown = null;
      for (const url of endpoints) {
        try {
          const res = await apiClient.post(url, body);
          setNovaCobranca(res.data);
          setShowModal(true);
          await carregarDados();
          return;
        } catch (err: any) {
          lastErr = err;
          const st = err?.response?.status;
          if (st !== 404 && st !== 405) break;
        }
      }
      throw lastErr;
    } catch (err: any) {
      const ax = err?.response;
      const raw = ax?.data?.error ?? ax?.data?.detail;
      const msg =
        typeof raw === 'string'
          ? raw
          : ax?.status === 404
            ? 'Serviço de cobrança indisponível. Tente em alguns minutos ou avise o suporte.'
            : 'Erro ao gerar cobrança';
      alert(`Erro: ${msg}`);
    } finally {
      setGerandoCobranca(false);
    }
  };

  const copiarPix = (text?: string) => {
    if (text) {
      navigator.clipboard.writeText(text);
      alert('Código PIX copiado!');
    }
  };

  const historico = data?.historico_pagamentos ?? [];
  const pagosCount = useMemo(() => historico.filter((h) => h.is_paid).length, [historico]);

  if (loading) {
    return (
      <div className={`${shell} flex items-center justify-center p-6`}>
        <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className={`${shell} container mx-auto p-6`}>
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error || 'Dados não encontrados'}</AlertDescription>
        </Alert>
        <Button variant="outline" className="mt-4" asChild>
          <Link href={`/loja/${slug}/dashboard`}>Voltar</Link>
        </Button>
      </div>
    );
  }

  const fin = data.financeiro;
  const pp = data.proximo_pagamento;
  const st = fin.status_pagamento?.toLowerCase() || 'pendente';
  const temPagamento = (fin.tem_asaas || fin.tem_mercadopago) && (fin.boleto_url || fin.pix_copy_paste);

  return (
    <div className={`${shell} container mx-auto p-3 sm:p-6 space-y-4 sm:space-y-6 max-w-5xl`}>
      {/* Header */}
      <div className="flex flex-col gap-3">
        <Button variant="ghost" size="sm" className="w-fit dark:text-gray-200" asChild>
          <Link href={`/loja/${slug}/dashboard`} className="flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" />
            Voltar
          </Link>
        </Button>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold dark:text-gray-100">Pagar Assinatura</h1>
            <p className="text-sm text-muted-foreground dark:text-gray-400">
              {data.loja.nome} – {data.loja.plano} ({data.loja.tipo_assinatura})
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={STATUS_BADGE[st] || 'secondary'} className="text-xs sm:text-sm gap-1">
              {STATUS_ICON[st] || <Clock className="w-4 h-4" />}
              {fin.status_pagamento}
            </Badge>
            <Button variant="outline" size="sm" onClick={carregarDados}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Atualizar
            </Button>
            {fin.tem_asaas && (
              <Button variant="outline" size="sm" onClick={atualizarStatus} disabled={atualizandoStatus}>
                <RefreshCw className={`w-4 h-4 mr-2 ${atualizandoStatus ? 'animate-spin' : ''}`} />
                Atualizar status
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Resumo */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className={cardCls}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground dark:text-gray-400 flex items-center gap-2">
              <CreditCard className="w-4 h-4" />
              Mensalidade
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold dark:text-gray-100">{formatCurrency(fin.valor_mensalidade)}</p>
            <p className="text-xs text-muted-foreground dark:text-gray-400 mt-1">
              Vencimento todo dia {fin.dia_vencimento}
            </p>
          </CardContent>
        </Card>
        <Card className={cardCls}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground dark:text-gray-400 flex items-center gap-2">
              <CalendarDays className="w-4 h-4" />
              Próxima cobrança
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xl font-bold dark:text-gray-100">{formatDate(fin.data_proxima_cobranca)}</p>
            <p className="text-xs text-muted-foreground dark:text-gray-400 mt-1">
              Boleto gerado automaticamente antes do vencimento
            </p>
          </CardContent>
        </Card>
        <Card className={cardCls}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground dark:text-gray-400 flex items-center gap-2">
              <Receipt className="w-4 h-4" />
              Histórico
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xl font-bold dark:text-gray-100">
              {pagosCount} pago{pagosCount !== 1 ? 's' : ''}
            </p>
            <p className="text-xs text-muted-foreground dark:text-gray-400 mt-1">
              {historico.length} cobrança{historico.length !== 1 ? 's' : ''} no total
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Ações */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 sm:gap-6">
        <Card className={`lg:col-span-2 ${cardCls}`}>
          <CardHeader>
            <CardTitle className="text-base dark:text-gray-100">Pagar antes do vencimento</CardTitle>
            <CardDescription className="dark:text-gray-400">
              Antecipe o pagamento e receba a NFS-e após a confirmação.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              {STEPS.map((step) => (
                <div key={step.n} className="flex gap-3 items-start">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-medium text-muted-foreground">
                    {step.n}
                  </span>
                  <div>
                    <p className="text-sm font-medium dark:text-gray-100">{step.title}</p>
                    <p className="text-xs text-muted-foreground dark:text-gray-400">{step.desc}</p>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-muted-foreground dark:text-gray-500 border-l-2 border-muted pl-3">
              Pagamento antecipado é justo: os dias pagos antes do vencimento entram no próximo ciclo.
            </p>
            <Button onClick={gerarNovaCobranca} disabled={gerandoCobranca} className="w-full sm:w-auto">
              {gerandoCobranca ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Gerando…
                </>
              ) : (
                <>
                  <CreditCard className="w-4 h-4 mr-2" />
                  Gerar boleto agora
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        <Card className={`lg:col-span-3 ${cardCls}`}>
          <CardHeader>
            <CardTitle className="text-base dark:text-gray-100 flex items-center gap-2">
              <FileText className="w-4 h-4 text-muted-foreground" />
              Cobrança em aberto
            </CardTitle>
            <CardDescription className="dark:text-gray-400">
              {temPagamento
                ? 'Pague por boleto ou PIX.'
                : 'Nenhum boleto ou PIX pendente no momento.'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {temPagamento ? (
              <PaymentTabs
                boletoUrl={fin.boleto_url}
                pixQrCode={fin.pix_qr_code}
                pixCopyPaste={fin.pix_copy_paste}
                proximoPagamentoId={pp?.id}
                asaasPaymentId={pp?.asaas_payment_id}
                onBaixarBoleto={baixarBoleto}
                onCopiarPix={() => copiarPix(fin.pix_copy_paste)}
              />
            ) : (
              <div className="rounded-lg border border-dashed border-gray-300 dark:border-neutral-600 py-8 px-4 text-center">
                <CheckCircle className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm font-medium dark:text-gray-200">Tudo em dia</p>
                <p className="text-xs text-muted-foreground dark:text-gray-400 mt-1">
                  Próxima cobrança em {formatDate(fin.data_proxima_cobranca)}.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Histórico */}
      <Card className={cardCls}>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <CardTitle className="text-base dark:text-gray-100">Histórico de pagamentos</CardTitle>
              <CardDescription className="dark:text-gray-400">
                Boletos, pagamentos e notas fiscais
              </CardDescription>
            </div>
            {historico.length > 0 && (
              <Badge variant="outline">{historico.length} registro{historico.length !== 1 ? 's' : ''}</Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <HistoricoPagamentos itens={historico} slug={slug} />
        </CardContent>
      </Card>

      {showModal && novaCobranca && (
        <NovaCobrancaModal
          data={novaCobranca}
          onClose={() => setShowModal(false)}
          onCopiarPix={() => copiarPix(novaCobranca.pix_copy_paste)}
        />
      )}
    </div>
  );
}
