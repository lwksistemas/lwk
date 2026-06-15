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
  CreditCard,
} from 'lucide-react';
import apiClient from '@/lib/api-client';
import { resolveLojaApiSlug } from '@/lib/resolve-loja-slug';
import { useLojaTheme } from '@/hooks/useLojaTheme';
import { LojaThemedPageShell } from '@/components/loja/LojaThemedPageShell';
import { assinaturaBackPath } from '@/lib/loja-theme';
import { resolveIsClinicaBeleza } from '@/lib/loja-tipo';
import {
  ClinicaBelezaPageContent,
  ClinicaBelezaPanel,
} from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import {
  ClinicaBelezaStandardPageHeader,
  useClinicaBelezaShellActions,
} from '@/components/clinica-beleza/ClinicaBelezaPageHeaderContext';
import { CLINICA_BELEZA_PRIMARY } from '@/components/clinica-beleza/clinica-beleza-nav';
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

export default function AssinaturaLojaPage() {
  const params = useParams();
  const slug = params.slug as string;
  const shellActions = useClinicaBelezaShellActions();
  const { loja, theme, loading: loadingTheme } = useLojaTheme(slug);
  const [tipoLojaNome, setTipoLojaNome] = useState('');

  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        const { data } = await apiClient.get<{ tipo_loja_nome?: string }>(
          `/superadmin/lojas/info_publica/?slug=${encodeURIComponent(slug)}`,
        );
        if (!cancel) setTipoLojaNome(data?.tipo_loja_nome || '');
      } catch {
        if (!cancel) setTipoLojaNome('');
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

  const tipoNome = loja?.tipo_loja_nome || tipoLojaNome;
  const backHref = assinaturaBackPath(slug, tipoNome);
  const clinicaBeleza =
    Boolean(shellActions) ||
    resolveIsClinicaBeleza(tipoNome, tipoLojaNome, data?.loja?.plano);
  const accent = clinicaBeleza ? CLINICA_BELEZA_PRIMARY : theme.corPrimaria;

  if (loadingTheme || loading) {
    return (
      <div
        className="min-h-screen flex items-center justify-center dark:bg-gray-950"
        style={{ backgroundColor: clinicaBeleza ? '#f7f2f4' : theme.pageBg }}
      >
        <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const renderHistorico = (corPrimaria: string, neutralStyle: boolean) => {
    if (error || !data) {
      return (
        <>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error || 'Dados não encontrados'}</AlertDescription>
          </Alert>
          {!clinicaBeleza && (
            <Button variant="outline" className="mt-4" asChild>
              <Link href={backHref}>Voltar</Link>
            </Button>
          )}
        </>
      );
    }

    const fin = data.financeiro;
    const pp = data.proximo_pagamento;
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
      <>
        <HistoricoPagamentos
          itens={historico}
          slug={slug}
          proximaCobranca={fin.data_proxima_cobranca}
          valorMensalidade={fin.valor_mensalidade}
          cobrancaAberta={cobrancaAberta}
          onGerarCobranca={gerarNovaCobranca}
          gerandoCobranca={gerandoCobranca}
          onCopiarPix={() => copiarPix(fin.pix_copy_paste)}
          corPrimaria={corPrimaria}
          neutralStyle={neutralStyle}
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

  const headerActionsThemed = data ? (
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

  const headerActionsClinica = data ? (
    <>
      <Badge variant={STATUS_BADGE[st] || 'secondary'} className="text-xs sm:text-sm gap-1">
        {STATUS_ICON[st] || <Clock className="w-4 h-4" />}
        {data.financeiro.status_pagamento}
      </Badge>
      <button
        type="button"
        onClick={carregarDados}
        className="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-800 transition-colors"
      >
        <RefreshCw className="w-4 h-4" />
        <span className="hidden sm:inline">Atualizar</span>
      </button>
      {data.financeiro.tem_asaas && (
        <button
          type="button"
          onClick={atualizarStatus}
          disabled={atualizandoStatus}
          className="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-800 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${atualizandoStatus ? 'animate-spin' : ''}`} />
          <span className="hidden lg:inline">Sync Asaas</span>
        </button>
      )}
    </>
  ) : null;

  if (clinicaBeleza) {
    return (
      <>
        <ClinicaBelezaStandardPageHeader
          title="Assinatura"
          subtitle={subtitle}
          icon={CreditCard}
          backHref={backHref}
          extraActions={headerActionsClinica}
        />
        <ClinicaBelezaPageContent>
          <ClinicaBelezaPanel className="p-4 sm:p-6">
            {renderHistorico(accent, true)}
          </ClinicaBelezaPanel>
        </ClinicaBelezaPageContent>
      </>
    );
  }

  if (error || !data) {
    return (
      <LojaThemedPageShell
        slug={slug}
        tipoLojaNome={tipoNome}
        theme={theme}
        title="Assinatura"
        subtitle={loja?.nome}
      >
        {renderHistorico(theme.corPrimaria, false)}
      </LojaThemedPageShell>
    );
  }

  return (
    <LojaThemedPageShell
      slug={slug}
      tipoLojaNome={tipoNome}
      theme={theme}
      title="Assinatura"
      subtitle={subtitle}
      headerActions={headerActionsThemed}
    >
      <Card
        className="w-full bg-white/95 dark:bg-slate-900/95 shadow-sm"
        style={{ borderColor: theme.cardBorder }}
      >
        <CardContent className="pt-6">
          {renderHistorico(theme.corPrimaria, false)}
        </CardContent>
      </Card>
    </LojaThemedPageShell>
  );
}
