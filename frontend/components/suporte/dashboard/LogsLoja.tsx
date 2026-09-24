'use client';
/**
 * LogsLoja — exibe automaticamente os logs da loja ao abrir um chamado.
 * Layout e helpers alinhados ao /superadmin/dashboard/logs para que o suporte
 * veja exatamente as mesmas informações que o superadmin veria.
 */
import { useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import { formatDateTime } from '@/lib/financeiro-helpers';
import {
  classeStatusLog,
  mensagemStatusLog,
  rotuloHttpLog,
  rotuloNavegadorLog,
  tipoResultadoLog,
  tituloStatusLog,
} from '@/lib/log-status';

// ── Tipos ────────────────────────────────────────────────────────────────────

export interface LogLoja {
  id: number;
  usuario_nome: string;
  usuario_email: string;
  loja_nome: string;
  acao: string;
  acao_display: string;
  recurso: string;
  ip_address: string;
  navegador: string;
  sistema_operacional: string;
  metodo_http: string;
  url: string;
  user_agent: string;
  sucesso: boolean;
  erro: string;
  mensagem_status: string;
  tipo_resultado: 'sucesso' | 'recusado' | 'erro';
  detalhes: string;
  created_at: string;
  data_hora: string;
}

// ── Mini-modal de detalhe (estilo superadmin) ─────────────────────────────────

function DetalheModal({ log, onClose }: { log: LogLoja; onClose: () => void }) {
  const tipo = tipoResultadoLog(log);
  const titulo = tituloStatusLog(tipo);
  const mensagem = mensagemStatusLog(log);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white px-5 py-3 border-b flex justify-between items-center">
          <h3 className="text-lg font-bold text-gray-900">Detalhes do log</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700 text-2xl leading-none">×</button>
        </div>

        <div className="p-5 space-y-5">
          {/* Banner resultado */}
          <div className={`rounded-lg px-4 py-3 ${classeStatusLog(tipo)}`}>
            <p className="font-semibold">{titulo}</p>
            <p className="text-sm mt-1">{mensagem}</p>
          </div>

          {/* Grid campos */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500 font-medium mb-0.5">Data/hora</p>
              <p className="text-gray-900">{log.data_hora}</p>
            </div>
            <div>
              <p className="text-gray-500 font-medium mb-0.5">Resultado</p>
              <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${classeStatusLog(tipo)}`}>
                {titulo}
              </span>
            </div>
            <div>
              <p className="text-gray-500 font-medium mb-0.5">Usuário</p>
              <p className="text-gray-900 font-medium">{log.usuario_nome || '—'}</p>
              <p className="text-gray-500 text-xs">{log.usuario_email}</p>
            </div>
            <div>
              <p className="text-gray-500 font-medium mb-0.5">Loja</p>
              <p className="text-gray-900">{log.loja_nome || '—'}</p>
            </div>
            <div>
              <p className="text-gray-500 font-medium mb-0.5">Ação</p>
              <p className="text-gray-900">{log.acao_display || log.acao || '—'}</p>
            </div>
            <div>
              <p className="text-gray-500 font-medium mb-0.5">Recurso</p>
              <p className="text-gray-900">{log.recurso || '—'}</p>
            </div>
            <div className="col-span-2">
              <p className="text-gray-500 font-medium mb-0.5">Requisição</p>
              <p className="font-mono text-xs bg-gray-100 p-2 rounded break-all text-gray-900">
                {rotuloHttpLog(log)}
              </p>
            </div>
            <div>
              <p className="text-gray-500 font-medium mb-0.5">IP</p>
              <p className="text-gray-900">{log.ip_address || '—'}</p>
            </div>
            <div>
              <p className="text-gray-500 font-medium mb-0.5">Navegador</p>
              <p className="text-gray-700 text-sm" title={log.user_agent}>{rotuloNavegadorLog(log)}</p>
            </div>
          </div>

          {/* Detalhes técnicos */}
          {log.detalhes && (
            <div>
              <p className="text-gray-500 font-medium text-sm mb-1">Detalhes técnicos</p>
              <pre className="bg-gray-100 p-3 rounded text-xs overflow-x-auto text-gray-900 whitespace-pre-wrap break-words">
                {(() => {
                  try { return JSON.stringify(JSON.parse(log.detalhes), null, 2); }
                  catch { return log.detalhes; }
                })()}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Linha da tabela ────────────────────────────────────────────────────────────

function LinhaLog({ log, onClick }: { log: LogLoja; onClick: () => void }) {
  const tipo = tipoResultadoLog(log);
  const titulo = tituloStatusLog(tipo);
  const mensagem = mensagemStatusLog(log);

  return (
    <tr
      className="hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-0"
      onClick={onClick}
    >
      <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500">{log.data_hora}</td>
      <td className="px-3 py-2 text-xs">
        <span className="font-medium text-gray-900">{log.usuario_nome || '—'}</span>
        {log.usuario_email && (
          <span className="text-gray-400 block text-[10px]">{log.usuario_email}</span>
        )}
      </td>
      <td className="px-3 py-2 text-xs text-gray-700">{log.acao_display || log.acao}</td>
      <td className="px-3 py-2 text-xs text-gray-600 max-w-[220px] truncate font-mono"
          title={rotuloHttpLog(log)}>
        {rotuloHttpLog(log)}
      </td>
      <td className="px-3 py-2 text-xs text-gray-600 max-w-[180px]">
        <span className="truncate block" title={mensagem}>{mensagem}</span>
      </td>
      <td className="px-3 py-2 whitespace-nowrap">
        <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-medium ${classeStatusLog(tipo)}`}>
          {titulo}
        </span>
      </td>
      <td className="px-3 py-2 text-xs text-gray-500 whitespace-nowrap">{rotuloNavegadorLog(log)}</td>
    </tr>
  );
}

// ── Componente principal ───────────────────────────────────────────────────────

interface LogsLojaProps {
  chamadoId: number;
}

export function LogsLoja({ chamadoId }: LogsLojaProps) {
  const [logs, setLogs] = useState<LogLoja[]>([]);
  const [periodo, setPeriodo] = useState('');
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');
  const [logDetalhe, setLogDetalhe] = useState<LogLoja | null>(null);
  const [filtro, setFiltro] = useState<'todos' | 'erro' | 'sucesso'>('todos');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setErro('');
    apiClient
      .get(`/suporte/chamados/${chamadoId}/logs-loja/`)
      .then((res) => {
        if (cancelled) return;
        setLogs(res.data.logs ?? []);
        setPeriodo(res.data.periodo ?? '');
      })
      .catch(() => {
        if (!cancelled) setErro('Não foi possível carregar os logs da loja.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [chamadoId]);

  const logsFiltrados = logs.filter((l) => {
    if (filtro === 'erro') return !l.sucesso;
    if (filtro === 'sucesso') return l.sucesso;
    return true;
  });

  const totalErros   = logs.filter((l) => !l.sucesso).length;
  const totalSucesso = logs.filter((l) =>  l.sucesso).length;

  return (
    <div className="mb-4">
      {/* Cabeçalho */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <span className="text-sm font-semibold text-gray-800">📋 Logs da loja</span>
          {periodo && <span className="ml-2 text-xs text-gray-400">{periodo}</span>}
        </div>
        {/* Filtros rápidos */}
        {!loading && !erro && (
          <div className="flex gap-1">
            {(['todos', 'erro', 'sucesso'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFiltro(f)}
                className={`px-2 py-0.5 text-xs rounded border transition-colors ${
                  filtro === f
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400'
                }`}
              >
                {f === 'todos' ? `Todos (${logs.length})` : f === 'erro' ? `❌ Erros (${totalErros})` : `✅ Sucesso (${totalSucesso})`}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Conteúdo */}
      {loading ? (
        <p className="text-xs text-gray-400 py-3">Carregando logs…</p>
      ) : erro ? (
        <p className="text-xs text-red-500 py-2">{erro}</p>
      ) : logsFiltrados.length === 0 ? (
        <p className="text-xs text-gray-400 py-2">Nenhum log encontrado neste período.</p>
      ) : (
        <div className="rounded-lg border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto max-h-[38vh] overflow-y-auto">
            <table className="min-w-full text-left">
              <thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
                <tr>
                  {['Data/hora', 'Usuário', 'Ação', 'Requisição', 'Mensagem', 'Resultado', 'Navegador'].map((h) => (
                    <th key={h} className="px-3 py-2 text-[11px] font-semibold text-gray-500 uppercase whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white">
                {logsFiltrados.map((log) => (
                  <LinhaLog key={log.id} log={log} onClick={() => setLogDetalhe(log)} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Mini-modal de detalhe */}
      {logDetalhe && <DetalheModal log={logDetalhe} onClose={() => setLogDetalhe(null)} />}
    </div>
  );
}
