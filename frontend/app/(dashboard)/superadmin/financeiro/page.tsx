'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { ModalNovaCobranca } from '@/components/superadmin/financeiro/ModalNovaCobranca';
import { ModalConfirmarExclusao } from '@/components/superadmin/financeiro/ModalConfirmarExclusao';
import { formatCurrency, formatDate } from '@/lib/financeiro-helpers';

interface AsaasPayment {
  id: number | null;
  asaas_id: string;
  customer_name: string;
  customer_email: string;
  value: string;
  status: string;
  status_display: string;
  due_date: string;
  payment_date: string | null;
  bank_slip_url: string;
  pix_copy_paste: string;
  pix_qr_code?: string | null;
  is_paid: boolean;
  is_overdue: boolean;
  is_pending: boolean;
  provedor?: 'asaas' | 'mercadopago';
}

interface LojaAssinatura {
  id: number | string;
  loja_slug: string;
  loja_nome: string;
  plano_nome: string;
  plano_valor: string;
  ativa: boolean;
  data_vencimento: string;
  current_payment_data: AsaasPayment | null;
  total_payments: number;
  subscription_status?: string;
  subscription_status_display?: string;
}

interface AsaasStats {
  total_assinaturas: number;
  assinaturas_ativas: number;
  pagamentos_pendentes: number;
  pagamentos_pagos: number;
  pagamentos_vencidos: number;
  receita_total: number;
  receita_pendente: number;
}

// Componente: Card de Estatística
function StatCard({ title, value, icon }: { title: string; value: string | number; icon: string }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-purple-600">{value}</p>
        </div>
        <div className="text-3xl">{icon}</div>
      </div>
    </div>
  );
}

// Componente: Card de Assinatura
function AssinaturaCard({
  assinatura,
  onDownloadBoleto,
  onCopyPix,
  onGerarPix,
  onUpdateStatus,
  onUpdateStatusMercadoPago,
  onNovaCobranca,
  onExcluirPagamento,
  gerandoCobranca,
  gerandoPix,
  atualizandoMP,
  formatDate,
  formatCurrency,
  getStatusColor
}: {
  assinatura: LojaAssinatura;
  onDownloadBoleto: (payment: AsaasPayment) => void;
  onCopyPix: (pixCode: string) => void;
  onGerarPix?: (payment: AsaasPayment) => void;
  onUpdateStatus: (paymentId: number) => void;
  onUpdateStatusMercadoPago?: (lojaSlug: string) => void;
  onNovaCobranca: (assinatura: LojaAssinatura) => void;
  onExcluirPagamento: (payment: AsaasPayment) => void;
  gerandoCobranca: number | string | null;
  gerandoPix: number | null;
  atualizandoMP: string | null;
  formatDate: (date: string) => string;
  formatCurrency: (value: string | number) => string;
  getStatusColor: (status: string) => string;
}) {
  const isAsaas = typeof assinatura.id === 'number';
  const isMercadoPago = assinatura.current_payment_data?.provedor === 'mercadopago';
  const updatingThisMP = atualizandoMP === assinatura.loja_slug;
  return (
    <div className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{assinatura.loja_nome}</h3>
          <p className="text-sm text-gray-600">
            {assinatura.plano_nome} - {formatCurrency(assinatura.plano_valor)}
          </p>
          <p className="text-sm text-gray-500">Vencimento: {formatDate(assinatura.data_vencimento)}</p>
          <p className="text-sm text-gray-500">Total de pagamentos: {assinatura.total_payments}</p>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 text-xs rounded-full ${
            assinatura.ativa ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {assinatura.subscription_status_display || (assinatura.ativa ? 'Ativa' : 'Inativa')}
          </span>
        </div>
      </div>
      
      {/* Pagamento Atual */}
      {assinatura.current_payment_data && (
        <div className="p-3 bg-gray-50 rounded">
          <h4 className="font-medium text-gray-900 mb-2">Próximo Pagamento</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm mb-3">
            <div>
              <span className="text-gray-600">Valor:</span>
              <span className="ml-2 font-medium">
                {formatCurrency(assinatura.current_payment_data.value)}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Vencimento:</span>
              <span className="ml-2">{formatDate(assinatura.current_payment_data.due_date)}</span>
            </div>
            <div>
              <span className="text-gray-600">Status do Pagamento:</span>
              <span className={`ml-2 px-2 py-0.5 text-xs rounded-full ${
                getStatusColor(assinatura.current_payment_data.status)
              }`}>
                {assinatura.current_payment_data.status_display}
              </span>
            </div>
          </div>
          
          {/* Ações: Baixar Boleto / PIX para todos; Atualizar/Nova Cobrança/Excluir só Asaas */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => onDownloadBoleto(assinatura.current_payment_data!)}
              className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors"
            >
              📄 Baixar Boleto
            </button>
            
            {assinatura.current_payment_data.pix_copy_paste ? (
              <button
                onClick={() => onCopyPix(assinatura.current_payment_data!.pix_copy_paste)}
                className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 transition-colors"
              >
                📱 Copiar PIX
              </button>
            ) : assinatura.current_payment_data.provedor === 'mercadopago' && assinatura.current_payment_data.id != null && onGerarPix && (
              <button
                onClick={() => onGerarPix(assinatura.current_payment_data!)}
                disabled={gerandoPix === assinatura.current_payment_data!.id}
                className="px-3 py-1 bg-emerald-600 text-white text-xs rounded hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {gerandoPix === assinatura.current_payment_data!.id ? 'Gerando...' : '🔲 Gerar PIX'}
              </button>
            )}

            {isMercadoPago && onUpdateStatusMercadoPago && (
              <button
                onClick={() => onUpdateStatusMercadoPago(assinatura.loja_slug)}
                disabled={updatingThisMP || assinatura.current_payment_data?.is_paid}
                className="px-3 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Consultar status no Mercado Pago e atualizar (ex.: boleto pago via PIX)"
              >
                {updatingThisMP ? 'Atualizando...' : '🔄 Atualizar Status'}
              </button>
            )}
            
            {isAsaas && (
              <>
                <button
                  onClick={() => {
                    const id = assinatura.current_payment_data?.id;
                    if (id != null) onUpdateStatus(id);
                  }}
                  disabled={assinatura.current_payment_data?.id == null}
                  className="px-3 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  🔄 Atualizar Status
                </button>
                <button
                  onClick={() => onNovaCobranca(assinatura)}
                  disabled={gerandoCobranca === assinatura.id}
                  className="px-3 py-1 bg-orange-600 text-white text-xs rounded hover:bg-orange-700 disabled:opacity-50 transition-colors"
                >
                  {gerandoCobranca === assinatura.id ? 'Gerando...' : '➕ Nova Cobrança'}
                </button>
                <button
                  onClick={() => onExcluirPagamento(assinatura.current_payment_data!)}
                  disabled={assinatura.current_payment_data!.is_paid}
                  className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  title={assinatura.current_payment_data!.is_paid ? 'Não é possível excluir cobrança paga' : 'Excluir cobrança'}
                >
                  🗑️ Excluir
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Componente Principal
export default function FinanceiroPage() {
  const router = useRouter();
  const [assinaturas, setAssinaturas] = useState<LojaAssinatura[]>([]);
  const [pagamentos, setPagamentos] = useState<AsaasPayment[]>([]);
  const [stats, setStats] = useState<AsaasStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filtroStatus, setFiltroStatus] = useState<string>('todos');
  const [activeTab, setActiveTab] = useState<'assinaturas' | 'pagamentos'>('assinaturas');
  const [gerandoCobranca, setGerandoCobranca] = useState<number | null>(null);
  const [gerandoPix, setGerandoPix] = useState<number | null>(null);
  const [atualizandoMP, setAtualizandoMP] = useState<string | null>(null);
  const [showModalNovaCobranca, setShowModalNovaCobranca] = useState(false);
  const [assinaturaParaCobranca, setAssinaturaParaCobranca] = useState<LojaAssinatura | null>(null);
  const [showModalExclusao, setShowModalExclusao] = useState(false);
  const [pagamentoParaExcluir, setPagamentoParaExcluir] = useState<AsaasPayment | null>(null);
  const [excluindoPagamento, setExcluindoPagamento] = useState(false);

  // Verificação de autenticação
  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    loadData();
  }, [router]);

  // Carregar dados (unificado: Asaas + Mercado Pago)
  const loadData = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get('/superadmin/financeiro-unificado/');
      const data = res.data;
      setStats({
        total_assinaturas: data.total_assinaturas ?? 0,
        assinaturas_ativas: data.assinaturas_ativas ?? 0,
        pagamentos_pendentes: data.pagamentos_pendentes ?? 0,
        pagamentos_pagos: data.pagamentos_pagos ?? 0,
        pagamentos_vencidos: data.pagamentos_vencidos ?? 0,
        receita_total: data.receita_total ?? 0,
        receita_pendente: data.receita_pendente ?? 0,
      });
      setAssinaturas(Array.isArray(data.assinaturas) ? data.assinaturas : []);
      setPagamentos(Array.isArray(data.pagamentos) ? data.pagamentos : []);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  // Baixar boleto (Mercado Pago: buscar URL na API; Asaas: abrir link direto)
  const downloadBoleto = async (payment: AsaasPayment) => {
    if (payment.provedor === 'mercadopago') {
      if (payment.id == null || payment.id === undefined) {
        alert('Link do boleto não disponível para este pagamento.');
        return;
      }
      try {
        const res = await apiClient.get(`/superadmin/loja-pagamentos/${payment.id}/baixar_boleto_pdf/`);
        const data = res.data as { boleto_url?: string; provedor?: string };
        if (data?.boleto_url) {
          window.open(data.boleto_url, '_blank', 'noopener,noreferrer');
        } else {
          alert('Link do boleto não disponível. Verifique se o pagamento existe na conta (produção/sandbox).');
        }
      } catch (e: unknown) {
        const msg = (e as { response?: { data?: { error?: string } } })?.response?.data?.error;
        alert(msg || 'Não foi possível obter o link do boleto.');
      }
      return;
    }
    if (payment.bank_slip_url) {
      window.open(payment.bank_slip_url, '_blank', 'noopener,noreferrer');
    } else {
      alert('Boleto não disponível');
    }
  };

  // Gerar PIX para pagamento Mercado Pago que ainda não tem PIX
  const handleGerarPix = async (payment: AsaasPayment) => {
    if (payment.id == null) return;
    try {
      setGerandoPix(payment.id);
      const res = await apiClient.post(`/superadmin/loja-pagamentos/${payment.id}/gerar_pix/`);
      const data = res.data as { pix_copy_paste?: string; pix_qr_code?: string };
      if (data?.pix_copy_paste) {
        navigator.clipboard.writeText(data.pix_copy_paste);
        await loadData();
        alert('PIX gerado! O código foi copiado para a área de transferência.');
      }
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: string } } })?.response?.data?.error;
      alert(msg || 'Não foi possível gerar o PIX.');
    } finally {
      setGerandoPix(null);
    }
  };

  // Atualizar status do pagamento (Asaas)
  const updatePaymentStatus = async (paymentId: number) => {
    try {
      await apiClient.post(`/asaas/payments/${paymentId}/update_status/`);
      await loadData();
      alert('Status atualizado com sucesso!');
    } catch (error) {
      console.error('Erro ao atualizar status:', error);
      alert('Erro ao atualizar status');
    }
  };

  // Atualizar status Mercado Pago (sync com API MP e atualiza financeiro/assinatura)
  const updatePaymentStatusMercadoPago = async (lojaSlug: string) => {
    setAtualizandoMP(lojaSlug);
    try {
      const res = await apiClient.post('/superadmin/sync-mercadopago/', { loja_slug: lojaSlug });
      await loadData();
      const processed = res.data?.processed ?? 0;
      if (processed > 0) {
        alert(`Status atualizado: ${processed} pagamento(s) sincronizado(s) com o Mercado Pago.`);
      } else {
        alert(res.data?.message || 'Nenhuma alteração. O pagamento pode ainda estar pendente no Mercado Pago.');
      }
    } catch (error: unknown) {
      console.error('Erro ao sincronizar Mercado Pago:', error);
      const msg = (error as { response?: { data?: { error?: string } } })?.response?.data?.error;
      alert(msg || 'Erro ao atualizar status. Tente novamente.');
    } finally {
      setAtualizandoMP(null);
    }
  };

  // Criar cobrança manual (apenas Asaas)
  const createManualPayment = async (assinaturaId: number | string, dueDate?: string) => {
    if (typeof assinaturaId !== 'number') {
      alert('Nova cobrança manual disponível apenas para assinaturas Asaas.');
      return;
    }
    setGerandoCobranca(assinaturaId);
    try {
      const endpoint = dueDate 
        ? `/asaas/subscriptions/${assinaturaId}/create_manual_payment/`
        : `/asaas/subscriptions/${assinaturaId}/generate_new_payment/`;
      
      const payload = dueDate ? { due_date: dueDate } : {};
      
      const response = await apiClient.post(endpoint, payload);
      if (response.data.success) {
        await loadData();
        setShowModalNovaCobranca(false);
        setAssinaturaParaCobranca(null);
        alert('Cobrança criada com sucesso!');
      } else {
        alert(response.data.error || 'Erro ao criar cobrança');
      }
    } catch (error: any) {
      console.error('Erro ao criar cobrança:', error);
      alert(`Erro: ${error.response?.data?.error || error.message || 'Erro ao criar cobrança'}`);
    } finally {
      setGerandoCobranca(null);
    }
  };

  // Excluir cobrança
  const deletePayment = async (paymentId: number) => {
    setExcluindoPagamento(true);
    try {
      const response = await apiClient.delete(`/asaas/payments/${paymentId}/delete_payment/`);
      if (response.data.success) {
        await loadData();
        setShowModalExclusao(false);
        setPagamentoParaExcluir(null);
        alert('Cobrança excluída com sucesso!');
      } else {
        alert(response.data.error || 'Erro ao excluir cobrança');
      }
    } catch (error: any) {
      console.error('Erro ao excluir cobrança:', error);
      alert(`Erro: ${error.response?.data?.error || error.message || 'Erro ao excluir cobrança'}`);
    } finally {
      setExcluindoPagamento(false);
    }
  };

  // Abrir modal de nova cobrança
  const handleNovaCobranca = (assinatura: LojaAssinatura) => {
    setAssinaturaParaCobranca(assinatura);
    setShowModalNovaCobranca(true);
  };

  // Abrir modal de exclusão
  const handleExcluirPagamento = (pagamento: AsaasPayment) => {
    if (pagamento.is_paid) {
      alert('Não é possível excluir uma cobrança já paga');
      return;
    }
    setPagamentoParaExcluir(pagamento);
    setShowModalExclusao(true);
  };

  // Copiar código PIX
  const copyPixCode = (pixCode: string) => {
    navigator.clipboard.writeText(pixCode);
    alert('Código PIX copiado!');
  };

  // Formatadores

  const getStatusColor = (status: string) => {
    const colors: { [key: string]: string } = {
      'PENDING': 'bg-yellow-100 text-yellow-800',
      'RECEIVED': 'bg-green-100 text-green-800',
      'CONFIRMED': 'bg-green-100 text-green-800',
      'OVERDUE': 'bg-red-100 text-red-800',
      'REFUNDED': 'bg-gray-100 text-gray-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  // Filtrar pagamentos
  const pagamentosFiltrados = filtroStatus === 'todos' 
    ? pagamentos 
    : pagamentos.filter(p => p.status === filtroStatus);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <nav className="bg-purple-900 dark:bg-purple-950 text-white shadow-lg">
        <div className="w-full max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <a href="/superadmin/dashboard" className="text-purple-200 hover:text-white transition-colors">
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
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <StatCard title="Receita Total" value={formatCurrency(stats.receita_total)} icon="💰" />
            <StatCard title="Assinaturas Ativas" value={stats.assinaturas_ativas} icon="✅" />
            <StatCard title="Pagamentos Pendentes" value={stats.pagamentos_pendentes} icon="⏳" />
            <StatCard title="Receita Pendente" value={formatCurrency(stats.receita_pendente)} icon="💸" />
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex">
              {(['assinaturas', 'pagamentos'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab
                      ? 'border-purple-500 text-purple-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab === 'assinaturas' ? 'Assinaturas' : 'Pagamentos'} (
                  {tab === 'assinaturas' ? assinaturas.length : pagamentos.length})
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {loading ? (
              <div className="text-center py-12">Carregando...</div>
            ) : activeTab === 'assinaturas' ? (
              /* Assinaturas Tab */
              <div>
                {assinaturas.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">Nenhuma assinatura encontrada.</p>
                ) : (
                  <div className="space-y-4">
                    {assinaturas.map((assinatura) => (
                      <AssinaturaCard
                        key={assinatura.id}
                        assinatura={assinatura}
                        onDownloadBoleto={downloadBoleto}
                        onCopyPix={copyPixCode}
                        onGerarPix={handleGerarPix}
                        onUpdateStatus={updatePaymentStatus}
                        onUpdateStatusMercadoPago={updatePaymentStatusMercadoPago}
                        onNovaCobranca={handleNovaCobranca}
                        onExcluirPagamento={handleExcluirPagamento}
                        gerandoCobranca={gerandoCobranca}
                        gerandoPix={gerandoPix}
                        atualizandoMP={atualizandoMP}
                        formatDate={formatDate}
                        formatCurrency={formatCurrency}
                        getStatusColor={getStatusColor}
                      />
                    ))}
                  </div>
                )}
              </div>
            ) : (
              /* Pagamentos Tab */
              <div>
                {/* Filtros */}
                <div className="mb-4 flex items-center space-x-4">
                  <span className="text-sm font-medium text-gray-700">Filtrar por status:</span>
                  <div className="flex space-x-2">
                    {['todos', 'PENDING', 'RECEIVED', 'CONFIRMED', 'OVERDUE'].map((status) => (
                      <button
                        key={status}
                        onClick={() => setFiltroStatus(status)}
                        className={`px-3 py-1 rounded text-sm transition-colors ${
                          filtroStatus === status
                            ? 'bg-purple-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {status === 'todos' ? 'Todos' : status}
                      </button>
                    ))}
                  </div>
                </div>

                {pagamentosFiltrados.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">Nenhum pagamento encontrado.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          {['Cliente', 'Valor', 'Status', 'Vencimento', 'Ações'].map((header) => (
                            <th key={header} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {pagamentosFiltrados.map((pagamento) => (
                          <tr key={pagamento.id ?? `pay-${pagamento.asaas_id}`} className="hover:bg-gray-50 transition-colors">
                            <td className="px-6 py-4">
                              <div className="font-medium text-gray-900">{pagamento.customer_name}</div>
                              <div className="text-sm text-gray-500">{pagamento.customer_email}</div>
                            </td>
                            <td className="px-6 py-4 text-sm font-medium text-gray-900">
                              {formatCurrency(pagamento.value)}
                            </td>
                            <td className="px-6 py-4">
                              <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(pagamento.status)}`}>
                                {pagamento.status_display}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-500">
                              {formatDate(pagamento.due_date)}
                            </td>
                            <td className="px-6 py-4 text-sm space-x-2">
                              <button
                                onClick={() => downloadBoleto(pagamento)}
                                className="text-blue-600 hover:text-blue-800 transition-colors"
                              >
                                📄 PDF
                              </button>
                              {pagamento.pix_copy_paste && (
                                <button
                                  onClick={() => copyPixCode(pagamento.pix_copy_paste)}
                                  className="text-green-600 hover:text-green-800 transition-colors"
                                >
                                  📱 PIX
                                </button>
                              )}
                              {pagamento.provedor === 'asaas' && (
                                <>
                                  <button
                                    onClick={() => pagamento.id != null && updatePaymentStatus(pagamento.id)}
                                    disabled={pagamento.id == null}
                                    className="text-purple-600 hover:text-purple-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                  >
                                    🔄 Status
                                  </button>
                                  <button
                                    onClick={() => handleExcluirPagamento(pagamento)}
                                    disabled={pagamento.is_paid}
                                    className="text-red-600 hover:text-red-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                    title={pagamento.is_paid ? 'Não é possível excluir cobrança paga' : 'Excluir cobrança'}
                                  >
                                    🗑️ Excluir
                                  </button>
                                </>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
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
          onConfirm={createManualPayment}
          loading={gerandoCobranca !== null}
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
          onConfirm={deletePayment}
          loading={excluindoPagamento}
        />
      )}
    </div>
  );
}
