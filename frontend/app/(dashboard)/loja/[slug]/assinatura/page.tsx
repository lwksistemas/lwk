'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
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
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import {
  ClinicaBelezaStandardPageHeader,
  useClinicaBelezaShellActions,
} from '@/components/clinica-beleza/ClinicaBelezaPageHeaderContext';
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
    em_degustacao?: boolean;
    degustacao_ate?: string | null;
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
  const clinicShell = useClinicaBelezaShellActions();
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
  const [decidindoDegustacao, setDecidindoDegustacao] = useState(false);
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

  const carregarDados = useCallback(async (opts?: { silencioso?: boolean }) => {
    const silencioso = opts?.silencioso ?? false;
    try {
      if (!silencioso) setLoading(true);
      setError(null);
      const apiSlug = await resolveLojaApiSlug(slug);
      const { data: d } = await apiClient.get<AssinaturaData>(`/superadmin/loja/${apiSlug}/financeiro/`);
      setData(d);
      await sincronizarBloqueio(Boolean(d?.is_blocked));
    } catch (err) {
      const errorObj = err && typeof err === 'object' ? (err as Record<string, unknown>) : null;
      const response = errorObj?.response as Record<string, unknown> | undefined;
      const errData = response?.data;
      const detail =
        typeof errData === 'object' && errData !== null
          ? (errData as { error?: unknown; detail?: unknown }).error ?? (errData as { detail?: unknown }).detail
          : null;
      const detailStr = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.join(', ') : '';
      const status = typeof response?.status === 'number' ? response.status : undefined;
      const networkError =
        !response &&
        (errorObj?.code === 'ERR_NETWORK' ||
          (err instanceof Error ? err.message.includes('Network') : false));
      if (status === 403) {
        setError(detailStr || 'Sem permissão. Apenas o responsável ou um administrador da loja pode acessar.');
      }
      else if (detailStr) setError(detailStr);
      else if (status === 404) setError('Financeiro não encontrado para esta loja.');
      else if (status && status >= 500) setError('Erro no servidor. Aguarde um momento e tente novamente.');
      else if (networkError) setError('Erro de conexão com o servidor. Verifique sua internet e tente novamente.');
      else setError('Não foi possível carregar os dados. Faça login novamente se o problema continuar.');
    } finally {
      if (!silencioso) setLoading(false);
    }
  }, [slug, sincronizarBloqueio]);

  useEffect(() => {
    carregarDados();
  }, [carregarDados]);

  const atualizarPagina = async () => {
    try {
      setAtualizandoStatus(true);
      if (data?.financeiro.tem_asaas && data?.loja?.id) {
        await apiClient.post(`/superadmin/loja-financeiro/${data.loja.id}/atualizar_status_asaas/`);
      }
      await carregarDados({ silencioso: true });
    } catch {
      alert('Erro ao atualizar. Tente novamente.');
    } finally {
      setAtualizandoStatus(false);
    }
  };

  const decidirDegustacao = async (acao: 'pagar' | 'cancelar') => {
    if (acao === 'cancelar' && !window.confirm('Cancelar a loja? Nenhum boleto será gerado e o acesso continua bloqueado.')) {
      return;
    }
    const apiSlug = await resolveLojaApiSlug(slug);
    try {
      setDecidindoDegustacao(true);
      const res = await apiClient.post(`/superadmin/loja/${apiSlug}/financeiro/degustacao/`, { acao });
      if (acao === 'pagar') {
        setNovaCobranca(res.data);
        setShowModal(true);
      } else {
        alert(res.data?.message || 'Loja cancelada. Nenhum boleto foi gerado.');
      }
      await carregarDados();
    } catch (err) {
      const errorObj = err && typeof err === 'object' ? (err as Record<string, unknown>) : null;
      const response = errorObj?.response as Record<string, unknown> | undefined;
      const errData = response?.data;
      const raw =
        typeof errData === 'object' && errData !== null
          ? (errData as { error?: unknown }).error
          : null;
      alert(typeof raw === 'string' ? raw : 'Não foi possível concluir a escolha.');
    } finally {
      setDecidindoDegustacao(false);
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
        } catch (err) {
          lastErr = err;
          const errorObj = err && typeof err === 'object' ? (err as Record<string, unknown>) : null;
          const response = errorObj?.response as Record<string, unknown> | undefined;
          const st = typeof response?.status === 'number' ? response.status : undefined;
          if (st !== 404 && st !== 405) break;
        }
      }
      throw lastErr;
    } catch (err) {
      const errorObj = err && typeof err === 'object' ? (err as Record<string, unknown>) : null;
      const response = errorObj?.response as Record<string, unknown> | undefined;
      const errData = response?.data;
      const raw =
        typeof errData === 'object' && errData !== null
          ? (errData as { error?: unknown; detail?: unknown }).error ?? (errData as { detail?: unknown }).detail
          : null;
      const status = typeof response?.status === 'number' ? response.status : undefined;
      const msg =
        typeof raw === 'string'
          ? raw
          : status === 404
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
    const spinner = <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />;
    if (clinicShell) {
      return (
        <>
          <ClinicaBelezaStandardPageHeader title="Assinatura" subtitle={loja?.nome || ''} />
          <ClinicaBelezaPageContent>
            <div className="flex justify-center py-16">{spinner}</div>
          </ClinicaBelezaPageContent>
        </>
      );
    }
    return (
      <div
        className="min-h-screen flex items-center justify-center dark:bg-gray-950"
        style={{ backgroundColor: theme.pageBg }}
      >
        {spinner}
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
    const emDegustacao = Boolean(fin.em_degustacao);
    const bloqueada = lojaBloqueada || Boolean(data.is_blocked);
    const avisoAssinatura = emDegustacao
      ? data.assinatura_aviso ?? null
      : data.assinatura_aviso ??
        calcularAvisoAssinaturaLocal(fin.data_proxima_cobranca, bloqueada);
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
        {bloqueada && emDegustacao && (
          <Alert variant="destructive" className="mb-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription className="text-sm leading-relaxed space-y-3">
              <p>
                A demonstração acabou. Escolha pagar o boleto ou cancelar a loja.
                Sem essa escolha, o sistema continua bloqueado e nenhum boleto é gerado.
              </p>
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  size="sm"
                  disabled={decidindoDegustacao}
                  onClick={() => decidirDegustacao('pagar')}
                >
                  Pagar boleto
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  disabled={decidindoDegustacao}
                  onClick={() => decidirDegustacao('cancelar')}
                >
                  Cancelar loja
                </Button>
              </div>
            </AlertDescription>
          </Alert>
        )}
        {bloqueada && !emDegustacao && (
          <Alert variant="destructive" className="mb-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription className="text-sm leading-relaxed">
              Sistema bloqueado por inadimplência. Regularize o pagamento abaixo para liberar o acesso.
            </AlertDescription>
          </Alert>
        )}
        {!bloqueada && emDegustacao && (
          <Alert className="mb-4 border-amber-400 bg-amber-50 text-amber-950 dark:bg-amber-950/30 dark:border-amber-700 dark:text-amber-100">
            <Clock className="h-4 w-4" />
            <AlertDescription className="text-sm leading-relaxed">
              Demonstração até{' '}
              {fin.degustacao_ate ? fin.degustacao_ate.split('-').reverse().join('/') : 'o prazo combinado'}.
              Nenhum boleto foi gerado.{' '}
              <Link href={backHref} className="font-semibold underline underline-offset-2">
                Acessar o sistema
              </Link>
            </AlertDescription>
          </Alert>
        )}
        {!bloqueada && !emDegustacao && (
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
          neutralStyle={Boolean(clinicShell)}
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

  const atualizarBtn = (
    <Button
      variant="secondary"
      size="sm"
      className={
        clinicShell
          ? 'text-white hover:opacity-90'
          : 'bg-white/15 text-white border-white/20 hover:bg-white/25'
      }
      style={clinicShell ? { backgroundColor: theme.corPrimaria } : undefined}
      onClick={atualizarPagina}
      disabled={atualizandoStatus || !data}
    >
      <RefreshCw className={`w-4 h-4 sm:mr-2 ${atualizandoStatus ? 'animate-spin' : ''}`} />
      <span className="hidden sm:inline">Atualizar</span>
    </Button>
  );

  const headerActions = data ? (
    <>
      <Badge
        variant={STATUS_BADGE[st] || 'secondary'}
        className={
          clinicShell
            ? 'text-xs sm:text-sm gap-1'
            : 'text-xs sm:text-sm gap-1 bg-white/20 text-white border-white/30'
        }
      >
        {STATUS_ICON[st] || <Clock className="w-4 h-4" />}
        {data.financeiro.status_pagamento}
      </Badge>
      {atualizarBtn}
    </>
  ) : null;

  const historicoLista = (
    <ClinicaBelezaPanel>
      <div className="p-3 sm:p-4">{renderHistorico()}</div>
    </ClinicaBelezaPanel>
  );

  if (clinicShell) {
    return (
      <>
        <ClinicaBelezaStandardPageHeader
          title="Assinatura"
          subtitle={subtitle}
          backHref={lojaBloqueada ? undefined : backHref}
          showBack={!lojaBloqueada}
          extraActions={headerActions}
        />
        <ClinicaBelezaPageContent>{historicoLista}</ClinicaBelezaPageContent>
      </>
    );
  }

  return (
    <LojaThemedPageShell
      slug={slug}
      tipoLojaNome={tipoNome}
      theme={theme}
      title="Assinatura"
      subtitle={subtitle}
      hideBackButton={lojaBloqueada}
      headerActions={headerActions}
      fullWidth
    >
      {historicoLista}
    </LojaThemedPageShell>
  );
}
