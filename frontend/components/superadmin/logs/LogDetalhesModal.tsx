/**
 * Modal de detalhes do log com contexto temporal
 */
import { formatDateTime } from '@/lib/financeiro-helpers';
import {
  classeStatusLog,
  mensagemStatusLog,
  rotuloHttpLog,
  rotuloNavegadorLog,
  tipoResultadoLog,
  tituloStatusLog,
} from '@/lib/log-status';
import type { Log } from '@/hooks/useLogsList';
import type { ContextoTemporal } from '@/hooks/useLogActions';

interface LogDetalhesModalProps {
  log: Log;
  contextoTemporal: ContextoTemporal | null;
  onClose: () => void;
}

function linhaContexto(item: Log) {
  const tipo = tipoResultadoLog(item);
  const acao = item.acao_display || item.acao || 'Ação';
  const recurso = item.recurso || '';
  return (
    <div key={item.id} className="p-3 rounded text-sm bg-gray-50 dark:bg-gray-700/40">
      <div className="flex justify-between items-start gap-3">
        <div className="text-gray-900 dark:text-gray-100">
          <span className="font-medium">{acao}</span>
          {recurso ? <span className="text-gray-600 dark:text-gray-400"> — {recurso}</span> : null}
        </div>
        <span className={`shrink-0 px-2 py-0.5 rounded text-xs ${classeStatusLog(tipo)}`}>
          {tituloStatusLog(tipo)}
        </span>
      </div>
      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{mensagemStatusLog(item)}</p>
      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
        {item.usuario_nome || 'Usuário não identificado'}
        {item.loja_nome ? ` • ${item.loja_nome}` : ''}
        {' • '}
        {new Date(item.created_at).toLocaleTimeString('pt-BR')}
      </div>
    </div>
  );
}

export function LogDetalhesModal({ log, contextoTemporal, onClose }: LogDetalhesModalProps) {
  const tipo = tipoResultadoLog(log);
  const titulo = tituloStatusLog(tipo);
  const mensagem = mensagemStatusLog(log);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b dark:border-gray-700 flex justify-between items-center sticky top-0 bg-white dark:bg-gray-800">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Detalhes do log</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 text-2xl"
            aria-label="Fechar"
          >
            ×
          </button>
        </div>

        <div className="p-6">
          <div className={`mb-6 rounded-lg px-4 py-3 ${classeStatusLog(tipo)}`}>
            <p className="font-semibold">{titulo}</p>
            <p className="text-sm mt-1">{mensagem}</p>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Data/hora</label>
              <p className="text-lg text-gray-900 dark:text-gray-100">{formatDateTime(log.created_at)}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Resultado</label>
              <span className={`inline-block px-3 py-1 rounded text-sm ${classeStatusLog(tipo)}`}>
                {titulo}
              </span>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Usuário</label>
              <p className="text-lg text-gray-900 dark:text-gray-100">{log.usuario_nome || 'Não identificado'}</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">{log.usuario_email || 'E-mail não informado'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Loja</label>
              <p className="text-lg text-gray-900 dark:text-gray-100">{log.loja_nome || 'Fora de loja (superadmin)'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Ação</label>
              <p className="text-lg text-gray-900 dark:text-gray-100">{log.acao_display || log.acao || 'Não informada'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Recurso</label>
              <p className="text-lg text-gray-900 dark:text-gray-100">{log.recurso || 'Não informado'}</p>
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Requisição</label>
              <p className="text-sm font-mono bg-gray-100 dark:bg-gray-700 p-2 rounded text-gray-900 dark:text-gray-100 break-all">
                {rotuloHttpLog(log)}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">IP</label>
              <p className="text-lg text-gray-900 dark:text-gray-100">{log.ip_address || 'Não informado'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Navegador</label>
              <p className="text-sm text-gray-700 dark:text-gray-300" title={log.user_agent || ''}>
                {rotuloNavegadorLog(log)}
              </p>
            </div>
          </div>

          {log.detalhes ? (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Detalhes técnicos</label>
              <pre className="bg-gray-100 dark:bg-gray-700 p-4 rounded text-sm overflow-x-auto text-gray-900 dark:text-gray-100">
                {(() => {
                  try {
                    return JSON.stringify(JSON.parse(log.detalhes), null, 2);
                  } catch {
                    return log.detalhes;
                  }
                })()}
              </pre>
            </div>
          ) : null}

          {contextoTemporal && (
            <div>
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Antes e depois</h3>

              {contextoTemporal.antes.length > 0 ? (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Ações anteriores ({contextoTemporal.antes.length})
                  </h4>
                  <div className="space-y-2">{contextoTemporal.antes.map(linhaContexto)}</div>
                </div>
              ) : null}

              <div className="border-2 border-purple-500 dark:border-purple-400 p-3 rounded mb-4 bg-purple-50 dark:bg-purple-900/20">
                <div className="font-semibold text-gray-900 dark:text-gray-100">Este registro</div>
                <div className="text-sm text-gray-700 dark:text-gray-300 mt-1">{mensagem}</div>
              </div>

              {contextoTemporal.depois.length > 0 ? (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Ações seguintes ({contextoTemporal.depois.length})
                  </h4>
                  <div className="space-y-2">{contextoTemporal.depois.map(linhaContexto)}</div>
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
