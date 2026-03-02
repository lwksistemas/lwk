/**
 * Componente de filtros de busca de logs
 * ✅ REFATORADO v777: Extraído da página de logs
 */
import type { FiltrosBusca, BuscaSalva } from '@/hooks/useLogsList';

interface LogFiltersProps {
  filtros: FiltrosBusca;
  setFiltros: (filtros: FiltrosBusca) => void;
  onBuscar: () => void;
  onLimpar: () => void;
  onExportarCSV: () => void;
  onExportarJSON: () => void;
  onSalvarBusca: () => void;
  buscasSalvas: BuscaSalva[];
  onCarregarBusca: (busca: BuscaSalva) => void;
  onExcluirBusca: (index: number) => void;
  loading: boolean;
  hasResults: boolean;
}

export function LogFilters({
  filtros,
  setFiltros,
  onBuscar,
  onLimpar,
  onExportarCSV,
  onExportarJSON,
  onSalvarBusca,
  buscasSalvas,
  onCarregarBusca,
  onExcluirBusca,
  loading,
  hasResults
}: LogFiltersProps) {
  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow mb-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Filtros de Busca</h2>
        <div className="flex gap-2">
          <button
            onClick={onSalvarBusca}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
          >
            💾 Salvar Busca
          </button>
          {buscasSalvas.length > 0 && (
            <div className="relative group">
              <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
                📋 Buscas Salvas ({buscasSalvas.length})
              </button>
              <div className="hidden group-hover:block absolute right-0 mt-2 w-64 bg-white dark:bg-gray-700 rounded-lg shadow-xl z-10 max-h-96 overflow-y-auto">
                {buscasSalvas.map((busca, index) => (
                  <div key={index} className="p-3 hover:bg-gray-50 dark:hover:bg-gray-600 border-b dark:border-gray-600 flex justify-between items-center">
                    <button
                      onClick={() => onCarregarBusca(busca)}
                      className="text-left flex-1"
                    >
                      <div className="font-medium text-gray-900 dark:text-gray-100">{busca.nome}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {Object.keys(busca.filtros).length} filtros
                      </div>
                    </button>
                    <button
                      onClick={() => onExcluirBusca(index)}
                      className="text-red-600 hover:text-red-800 ml-2"
                    >
                      🗑️
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Busca por Texto
          </label>
          <input
            type="text"
            value={filtros.q || ''}
            onChange={(e) => setFiltros({ ...filtros, q: e.target.value })}
            placeholder="Buscar em todos os campos..."
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Data Início
          </label>
          <input
            type="date"
            value={filtros.data_inicio || ''}
            onChange={(e) => setFiltros({ ...filtros, data_inicio: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Data Fim
          </label>
          <input
            type="date"
            value={filtros.data_fim || ''}
            onChange={(e) => setFiltros({ ...filtros, data_fim: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Loja
          </label>
          <input
            type="text"
            value={filtros.loja_nome || ''}
            onChange={(e) => setFiltros({ ...filtros, loja_nome: e.target.value })}
            placeholder="Nome da loja..."
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Email do Usuário
          </label>
          <input
            type="text"
            value={filtros.usuario_email || ''}
            onChange={(e) => setFiltros({ ...filtros, usuario_email: e.target.value })}
            placeholder="email@exemplo.com"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Ação
          </label>
          <input
            type="text"
            value={filtros.acao || ''}
            onChange={(e) => setFiltros({ ...filtros, acao: e.target.value })}
            placeholder="Ex: login, criar, editar..."
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Status
          </label>
          <select
            value={filtros.sucesso || ''}
            onChange={(e) => setFiltros({ ...filtros, sucesso: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          >
            <option value="">Todos</option>
            <option value="true">Sucesso</option>
            <option value="false">Erro</option>
          </select>
        </div>
      </div>

      <div className="flex gap-2 flex-wrap">
        <button
          onClick={onBuscar}
          disabled={loading}
          className="px-6 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-400 transition-colors"
        >
          {loading ? 'Buscando...' : '🔍 Buscar'}
        </button>
        <button
          onClick={onLimpar}
          className="px-6 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
        >
          🔄 Limpar
        </button>
        <button
          onClick={onExportarCSV}
          disabled={!hasResults}
          className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400 transition-colors"
        >
          📥 CSV
        </button>
        <button
          onClick={onExportarJSON}
          disabled={!hasResults}
          className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
        >
          📥 JSON
        </button>
      </div>
    </div>
  );
}
