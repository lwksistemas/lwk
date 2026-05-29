'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CreditCard, Download, RefreshCw, CheckCircle, Clock, AlertTriangle, ArrowLeft } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { resolveLojaApiSlug } from '@/lib/resolve-loja-slug';
import { formatCurrency, formatDate } from '@/lib/financeiro-helpers';
import { PaymentTabs } from './components/PaymentTabs';
import { NovaCobrancaModal } from './components/NovaCobrancaModal';
import { HistoricoPagamentos, type HistoricoPagamentoItem } from './components/HistoricoPagamentos';

interface AssinaturaData {
  loja: { id: number; nome: string; slug: string; plano: string; tipo_assinatura: string };
  financeiro: {
    status_pagamento: string; valor_mensalidade: number; data_proxima_cobranca: string;
    dia_vencimento: number; tem_asaas: boolean; tem_mercadopago?: boolean;
    provedor_boleto?: 'asaas' | 'mercadopago'; boleto_url: string; pix_qr_code: string; pix_copy_paste: string;
  };
  proximo_pagamento: { id: number; valor: number; data_vencimento: string; referencia_mes: string; boleto_url?: string; asaas_payment_id?: string } | null;
  historico_pagamentos?: HistoricoPagamentoItem[];
}

const STATUS_ICON: Record<string, React.ReactNode> = {
  ativo: <CheckCircle className="w-4 h-4" />,
  atrasado: <AlertTriangle className="w-4 h-4" />,
  suspenso: <AlertTriangle className="w-4 h-4" />,
};

const STATUS_COLOR: Record<string, 'default' | 'secondary' | 'destructive'> = {
  ativo: 'default', pendente: 'secondary', atrasado: 'destructive', suspenso: 'destructive',
};

export default function AssinaturaLojaPage() {
  const params = useParams();
  const slug = params.slug as string;

  // Aplicar dark mode baseado na preferência salva (mesma chave do CRM)
  useEffect(() => {
    const theme = localStorage.getItem('theme');
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    }
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
      setLoading(true); setError(null);
      const apiSlug = await resolveLojaApiSlug(slug);
      const { data: d } = await apiClient.get(`/superadmin/loja/${apiSlug}/financeiro/`);
      setData(d);
    } catch (err: any) {
      const ax = err?.response;
      const detail = ax?.data?.error ?? ax?.data?.detail;
      const detailStr = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.join(', ') : '';
      if (ax?.status === 403) {
        setError('Sem permissão. Apenas o responsável pode acessar.');
      } else if (detailStr) {
        setError(detailStr);
      } else if (ax?.status === 404) {
        setError('Financeiro não encontrado para esta loja.');
      } else if (ax?.status && ax.status >= 500) {
        setError('Erro no servidor. Aguarde um momento e tente novamente.');
      } else if (!ax && (err?.code === 'ERR_NETWORK' || err?.message?.includes('Network'))) {
        setError('Erro de conexão com o servidor. Verifique sua internet e tente novamente.');
      } else {
        setError('Não foi possível carregar os dados. Faça login novamente se o problema continuar.');
      }
    } finally { setLoading(false); }
  }, [slug]);

  useEffect(() => { carregarDados(); }, [carregarDados]);

  const baixarBoleto = async (pagamentoId: number) => {
    try {
      const res = await apiClient.get(`/superadmin/loja-pagamentos/${pagamentoId}/baixar_boleto_pdf/`, { responseType: 'blob' });
      const blob = res.data as Blob;
      const ct = res.headers?.['content-type'] || blob.type || '';
      if (ct.includes('json') || blob.type?.includes('json')) {
        const d = JSON.parse(await blob.text());
        if (d?.error) { alert(d.error); return; }
        if (d?.boleto_url && d.provedor === 'mercadopago') { window.open(d.boleto_url, '_blank'); return; }
      }
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = `boleto_${slug}.pdf`;
      document.body.appendChild(a); a.click(); window.URL.revokeObjectURL(url); document.body.removeChild(a);
    } catch (err: any) {
      let msg = 'Erro ao baixar boleto';
      const ax = err?.response;
      if (ax?.status === 400 && ax.data instanceof Blob) { try { msg = JSON.parse(await ax.data.text()).error || msg; } catch {} }
      else if (ax?.data?.error) msg = ax.data.error;
      alert(msg);
    }
  };

  const atualizarStatus = async () => {
    if (!data?.financeiro.tem_asaas) return;
    try { setAtualizandoStatus(true); await apiClient.post(`/superadmin/loja-financeiro/${data.loja.id}/atualizar_status_asaas/`); await carregarDados(); alert('Status atualizado!'); }
    catch { alert('Erro ao atualizar status'); } finally { setAtualizandoStatus(false); }
  };

  const gerarNovaCobranca = async () => {
    if (!data?.loja.id) return;
    try {
      setGerandoCobranca(true);
      const res = await apiClient.post(`/superadmin/financeiro/${data.loja.id}/renovar/`, { dia_vencimento: data.financeiro.dia_vencimento });
      setNovaCobranca(res.data); setShowModal(true); await carregarDados();
    } catch (err: any) { alert(`Erro: ${err.response?.data?.error || 'Erro ao gerar cobrança'}`); }
    finally { setGerandoCobranca(false); }
  };

  const copiarPix = (text?: string) => { if (text) { navigator.clipboard.writeText(text); alert('Código PIX copiado!'); } };

  const pw = 'min-h-screen bg-white dark:bg-[#0d1117] text-gray-800 dark:text-gray-100';

  if (loading) return <div className={`${pw} flex items-center justify-center p-6`}><RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" /></div>;
  if (error || !data) return (
    <div className={`${pw} container mx-auto p-6`}>
      <Alert variant="destructive"><AlertTriangle className="h-4 w-4" /><AlertDescription>{error || 'Dados não encontrados'}</AlertDescription></Alert>
      <Button variant="outline" className="mt-4" asChild><Link href={`/loja/${slug}/dashboard`}>Voltar</Link></Button>
    </div>
  );

  const fin = data.financeiro;
  const pp = data.proximo_pagamento;
  const st = fin.status_pagamento?.toLowerCase();

  return (
    <div className={`${pw} container mx-auto p-3 sm:p-6 space-y-4 sm:space-y-6`}>
      {/* Header */}
      <div className="flex flex-col gap-3">
        <Button variant="ghost" size="sm" className="w-fit dark:text-gray-200" asChild>
          <Link href={`/loja/${slug}/dashboard`} className="flex items-center gap-2"><ArrowLeft className="w-4 h-4" /> Voltar</Link>
        </Button>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold dark:text-gray-100">Pagar Assinatura</h1>
            <p className="text-sm text-muted-foreground dark:text-gray-400">{data.loja.nome} – {data.loja.plano} ({data.loja.tipo_assinatura})</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={STATUS_COLOR[st] || 'secondary'} className="text-xs sm:text-sm">
              {STATUS_ICON[st] || <Clock className="w-4 h-4" />} {fin.status_pagamento}
            </Badge>
            {fin.tem_asaas && (
              <Button variant="outline" size="sm" onClick={atualizarStatus} disabled={atualizandoStatus}>
                <RefreshCw className={`w-4 h-4 mr-2 ${atualizandoStatus ? 'animate-spin' : ''}`} /> Atualizar status
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Card className="dark:bg-neutral-800 dark:border-neutral-700">
          <CardHeader className="pb-2"><CardTitle className="text-base dark:text-gray-100">Valor da assinatura</CardTitle></CardHeader>
          <CardContent>
            <p className="text-2xl font-bold dark:text-gray-100">{formatCurrency(fin.valor_mensalidade)}</p>
            <p className="text-xs text-muted-foreground dark:text-gray-400">Vencimento todo dia {fin.dia_vencimento}</p>
          </CardContent>
        </Card>
        <Card className="dark:bg-neutral-800 dark:border-neutral-700">
          <CardHeader className="pb-2"><CardTitle className="text-base dark:text-gray-100">Próxima cobrança</CardTitle></CardHeader>
          <CardContent><p className="text-xl font-bold dark:text-gray-100">{formatDate(fin.data_proxima_cobranca)}</p></CardContent>
        </Card>
      </div>

      {/* Renovar */}
      <Card className="dark:bg-neutral-800 dark:border-neutral-700">
        <CardHeader>
          <CardTitle className="text-base dark:text-gray-100">Renovar Assinatura</CardTitle>
          <CardDescription className="dark:text-gray-400">Gere uma nova cobrança para renovar</CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={gerarNovaCobranca} disabled={gerandoCobranca} className="w-full sm:w-auto">
            {gerandoCobranca ? <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Gerando...</> : <><CreditCard className="w-4 h-4 mr-2" /> Gerar Nova Cobrança</>}
          </Button>
        </CardContent>
      </Card>

      {/* Pagamento */}
      {(fin.tem_asaas || fin.tem_mercadopago) && (fin.boleto_url || fin.pix_copy_paste) ? (
        <Card className="dark:bg-neutral-800 dark:border-neutral-700">
          <CardHeader>
            <CardTitle className="dark:text-gray-100">Formas de pagamento</CardTitle>
            <CardDescription className="dark:text-gray-400">Pague por boleto ou PIX</CardDescription>
          </CardHeader>
          <CardContent>
            <PaymentTabs boletoUrl={fin.boleto_url} pixQrCode={fin.pix_qr_code} pixCopyPaste={fin.pix_copy_paste} proximoPagamentoId={pp?.id} asaasPaymentId={pp?.asaas_payment_id} onBaixarBoleto={baixarBoleto} onCopiarPix={() => copiarPix(fin.pix_copy_paste)} />
          </CardContent>
        </Card>
      ) : (
        <Card className="dark:bg-neutral-800 dark:border-neutral-700">
          <CardContent className="py-8">
            <p className="text-center text-muted-foreground dark:text-gray-400">Nenhum boleto ou PIX disponível. Entre em contato com o suporte.</p>
          </CardContent>
        </Card>
      )}

      {/* Próximo pagamento */}
      {/* Histórico de pagamentos */}
      <Card className="dark:bg-neutral-800 dark:border-neutral-700">
        <CardHeader>
          <CardTitle className="text-base dark:text-gray-100">Histórico de pagamentos</CardTitle>
          <CardDescription className="dark:text-gray-400">
            Consulte cobranças anteriores, baixe boletos e acesse as notas fiscais emitidas
          </CardDescription>
        </CardHeader>
        <CardContent>
          <HistoricoPagamentos itens={data.historico_pagamentos ?? []} slug={slug} />
        </CardContent>
      </Card>

      {showModal && novaCobranca && (
        <NovaCobrancaModal data={novaCobranca} onClose={() => setShowModal(false)} onCopiarPix={() => copiarPix(novaCobranca.pix_copy_paste)} />
      )}
    </div>
  );
}
