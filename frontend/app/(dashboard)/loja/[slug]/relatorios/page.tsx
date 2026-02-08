'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
}

// Adicionar estilos para impressão
if (typeof window !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    @media print {
      body * {
        visibility: hidden;
      }
      .print-area, .print-area * {
        visibility: visible;
      }
      .print-area {
        position: absolute;
        left: 0;
        top: 0;
        width: 100%;
      }
      .no-print {
        display: none !important;
      }
      nav {
        display: none !important;
      }
      button {
        display: none !important;
      }
    }
  `;
  document.head.appendChild(style);
}

export default function RelatoriosPage() {
  const router = useRouter();
  const params = useParams();
  const slug = params.slug as string;
  
  const [lojaInfo, setLojaInfo] = useState<LojaInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [periodoSelecionado, setPeriodoSelecionado] = useState('mes_atual');
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');
  const [showEmailModal, setShowEmailModal] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const userType = authService.getUserType();
      if (userType !== 'loja') {
        router.push(`/loja/${slug}/login`);
        return;
      }

      carregarLoja();
      
      // Definir datas padrão (mês atual)
      const hoje = new Date();
      const primeiroDia = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
      setDataInicio(primeiroDia.toISOString().split('T')[0]);
      setDataFim(hoje.toISOString().split('T')[0]);
    }
  }, [router, slug]);

  const carregarLoja = async () => {
    try {
      setLoading(true);
      const lojaResponse = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
      setLojaInfo(lojaResponse.data);
    } catch (error: any) {
      console.error('Erro ao carregar loja:', error);
      if (error.response?.status === 401) {
        router.push(`/loja/${slug}/login`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVoltar = () => {
    router.push(`/loja/${slug}/dashboard`);
  };

  const handleLogout = () => {
    authService.logout();
    router.push(`/loja/${slug}/login`);
  };

  const handleExportarExcel = () => {
    // Criar dados do relatório
    const dados = gerarDadosRelatorio();
    
    // Converter para CSV (compatível com Excel)
    const csv = converterParaCSV(dados);
    
    // Criar blob e fazer download
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `relatorio_${lojaInfo?.nome}_${dataInicio}_${dataFim}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    alert('✅ Relatório exportado com sucesso!');
  };

  const handleExportarPDF = () => {
    // Abrir janela de impressão (que permite salvar como PDF)
    window.print();
  };

  const handleEnviarEmail = () => {
    setShowEmailModal(true);
  };

  const gerarDadosRelatorio = () => {
    return {
      loja: lojaInfo?.nome || '',
      periodo: `${dataInicio} a ${dataFim}`,
      resumo_financeiro: {
        receita_total: 'R$ 0,00',
        despesas: 'R$ 0,00',
        lucro_liquido: 'R$ 0,00',
        margem: '0%'
      },
      agendamentos: {
        total: 0,
        realizados: 0,
        cancelados: 0
      },
      clientes: {
        total: 0,
        novos: 0,
        ativos: 0,
        taxa_retorno: '0%'
      }
    };
  };

  const converterParaCSV = (dados: any) => {
    let csv = '';
    
    // Cabeçalho
    csv += `RELATÓRIO - ${dados.loja}\n`;
    csv += `Período: ${dados.periodo}\n\n`;
    
    // Resumo Financeiro
    csv += 'RESUMO FINANCEIRO\n';
    csv += 'Métrica,Valor\n';
    csv += `Receita Total,${dados.resumo_financeiro.receita_total}\n`;
    csv += `Despesas,${dados.resumo_financeiro.despesas}\n`;
    csv += `Lucro Líquido,${dados.resumo_financeiro.lucro_liquido}\n`;
    csv += `Margem,${dados.resumo_financeiro.margem}\n\n`;
    
    // Agendamentos
    csv += 'AGENDAMENTOS\n';
    csv += 'Métrica,Valor\n';
    csv += `Total de Agendamentos,${dados.agendamentos.total}\n`;
    csv += `Realizados,${dados.agendamentos.realizados}\n`;
    csv += `Cancelados,${dados.agendamentos.cancelados}\n\n`;
    
    // Clientes
    csv += 'CLIENTES\n';
    csv += 'Métrica,Valor\n';
    csv += `Total de Clientes,${dados.clientes.total}\n`;
    csv += `Novos no Período,${dados.clientes.novos}\n`;
    csv += `Clientes Ativos,${dados.clientes.ativos}\n`;
    csv += `Taxa de Retorno,${dados.clientes.taxa_retorno}\n`;
    
    return csv;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-xl text-gray-600">Carregando...</div>
      </div>
    );
  }

  if (!lojaInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Erro ao carregar loja</h2>
          <button
            onClick={() => router.push(`/loja/${slug}/login`)}
            className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Voltar para Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav 
        className="text-white shadow-lg"
        style={{ backgroundColor: lojaInfo.cor_primaria }}
      >
        <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row justify-between min-h-[56px] sm:h-16 py-2 sm:py-0 items-start sm:items-center gap-2 sm:gap-0">
            <div className="w-full sm:w-auto">
              <h1 className="text-lg sm:text-xl md:text-2xl font-bold">{lojaInfo.nome}</h1>
              <p className="text-xs sm:text-sm opacity-90">Relatórios</p>
            </div>
            <div className="flex items-center gap-2 sm:gap-4 w-full sm:w-auto">
              <button
                onClick={handleVoltar}
                className="flex-1 sm:flex-none px-3 sm:px-4 py-2 min-h-[40px] bg-white bg-opacity-20 hover:bg-opacity-30 rounded-md transition-colors text-sm"
              >
                ← Voltar
              </button>
              <button
                onClick={handleLogout}
                className="flex-1 sm:flex-none px-3 sm:px-4 py-2 min-h-[40px] bg-red-600 hover:bg-red-700 rounded-md transition-colors text-sm"
              >
                Sair
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-4 sm:py-6 px-3 sm:px-4 md:px-6 lg:px-8 print-area">
        <div className="py-4 sm:py-6">
          
          {/* Cabeçalho para impressão */}
          <div className="hidden print:block mb-6">
            <h1 className="text-3xl font-bold" style={{ color: lojaInfo.cor_primaria }}>
              {lojaInfo.nome}
            </h1>
            <p className="text-lg text-gray-600">Relatório de Atividades</p>
            <p className="text-sm text-gray-500">Período: {dataInicio} a {dataFim}</p>
            <hr className="my-4" />
          </div>
          
          {/* Filtros */}
          <div className="bg-white p-4 sm:p-6 rounded-lg shadow mb-4 sm:mb-6 no-print">
            <h3 className="text-base sm:text-lg font-semibold mb-4">Filtros</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 sm:gap-4">
              <div>
                <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1">
                  Período
                </label>
                <select
                  value={periodoSelecionado}
                  onChange={(e) => setPeriodoSelecionado(e.target.value)}
                  className="w-full px-3 py-2 min-h-[44px] text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                >
                  <option value="hoje">Hoje</option>
                  <option value="semana_atual">Semana Atual</option>
                  <option value="mes_atual">Mês Atual</option>
                  <option value="mes_anterior">Mês Anterior</option>
                  <option value="trimestre">Último Trimestre</option>
                  <option value="ano">Ano Atual</option>
                  <option value="personalizado">Personalizado</option>
                </select>
              </div>

              <div>
                <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1">
                  Data Início
                </label>
                <input
                  type="date"
                  value={dataInicio}
                  onChange={(e) => setDataInicio(e.target.value)}
                  className="w-full px-3 py-2 min-h-[44px] text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                />
              </div>

              <div>
                <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1">
                  Data Fim
                </label>
                <input
                  type="date"
                  value={dataFim}
                  onChange={(e) => setDataFim(e.target.value)}
                  className="w-full px-3 py-2 min-h-[44px] text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                />
              </div>
            </div>

            <div className="mt-4 flex justify-end">
              <button
                className="w-full sm:w-auto px-4 sm:px-6 py-2 min-h-[44px] text-sm sm:text-base text-white rounded-md hover:opacity-90"
                style={{ backgroundColor: lojaInfo.cor_primaria }}
              >
                Aplicar Filtros
              </button>
            </div>
          </div>

          {/* Resumo Financeiro */}
          <div className="bg-white p-4 sm:p-6 rounded-lg shadow mb-4 sm:mb-6">
            <h3 className="text-base sm:text-lg font-semibold mb-4" style={{ color: lojaInfo.cor_primaria }}>
              📊 Resumo Financeiro
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-6">
              <div className="text-center p-3 sm:p-4 bg-gray-50 rounded-lg">
                <p className="text-xs sm:text-sm text-gray-600 mb-1">Receita Total</p>
                <p className="text-lg sm:text-2xl font-bold" style={{ color: lojaInfo.cor_primaria }}>
                  R$ 0,00
                </p>
              </div>
              <div className="text-center p-3 sm:p-4 bg-gray-50 rounded-lg">
                <p className="text-xs sm:text-sm text-gray-600 mb-1">Despesas</p>
                <p className="text-lg sm:text-2xl font-bold text-red-600">
                  R$ 0,00
                </p>
              </div>
              <div className="text-center p-3 sm:p-4 bg-gray-50 rounded-lg">
                <p className="text-xs sm:text-sm text-gray-600 mb-1">Lucro Líquido</p>
                <p className="text-lg sm:text-2xl font-bold text-green-600">
                  R$ 0,00
                </p>
              </div>
              <div className="text-center p-3 sm:p-4 bg-gray-50 rounded-lg">
                <p className="text-xs sm:text-sm text-gray-600 mb-1">Margem</p>
                <p className="text-lg sm:text-2xl font-bold" style={{ color: lojaInfo.cor_primaria }}>
                  0%
                </p>
              </div>
            </div>
          </div>

          {/* Agendamentos */}
          <div className="bg-white p-4 sm:p-6 rounded-lg shadow mb-4 sm:mb-6">
            <h3 className="text-base sm:text-lg font-semibold mb-4" style={{ color: lojaInfo.cor_primaria }}>
              📅 Relatório de Agendamentos
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 sm:gap-6 mb-4 sm:mb-6">
              <div className="text-center p-3 sm:p-4 bg-gray-50 rounded-lg">
                <p className="text-xs sm:text-sm text-gray-600 mb-1">Total de Agendamentos</p>
                <p className="text-lg sm:text-2xl font-bold" style={{ color: lojaInfo.cor_primaria }}>
                  0
                </p>
              </div>
              <div className="text-center p-3 sm:p-4 bg-gray-50 rounded-lg">
                <p className="text-xs sm:text-sm text-gray-600 mb-1">Realizados</p>
                <p className="text-lg sm:text-2xl font-bold text-green-600">
                  0 (0%)
                </p>
              </div>
              <div className="text-center p-3 sm:p-4 bg-gray-50 rounded-lg">
                <p className="text-xs sm:text-sm text-gray-600 mb-1">Cancelados</p>
                <p className="text-lg sm:text-2xl font-bold text-red-600">
                  0 (0%)
                </p>
              </div>
            </div>

            <div className="text-center py-6 sm:py-8 text-gray-500">
              <p className="text-sm sm:text-lg">Nenhum agendamento registrado no período</p>
            </div>
          </div>

          {/* Clientes */}
          <div className="bg-white p-4 sm:p-6 rounded-lg shadow mb-4 sm:mb-6">
            <h3 className="text-base sm:text-lg font-semibold mb-4" style={{ color: lojaInfo.cor_primaria }}>
              👥 Relatório de Clientes
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-6">
              <div className="text-center p-3 sm:p-4 bg-gray-50 rounded-lg">
                <p className="text-xs sm:text-sm text-gray-600 mb-1">Total de Clientes</p>
                <p className="text-lg sm:text-2xl font-bold" style={{ color: lojaInfo.cor_primaria }}>
                  0
                </p>
              </div>
              <div className="text-center p-3 sm:p-4 bg-gray-50 rounded-lg">
                <p className="text-xs sm:text-sm text-gray-600 mb-1">Novos no Período</p>
                <p className="text-lg sm:text-2xl font-bold text-green-600">
                  0
                </p>
              </div>
              <div className="text-center p-3 sm:p-4 bg-gray-50 rounded-lg">
                <p className="text-xs sm:text-sm text-gray-600 mb-1">Clientes Ativos</p>
                <p className="text-lg sm:text-2xl font-bold" style={{ color: lojaInfo.cor_primaria }}>
                  0
                </p>
              </div>
              <div className="text-center p-3 sm:p-4 bg-gray-50 rounded-lg">
                <p className="text-xs sm:text-sm text-gray-600 mb-1">Taxa de Retorno</p>
                <p className="text-lg sm:text-2xl font-bold text-green-600">
                  0%
                </p>
              </div>
            </div>
          </div>

          {/* Profissionais */}
          <div className="bg-white p-4 sm:p-6 rounded-lg shadow mb-4 sm:mb-6">
            <h3 className="text-base sm:text-lg font-semibold mb-4" style={{ color: lojaInfo.cor_primaria }}>
              👨‍⚕️ Desempenho dos Profissionais
            </h3>
            <div className="text-center py-6 sm:py-8 text-gray-500">
              <p className="text-sm sm:text-lg">Nenhum profissional cadastrado</p>
            </div>
          </div>

          {/* Botões de Exportação */}
          <div className="bg-white p-4 sm:p-6 rounded-lg shadow no-print">
            <h3 className="text-base sm:text-lg font-semibold mb-4">Exportar Relatórios</h3>
            <div className="flex flex-col sm:flex-row flex-wrap gap-3 sm:gap-4">
              <button
                onClick={handleExportarExcel}
                className="w-full sm:w-auto px-4 sm:px-6 py-3 min-h-[44px] bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors flex items-center justify-center gap-2 text-sm sm:text-base"
              >
                <span>📄</span>
                <span>Exportar Excel</span>
              </button>
              <button
                onClick={handleExportarPDF}
                className="w-full sm:w-auto px-4 sm:px-6 py-3 min-h-[44px] bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors flex items-center justify-center gap-2 text-sm sm:text-base"
              >
                <span>📑</span>
                <span>Exportar PDF</span>
              </button>
              <button
                onClick={handleEnviarEmail}
                className="w-full sm:w-auto px-4 sm:px-6 py-3 min-h-[44px] text-white rounded-md hover:opacity-90 transition-colors flex items-center justify-center gap-2 text-sm sm:text-base"
                style={{ backgroundColor: lojaInfo.cor_primaria }}
              >
                <span>📧</span>
                <span>Enviar por Email</span>
              </button>
            </div>
          </div>

        </div>
      </main>

      {/* Modal Enviar Email */}
      {showEmailModal && (
        <ModalEnviarEmail 
          lojaInfo={lojaInfo!}
          dataInicio={dataInicio}
          dataFim={dataFim}
          onClose={() => setShowEmailModal(false)}
        />
      )}
    </div>
  );
}

// Modal Enviar Email
function ModalEnviarEmail({ 
  lojaInfo, 
  dataInicio, 
  dataFim, 
  onClose 
}: { 
  lojaInfo: LojaInfo; 
  dataInicio: string; 
  dataFim: string; 
  onClose: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    assunto: `Relatório ${lojaInfo.nome} - ${dataInicio} a ${dataFim}`,
    mensagem: 'Segue em anexo o relatório solicitado.'
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Simular envio de email
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      alert(`✅ Relatório enviado com sucesso para ${formData.email}!`);
      onClose();
    } catch (error) {
      alert('❌ Erro ao enviar email');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-md w-full">
        <h2 className="text-2xl font-bold mb-6" style={{ color: lojaInfo.cor_primaria }}>
          📧 Enviar Relatório por Email
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email do Destinatário *
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
              placeholder="email@exemplo.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Assunto
            </label>
            <input
              type="text"
              name="assunto"
              value={formData.assunto}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Mensagem
            </label>
            <textarea
              name="mensagem"
              value={formData.mensagem}
              onChange={handleChange}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
            />
          </div>

          <div className="bg-gray-50 p-4 rounded-md">
            <p className="text-sm text-gray-600">
              <strong>Período:</strong> {dataInicio} a {dataFim}
            </p>
            <p className="text-sm text-gray-600 mt-1">
              <strong>Formato:</strong> PDF
            </p>
          </div>

          <div className="flex justify-end space-x-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50"
              style={{ backgroundColor: lojaInfo.cor_primaria }}
            >
              {loading ? 'Enviando...' : 'Enviar Email'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
