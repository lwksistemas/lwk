'use client';

import { FileText } from 'lucide-react';
import { useCrmRelatoriosPage } from '@/hooks/crm-vendas/useCrmRelatoriosPage';
import { StatsCards } from './components/StatsCards';
import { RelatorioForm } from './components/RelatorioForm';
import { RelatoriosComissao } from './components/RelatoriosComissao';

export default function RelatoriosPage() {
  const {
    periodo,
    setPeriodo,
    dataInicio,
    setDataInicio,
    dataFim,
    setDataFim,
    tipoRelatorio,
    setTipoRelatorio,
    vendedorSelecionado,
    setVendedorSelecionado,
    empresaPrestadoraSelecionada,
    setEmpresaPrestadoraSelecionada,
    gerando,
    vendedores,
    empresasPrestadoras,
    dashboardData,
    loading,
    isVendedor,
    handleGerar,
  } = useCrmRelatoriosPage();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <FileText size={28} className="text-[#0176d3]" /> Relatórios de Vendas
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Gere relatórios detalhados de vendas, comissões e desempenho
        </p>
      </div>

      <StatsCards
        totalVendas={dashboardData?.receita || 0}
        vendedoresAtivos={dashboardData?.performance_vendedores?.length || 0}
        totalComissoes={dashboardData?.comissao_total_mes || 0}
        loading={loading}
      />

      <RelatorioForm
        tipoRelatorio={tipoRelatorio}
        periodo={periodo}
        dataInicio={dataInicio}
        dataFim={dataFim}
        vendedorSelecionado={vendedorSelecionado}
        vendedores={vendedores}
        empresasPrestadoras={empresasPrestadoras}
        empresaPrestadoraSelecionada={empresaPrestadoraSelecionada}
        isVendedor={isVendedor}
        gerando={gerando}
        loading={loading}
        onTipoChange={setTipoRelatorio}
        onPeriodoChange={setPeriodo}
        onDataInicioChange={setDataInicio}
        onDataFimChange={setDataFim}
        onVendedorChange={setVendedorSelecionado}
        onEmpresaPrestadoraChange={setEmpresaPrestadoraSelecionada}
        onGerar={handleGerar}
      />

      <RelatoriosComissao empresasPrestadoras={empresasPrestadoras} vendedores={vendedores} isVendedor={isVendedor} />

      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-blue-800 dark:text-blue-300 mb-2">Sobre os Relatórios</h3>
        <ul className="text-sm text-blue-700 dark:text-blue-400 space-y-1">
          <li>• <strong>Total de Vendas:</strong> Resumo geral de todas as vendas fechadas no período</li>
          <li>• <strong>Vendas por Vendedor:</strong> Detalhamento individual com valores de comissão</li>
          <li>• <strong>Exportar comissões (PDF):</strong> Relatório pontual para download ou e-mail</li>
          <li>• <strong>Relatório formal:</strong> Fluxo com aprovação da empresa, assinatura e pagamento</li>
          <li>• Os relatórios incluem apenas oportunidades com status &quot;Fechado ganho&quot;</li>
        </ul>
      </div>
    </div>
  );
}
