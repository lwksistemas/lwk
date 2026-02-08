'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';
import { CrudModal } from '../shared/CrudModal';
import type { LojaInfo } from '../shared/CrudModal';

interface DadosFinanceiros {
  loja: {
    nome: string;
    plano: string;
    tipo_assinatura: string;
  };
  financeiro: {
    status_pagamento: string;
    valor_mensalidade: number;
    data_proxima_cobranca: string;
    ultimo_pagamento?: string;
    dia_vencimento: number;
    tem_asaas: boolean;
    boleto_url?: string;
    pix_copy_paste?: string;
    pix_qr_code?: string;
  };
  estatisticas: {
    total_pagamentos: number;
    pagamentos_pagos: number;
    pagamentos_pendentes: number;
    pagamentos_atrasados: number;
  };
  historico_pagamentos?: Array<{
    id: number;
    asaas_id: string;
    valor: number;
    status: string;
    status_display: string;
    data_vencimento: string;
    data_pagamento?: string;
    boleto_url?: string;
    is_paid: boolean;
    is_pending: boolean;
    is_overdue: boolean;
  }>;
  proximo_pagamento?: {
    valor: string;
    data_vencimento: string;
    status: string;
  };
}

interface ConfiguracoesModalProps {
  loja: LojaInfo;
  onClose: () => void;
}

export function ConfiguracoesModal({ loja, onClose }: ConfiguracoesModalProps) {
  const [dadosFinanceiros, setDadosFinanceiros] = useState<DadosFinanceiros | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  const loadDadosFinanceiros = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiClient.get(`/superadmin/loja/${loja.slug}/financeiro/`);
      setDadosFinanceiros(response.data);
      setError('');
    } catch (err: unknown) {
      console.error('Erro ao carregar dados financeiros:', err);
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { status?: number } };
        if (axiosError.response?.status === 401) {
          setError('Acesso negado. Faça login novamente.');
        } else if (axiosError.response?.status === 404) {
          setError('Dados financeiros não encontrados para esta loja');
        } else {
          setError('Erro ao carregar dados financeiros');
        }
      } else {
        setError('Erro ao carregar dados financeiros');
      }
    } finally {
      setLoading(false);
    }
  }, [loja.slug]);

  useEffect(() => {
    loadDadosFinanceiros();
  }, [loadDadosFinanceiros]);

  return (
    <CrudModal loja={loja} onClose={onClose} title="Configurações da Loja" icon="⚙️">
      {loading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 mx-auto mb-4" style={{ borderColor: loja.cor_primaria }}></div>
          <p>Carregando informações financeiras...</p>
        </div>
      ) : error ? (
        <div className="text-center py-12 text-red-500">
          <p className="text-lg mb-2">❌ {error}</p>
          <button onClick={loadDadosFinanceiros} className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600">
            🔄 Tentar Novamente
          </button>
        </div>
      ) : dadosFinanceiros ? (
        <div className="space-y-6">
          {/* Histórico de Pagamentos */}
          {dadosFinanceiros.historico_pagamentos && dadosFinanceiros.historico_pagamentos.length > 0 ? (
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 px-6 py-4 border-b border-gray-200">
                <h4 className="text-lg font-semibold" style={{ color: loja.cor_primaria }}>
                  📋 Histórico de Pagamentos ({dadosFinanceiros.historico_pagamentos.length})
                </h4>
              </div>
              <div className="divide-y divide-gray-200">
                {dadosFinanceiros.historico_pagamentos.map((pagamento, index) => (
                  <div 
                    key={pagamento.id} 
                    className="px-6 py-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      {/* Informações do Pagamento */}
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <span className="text-sm font-medium text-gray-500">
                            #{(dadosFinanceiros.historico_pagamentos?.length || 0) - index}
                          </span>
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            pagamento.is_paid
                              ? 'bg-green-100 text-green-800'
                              : pagamento.is_overdue
                              ? 'bg-red-100 text-red-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {pagamento.is_paid ? '✓ Pago' : pagamento.is_overdue ? '⚠ Vencido' : '⏳ Pendente'}
                          </span>
                          <span className="text-lg font-bold" style={{ color: loja.cor_primaria }}>
                            R$ {pagamento.valor.toFixed(2)}
                          </span>
                        </div>
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <span>
                            <strong>Vencimento:</strong> {pagamento.data_vencimento.split('-').reverse().join('/')}
                          </span>
                          {pagamento.data_pagamento && (
                            <span className="text-green-600">
                              <strong>Pago em:</strong> {pagamento.data_pagamento.split('-').reverse().join('/')}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Ações */}
                      <div className="flex items-center space-x-2">
                        {pagamento.boleto_url && (
                          <button
                            onClick={() => window.open(pagamento.boleto_url, '_blank')}
                            className="px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 transition-colors text-sm font-medium"
                          >
                            📄 Ver Boleto
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <p className="text-lg mb-2">📋 Nenhum histórico de pagamento encontrado</p>
              <p className="text-sm">Os pagamentos aparecerão aqui quando forem gerados</p>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg mb-2">Nenhum dado financeiro encontrado</p>
          <p className="text-sm">Entre em contato com o suporte</p>
        </div>
      )}

      <div className="flex justify-end mt-8 pt-4 border-t">
        <button 
          onClick={onClose} 
          className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        >
          Fechar
        </button>
      </div>
    </CrudModal>
  );
}
