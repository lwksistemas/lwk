'use client';

import { useState, useEffect } from 'react';
import { FileText } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { normalizeListResponse } from '@/lib/crm-utils';
import { StatsCards } from './components/StatsCards';
import { RelatorioForm } from './components/RelatorioForm';

interface Vendedor { id: number; nome: string; email: string; }
interface EmpresaPrestadora { id: number; nome: string; cnpj?: string; }
interface DashboardData {
  receita: number;
  comissao_total_mes: number;
  performance_vendedores: Array<{ id: number; nome: string; receita_mes: number; comissao_mes: number }>;
}

export default function RelatoriosPage() {
  const [periodo, setPeriodo] = useState('mes_atual');
  const [tipoRelatorio, setTipoRelatorio] = useState('vendas_total');
  const [vendedorSelecionado, setVendedorSelecionado] = useState('todos');
  const [empresaPrestadoraSelecionada, setEmpresaPrestadoraSelecionada] = useState('todas');
  const [gerando, setGerando] = useState(false);
  const [vendedores, setVendedores] = useState<Vendedor[]>([]);
  const [empresasPrestadoras, setEmpresasPrestadoras] = useState<EmpresaPrestadora[]>([]);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [isVendedor, setIsVendedor] = useState(false);
  const [meuVendedorId, setMeuVendedorId] = useState<number | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const resMe = await apiClient.get<{ vendedor_id: number | null; is_vendedor: boolean }>('/crm-vendas/me/');
        const isVend = !!resMe.data?.is_vendedor;
        setIsVendedor(isVend);
        setMeuVendedorId(resMe.data?.vendedor_id ?? null);
        try {
          const resV = await apiClient.get<Vendedor[] | { results: Vendedor[] }>('/crm-vendas/vendedores/');
          setVendedores(normalizeListResponse(resV.data));
        } catch { setVendedores([]); }
        try {
          const resEP = await apiClient.get<EmpresaPrestadora[] | { results: EmpresaPrestadora[] }>('/crm-vendas/contas/?tipo=prestadora');
          setEmpresasPrestadoras(normalizeListResponse(resEP.data));
        } catch { setEmpresasPrestadoras([]); }
        const resD = await apiClient.get<DashboardData>('/crm-vendas/dashboard/');
        setDashboardData(resD.data);
      } catch (err) { console.error('Erro ao carregar dados:', err); }
      finally { setLoading(false); }
    })();
  }, []);

  useEffect(() => {
    if (isVendedor && tipoRelatorio === 'vendas_total') setTipoRelatorio('vendas_vendedor');
  }, [isVendedor, tipoRelatorio]);

  const handleGerar = async (acao: 'pdf' | 'email') => {
    setGerando(true);
    try {
      const vendedorIdPayload = isVendedor ? meuVendedorId : (vendedorSelecionado !== 'todos' ? vendedorSelecionado : null);
      const empresaPrestadoraPayload = empresaPrestadoraSelecionada !== 'todas' ? parseInt(empresaPrestadoraSelecionada, 10) : null;
      const payload = { tipo: tipoRelatorio, periodo, vendedor_id: vendedorIdPayload, empresa_prestadora_id: empresaPrestadoraPayload, acao };

      if (acao === 'pdf') {
        const res = await apiClient.post('/crm-vendas/relatorios/gerar/', payload, { responseType: 'blob' });
        const url = window.URL.createObjectURL(new Blob([res.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `relatorio_${tipoRelatorio}_${periodo}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        alert('PDF gerado com sucesso!');
      } else {
        const res = await apiClient.post('/crm-vendas/relatorios/gerar/', payload);
        alert(res.data.message || 'Relatório enviado por email!');
      }
    } catch (error: any) {
      let msg = 'Erro ao gerar relatório.';
      const data = error.response?.data;
      if (data instanceof Blob) {
        try { msg = JSON.parse(await data.text()).detail || msg; } catch {}
      } else if (typeof data === 'string') {
        try { msg = JSON.parse(data).detail || msg; } catch { msg = data || msg; }
      } else if (data?.detail) { msg = data.detail; }
      alert(msg);
    } finally { setGerando(false); }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <FileText size={28} className="text-[#0176d3]" /> Relatórios de Vendas
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Gere relatórios detalhados de vendas, comissões e desempenho</p>
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
        vendedorSelecionado={vendedorSelecionado}
        vendedores={vendedores}
        empresasPrestadoras={empresasPrestadoras}
        empresaPrestadoraSelecionada={empresaPrestadoraSelecionada}
        isVendedor={isVendedor}
        gerando={gerando}
        loading={loading}
        onTipoChange={setTipoRelatorio}
        onPeriodoChange={setPeriodo}
        onVendedorChange={setVendedorSelecionado}
        onEmpresaPrestadoraChange={setEmpresaPrestadoraSelecionada}
        onGerar={handleGerar}
      />

      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-blue-800 dark:text-blue-300 mb-2">📊 Sobre os Relatórios</h3>
        <ul className="text-sm text-blue-700 dark:text-blue-400 space-y-1">
          <li>• <strong>Total de Vendas:</strong> Resumo geral de todas as vendas fechadas no período</li>
          <li>• <strong>Vendas por Vendedor:</strong> Detalhamento individual com valores de comissão</li>
          <li>• <strong>Comissões:</strong> Relatório específico para cálculo de comissões</li>
          <li>• Os relatórios incluem apenas oportunidades com status &quot;Fechado ganho&quot;</li>
        </ul>
      </div>
    </div>
  );
}
