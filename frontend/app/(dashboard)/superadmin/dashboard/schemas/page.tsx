'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { Database, CheckCircle, XCircle, AlertTriangle, RefreshCw, Wrench } from 'lucide-react';

interface AppDetalhe {
  app: string;
  ok: boolean;
  tabelas_prefixo: number;
  migrations_registradas: number;
}

interface AuditResult {
  loja_id: number;
  slug: string;
  nome: string;
  tipo_slug: string;
  ok: boolean;
  erro?: string | null;
  schema_existe?: boolean | null;
  tabelas_total?: number;
  tabelas_negocio?: number;
  apps_detalhe?: AppDetalhe[];
}

interface SchemaRow {
  audit: AuditResult;
  correcao?: { sucesso?: boolean; mensagem?: string } | null;
  audit_pos?: Record<string, unknown> | null;
  ok_final: boolean;
}

interface SchemaResult {
  postgresql?: boolean;
  mensagem?: string;
  aplicar_correcao?: boolean;
  resumo?: { total: number; ok: number; falhas: number; corrigidos: number };
  resultados?: SchemaRow[];
}

export default function SchemasPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SchemaResult | null>(null);
  const [filtro, setFiltro] = useState<'todos' | 'ok' | 'falha'>('todos');

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
    }
  }, [router]);

  const executar = async (aplicarCorrecao: boolean) => {
    if (aplicarCorrecao) {
      const ok = window.confirm(
        'Serão aplicadas migrations nos schemas das lojas com falha. Pode levar alguns minutos. Continuar?'
      );
      if (!ok) return;
    }
    try {
      setLoading(true);
      setResult(null);
      const { data } = await apiClient.post(
        '/superadmin/security-dashboard/verificar_corrigir_schemas_lojas/',
        { aplicar_correcao: aplicarCorrecao, limite: 80 }
      );
      setResult(data);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } }; message?: string };
      setResult({
        postgresql: false,
        mensagem: ax?.response?.data?.detail || ax?.message || 'Falha ao executar auditoria.',
      });
    } finally {
      setLoading(false);
    }
  };

  const resultados = result?.resultados || [];
  const filtrados = resultados.filter((r) => {
    if (filtro === 'ok') return r.ok_final;
    if (filtro === 'falha') return !r.ok_final;
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <Database size={28} className="text-indigo-500" /> Auditoria de Schemas
              </h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Verifica se cada loja ativa tem as tabelas esperadas para o tipo (CRM, clínica, hotel, etc.)
              </p>
            </div>
            <button
              onClick={() => router.push('/superadmin/dashboard')}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md"
            >
              ← Voltar
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Ações */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow border border-gray-200 dark:border-gray-700">
          <div className="flex flex-wrap gap-3 items-center">
            <button
              type="button"
              disabled={loading}
              onClick={() => executar(false)}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 font-medium"
            >
              <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
              {loading ? 'Verificando…' : 'Verificar schemas'}
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={() => executar(true)}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50 font-medium"
            >
              <Wrench size={18} />
              Verificar e corrigir
            </button>
            {result?.resumo && (
              <div className="ml-auto flex gap-4 text-sm">
                <span className="text-gray-600 dark:text-gray-400">{result.resumo.total} lojas</span>
                <span className="text-green-600 dark:text-green-400">{result.resumo.ok} OK</span>
                <span className="text-red-600 dark:text-red-400">{result.resumo.falhas} falha(s)</span>
                {result.aplicar_correcao && (
                  <span className="text-amber-600 dark:text-amber-400">{result.resumo.corrigidos} corrigida(s)</span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Mensagem de erro */}
        {result?.postgresql === false && (
          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
            <p className="text-amber-700 dark:text-amber-300 flex items-center gap-2">
              <AlertTriangle size={18} />
              {result.mensagem || 'Ambiente sem PostgreSQL: auditoria de schema só se aplica em produção.'}
            </p>
          </div>
        )}

        {/* Resultados */}
        {resultados.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 overflow-hidden">
            {/* Filtros */}
            <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex gap-2">
              {(['todos', 'ok', 'falha'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFiltro(f)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition ${
                    filtro === f
                      ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  {f === 'todos' ? `Todos (${resultados.length})` : f === 'ok' ? `OK (${resultados.filter((r) => r.ok_final).length})` : `Falha (${resultados.filter((r) => !r.ok_final).length})`}
                </button>
              ))}
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Loja</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Tipo</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Tabelas</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Status</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Apps</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Detalhe</th>
                  </tr>
                </thead>
                <tbody>
                  {filtrados.map((row, i) => {
                    const a = row.audit;
                    const badApps = a.apps_detalhe?.filter((x) => !x.ok) || [];
                    return (
                      <tr key={i} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30">
                        <td className="py-3 px-4">
                          <span className="font-medium text-gray-900 dark:text-white">{a.nome}</span>
                          <p className="text-xs text-gray-500 dark:text-gray-400 font-mono">{a.slug}</p>
                        </td>
                        <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{a.tipo_slug}</td>
                        <td className="py-3 px-4 text-center">
                          {(a.tabelas_total ?? 0) > 0 ? (
                            <span className="text-blue-600 dark:text-blue-400">
                              {a.tabelas_total} <span className="text-xs text-gray-500">({a.tabelas_negocio ?? 0} negócio)</span>
                            </span>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-center">
                          {row.ok_final ? (
                            <CheckCircle size={18} className="text-green-500 mx-auto" />
                          ) : (
                            <XCircle size={18} className="text-red-500 mx-auto" />
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex gap-1 flex-wrap">
                            {a.apps_detalhe?.map((app) => (
                              <span
                                key={app.app}
                                className={`text-xs px-1.5 py-0.5 rounded ${
                                  app.ok
                                    ? 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400'
                                    : 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400'
                                }`}
                              >
                                {app.app}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-xs text-gray-600 dark:text-gray-400 max-w-xs break-words">
                          {a.erro && <span className="text-red-500">{a.erro}</span>}
                          {badApps.length > 0 && !a.erro && (
                            <span className="text-red-500">Apps com falha: {badApps.map((x) => x.app).join(', ')}</span>
                          )}
                          {row.correcao?.mensagem && (
                            <span className={row.correcao.sucesso ? 'text-green-600' : 'text-amber-600'}>
                              {' '}— {row.correcao.mensagem}
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Estado vazio */}
        {!loading && !result && (
          <div className="text-center py-16 bg-white dark:bg-gray-800 rounded-lg shadow">
            <Database size={48} className="mx-auto mb-4 text-gray-300 dark:text-gray-600" />
            <p className="text-gray-500 dark:text-gray-400">Clique em &quot;Verificar schemas&quot; para iniciar a auditoria</p>
          </div>
        )}
      </div>
    </div>
  );
}
