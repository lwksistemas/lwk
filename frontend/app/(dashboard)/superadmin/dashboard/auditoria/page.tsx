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
  const [error, setError] = useState<string | null>(null);
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

  const [schemaLoading, setSchemaLoading] = useState(false);
  const [schemaResult, setSchemaResult] = useState<{
    postgresql?: boolean;
    mensagem?: string;
    aplicar_correcao?: boolean;
    resumo?: { total: number; ok: number; falhas: number; corrigidos: number };
    resultados?: Array<{
      audit: {
        loja_id: number;
        slug: string;
        nome: string;
        tipo_slug: string;
        ok: boolean;
        erro?: string | null;
        schema_existe?: boolean | null;
        tabelas_total?: number;
        tabelas_negocio?: number;
        apps_detalhe?: Array<{ app: string; ok: boolean; tabelas_prefixo: number; migrations_registradas: number }>;
      };
      correcao?: { sucesso?: boolean; mensagem?: string } | null;
      audit_pos?: Record<string, unknown> | null;
      ok_final: boolean;
    }>;
  } | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    loadData();
    // loadData omitido: definido abaixo, usa periodo/dataInicio/dataFim
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router, periodo, dataInicio, dataFim]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
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
      
      // Aceitar formato novo (objeto com chaves) ou antigo (array direto)
      const d = (r: { data: any }) => r.data;
      setAcoesPorDia(Array.isArray(d(acoesDiaRes)) ? (d(acoesDiaRes) as any[]).map((x: any) => ({ periodo: x.periodo || x.dia, total: x.total ?? x.count ?? 0, sucessos: x.sucessos ?? x.total ?? x.count ?? 0, erros: x.erros ?? 0 })) : (d(acoesDiaRes).acoes || []));
      setAcoesPorTipo(Array.isArray(d(acoesTipoRes)) ? (d(acoesTipoRes) as any[]).map((x: any) => ({ acao: x.acao, total: x.total ?? x.count ?? 0 })) : (d(acoesTipoRes).acoes || []));
      const lojasRaw = d(lojasRes).lojas ?? d(lojasRes);
      setLojasAtivas(Array.isArray(lojasRaw) ? lojasRaw.map((l: any) => ({ nome: l.loja_nome ?? l.nome, total: l.total ?? l.count ?? 0 })) : []);
      const usuariosRaw = d(usuariosRes).usuarios ?? d(usuariosRes);
      setUsuariosAtivos(Array.isArray(usuariosRaw) ? usuariosRaw.map((u: any) => ({ nome: u.usuario_nome ?? u.nome, total: u.total ?? u.count ?? 0 })) : []);
      const horariosRaw = d(horariosRes).horarios ?? d(horariosRes);
      setHorariosPico(Array.isArray(horariosRaw) ? horariosRaw.map((h: any) => ({ hora: h.hora, total: h.total ?? h.count ?? 0 })) : []);
      const taxa = d(taxaRes);
      setTaxaSucesso(taxa ? { total: taxa.total ?? 0, sucessos: taxa.sucessos ?? 0, erros: taxa.erros ?? taxa.falhas ?? 0, taxa_sucesso: taxa.taxa_sucesso ?? 0 } : null);
    } catch (err: any) {
      console.error('Erro ao carregar dados de auditoria:', err);
      const msg = err?.response?.data?.detail || err?.response?.status === 403 ? 'Sem permissão para ver auditoria.' : err?.message || 'Falha ao carregar dados. Tente novamente.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handlePeriodoChange = (novoPeriodo: string) => {
    setPeriodo(novoPeriodo);
    setDataInicio('');
    setDataFim('');
  };

  const executarAuditoriaSchema = async (aplicarCorrecao: boolean) => {
    if (aplicarCorrecao) {
      const ok = window.confirm(
        'Serão aplicadas migrations nos schemas das lojas com falha (até 80 lojas ativas). ' +
          'Pode levar alguns minutos. Continuar?'
      );
      if (!ok) return;
    }
    try {
      setSchemaLoading(true);
      setSchemaResult(null);
      const { data } = await apiClient.post(
        '/superadmin/security-dashboard/verificar_corrigir_schemas_lojas/',
        { aplicar_correcao: aplicarCorrecao, limite: 80 }
      );
      setSchemaResult(data);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } }; message?: string };
      setSchemaResult({
        postgresql: false,
        mensagem: ax?.response?.data?.detail || ax?.message || 'Falha ao executar auditoria de schemas.',
      });
    } finally {
      setSchemaLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-xl text-gray-900 dark:text-gray-100">Carregando dados de auditoria...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 p-4 bg-gray-50 dark:bg-gray-900">
        <p className="text-xl text-red-600 dark:text-red-400">{error}</p>
        <button
          onClick={() => { setError(null); loadData(); }}
          className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
        >
          Tentar novamente
        </button>
        <button
          onClick={() => router.push('/superadmin/dashboard')}
          className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
        >
          Voltar ao dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">📊 Dashboard de Auditoria</h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
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
        {/* Schemas PostgreSQL por loja */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow mb-6 border border-slate-200 dark:border-slate-600">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Banco isolado por loja (schema PostgreSQL)
          </h3>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400 mb-4">
            Verifica se cada loja ativa tem as tabelas esperadas para o tipo (CRM, clínica, etc.). Opcionalmente
            aplica migrations para corrigir schemas incompletos.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              disabled={schemaLoading}
              onClick={() => executarAuditoriaSchema(false)}
              className="px-4 py-2 rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {schemaLoading ? 'Processando…' : 'Verificar schemas'}
            </button>
            <button
              type="button"
              disabled={schemaLoading}
              onClick={() => executarAuditoriaSchema(true)}
              className="px-4 py-2 rounded-md bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Verificar e corrigir
            </button>
          </div>

          {schemaResult && (
            <div className="mt-4 text-sm">
              {schemaResult.postgresql === false && (
                <p className="text-amber-700 dark:text-amber-300">
                  {schemaResult.mensagem ||
                    'Ambiente sem PostgreSQL no servidor de API: a auditoria de schema só se aplica em produção (Heroku).'}
                </p>
              )}
              {schemaResult.postgresql !== false && schemaResult.resumo && (
                <div className="rounded-md bg-slate-50 dark:bg-slate-900/50 p-4 space-y-2">
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    Resumo: {schemaResult.resumo.total} loja(s) — {schemaResult.resumo.ok} OK,{' '}
                    {schemaResult.resumo.falhas} com falha
                    {schemaResult.aplicar_correcao ? ` — ${schemaResult.resumo.corrigidos} correção(ões) aplicada(s)` : ''}
                  </p>
                  <div className="max-h-64 overflow-y-auto border border-slate-200 dark:border-slate-600 rounded">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-100 dark:bg-slate-800 sticky top-0">
                        <tr>
                          <th className="p-2">Slug</th>
                          <th className="p-2">Tipo</th>
                          <th className="p-2">OK</th>
                          <th className="p-2">Detalhe</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(schemaResult.resultados || []).map((row, i) => {
                          const a = row.audit;
                          const badApps =
                            a.apps_detalhe?.filter((x) => !x.ok).map((x) => x.app).join(', ') || '';
                          const err = a.erro || (badApps ? `Apps: ${badApps}` : '');
                          return (
                            <tr key={i} className="border-t border-slate-200 dark:border-slate-600">
                              <td className="p-2 font-mono">{a.slug}</td>
                              <td className="p-2">{a.tipo_slug}</td>
                              <td className="p-2">
                                {row.ok_final ? (
                                  <span className="text-green-600 dark:text-green-400">Sim</span>
                                ) : (
                                  <span className="text-red-600 dark:text-red-400">Não</span>
                                )}
                              </td>
                              <td className="p-2 text-gray-700 dark:text-gray-300 break-words max-w-md">
                                {(a.tabelas_total ?? 0) > 0 && (
                                  <span className="text-blue-600 dark:text-blue-400 mr-2">
                                    {a.tabelas_total} tabelas ({a.tabelas_negocio ?? 0} negócio)
                                  </span>
                                )}
                                {err && <span className="text-red-500">{err}</span>}
                                {!err && !(a.tabelas_total ?? 0) && (row.ok_final ? '—' : 'Ver apps esperados')}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Seletor de Período */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow mb-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Período de Análise</h3>
          <div className="flex flex-wrap gap-4">
            <button
              onClick={() => handlePeriodoChange('7')}
              className={`px-4 py-2 rounded-md transition-colors ${
                periodo === '7' && !dataInicio
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-500'
              }`}
            >
              Últimos 7 dias
            </button>
            <button
              onClick={() => handlePeriodoChange('30')}
              className={`px-4 py-2 rounded-md transition-colors ${
                periodo === '30' && !dataInicio
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-500'
              }`}
            >
              Últimos 30 dias
            </button>
            <button
              onClick={() => handlePeriodoChange('90')}
              className={`px-4 py-2 rounded-md transition-colors ${
                periodo === '90' && !dataInicio
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-500'
              }`}
            >
              Últimos 90 dias
            </button>
            
            <div className="flex gap-2 items-center ml-auto">
              <input
                type="date"
                value={dataInicio}
                onChange={(e) => setDataInicio(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <span className="text-gray-500 dark:text-gray-400">até</span>
              <input
                type="date"
                value={dataFim}
                onChange={(e) => setDataFim(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
        </div>

        {/* Taxa de Sucesso */}
        {taxaSucesso && (
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow mb-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Taxa de Sucesso</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="text-center">
                <p className="text-4xl font-bold text-purple-600 dark:text-purple-400">
                  {taxaSucesso.taxa_sucesso.toFixed(1)}%
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Taxa de Sucesso</p>
              </div>
              <div className="text-center">
                <p className="text-4xl font-bold text-blue-600 dark:text-blue-400">{taxaSucesso.total}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Total de Ações</p>
              </div>
              <div className="text-center">
                <p className="text-4xl font-bold text-green-600 dark:text-green-400">{taxaSucesso.sucessos}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Sucessos</p>
              </div>
              <div className="text-center">
                <p className="text-4xl font-bold text-red-600 dark:text-red-400">{taxaSucesso.erros}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Erros</p>
              </div>
            </div>
            
            {/* Barra de progresso */}
            <div className="mt-6">
              <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-4 overflow-hidden">
                <div
                  className="bg-green-600 h-4 transition-all duration-500"
                  style={{ width: `${taxaSucesso.taxa_sucesso}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Gráfico de Ações por Dia */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow mb-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Ações por Dia</h3>
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
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">Nenhum dado disponível</p>
          )}
        </div>

        {/* Grid de 2 colunas */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Gráfico de Ações por Tipo */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Ações por Tipo</h3>
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
                    label={(entry: any) => `${entry.acao}: ${entry.total}`}
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
