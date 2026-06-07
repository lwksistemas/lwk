'use client';

import { Suspense, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { logger } from '@/lib/logger';

interface Violacao {
  id: number;
  tipo: string;
  tipo_display: string;
  tipo_display_friendly?: string;
  criticidade: string;
  criticidade_display: string;
  criticidade_color: string;
  status: string;
  status_display: string;
  usuario_nome: string;
  usuario_email: string;
  loja_nome: string;
  descricao: string;
  detalhes_tecnicos?: Record<string, unknown>;
  ip_address: string;
  data_hora: string;
  logs_relacionados_count: number;
  resolvido_por_nome: string | null;
  data_resolucao_formatada: string | null;
  notas?: string;
}

interface Estatisticas {
  total: number;
  nao_resolvidas: number;
  ultimas_24h: number;
  por_status: { [key: string]: number };
  por_criticidade: { [key: string]: number };
  por_tipo: { [key: string]: number };
}

function AlertasContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [violacoes, setViolacoes] = useState<Violacao[]>([]);
  const [stats, setStats] = useState<Estatisticas | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedViolacao, setSelectedViolacao] = useState<Violacao | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const [filtroStatus, setFiltroStatus] = useState('');
  const [filtroCriticidade, setFiltroCriticidade] = useState('');
  const [filtroTipo, setFiltroTipo] = useState('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 50;

  const openViolacao = useCallback(async (id: number) => {
    setDetailLoading(true);
    setShowModal(true);
    try {
      const { data } = await apiClient.get<Violacao>(`/superadmin/violacoes-seguranca/${id}/`);
      setSelectedViolacao(data);
    } catch (error) {
      logger.warn('Erro ao carregar detalhe da violação:', error);
      setLoadError('Não foi possível carregar os detalhes desta violação.');
      setShowModal(false);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const loadData = useCallback(async () => {
    try {
      setLoadError(null);
      const params = new URLSearchParams();
      params.append('page', String(page));
      if (filtroStatus) params.append('status', filtroStatus);
      if (filtroCriticidade) params.append('criticidade', filtroCriticidade);
      if (filtroTipo) params.append('tipo', filtroTipo);

      const [violacoesRes, statsRes] = await Promise.all([
        apiClient.get(`/superadmin/violacoes-seguranca/?${params.toString()}`),
        apiClient.get('/superadmin/violacoes-seguranca/estatisticas/'),
      ]);

      const list = violacoesRes.data.results ?? violacoesRes.data;
      setViolacoes(Array.isArray(list) ? list : []);
      setTotalCount(violacoesRes.data.count ?? (Array.isArray(list) ? list.length : 0));
      setStats(statsRes.data);
    } catch (error) {
      logger.warn('Erro ao carregar alertas:', error);
      setLoadError('Falha ao carregar alertas. Verifique se você está logado como superadmin.');
      setViolacoes([]);
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, [filtroStatus, filtroCriticidade, filtroTipo, page]);

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [router, loadData]);

  useEffect(() => {
    const violacaoId = searchParams.get('violacao_id');
    if (violacaoId && !loading) {
      const id = parseInt(violacaoId, 10);
      if (!Number.isNaN(id)) {
        openViolacao(id);
      }
    }
  }, [searchParams, loading, openViolacao]);

  const refreshAfterAction = async () => {
    await loadData();
    setShowModal(false);
    setSelectedViolacao(null);
  };

  const handleInvestigar = async (id: number) => {
    setActionLoading(true);
    try {
      await apiClient.post(`/superadmin/violacoes-seguranca/${id}/investigar/`);
      await refreshAfterAction();
    } catch (error) {
      logger.warn('Erro ao investigar violação:', error);
      alert('Erro ao marcar como investigando');
    } finally {
      setActionLoading(false);
    }
  };

  const handleResolver = async (id: number) => {
    setActionLoading(true);
    try {
      await apiClient.post(`/superadmin/violacoes-seguranca/${id}/resolver/`, {
        notas: 'Resolvido via dashboard',
      });
      await refreshAfterAction();
    } catch (error) {
      logger.warn('Erro ao resolver violação:', error);
      alert('Erro ao resolver violação');
    } finally {
      setActionLoading(false);
    }
  };

  const handleFalsoPositivo = async (id: number) => {
    setActionLoading(true);
    try {
      await apiClient.post(`/superadmin/violacoes-seguranca/${id}/marcar_falso_positivo/`);
      await refreshAfterAction();
    } catch (error) {
      logger.warn('Erro ao marcar como falso positivo:', error);
      alert('Erro ao marcar como falso positivo');
    } finally {
      setActionLoading(false);
    }
  };

  const getCriticidadeClass = (criticidade: string) => {
    const classes: Record<string, string> = {
      critica: 'bg-red-100 text-red-800 border-red-300 dark:bg-red-900/30 dark:text-red-200',
      alta: 'bg-orange-100 text-orange-800 border-orange-300 dark:bg-orange-900/30 dark:text-orange-200',
      media: 'bg-yellow-100 text-yellow-800 border-yellow-300 dark:bg-yellow-900/30 dark:text-yellow-200',
      baixa: 'bg-green-100 text-green-800 border-green-300 dark:bg-green-900/30 dark:text-green-200',
    };
    return classes[criticidade] || 'bg-gray-100 text-gray-800';
  };

  const getStatusClass = (status: string) => {
    const classes: Record<string, string> = {
      nova: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200',
      investigando: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200',
      resolvida: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200',
      falso_positivo: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  };

  const logsSearchUrl = (v: Violacao) => {
    const q = new URLSearchParams();
    if (v.usuario_email) q.set('usuario_email', v.usuario_email);
    if (v.ip_address) q.set('q', v.ip_address);
    return `/superadmin/dashboard/logs?${q.toString()}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center dark:bg-gray-900">
        <div className="text-xl text-gray-700 dark:text-gray-200">Carregando alertas...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-4">
            <Link
              href="/superadmin/dashboard"
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Alertas de Segurança</h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Monitoramento de violações e atividades suspeitas
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loadError && (
          <div className="mb-6 rounded-lg border border-red-300 bg-red-50 dark:bg-red-900/20 dark:border-red-800 px-4 py-3 text-red-800 dark:text-red-200">
            {loadError}
            <button
              type="button"
              onClick={() => { setLoading(true); loadData(); }}
              className="ml-3 underline text-sm"
            >
              Tentar novamente
            </button>
          </div>
        )}

        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <h3 className="text-gray-500 dark:text-gray-400 text-sm font-medium">Total</h3>
              <p className="text-3xl font-bold text-purple-600 dark:text-purple-400 mt-2">{stats.total}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <h3 className="text-gray-500 dark:text-gray-400 text-sm font-medium">Novas</h3>
              <p className="text-3xl font-bold text-red-600 dark:text-red-400 mt-2">{stats.por_status?.nova ?? 0}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <h3 className="text-gray-500 dark:text-gray-400 text-sm font-medium">Críticas</h3>
              <p className="text-3xl font-bold text-red-600 dark:text-red-400 mt-2">{stats.por_criticidade?.critica ?? 0}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <h3 className="text-gray-500 dark:text-gray-400 text-sm font-medium">Não resolvidas</h3>
              <p className="text-3xl font-bold text-orange-600 dark:text-orange-400 mt-2">{stats.nao_resolvidas ?? 0}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <h3 className="text-gray-500 dark:text-gray-400 text-sm font-medium">Últimas 24h</h3>
              <p className="text-3xl font-bold text-blue-600 dark:text-blue-400 mt-2">{stats.ultimas_24h ?? 0}</p>
            </div>
          </div>
        )}

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Filtros</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Status</label>
              <select
                value={filtroStatus}
                onChange={(e) => { setPage(1); setFiltroStatus(e.target.value); }}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md"
              >
                <option value="">Todos</option>
                <option value="nova">Nova</option>
                <option value="investigando">Investigando</option>
                <option value="resolvida">Resolvida</option>
                <option value="falso_positivo">Falso Positivo</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Criticidade</label>
              <select
                value={filtroCriticidade}
                onChange={(e) => { setPage(1); setFiltroCriticidade(e.target.value); }}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md"
              >
                <option value="">Todas</option>
                <option value="critica">Crítica</option>
                <option value="alta">Alta</option>
                <option value="media">Média</option>
                <option value="baixa">Baixa</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Tipo</label>
              <select
                value={filtroTipo}
                onChange={(e) => { setPage(1); setFiltroTipo(e.target.value); }}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md"
              >
                <option value="">Todos</option>
                <option value="brute_force">Brute Force</option>
                <option value="rate_limit_exceeded">Rate Limit</option>
                <option value="acesso_cross_tenant">Cross-Tenant</option>
                <option value="privilege_escalation">Escalação de Privilégios</option>
                <option value="mass_deletion">Exclusão em Massa</option>
                <option value="ip_change">Mudança de IP</option>
                <option value="suspicious_pattern">Padrão Suspeito</option>
              </select>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Violações Detectadas ({totalCount})
            </h3>
            <button
              type="button"
              onClick={() => { setLoading(true); loadData(); }}
              className="text-sm text-purple-600 dark:text-purple-400 hover:underline"
            >
              Atualizar agora
            </button>
          </div>

          {violacoes.length === 0 && !loadError ? (
            <div className="p-8 text-center text-gray-500 dark:text-gray-400">
              <p className="text-lg">Nenhuma violação encontrada com os filtros atuais</p>
              <p className="text-sm mt-2">O detector roda automaticamente a cada 5 minutos no servidor.</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {violacoes.map((violacao) => (
                <div
                  key={violacao.id}
                  className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer transition-colors"
                  onClick={() => openViolacao(violacao.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2 flex-wrap">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getCriticidadeClass(violacao.criticidade)}`}>
                          {violacao.criticidade_display.toUpperCase()}
                        </span>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusClass(violacao.status)}`}>
                          {violacao.status_display}
                        </span>
                        <span className="text-sm text-gray-500 dark:text-gray-400">{violacao.data_hora}</span>
                      </div>
                      <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">{violacao.tipo_display}</h4>
                      <p className="text-gray-700 dark:text-gray-300 mb-2">{violacao.descricao}</p>
                      <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 flex-wrap">
                        <span>{violacao.usuario_nome}</span>
                        <span>{violacao.usuario_email}</span>
                        <span>{violacao.ip_address}</span>
                        {violacao.loja_nome && <span>{violacao.loja_nome}</span>}
                        <span>{violacao.logs_relacionados_count ?? 0} logs</span>
                      </div>
                    </div>
                    <span className="text-purple-600 dark:text-purple-400 font-medium text-sm ml-4">Detalhes →</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {totalCount > pageSize && (
            <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Página {page} de {Math.ceil(totalCount / pageSize)}
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => { setLoading(true); setPage((p) => p - 1); }}
                  className="px-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Anterior
                </button>
                <button
                  type="button"
                  disabled={page >= Math.ceil(totalCount / pageSize)}
                  onClick={() => { setLoading(true); setPage((p) => p + 1); }}
                  className="px-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Próxima
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {detailLoading || !selectedViolacao ? (
              <div className="p-8 text-center text-gray-600 dark:text-gray-300">Carregando detalhes...</div>
            ) : (
              <>
                <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-start">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{selectedViolacao.tipo_display}</h2>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{selectedViolacao.data_hora}</p>
                  </div>
                  <button type="button" onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
                </div>

                <div className="p-6 space-y-4">
                  <div className="flex gap-2 flex-wrap">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getCriticidadeClass(selectedViolacao.criticidade)}`}>
                      {selectedViolacao.criticidade_display.toUpperCase()}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusClass(selectedViolacao.status)}`}>
                      {selectedViolacao.status_display}
                    </span>
                  </div>

                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Descrição</h3>
                    <p className="text-gray-700 dark:text-gray-300">{selectedViolacao.descricao}</p>
                  </div>

                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Usuário e origem</h3>
                    <div className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-md space-y-1 text-sm text-gray-800 dark:text-gray-200">
                      <p><strong>Nome:</strong> {selectedViolacao.usuario_nome}</p>
                      <p><strong>Email:</strong> {selectedViolacao.usuario_email}</p>
                      <p><strong>IP:</strong> {selectedViolacao.ip_address}</p>
                      {selectedViolacao.loja_nome && <p><strong>Loja:</strong> {selectedViolacao.loja_nome}</p>}
                    </div>
                  </div>

                  {selectedViolacao.detalhes_tecnicos && Object.keys(selectedViolacao.detalhes_tecnicos).length > 0 && (
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Detalhes técnicos</h3>
                      <pre className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-md text-xs overflow-x-auto text-gray-800 dark:text-gray-200">
                        {JSON.stringify(selectedViolacao.detalhes_tecnicos, null, 2)}
                      </pre>
                    </div>
                  )}

                  <div className="flex items-center justify-between gap-4 flex-wrap">
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      {selectedViolacao.logs_relacionados_count ?? 0} log(s) relacionado(s)
                    </p>
                    <Link
                      href={logsSearchUrl(selectedViolacao)}
                      className="text-sm text-purple-600 dark:text-purple-400 hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Buscar nos logs →
                    </Link>
                  </div>

                  {selectedViolacao.resolvido_por_nome && (
                    <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-md text-sm">
                      <p><strong>Resolvido por:</strong> {selectedViolacao.resolvido_por_nome}</p>
                      <p><strong>Data:</strong> {selectedViolacao.data_resolucao_formatada}</p>
                      {selectedViolacao.notas && <p className="mt-1"><strong>Notas:</strong> {selectedViolacao.notas}</p>}
                    </div>
                  )}
                </div>

                {['nova', 'investigando'].includes(selectedViolacao.status) && (
                  <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex flex-wrap gap-3">
                    {selectedViolacao.status === 'nova' && (
                      <button
                        type="button"
                        disabled={actionLoading}
                        onClick={() => handleInvestigar(selectedViolacao.id)}
                        className="flex-1 min-w-[140px] px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-md disabled:opacity-50"
                      >
                        Investigar
                      </button>
                    )}
                    <button
                      type="button"
                      disabled={actionLoading}
                      onClick={() => handleResolver(selectedViolacao.id)}
                      className="flex-1 min-w-[140px] px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md disabled:opacity-50"
                    >
                      Resolvida
                    </button>
                    <button
                      type="button"
                      disabled={actionLoading}
                      onClick={() => handleFalsoPositivo(selectedViolacao.id)}
                      className="flex-1 min-w-[140px] px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md disabled:opacity-50"
                    >
                      Falso positivo
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function AlertasPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center dark:bg-gray-900 text-gray-700 dark:text-gray-200">
        Carregando alertas...
      </div>
    }>
      <AlertasContent />
    </Suspense>
  );
}
