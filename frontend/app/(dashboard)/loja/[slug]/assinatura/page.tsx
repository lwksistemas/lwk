'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  RefreshCw,
  CheckCircle,
  Clock,
  AlertTriangle,
} from 'lucide-react';
import apiClient from '@/lib/api-client';
import { resolveLojaApiSlug } from '@/lib/resolve-loja-slug';
import { useLojaTheme } from '@/hooks/useLojaTheme';
import { LojaThemedPageShell } from '@/components/loja/LojaThemedPageShell';
import { assinaturaBackPath } from '@/lib/loja-theme';
import { NovaCobrancaModal } from './components/NovaCobrancaModal';
import { HistoricoPagamentos, type HistoricoPagamentoItem } from './components/HistoricoPagamentos';
import { AssinaturaAvisoAlert } from '@/components/loja/AssinaturaAvisoAlert';
import { calcularAvisoAssinaturaLocal, type AssinaturaAviso } from '@/lib/assinatura-aviso';
import { clearStoreBlockedMark } from '@/lib/loja-bloqueio-inadimplencia';

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
  assinatura_aviso?: AssinaturaAviso | null;
  is_blocked?: boolean;
  geracao_boleto?: {
    pode_gerar: boolean;
    motivo?: string | null;
    data_liberacao?: string | null;
    dias_ate_liberacao?: number | null;
  };
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

export default function AssinaturaLojaPage() {
  const params = useParams();
  const slug = params.slug as string;
  const { loja, theme, loading: loadingTheme } = useLojaTheme(slug);
  const [tipoLojaNome, setTipoLojaNome] = useState('');

  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        const { data } = await apiClient.get<{ tipo_loja_nome?: string; is_blocked?: boolean }>(
          `/superadmin/lojas/info_publica/?slug=${encodeURIComponent(slug)}`,
        );
        if (!cancel) {
          setTipoLojaNome(data?.tipo_loja_nome || '');
          setLojaBloqueada(Boolean(data?.is_blocked));
        }
      } catch {
        if (!cancel) {
          setTipoLojaNome('');
          setLojaBloqueada(false);
        }
      }
    })();
    return () => {
      cancel = true;
    };
  }, [slug]);

  useEffect(() => {
    const stored = localStorage.getItem('theme');
    if (stored === 'dark') document.documentElement.classList.add('dark');
  }, []);

  const [data, setData] = useState<AssinaturaData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lojaBloqueada, setLojaBloqueada] = useState(false);
  const [atualizandoStatus, setAtualizandoStatus] = useState(false);
  const [gerandoCobranca, setGerandoCobranca] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [novaCobranca, setNovaCobranca] = useState<any>(null);

  const sincronizarBloqueio = useCallback(async (blockedHint?: boolean) => {
    try {
      const { data: info } = await apiClient.get<{ is_blocked?: boolean }>(
        `/superadmin/lojas/info_publica/?slug=${encodeURIComponent(slug)}&_t=${Date.now()}`,
      );
      const blocked = Boolean(info?.is_blocked ?? blockedHint);
      setLojaBloqueada(blocked);
      if (!blocked) clearStoreBlockedMark();
    } catch {
      if (typeof blockedHint === 'boolean') {
        setLojaBloqueada(blockedHint);
        if (!blockedHint) clearStoreBlockedMark();
      }
    }
  }, [slug]);

  const carregarDados = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const apiSlug = await resolveLojaApiSlug(slug);
      const { data: d } = await apiClient.get<AssinaturaData>(`/superadmin/loja/${apiSlug}/financeiro/`);
      setData(d);
      await sincronizarBloqueio(Boolean(d?.is_blocked));
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
  }, [slug, sincronizarBloqueio]);

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
    const body = {};
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

  const tipoNome = loja?.tipo_loja_nome || tipoLojaNome;
  const backHref = assinaturaBackPath(slug, tipoNome);

  if (loadingTheme || loading) {
    return (
      <div
        className="min-h-screen flex items-center justify-center dark:bg-gray-950"
        style={{ backgroundColor: theme.pageBg }}
      >
        <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const renderHistorico = () => {
    if (error || !data) {
      return (
        <>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error || 'Dados não encontrados'}</AlertDescription>
          </Alert>
          <Button variant="outline" className="mt-4" asChild>
            <Link href={backHref}>Voltar</Link>
          </Button>
        </>
      );
    }

    const fin = data.financeiro;
    const pp = data.proximo_pagamento;
    const historico = data.historico_pagamentos ?? [];
    const avisoAssinatura =
      data.assinatura_aviso ??
      calcularAvisoAssinaturaLocal(fin.data_proxima_cobranca, lojaBloqueada);
    const temPagamentoAberto =
      (fin.tem_asaas || fin.tem_mercadopago) && (fin.boleto_url || fin.pix_copy_paste);
    const temCobrancaEmAbertoNoHistorico = historico.some(
      (i) => i.is_pending || i.is_overdue,
    );

    const cobrancaAberta =
      temPagamentoAberto && !temCobrancaEmAbertoNoHistorico
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
      <>
        {lojaBloqueada && (
          <Alert variant="destructive" className="mb-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription className="text-sm leading-relaxed">
              Sistema bloqueado por inadimplência. Regularize o pagamento abaixo para liberar o acesso.
            </AlertDescription>
          </Alert>
        )}
        {!lojaBloqueada && (
          <Alert className="mb-4 border-green-400 bg-green-50 text-green-950 dark:bg-green-950/30 dark:border-green-700 dark:text-green-100">
            <CheckCircle className="h-4 w-4" />
            <AlertDescription className="text-sm leading-relaxed">
              Pagamento em dia — sistema liberado.{' '}
              <Link href={backHref} className="font-semibold underline underline-offset-2">
                Acessar o sistema
              </Link>
            </AlertDescription>
          </Alert>
        )}
        <AssinaturaAvisoAlert slug={slug} aviso={avisoAssinatura} className="mb-4" />
        <HistoricoPagamentos
          itens={historico}
          slug={slug}
          proximaCobranca={fin.data_proxima_cobranca}
          valorMensalidade={fin.valor_mensalidade}
          cobrancaAberta={cobrancaAberta}
          geracaoBoleto={data.geracao_boleto}
          onGerarCobranca={gerarNovaCobranca}
          gerandoCobranca={gerandoCobranca}
          onCopiarPix={() => copiarPix(fin.pix_copy_paste)}
          corPrimaria={theme.corPrimaria}
          neutralStyle={false}
        />
        {showModal && novaCobranca && (
          <NovaCobrancaModal
            data={novaCobranca}
            onClose={() => setShowModal(false)}
            onCopiarPix={() => copiarPix(novaCobranca.pix_copy_paste)}
          />
        )}
      </>
    );
  };

  const st = data?.financeiro.status_pagamento?.toLowerCase() || 'pendente';
  const subtitle = data
    ? `${data.loja.nome} · ${data.loja.plano} (${data.loja.tipo_assinatura})`
    : loja?.nome || '';

  const headerActions = data ? (
    <>
      <Badge variant={STATUS_BADGE[st] || 'secondary'} className="text-xs sm:text-sm gap-1 bg-white/20 text-white border-white/30">
        {STATUS_ICON[st] || <Clock className="w-4 h-4" />}
        {data.financeiro.status_pagamento}
      </Badge>
      <Button
        variant="secondary"
        size="sm"
        className="bg-white/15 text-white border-white/20 hover:bg-white/25"
        onClick={carregarDados}
      >
        <RefreshCw className="w-4 h-4 sm:mr-2" />
        <span className="hidden sm:inline">Atualizar</span>
      </Button>
      {data.financeiro.tem_asaas && (
        <Button
          variant="secondary"
          size="sm"
          className="bg-white/15 text-white border-white/20 hover:bg-white/25"
          onClick={atualizarStatus}
          disabled={atualizandoStatus}
        >
          <RefreshCw className={`w-4 h-4 sm:mr-2 ${atualizandoStatus ? 'animate-spin' : ''}`} />
          <span className="hidden lg:inline">Sync Asaas</span>
        </Button>
      )}
    </>
  ) : null;

  return (
    <LojaThemedPageShell
      slug={slug}
      tipoLojaNome={tipoNome}
      theme={theme}
      title="Assinatura"
      subtitle={subtitle}
      hideBackButton={lojaBloqueada}
      headerActions={headerActions}
    >
      <Card
        className="w-full bg-white/95 dark:bg-slate-900/95 shadow-sm"
        style={{ borderColor: theme.cardBorder }}
      >
        <CardContent className="pt-6">{renderHistorico()}</CardContent>
      </Card>
    </LojaThemedPageShell>
  );
}
