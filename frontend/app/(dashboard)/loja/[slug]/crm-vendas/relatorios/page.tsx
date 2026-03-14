'use client';

import { useState, useEffect } from 'react';
import { FileText, Download, Mail, Calendar, DollarSign, Users, TrendingUp } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { normalizeListResponse } from '@/lib/crm-utils';

interface Vendedor {
  id: number;
  nome: string;
  email: string;
}

interface DashboardData {
  receita: number;
  comissao_total_mes: number;
  performance_vendedores: Array<{
    id: number;
    nome: string;
    receita_mes: number;
    comissao_mes: number;
  }>;
}

export default function RelatoriosPage() {
  const [periodo, setPeriodo] = useState('mes_atual');
  const [tipoRelatorio, setTipoRelatorio] = useState('vendas_total');
  const [vendedorSelecionado, setVendedorSelecionado] = useState('todos');
  const [gerando, setGerando] = useState(false);
  
  // Estados para dados
  const [vendedores, setVendedores] = useState<Vendedor[]>([]);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  // Carregar dados ao montar o componente
  useEffect(() => {
    const carregarDados = async () => {
      try {
        setLoading(true);
        
        // Carregar vendedores
        const resVendedores = await apiClient.get<Vendedor[] | { results: Vendedor[] }>('/crm-vendas/vendedores/');
        setVendedores(normalizeListResponse(resVendedores.data));
        
        // Carregar dados do dashboard (contém receita e comissões)
        const resDashboard = await apiClient.get<DashboardData>('/crm-vendas/dashboard/');
        setDashboardData(resDashboard.data);
      } catch (error) {
        console.error('Erro ao carregar dados:', error);
      } finally {
        setLoading(false);
      }
    };
    
    carregarDados();
  }, []);

  const formatarMoeda = (valor: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(valor);
  };

  const handleGerarRelatorio = async (acao: 'pdf' | 'email') => {
    setGerando(true);
    
    try {
      const payload = {
        tipo: tipoRelatorio,
        periodo: periodo,
        vendedor_id: vendedorSelecionado !== 'todos' ? vendedorSelecionado : null,
        acao: acao,
      };

      if (acao === 'pdf') {
        // Download do PDF
        const response = await apiClient.post('/crm-vendas/relatorios/gerar/', payload, {
          responseType: 'blob',
        });
        
        // Criar URL do blob e fazer download
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `relatorio_${tipoRelatorio}_${periodo}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        
        alert('PDF gerado com sucesso!');
      } else {
        // Enviar por email
        const response = await apiClient.post('/crm-vendas/relatorios/gerar/', payload);
        alert(response.data.message || 'Relatório enviado por email com sucesso!');
      }
    } catch (error: any) {
      console.error('Erro ao gerar relatório:', error);
      let mensagem = 'Erro ao gerar relatório. Tente novamente.';
      const data = error.response?.data;
      if (data) {
        if (typeof data === 'string') {
          try {
            const parsed = JSON.parse(data);
            mensagem = parsed.detail || mensagem;
          } catch {
            mensagem = data || mensagem;
          }
        } else if (data instanceof Blob) {
          // responseType: 'blob' retorna erro como Blob - converter para texto
          try {
            const text = await data.text();
            const parsed = JSON.parse(text);
            mensagem = parsed.detail || mensagem;
          } catch {
            mensagem = 'Erro ao gerar relatório. Tente novamente.';
          }
        } else if (typeof data === 'object' && data.detail) {
          mensagem = data.detail;
        }
      }
      alert(mensagem);
    } finally {
      setGerando(false);
    }
  };

  const totalVendas = dashboardData?.receita || 0;
  const totalComissoes = dashboardData?.comissao_total_mes || 0;
  const vendedoresAtivos = dashboardData?.performance_vendedores?.length || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <FileText size={28} className="text-[#0176d3]" />
          Relatórios de Vendas
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Gere relatórios detalhados de vendas, comissões e desempenho
        </p>
      </div>

      {/* Cards de Estatísticas Rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">
              <DollarSign size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Total de Vendas (Mês)</p>
              {loading ? (
                <div className="h-6 w-24 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
              ) : (
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {formatarMoeda(totalVendas)}
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
              <Users size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Vendedores Ativos</p>
              {loading ? (
                <div className="h-6 w-12 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
              ) : (
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {vendedoresAtivos}
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400">
              <TrendingUp size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Comissões (Mês)</p>
              {loading ? (
                <div className="h-6 w-24 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
              ) : (
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {formatarMoeda(totalComissoes)}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Formulário de Geração de Relatório */}
      <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Gerar Relatório
        </h2>

        <div className="space-y-4">
          {/* Tipo de Relatório */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Tipo de Relatório
            </label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setTipoRelatorio('vendas_total')}
                className={`p-4 rounded-lg border-2 transition-all text-left ${
                  tipoRelatorio === 'vendas_total'
                    ? 'border-[#0176d3] bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <DollarSign size={18} className="text-[#0176d3]" />
                  <span className="font-medium text-gray-900 dark:text-white text-sm">
                    Total de Vendas
                  </span>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Todos os vendedores
                </p>
              </button>

              <button
                type="button"
                onClick={() => setTipoRelatorio('vendas_vendedor')}
                className={`p-4 rounded-lg border-2 transition-all text-left ${
                  tipoRelatorio === 'vendas_vendedor'
                    ? 'border-[#0176d3] bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Users size={18} className="text-[#0176d3]" />
                  <span className="font-medium text-gray-900 dark:text-white text-sm">
                    Vendas por Vendedor
                  </span>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Com comissões
                </p>
              </button>

              <button
                type="button"
                onClick={() => setTipoRelatorio('comissoes')}
                className={`p-4 rounded-lg border-2 transition-all text-left ${
                  tipoRelatorio === 'comissoes'
                    ? 'border-[#0176d3] bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp size={18} className="text-[#0176d3]" />
                  <span className="font-medium text-gray-900 dark:text-white text-sm">
                    Apenas Comissões
                  </span>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Detalhamento completo
                </p>
              </button>
            </div>
          </div>

          {/* Período */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              <Calendar size={16} className="inline mr-1" />
              Período
            </label>
            <select
              value={periodo}
              onChange={(e) => setPeriodo(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="hoje">Hoje</option>
              <option value="ontem">Ontem</option>
              <option value="semana_atual">Esta Semana</option>
              <option value="semana_passada">Semana Passada</option>
              <option value="mes_atual">Este Mês</option>
              <option value="mes_passado">Mês Passado</option>
              <option value="trimestre_atual">Este Trimestre</option>
              <option value="ano_atual">Este Ano</option>
              <option value="personalizado">Período Personalizado</option>
            </select>
          </div>

          {/* Vendedor (apenas se tipo for vendas_vendedor) */}
          {tipoRelatorio === 'vendas_vendedor' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Vendedor
              </label>
              <select
                value={vendedorSelecionado}
                onChange={(e) => setVendedorSelecionado(e.target.value)}
                className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                disabled={loading}
              >
                <option value="todos">Todos os Vendedores</option>
                {vendedores.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.nome}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Ações */}
          <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={() => handleGerarRelatorio('pdf')}
              disabled={gerando}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Download size={18} />
              {gerando ? 'Gerando...' : 'Exportar PDF'}
            </button>

            <button
              type="button"
              onClick={() => handleGerarRelatorio('email')}
              disabled={gerando}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Mail size={18} />
              {gerando ? 'Enviando...' : 'Enviar por Email'}
            </button>
          </div>
        </div>
      </div>

      {/* Informações Adicionais */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-blue-800 dark:text-blue-300 mb-2">
          📊 Sobre os Relatórios
        </h3>
        <ul className="text-sm text-blue-700 dark:text-blue-400 space-y-1">
          <li>• <strong>Total de Vendas:</strong> Resumo geral de todas as vendas fechadas no período</li>
          <li>• <strong>Vendas por Vendedor:</strong> Detalhamento individual com valores de comissão</li>
          <li>• <strong>Comissões:</strong> Relatório específico para cálculo de comissões</li>
          <li>• Os relatórios incluem apenas oportunidades com status "Fechado ganho"</li>
        </ul>
      </div>
    </div>
  );
}
