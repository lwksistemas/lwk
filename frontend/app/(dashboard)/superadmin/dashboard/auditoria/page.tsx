'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface AcoesPorDia {
  periodo: string;
  total: number;
  sucessos: number;
  erros: number;
}

interface AcoesPorTipo {
  acao: string;
  total: number;
}

interface RankingItem {
  nome: string;
  total: number;
}

interface HorarioPico {
  hora: number;
  total: number;
}

interface TaxaSucesso {
  total: number;
  sucessos: number;
  erros: number;
  taxa_sucesso: number;
}

const COLORS = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#6366f1', '#14b8a6'];

export default function AuditoriaPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [periodo, setPeriodo] = useState('7');
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');
  
  // Dados dos gráficos
  const [acoesPorDia, setAcoesPorDia] = useState<AcoesPorDia[]>([]);
  const [acoesPorTipo, setAcoesPorTipo] = useState<AcoesPorTipo[]>([]);
  const [lojasAtivas, setLojasAtivas] = useState<RankingItem[]>([]);
  const [usuariosAtivos, setUsuariosAtivos] = useState<RankingItem[]>([]);
  const [horariosPico, setHorariosPico] = useState<HorarioPico[]>([]);
  const [taxaSucesso, setTaxaSucesso] = useState<TaxaSucesso | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    loadData();
  }, [router, periodo, dataInicio, dataFim]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Construir query params
      const params = new URLSearchParams();
      if (dataInicio) params.append('data_inicio', dataInicio);
      if (dataFim) params.append('data_fim', dataFim);
      if (!dataInicio && periodo) {
        const hoje = new Date();
        const inicio = new Date(hoje);
        inicio.setDate(hoje.getDate() - parseInt(periodo));
        params.append('data_inicio', inicio.toISOString().split('T')[0]);
        params.append('data_fim', hoje.toISOString().split('T')[0]);
      }
      
      const queryString = params.toString();
      
      // Carregar todos os dados em paralelo
      const [
        acoesDiaRes,
        acoesTipoRes,
        lojasRes,
        usuariosRes,
        horariosRes,
        taxaRes,
      ] = await Promise.all([
        apiClient.get(`/superadmin/estatisticas-auditoria/acoes_por_dia/?${queryString}`),
        apiClient.get(`/superadmin/estatisticas-auditoria/acoes_por_tipo/?${queryString}`),
        apiClient.get(`/superadmin/estatisticas-auditoria/lojas_mais_ativas/?${queryString}`),
        apiClient.get(`/superadmin/estatisticas-auditoria/usuarios_mais_ativos/?${queryString}`),
        apiClient.get(`/superadmin/estatisticas-auditoria/horarios_pico/?${queryString}`),
        apiClient.get(`/superadmin/estatisticas-auditoria/taxa_sucesso/?${queryString}`),
      ]);
      
      setAcoesPorDia(acoesDiaRes.data.acoes || []);
      setAcoesPorTipo(acoesTipoRes.data.acoes || []);
      setLojasAtivas(lojasRes.data.lojas?.map((l: any) => ({ nome: l.loja_nome, total: l.total })) || []);
      setUsuariosAtivos(usuariosRes.data.usuarios?.map((u: any) => ({ nome: u.usuario_nome, total: u.total })) || []);
      setHorariosPico(horariosRes.data.horarios?.map((h: any) => ({ hora: h.hora, total: h.total })) || []);
      setTaxaSucesso(taxaRes.data);
    } catch (error) {
      console.error('Erro ao carregar dados de auditoria:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePeriodoChange = (novoPeriodo: string) => {
    setPeriodo(novoPeriodo);
    setDataInicio('');
    setDataFim('');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Carregando dados de auditoria...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">📊 Dashboard de Auditoria</h1>
              <p className="mt-1 text-sm text-gray-500">
                Análise de atividades e métricas do sistema
              </p>
            </div>
            <button
              onClick={() => router.push('/superadmin/dashboard')}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
            >
              ← Voltar
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Seletor de Período */}
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h3 className="text-lg font-semibold mb-4">Período de Análise</h3>
          <div className="flex flex-wrap gap-4">
            <button
              onClick={() => handlePeriodoChange('7')}
              className={`px-4 py-2 rounded-md transition-colors ${
                periodo === '7' && !dataInicio
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Últimos 7 dias
            </button>
            <button
              onClick={() => handlePeriodoChange('30')}
              className={`px-4 py-2 rounded-md transition-colors ${
                periodo === '30' && !dataInicio
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Últimos 30 dias
            </button>
            <button
              onClick={() => handlePeriodoChange('90')}
              className={`px-4 py-2 rounded-md transition-colors ${
                periodo === '90' && !dataInicio
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Últimos 90 dias
            </button>
            
            <div className="flex gap-2 items-center ml-auto">
              <input
                type="date"
                value={dataInicio}
                onChange={(e) => setDataInicio(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <span className="text-gray-500">até</span>
              <input
                type="date"
                value={dataFim}
                onChange={(e) => setDataFim(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
        </div>

        {/* Taxa de Sucesso */}
        {taxaSucesso && (
          <div className="bg-white p-6 rounded-lg shadow mb-6">
            <h3 className="text-lg font-semibold mb-4">Taxa de Sucesso</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="text-center">
                <p className="text-4xl font-bold text-purple-600">
                  {taxaSucesso.taxa_sucesso.toFixed(1)}%
                </p>
                <p className="text-sm text-gray-500 mt-2">Taxa de Sucesso</p>
              </div>
              <div className="text-center">
                <p className="text-4xl font-bold text-blue-600">{taxaSucesso.total}</p>
                <p className="text-sm text-gray-500 mt-2">Total de Ações</p>
              </div>
              <div className="text-center">
                <p className="text-4xl font-bold text-green-600">{taxaSucesso.sucessos}</p>
                <p className="text-sm text-gray-500 mt-2">Sucessos</p>
              </div>
              <div className="text-center">
                <p className="text-4xl font-bold text-red-600">{taxaSucesso.erros}</p>
                <p className="text-sm text-gray-500 mt-2">Erros</p>
              </div>
            </div>
            
            {/* Barra de progresso */}
            <div className="mt-6">
              <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                <div
                  className="bg-green-600 h-4 transition-all duration-500"
                  style={{ width: `${taxaSucesso.taxa_sucesso}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Gráfico de Ações por Dia */}
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h3 className="text-lg font-semibold mb-4">Ações por Dia</h3>
          {acoesPorDia.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={acoesPorDia}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="periodo" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="total" stroke="#8b5cf6" name="Total" strokeWidth={2} />
                <Line type="monotone" dataKey="sucessos" stroke="#10b981" name="Sucessos" strokeWidth={2} />
                <Line type="monotone" dataKey="erros" stroke="#ef4444" name="Erros" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-center text-gray-500 py-8">Nenhum dado disponível</p>
          )}
        </div>

        {/* Grid de 2 colunas */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Gráfico de Ações por Tipo */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Ações por Tipo</h3>
            {acoesPorTipo.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={acoesPorTipo}
                    dataKey="total"
                    nameKey="acao"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={(entry) => `${entry.acao}: ${entry.total}`}
                  >
                    {acoesPorTipo.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-center text-gray-500 py-8">Nenhum dado disponível</p>
            )}
          </div>

          {/* Gráfico de Horários de Pico */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Horários de Pico</h3>
            {horariosPico.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={horariosPico}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hora" tickFormatter={(hora) => `${hora}h`} />
                  <YAxis />
                  <Tooltip labelFormatter={(hora) => `${hora}:00`} />
                  <Bar dataKey="total" fill="#8b5cf6" name="Ações" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-center text-gray-500 py-8">Nenhum dado disponível</p>
            )}
          </div>
        </div>

        {/* Rankings */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Ranking de Lojas */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">🏪 Lojas Mais Ativas</h3>
            {lojasAtivas.length > 0 ? (
              <div className="space-y-3">
                {lojasAtivas.map((loja, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl font-bold text-purple-600">#{index + 1}</span>
                      <span className="font-medium text-gray-900">{loja.nome}</span>
                    </div>
                    <span className="text-lg font-semibold text-gray-700">{loja.total} ações</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-gray-500 py-8">Nenhum dado disponível</p>
            )}
          </div>

          {/* Ranking de Usuários */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">👥 Usuários Mais Ativos</h3>
            {usuariosAtivos.length > 0 ? (
              <div className="space-y-3">
                {usuariosAtivos.map((usuario, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl font-bold text-blue-600">#{index + 1}</span>
                      <span className="font-medium text-gray-900">{usuario.nome}</span>
                    </div>
                    <span className="text-lg font-semibold text-gray-700">{usuario.total} ações</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-gray-500 py-8">Nenhum dado disponível</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
