/**
 * Componente de Filtros para Produtos e Serviços.
 * 
 * Responsabilidade única: Renderizar filtros de busca.
 */
import { Plus, FolderOpen } from 'lucide-react';
import { Categoria } from '@/hooks/useProdutosServicos';

interface ProdutoServicoFiltersProps {
  filtroCategoria: string;
  filtroTipo: string;
  categorias: Categoria[];
  onCategoriaChange: (value: string) => void;
  onTipoChange: (value: string) => void;
  onNovoClick: () => void;
  onGerenciarCategoriasClick?: () => void;
}

export function ProdutoServicoFilters({
  filtroCategoria,
  filtroTipo,
  categorias,
  onCategoriaChange,
  onTipoChange,
  onNovoClick,
  onGerenciarCategoriasClick,
}: ProdutoServicoFiltersProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Cadastrar Serviço e Produto
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Produtos e serviços disponíveis para incluir em novas oportunidades
        </p>
      </div>
      <div className="flex gap-2">
        <select
          value={filtroCategoria}
          onChange={(e) => onCategoriaChange(e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
        >
          <option value="">Todas categorias</option>
          {categorias.map((cat) => (
            <option key={cat.id} value={cat.id}>
              {cat.nome}
            </option>
          ))}
        </select>
        <select
          value={filtroTipo}
          onChange={(e) => onTipoChange(e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
        >
          <option value="">Todos tipos</option>
          <option value="produto">Produtos</option>
          <option value="servico">Serviços</option>
        </select>
        {onGerenciarCategoriasClick && (
          <button
            type="button"
            onClick={onGerenciarCategoriasClick}
            className="flex items-center gap-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm font-medium transition-colors shadow-sm"
            title="Gerenciar Categorias"
          >
            <FolderOpen size={18} />
            <span className="hidden sm:inline">Categorias</span>
          </button>
        )}
        <button
          type="button"
          onClick={onNovoClick}
          className="flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded text-sm font-medium transition-colors shadow-sm"
        >
          <Plus size={18} />
          <span>Novo</span>
        </button>
      </div>
    </div>
  );
}
