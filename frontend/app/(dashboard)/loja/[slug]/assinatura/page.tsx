'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
} from 'lucide-react';
import apiClient from '@/lib/api-client';
import { resolveLojaApiSlug } from '@/lib/resolve-loja-slug';
import { formatCurrency, formatDate } from '@/lib/financeiro-helpers';
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

const shell =
  'min-h-screen w-full bg-sky-50 dark:bg-slate-950 text-gray-800 dark:text-gray-100';
const pagePad = 'w-full min-h-screen px-4 sm:px-6 lg:px-8 py-4 sm:py-6 space-y-4 sm:space-y-6';
const cardCls =
  'w-full bg-white/95 dark:bg-slate-900/95 border border-sky-100 dark:border-slate-700 shadow-sm';

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

  if (loading) {
    return (
      <div className={`${shell} flex items-center justify-center p-6`}>
        <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className={`${shell} ${pagePad}`}>
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
  const historico = data.historico_pagamentos ?? [];
  const temPagamentoAberto =
    (fin.tem_asaas || fin.tem_mercadopago) && (fin.boleto_url || fin.pix_copy_paste);

  const cobrancaAberta = temPagamentoAberto
    ? {
        valor: pp?.valor ?? fin.valor_mensalidade,
        data_vencimento: pp?.data_vencimento ?? fin.data_proxima_cobranca,
        referencia_mes: pp?.referencia_mes ?? null,
        boleto_url: fin.boleto_url || pp?.boleto_url,
        pix_copy_paste: fin.pix_copy_paste,
        pagamento_id: pp?.id,
      }
    : null;

  return (
    <div className={`${shell} ${pagePad}`}>
      <div className="flex flex-col gap-3">
        <Button variant="ghost" size="sm" className="w-fit dark:text-gray-200" asChild>
          <Link href={`/loja/${slug}/dashboard`} className="flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" />
            Voltar
          </Link>
        </Button>
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold dark:text-gray-100">Assinatura</h1>
            <p className="text-sm text-muted-foreground dark:text-gray-400">
              {data.loja.nome} · {data.loja.plano} ({data.loja.tipo_assinatura})
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={STATUS_BADGE[st] || 'secondary'} className="text-xs sm:text-sm gap-1">
              {STATUS_ICON[st] || <Clock className="w-4 h-4" />}
              {fin.status_pagamento}
            </Badge>
            <Button variant="outline" size="sm" onClick={carregarDados}>
              <RefreshCw className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">Atualizar</span>
            </Button>
            {fin.tem_asaas && (
              <Button variant="outline" size="sm" onClick={atualizarStatus} disabled={atualizandoStatus}>
                <RefreshCw className={`w-4 h-4 sm:mr-2 ${atualizandoStatus ? 'animate-spin' : ''}`} />
                <span className="hidden sm:inline">Sync Asaas</span>
              </Button>
            )}
          </div>
        </div>
      </div>

      <Card className={cardCls}>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium dark:text-gray-100 flex flex-wrap items-center gap-x-4 gap-y-1">
            <span className="inline-flex items-center gap-1.5">
              <CreditCard className="w-4 h-4 text-muted-foreground" />
              {formatCurrency(fin.valor_mensalidade)}/mês
            </span>
            <span className="text-muted-foreground font-normal">·</span>
            <span className="inline-flex items-center gap-1.5 font-normal text-muted-foreground dark:text-gray-400">
              <CalendarDays className="w-4 h-4" />
              Próximo vencimento:{' '}
              <strong className="text-foreground dark:text-gray-100">
                {formatDate(fin.data_proxima_cobranca)}
              </strong>
              <span className="text-xs">(dia {fin.dia_vencimento})</span>
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <HistoricoPagamentos
            itens={historico}
            slug={slug}
            proximaCobranca={fin.data_proxima_cobranca}
            valorMensalidade={fin.valor_mensalidade}
            cobrancaAberta={cobrancaAberta}
            onGerarCobranca={gerarNovaCobranca}
            gerandoCobranca={gerandoCobranca}
            onCopiarPix={() => copiarPix(fin.pix_copy_paste)}
          />
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
