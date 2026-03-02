/**
 * Página de Financeiro (Asaas + Mercado Pago)
 * ✅ REFATORADO v780: Reduzido de 673 para ~180 linhas
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';
import { useFinanceiroStats } from '@/hooks/useFinanceiroStats';
import { useAssinaturas } from '@/hooks/useAssinaturas';
import { usePagamentos } from '@/hooks/usePagamentos';
import { useAsaasActions } from '@/hooks/useAsaasActions';
import { useMercadoPagoActions } from '@/hooks/useMercadoPagoActions';
import {
  FinanceiroStats,
  AssinaturasTab,
  PagamentosTab,
  ModalNovaCobranca,
  ModalConfirmarExclusao
} from '@/components/superadmin/financeiro';
import type { Assinatura, Pagamento } from '@/hooks/useAssinaturas';

export default function FinanceiroPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'assinaturas' | 'pagamentos'>('assinaturas');
  
  // Hooks de dados
  const { stats, loading: loadingStats, reload: reloadStats } = useFinanceiroStats();
  const {
    assinaturasFiltradas,
    filtroProvedor,
    setFiltroProvedor,
    loading: loadingAssinaturas,
    reload: reloadAssinaturas
  } = useAssinaturas();
  const {
    pagamentosFiltrados,
    filtroStatus,
    setFiltroStatus,
    loading: loadingPagamentos,
    reload: reloadPagamentos
  } = usePagamentos();
  
  // Hooks de ações
  const asaasActions = useAsaasActions();
  const mercadoPagoActions = useMercadoPagoActions();
  
  // Modais
  const [showModalNovaCobranca, setShowModalNovaCobranca] = useState(false);
  const [assinaturaParaCobranca, setAssinaturaParaCobranca] = useState<Assinatura | null>(null);
  const [showModalExclusao, setShowModalExclusao] = useState(false);
  const [pagamentoParaExcluir, setPagamentoParaExcluir] = useState<Pagamento | null>(null);

  // Verificação de autenticação e carregamento inicial
  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    loadAll();
  }, [router]);

  const loadAll = () => {
    reloadStats();
    reloadAssinaturas();
    reloadPagamentos();
  };

  // Handlers de ações Asaas
  const handleUpdateStatusAsaas = (paymentId: number) => {
    asaasActions.updateStatus(paymentId, loadAll);
  };

  const handleNovaCobranca = (assinatura: Assinatura) => {
    setAssinaturaParaCobranca(assinatura);
    setShowModalNovaCobranca(true);
  };

  const handleConfirmarNovaCobranca = async (assinaturaId: number | string, dueDate?: string) => {
    if (typeof assinaturaId !== 'number') {
      alert('Nova cobrança manual disponível apenas para assinaturas Asaas.');
      return;
    }
    
    const success = await asaasActions.createManualPayment(assinaturaId, dueDate, loadAll);
    if (success) {
      setShowModalNovaCobranca(false);
      setAssinaturaParaCobranca(null);
    }
  };

  const handleExcluirPagamento = (pagamento: Pagamento) => {
    if (pagamento.is_paid) {
      alert('Não é possível excluir uma cobrança já paga');
      return;
    }
    setPagamentoParaExcluir(pagamento);
    setShowModalExclusao(true);
  };

  const handleConfirmarExclusao = async (paymentId: number) => {
    const success = await asaasActions.deletePayment(paymentId, loadAll);
    if (success) {
      setShowModalExclusao(false);
      setPagamentoParaExcluir(null);
    }
  };

  // Handlers de ações Mercado Pago
  const handleGerarPixMP = (payment: Pagamento) => {
    mercadoPagoActions.gerarPix(payment, loadAll);
  };

  const handleUpdateStatusMP = (lojaSlug: string) => {
    mercadoPagoActions.updateStatus(lojaSlug, loadAll);
  };

  // Handler unificado para download de boleto
  const handleDownloadBoleto = (payment: Pagamento) => {
    if (payment.provedor === 'mercadopago') {
      mercadoPagoActions.downloadBoleto(payment);
    } else {
      asaasActions.downloadBoleto(payment);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <nav className="bg-purple-900 dark:bg-purple-950 text-white shadow-lg">
        <div className="w-full max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <a
                href="/superadmin/dashboard"
                className="text-purple-200 hover:text-white transition-colors"
              >
                ← Voltar
              </a>
              <h1 className="text-2xl font-bold">Financeiro (Asaas + Mercado Pago)</h1>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="w-full max-w-full py-6 px-4 sm:px-6 lg:px-8">
        {/* Estatísticas */}
        <FinanceiroStats stats={stats} loading={loadingStats} />

        {/* Tabs */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow mb-6">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="-mb-px flex">
              {(['assinaturas', 'pagamentos'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab
                      ? 'border-purple-500 text-purple-600 dark:text-purple-400'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                >
                  {tab === 'assinaturas' ? 'Assinaturas' : 'Pagamentos'} (
                  {tab === 'assinaturas' ? assinaturasFiltradas.length : pagamentosFiltrados.length})
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'assinaturas' ? (
              <AssinaturasTab
                assinaturas={assinaturasFiltradas}
                loading={loadingAssinaturas}
                filtroProvedor={filtroProvedor}
                setFiltroProvedor={setFiltroProvedor}
                onDownloadBoletoAsaas={asaasActions.downloadBoleto}
                onCopyPixAsaas={asaasActions.copyPixCode}
                onUpdateStatusAsaas={handleUpdateStatusAsaas}
                onNovaCobranca={handleNovaCobranca}
                onExcluirAsaas={handleExcluirPagamento}
                gerandoCobranca={asaasActions.gerandoCobranca}
                onDownloadBoletoMP={mercadoPagoActions.downloadBoleto}
                onCopyPixMP={mercadoPagoActions.copyPixCode}
                onGerarPixMP={handleGerarPixMP}
                onUpdateStatusMP={handleUpdateStatusMP}
                gerandoPix={mercadoPagoActions.gerandoPix}
                atualizandoMP={mercadoPagoActions.atualizandoMP}
              />
            ) : (
              <PagamentosTab
                pagamentos={pagamentosFiltrados}
                loading={loadingPagamentos}
                filtroStatus={filtroStatus}
                setFiltroStatus={setFiltroStatus}
                onDownloadBoleto={handleDownloadBoleto}
                onCopyPix={(pixCode) => {
                  navigator.clipboard.writeText(pixCode);
                  alert('Código PIX copiado!');
                }}
                onUpdateStatusAsaas={handleUpdateStatusAsaas}
                onExcluirAsaas={handleExcluirPagamento}
              />
            )}
          </div>
        </div>
      </main>

      {/* Modal: Nova Cobrança */}
      {showModalNovaCobranca && assinaturaParaCobranca && (
        <ModalNovaCobranca
          assinatura={assinaturaParaCobranca}
          onClose={() => {
            setShowModalNovaCobranca(false);
            setAssinaturaParaCobranca(null);
          }}
          onConfirm={handleConfirmarNovaCobranca}
          loading={asaasActions.gerandoCobranca !== null}
        />
      )}

      {/* Modal: Confirmar Exclusão */}
      {showModalExclusao && pagamentoParaExcluir && (
        <ModalConfirmarExclusao
          pagamento={pagamentoParaExcluir}
          onClose={() => {
            setShowModalExclusao(false);
            setPagamentoParaExcluir(null);
          }}
          onConfirm={handleConfirmarExclusao}
          loading={asaasActions.excluindoPagamento}
        />
      )}
    </div>
  );
}
