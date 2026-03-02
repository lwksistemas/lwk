/**
 * Modal de detalhes do log com contexto temporal
 * ✅ REFATORADO v777: Extraído da página de logs
 */
import { formatDateTime } from '@/lib/financeiro-helpers';
import type { Log } from '@/hooks/useLogsList';
import type { ContextoTemporal } from '@/hooks/useLogActions';

interface LogDetalhesModalProps {
  log: Log;
  contextoTemporal: ContextoTemporal | null;
  onClose: () => void;
}

export function LogDetalhesModal({ log, contextoTemporal, onClose }: LogDetalhesModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b dark:border-gray-700 flex justify-between items-center sticky top-0 bg-white dark:bg-gray-800">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Detalhes do Log</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 text-2xl"
          >
            ×
          </button>
        </div>

        <div className="p-6">
          {/* Informações Principais */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Data/Hora</label>
              <p className="text-lg text-gray-900 dark:text-gray-100">{formatDateTime(log.created_at)}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Status</label>
              <span className={`inline-block px-3 py-1 rounded text-sm ${
                log.sucesso 
                  ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200' 
                  : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
              }`}>
                {log.sucesso ? '✓ Sucesso' : '✗ Erro'} ({log.status_code})
              </span>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Usuário</label>
              <p className="text-lg text-gray-900 dark:text-gray-100">{log.usuario_nome || 'N/A'}</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">{log.usuario_email || 'N/A'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Loja</label>
              <p className="text-lg text-gray-900 dark:text-gray-100">{log.loja_nome || 'N/A'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Ação</label>
              <p className="text-lg text-gray-900 dark:text-gray-100">{log.acao || 'N/A'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Recurso</label>
              <p className="text-lg text-gray-900 dark:text-gray-100">{log.recurso || 'N/A'}</p>
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">URL</label>
              <p className="text-sm font-mono bg-gray-100 dark:bg-gray-700 p-2 rounded text-gray-900 dark:text-gray-100">
                {log.metodo_http || 'GET'} {log.url || 'N/A'}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">IP Address</label>
              <p className="text-lg text-gray-900 dark:text-gray-100">{log.ip_address || 'N/A'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">User Agent</label>
              <p className="text-sm text-gray-600 dark:text-gray-400 truncate" title={log.user_agent || ''}>
                {log.user_agent || 'N/A'}
              </p>
            </div>
          </div>

          {/* Detalhes JSON */}
          {log.detalhes && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Detalhes</label>
              <pre className="bg-gray-100 dark:bg-gray-700 p-4 rounded text-sm overflow-x-auto text-gray-900 dark:text-gray-100">
                {(() => {
                  try {
                    return JSON.stringify(JSON.parse(log.detalhes), null, 2);
                  } catch (error) {
                    return log.detalhes;
                  }
                })()}
              </pre>
            </div>
          )}

          {/* Contexto Temporal */}
          {contextoTemporal && (
            <div>
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Contexto Temporal</h3>
              
              {/* Logs Anteriores */}
              {contextoTemporal.antes && contextoTemporal.antes.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    ⬆️ Ações Anteriores ({contextoTemporal.antes.length})
                  </h4>
                  <div className="space-y-2">
                    {contextoTemporal.antes.map((logItem) => (
                      <div key={logItem.id} className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded text-sm">
                        <div className="flex justify-between items-start">
                          <div className="text-gray-900 dark:text-gray-100">
                            <span className="font-medium">{logItem.acao || 'N/A'}</span>
                            <span className="text-gray-600 dark:text-gray-400"> - {logItem.recurso || 'N/A'}</span>
                          </div>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {new Date(logItem.created_at).toLocaleTimeString('pt-BR')}
                          </span>
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                          {logItem.usuario_nome || 'N/A'} • {logItem.loja_nome || 'N/A'}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Log Atual */}
              <div className="bg-purple-100 dark:bg-purple-900/20 border-2 border-purple-500 dark:border-purple-400 p-3 rounded mb-4">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">📍</span>
                  <div>
                    <div className="font-semibold text-gray-900 dark:text-gray-100">Log Atual</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {log.acao || 'N/A'} - {log.recurso || 'N/A'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Logs Posteriores */}
              {contextoTemporal.depois && contextoTemporal.depois.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    ⬇️ Ações Posteriores ({contextoTemporal.depois.length})
                  </h4>
                  <div className="space-y-2">
                    {contextoTemporal.depois.map((logItem) => (
                      <div key={logItem.id} className="bg-green-50 dark:bg-green-900/20 p-3 rounded text-sm">
                        <div className="flex justify-between items-start">
                          <div className="text-gray-900 dark:text-gray-100">
                            <span className="font-medium">{logItem.acao || 'N/A'}</span>
                            <span className="text-gray-600 dark:text-gray-400"> - {logItem.recurso || 'N/A'}</span>
                          </div>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {new Date(logItem.created_at).toLocaleTimeString('pt-BR')}
                          </span>
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                          {logItem.usuario_nome || 'N/A'} • {logItem.loja_nome || 'N/A'}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
