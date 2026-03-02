/**
 * Componente de tabela de logs
 * ✅ REFATORADO v777: Extraído da página de logs
 */
import { formatDateTime } from '@/lib/financeiro-helpers';
import type { Log } from '@/hooks/useLogsList';

interface LogTableProps {
  logs: Log[];
  loading: boolean;
  searchQuery?: string;
  onVerDetalhes: (log: Log) => void;
}

export function LogTable({ logs, loading, searchQuery, onVerDetalhes }: LogTableProps) {
  const highlightText = (text: string | null | undefined, query?: string) => {
    if (!text) return text || '';
    if (!query) return text;
    
    try {
      const parts = text.split(new RegExp(`(${query})`, 'gi'));
      return parts.map((part, i) => 
        part.toLowerCase() === query.toLowerCase() 
          ? <mark key={i} className="bg-yellow-200 dark:bg-yellow-600">{part}</mark>
          : part
      );
    } catch (error) {
      console.error('Erro ao destacar texto:', error);
      return text;
    }
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-8 text-center text-gray-500 dark:text-gray-400">
          Carregando...
        </div>
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-8 text-center text-gray-500 dark:text-gray-400">
          Nenhum log encontrado. Use os filtros acima para buscar.
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
      <div className="p-4 border-b dark:border-gray-700">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          Resultados ({logs.length})
        </h2>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Data/Hora</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Usuário</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Loja</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Ação</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Recurso</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">IP</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {logs.map((log) => (
              <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                  {formatDateTime(log.created_at)}
                </td>
                <td className="px-4 py-3 text-sm">
                  <div className="font-medium text-gray-900 dark:text-gray-100">{highlightText(log.usuario_nome, searchQuery)}</div>
                  <div className="text-gray-500 dark:text-gray-400 text-xs">{highlightText(log.usuario_email, searchQuery)}</div>
                </td>
                <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                  {highlightText(log.loja_nome, searchQuery)}
                </td>
                <td className="px-4 py-3 text-sm">
                  <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded text-xs">
                    {highlightText(log.acao, searchQuery)}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                  {highlightText(log.recurso, searchQuery)}
                </td>
                <td className="px-4 py-3 text-sm">
                  <span className={`px-2 py-1 rounded text-xs ${
                    log.sucesso 
                      ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200' 
                      : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                  }`}>
                    {log.sucesso ? '✓ Sucesso' : '✗ Erro'}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                  {log.ip_address}
                </td>
                <td className="px-4 py-3 text-sm">
                  <button
                    onClick={() => onVerDetalhes(log)}
                    className="text-purple-600 dark:text-purple-400 hover:text-purple-800 dark:hover:text-purple-300"
                  >
                    Ver Detalhes
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
