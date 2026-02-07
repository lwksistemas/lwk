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

  const abrirBoleto = () => {
    if (dadosFinanceiros?.financeiro?.boleto_url) {
      window.open(dadosFinanceiros.financeiro.boleto_url, '_blank');
    } else {
      alert('❌ Boleto não disponível');
    }
  };

  const copiarPix = () => {
    if (dadosFinanceiros?.financeiro?.pix_copy_paste) {
      navigator.clipboard.writeText(dadosFinanceiros.financeiro.pix_copy_paste);
      alert('✅ PIX copiado para a área de transferência!');
    } else {
      alert('❌ PIX não disponível');
    }
  };

  return (
    <CrudModal loja={loja} onClose={onClose} title="Configurações da Loja" icon="⚙️" fullScreen>
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
          {/* Informações da Loja */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg">
            <h4 className="text-lg font-semibold mb-3" style={{ color: loja.cor_primaria }}>
              🏪 Informações da Loja
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Nome da Loja</p>
                <p className="font-semibold">{dadosFinanceiros.loja.nome}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Plano Atual</p>
                <p className="font-semibold">{dadosFinanceiros.loja.plano}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Tipo de Assinatura</p>
                <p className="font-semibold">{dadosFinanceiros.loja.tipo_assinatura}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Status</p>
                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                  dadosFinanceiros.financeiro.status_pagamento === 'Ativo' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {dadosFinanceiros.financeiro.status_pagamento}
                </span>
              </div>
            </div>
          </div>

          {/* Informações Financeiras */}
          <div className="bg-gray-50 p-6 rounded-lg">
            <h4 className="text-lg font-semibold mb-3" style={{ color: loja.cor_primaria }}>
              💰 Informações Financeiras
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-sm text-gray-600">Valor Mensal</p>
                <p className="text-2xl font-bold" style={{ color: loja.cor_primaria }}>
                  R$ {dadosFinanceiros.financeiro.valor_mensalidade.toFixed(2)}
                </p>
              </div>
              {dadosFinanceiros.financeiro.ultimo_pagamento && (
                <div className="text-center">
                  <p className="text-sm text-gray-600">Último Pagamento</p>
                  <p className="text-lg font-semibold text-green-600">
                    {dadosFinanceiros.financeiro.ultimo_pagamento.split('-').reverse().join('/')}
                  </p>
                </div>
              )}
              <div className="text-center">
                <p className="text-sm text-gray-600">Próximo Vencimento</p>
                <p className="text-lg font-semibold">
                  {dadosFinanceiros.financeiro.data_proxima_cobranca.split('-').reverse().join('/')}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600">Dia do Vencimento</p>
                <p className="text-lg font-semibold">
                  Todo dia {dadosFinanceiros.financeiro.dia_vencimento}
                </p>
              </div>
            </div>
          </div>

          {/* Formas de Pagamento */}
          {dadosFinanceiros.financeiro.tem_asaas && (
            <div className="bg-green-50 p-6 rounded-lg">
              <h4 className="text-lg font-semibold mb-4" style={{ color: loja.cor_primaria }}>
                💳 Formas de Pagamento Disponíveis
              </h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {dadosFinanceiros.financeiro.boleto_url && (
                  <div className="border border-orange-200 bg-orange-50 p-4 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h5 className="font-semibold text-orange-800">🧾 Boleto Bancário</h5>
                        <p className="text-sm text-orange-600">Pague em qualquer banco ou lotérica</p>
                      </div>
                      <button onClick={abrirBoleto} className="px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 text-sm">
                        📄 Ver Boleto
                      </button>
                    </div>
                  </div>
                )}

                {dadosFinanceiros.financeiro.pix_copy_paste && (
                  <div className="border border-green-200 bg-green-50 p-4 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h5 className="font-semibold text-green-800">🔄 PIX</h5>
                        <p className="text-sm text-green-600">Pagamento instantâneo</p>
                      </div>
                      <button onClick={copiarPix} className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 text-sm">
                        📋 Copiar PIX
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {dadosFinanceiros.financeiro.pix_qr_code && (
                <div className="mt-4 text-center">
                  <p className="text-sm text-gray-600 mb-2">Ou escaneie o QR Code:</p>
                  <div className="inline-block p-4 bg-white rounded-lg border">
                    <img 
                      src={`data:image/png;base64,${dadosFinanceiros.financeiro.pix_qr_code}`}
                      alt="QR Code PIX"
                      className="w-32 h-32 mx-auto"
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Estatísticas */}
          <div className="bg-blue-50 p-6 rounded-lg">
            <h4 className="text-lg font-semibold mb-4" style={{ color: loja.cor_primaria }}>
              📊 Estatísticas de Pagamento
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">{dadosFinanceiros.estatisticas.total_pagamentos}</p>
                <p className="text-sm text-gray-600">Total de Cobranças</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{dadosFinanceiros.estatisticas.pagamentos_pagos}</p>
                <p className="text-sm text-gray-600">Pagamentos Realizados</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-yellow-600">{dadosFinanceiros.estatisticas.pagamentos_pendentes}</p>
                <p className="text-sm text-gray-600">Pendentes</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">{dadosFinanceiros.estatisticas.pagamentos_atrasados}</p>
                <p className="text-sm text-gray-600">Em Atraso</p>
              </div>
            </div>
          </div>

          {/* Histórico de Pagamentos */}
          {dadosFinanceiros.historico_pagamentos && dadosFinanceiros.historico_pagamentos.length > 0 && (
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
          )}

          {/* Próximo Pagamento */}
          {dadosFinanceiros.proximo_pagamento && (
            <div className="bg-yellow-50 border border-yellow-200 p-6 rounded-lg">
              <h4 className="text-lg font-semibold mb-3 text-yellow-800">
                ⏰ Próximo Pagamento
              </h4>
              <div className="flex justify-between items-center">
                <div>
                  <p className="font-semibold">
                    R$ {dadosFinanceiros.proximo_pagamento.valor}
                  </p>
                  <p className="text-sm text-gray-600">
                    Vencimento: {new Date(dadosFinanceiros.proximo_pagamento.data_vencimento).toLocaleDateString('pt-BR')}
                  </p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                  dadosFinanceiros.proximo_pagamento.status === 'pago' 
                    ? 'bg-green-100 text-green-800'
                    : dadosFinanceiros.proximo_pagamento.status === 'pendente'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {dadosFinanceiros.proximo_pagamento.status}
                </span>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg mb-2">Nenhum dado financeiro encontrado</p>
          <p className="text-sm">Entre em contato com o suporte</p>
        </div>
      )}

      <div className="flex justify-end space-x-4 mt-8 pt-4 border-t">
        <button onClick={onClose} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
          Fechar
        </button>
        {dadosFinanceiros?.financeiro?.boleto_url && (
          <button onClick={abrirBoleto} className="px-6 py-2 text-white rounded-md hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>
            📄 Acessar Boleto
          </button>
        )}
      </div>
    </CrudModal>
  );
}
