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
  due_date: string;
  payment_date: string | null;
  bank_slip_url: string;
  pix_copy_paste: string;
  is_paid: boolean;
  is_overdue: boolean;
  is_pending: boolean;
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
  onUpdateStatus,
  onNovaCobranca,
  gerandoCobranca,
  formatDate,
  formatCurrency,
  getStatusColor
}: {
  assinatura: LojaAssinatura;
  onDownloadBoleto: (payment: AsaasPayment) => void;
  onCopyPix: (pixCode: string) => void;
  onUpdateStatus: (paymentId: number) => void;
  onNovaCobranca: (assinaturaId: number) => void;
  gerandoCobranca: number | null;
  formatDate: (date: string) => string;
  formatCurrency: (value: string | number) => string;
  getStatusColor: (status: string) => string;
}) {
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
        <div className="p-3 bg-gray-50 rounded">
          <h4 className="font-medium text-gray-900 mb-2">Pagamento Atual</h4>
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
              <span className="text-gray-600">Status:</span>
              <span className="ml-2">{assinatura.current_payment_data.status_display}</span>
            </div>
          </div>
          
          {/* Ações */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => onDownloadBoleto(assinatura.current_payment_data!)}
              className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors"
            >
              📄 Baixar Boleto
            </button>
            
            {assinatura.current_payment_data.pix_copy_paste && (
              <button
                onClick={() => onCopyPix(assinatura.current_payment_data!.pix_copy_paste)}
                className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 transition-colors"
              >
                📱 Copiar PIX
              </button>
            )}
            
            <button
              onClick={() => onUpdateStatus(assinatura.current_payment_data!.id)}
              className="px-3 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700 transition-colors"
            >
              🔄 Atualizar Status
            </button>
            
            <button
              onClick={() => onNovaCobranca(assinatura.id)}
              disabled={gerandoCobranca === assinatura.id}
              className="px-3 py-1 bg-orange-600 text-white text-xs rounded hover:bg-orange-700 disabled:opacity-50 transition-colors"
            >
              {gerandoCobranca === assinatura.id ? 'Gerando...' : '➕ Nova Cobrança'}
            </button>
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
  const [showModalNovaCobranca, setShowModalNovaCobranca] = useState(false);

  // Verificação de autenticação
  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    loadData();
  }, [router]);

  // Carregar dados
  const loadData = async () => {
    try {
      setLoading(true);
      const [statsRes, assinaturasRes, pagamentosRes] = await Promise.all([
        apiClient.get('/asaas/subscriptions/dashboard_stats/'),
        apiClient.get('/asaas/subscriptions/'),
        apiClient.get('/asaas/payments/')
      ]);
      
      setStats(statsRes.data);
      setAssinaturas(assinaturasRes.data.results || assinaturasRes.data);
      setPagamentos(pagamentosRes.data.results || pagamentosRes.data);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  // Baixar boleto
  const downloadBoleto = (payment: AsaasPayment) => {
    if (payment.bank_slip_url) {
      window.open(payment.bank_slip_url, '_blank', 'noopener,noreferrer');
    } else {
      alert('Boleto não disponível');
    }
  };

  // Atualizar status do pagamento
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

  // Gerar nova cobrança
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
      alert(`Erro: ${error.response?.data?.error || error.message || 'Erro ao gerar nova cobrança'}`);
    } finally {
      setGerandoCobranca(null);
    }
  };

  // Copiar código PIX
  const copyPixCode = (pixCode: string) => {
    navigator.clipboard.writeText(pixCode);
    alert('Código PIX copiado!');
  };

  // Formatadores
  const formatCurrency = (value: string | number) => {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '-';
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

  // Filtrar pagamentos
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
              <a href="/superadmin/dashboard" className="text-purple-200 hover:text-white transition-colors">
                ← Voltar
              </a>
              <h1 className="text-2xl font-bold">Financeiro - Asaas</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => {
                  if (assinaturas.length === 0) {
                    alert('Não há assinaturas no momento.');
                    return;
                  }
                  assinaturas.length === 1 
                    ? generateNewPayment(assinaturas[0].id)
                    : setShowModalNovaCobranca(true);
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
                        onUpdateStatus={updatePaymentStatus}
                        onNovaCobranca={generateNewPayment}
                        gerandoCobranca={gerandoCobranca}
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
                          <tr key={pagamento.id} className="hover:bg-gray-50 transition-colors">
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
                              <button
                                onClick={() => updatePaymentStatus(pagamento.id)}
                                className="text-purple-600 hover:text-purple-800 transition-colors"
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
      </main>

      {/* Modal: Nova Cobrança */}
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
                    className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:bg-purple-50 hover:border-purple-300 disabled:opacity-50 transition-colors"
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
              className="w-full px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
