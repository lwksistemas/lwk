'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

interface AsaasPayment {
  id: number;
  asaas_id: string;
  customer_name: string;
  customer_email: string;
  value: string;
  status: string;
  status_display: string;
  billing_type: string;
  billing_type_display: string;
  due_date: string;
  payment_date: string | null;
  invoice_url: string;
  bank_slip_url: string;
  pix_qr_code: string;
  pix_copy_paste: string;
  description: string;
  is_paid: boolean;
  is_overdue: boolean;
  is_pending: boolean;
  created_at: string;
}

interface LojaAssinatura {
  id: number;
  loja_slug: string;
  loja_nome: string;
  plano_nome: string;
  plano_valor: string;
  ativa: boolean;
  data_vencimento: string;
  current_payment_data: AsaasPayment | null;
  total_payments: number;
  created_at: string;
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

export default function FinanceiroPage() {
  const router = useRouter();
  const [assinaturas, setAssinaturas] = useState<LojaAssinatura[]>([]);
  const [pagamentos, setPagamentos] = useState<AsaasPayment[]>([]);
  const [stats, setStats] = useState<AsaasStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'assinaturas' | 'pagamentos'>('assinaturas');
  const [filtroStatus, setFiltroStatus] = useState<string>('todos');

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    loadData();
  }, [router]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Carregar estatísticas
      const statsResponse = await apiClient.get('/asaas/subscriptions/dashboard_stats/');
      setStats(statsResponse.data);
      
      // Carregar assinaturas
      const assinaturasResponse = await apiClient.get('/asaas/subscriptions/');
      setAssinaturas(assinaturasResponse.data.results || assinaturasResponse.data);
      
      // Carregar pagamentos
      const pagamentosResponse = await apiClient.get('/asaas/payments/');
      setPagamentos(pagamentosResponse.data.results || pagamentosResponse.data);
      
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  const downloadBoleto = async (payment: AsaasPayment) => {
    // Preferir abrir URL do boleto diretamente (evita erro de blob/CORS)
    if (payment.bank_slip_url) {
      window.open(payment.bank_slip_url, '_blank', 'noopener,noreferrer');
      return;
    }
    try {
      const response = await apiClient.get(`/asaas/payments/${payment.id}/download_pdf/`, {
        responseType: 'blob'
      });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `boleto_${payment.id}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error: any) {
      console.error('Erro ao baixar boleto:', error);
      const msg = error.response?.data instanceof Blob
        ? 'Erro ao baixar boleto. Tente abrir o link do boleto em nova aba.'
        : (error.response?.data?.error || 'Erro ao baixar boleto');
      alert(msg);
    }
  };

  const updatePaymentStatus = async (paymentId: number) => {
    try {
      await apiClient.post(`/asaas/payments/${paymentId}/update_status/`);
      loadData(); // Recarregar dados
      alert('Status atualizado com sucesso!');
    } catch (error) {
      console.error('Erro ao atualizar status:', error);
      alert('Erro ao atualizar status');
    }
  };

  const [gerandoCobranca, setGerandoCobranca] = useState<number | null>(null);
  const [showModalNovaCobranca, setShowModalNovaCobranca] = useState(false);

  const generateNewPayment = async (assinaturaId: number) => {
    setGerandoCobranca(assinaturaId);
    try {
      const response = await apiClient.post(`/asaas/subscriptions/${assinaturaId}/generate_new_payment/`);
      if (response.data.success) {
        await loadData();
        alert('Nova cobrança gerada com sucesso!');
      } else {
        alert(response.data.error || 'Erro ao gerar cobrança');
      }
    } catch (error: any) {
      console.error('Erro ao gerar nova cobrança:', error);
      const msg = error.response?.data?.error || error.message || 'Erro ao gerar nova cobrança';
      alert(`Erro: ${msg}`);
    } finally {
      setGerandoCobranca(null);
    }
  };

  const copyPixCode = (pixCode: string) => {
    navigator.clipboard.writeText(pixCode);
    alert('Código PIX copiado!');
  };

  const formatCurrency = (value: string | number) => {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return num.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    });
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '-';
    // Parse manual para evitar problema de timezone
    const [year, month, day] = dateString.split('T')[0].split('-');
    return `${day}/${month}/${year}`;
  };

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

  const pagamentosFiltrados = filtroStatus === 'todos' 
    ? pagamentos 
    : pagamentos.filter(p => p.status === filtroStatus);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-purple-900 text-white shadow-lg">
        <div className="w-full max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <a href="/superadmin/dashboard" className="text-purple-200 hover:text-white">
                ← Voltar
              </a>
              <h1 className="text-2xl font-bold">Financeiro - Asaas</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => {
                  if (assinaturas.length === 0) {
                    alert('Não há assinaturas no momento. Crie uma loja em "Gerenciar Lojas" e ative a cobrança para ver assinaturas aqui.');
                    return;
                  }
                  if (assinaturas.length === 1) {
                    generateNewPayment(assinaturas[0].id);
                  } else {
                    setShowModalNovaCobranca(true);
                  }
                }}
                disabled={gerandoCobranca !== null}
                className="px-4 py-2 bg-orange-600 hover:bg-orange-700 rounded-md transition-colors disabled:opacity-50"
              >
                {gerandoCobranca !== null ? 'Gerando...' : '➕ Nova Cobrança'}
              </button>
              <button
                onClick={loadData}
                className="px-4 py-2 bg-purple-700 hover:bg-purple-800 rounded-md transition-colors"
              >
                🔄 Atualizar
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="w-full max-w-full py-6 px-4 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Estatísticas */}
          {stats && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Receita Total</p>
                    <p className="text-2xl font-bold text-green-600">
                      {formatCurrency(stats.receita_total)}
                    </p>
                  </div>
                  <div className="text-3xl">💰</div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Assinaturas Ativas</p>
                    <p className="text-2xl font-bold text-purple-600">
                      {stats.assinaturas_ativas}
                    </p>
                  </div>
                  <div className="text-3xl">✅</div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Pagamentos Pendentes</p>
                    <p className="text-2xl font-bold text-yellow-600">
                      {stats.pagamentos_pendentes}
                    </p>
                  </div>
                  <div className="text-3xl">⏳</div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Receita Pendente</p>
                    <p className="text-2xl font-bold text-orange-600">
                      {formatCurrency(stats.receita_pendente)}
                    </p>
                  </div>
                  <div className="text-3xl">💸</div>
                </div>
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="bg-white rounded-lg shadow mb-6">
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex">
                <button
                  onClick={() => setActiveTab('assinaturas')}
                  className={`py-4 px-6 text-sm font-medium border-b-2 ${
                    activeTab === 'assinaturas'
                      ? 'border-purple-500 text-purple-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Assinaturas ({assinaturas.length})
                </button>
                <button
                  onClick={() => setActiveTab('pagamentos')}
                  className={`py-4 px-6 text-sm font-medium border-b-2 ${
                    activeTab === 'pagamentos'
                      ? 'border-purple-500 text-purple-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Pagamentos ({pagamentos.length})
                </button>
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
                        <div key={assinatura.id} className="border rounded-lg p-4 hover:bg-gray-50">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <h3 className="text-lg font-semibold text-gray-900">
                                {assinatura.loja_nome}
                              </h3>
                              <p className="text-sm text-gray-600">
                                {assinatura.plano_nome} - {formatCurrency(assinatura.plano_valor)}
                              </p>
                              <p className="text-sm text-gray-500">
                                Vencimento: {formatDate(assinatura.data_vencimento)}
                              </p>
                              <p className="text-sm text-gray-500">
                                Total de pagamentos: {assinatura.total_payments}
                              </p>
                            </div>
                            
                            <div className="flex items-center space-x-2">
                              <span className={`px-2 py-1 text-xs rounded-full ${
                                assinatura.ativa ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                {assinatura.ativa ? 'Ativa' : 'Inativa'}
                              </span>
                              
                              {assinatura.current_payment_data && (
                                <span className={`px-2 py-1 text-xs rounded-full ${
                                  getStatusColor(assinatura.current_payment_data.status)
                                }`}>
                                  {assinatura.current_payment_data.status_display}
                                </span>
                              )}
                            </div>
                          </div>
                          
                          {/* Pagamento Atual */}
                          {assinatura.current_payment_data && (
                            <div className="mt-4 p-3 bg-gray-50 rounded">
                              <h4 className="font-medium text-gray-900 mb-2">Pagamento Atual</h4>
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                                <div>
                                  <span className="text-gray-600">Valor:</span>
                                  <span className="ml-2 font-medium">
                                    {formatCurrency(assinatura.current_payment_data.value)}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-gray-600">Vencimento:</span>
                                  <span className="ml-2">
                                    {formatDate(assinatura.current_payment_data.due_date)}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-gray-600">Status:</span>
                                  <span className="ml-2">
                                    {assinatura.current_payment_data.status_display}
                                  </span>
                                </div>
                              </div>
                              
                              {/* Ações do Pagamento */}
                              <div className="mt-3 flex flex-wrap gap-2">
                                {(assinatura.current_payment_data.bank_slip_url || true) && (
                                  <button
                                    onClick={() => downloadBoleto(assinatura.current_payment_data!)}
                                    className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                                  >
                                    📄 Baixar Boleto
                                  </button>
                                )}
                                
                                {assinatura.current_payment_data.pix_copy_paste && (
                                  <button
                                    onClick={() => copyPixCode(assinatura.current_payment_data!.pix_copy_paste)}
                                    className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                                  >
                                    📱 Copiar PIX
                                  </button>
                                )}
                                
                                <button
                                  onClick={() => updatePaymentStatus(assinatura.current_payment_data!.id)}
                                  className="px-3 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700"
                                >
                                  🔄 Atualizar Status
                                </button>
                                
                                <button
                                  onClick={() => generateNewPayment(assinatura.id)}
                                  disabled={gerandoCobranca === assinatura.id}
                                  className="px-3 py-1 bg-orange-600 text-white text-xs rounded hover:bg-orange-700 disabled:opacity-50"
                                >
                                  {gerandoCobranca === assinatura.id ? 'Gerando...' : '➕ Nova Cobrança'}
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
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
                          className={`px-3 py-1 rounded text-sm ${
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
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Cliente
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Valor
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Status
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Vencimento
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Ações
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {pagamentosFiltrados.map((pagamento) => (
                            <tr key={pagamento.id} className="hover:bg-gray-50">
                              <td className="px-6 py-4">
                                <div>
                                  <div className="font-medium text-gray-900">{pagamento.customer_name}</div>
                                  <div className="text-sm text-gray-500">{pagamento.customer_email}</div>
                                </div>
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
                                {(pagamento.bank_slip_url || true) && (
                                  <button
                                    onClick={() => downloadBoleto(pagamento)}
                                    className="text-blue-600 hover:text-blue-800"
                                  >
                                    📄 PDF
                                  </button>
                                )}
                                {pagamento.pix_copy_paste && (
                                  <button
                                    onClick={() => copyPixCode(pagamento.pix_copy_paste)}
                                    className="text-green-600 hover:text-green-800"
                                  >
                                    📱 PIX
                                  </button>
                                )}
                                <button
                                  onClick={() => updatePaymentStatus(pagamento.id)}
                                  className="text-purple-600 hover:text-purple-800"
                                >
                                  🔄 Status
                                </button>
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
        </div>
      </main>

      {/* Modal: escolher assinatura para nova cobrança */}
      {showModalNovaCobranca && assinaturas.length > 1 && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Nova Cobrança - Escolha a loja</h3>
            <ul className="space-y-2 mb-4">
              {assinaturas.map((a) => (
                <li key={a.id}>
                  <button
                    type="button"
                    onClick={() => {
                      setShowModalNovaCobranca(false);
                      generateNewPayment(a.id);
                    }}
                    disabled={gerandoCobranca !== null}
                    className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:bg-purple-50 hover:border-purple-300 disabled:opacity-50"
                  >
                    <span className="font-medium text-gray-900">{a.loja_nome}</span>
                    <span className="text-gray-500 text-sm block">{a.loja_slug} · {a.plano_nome}</span>
                  </button>
                </li>
              ))}
            </ul>
            <button
              type="button"
              onClick={() => setShowModalNovaCobranca(false)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
