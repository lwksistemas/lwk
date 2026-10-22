/**
 * Grade inicial: categorias cadastradas; clique abre a lista filtrada.
 */
import { FolderOpen, Package, Layers, Trash2 } from 'lucide-react';
import { Categoria } from '@/hooks/useProdutosServicos';

interface CategoriasProdutosGridProps {
  categorias: Categoria[];
  countSemCategoria: number | null;
  pastaId?: number | null;
  onSelectCategoria: (id: number) => void;
  onSelectSemCategoria: () => void;
  onVerTodos: () => void;
  onExcluirCategoria: (categoria: Categoria) => void;
}

function totalNaPasta(cat: Categoria, todas: Categoria[]): number {
  const filhos = todas.filter((outra) => outra.pai === cat.id);
  return (cat.produtos_count ?? 0) + filhos.reduce((soma, filho) => soma + totalNaPasta(filho, todas), 0);
}

function ordenarCategorias(cats: Categoria[]): Categoria[] {
  return [...cats].sort((a, b) => (a.ordem ?? 0) - (b.ordem ?? 0) || a.nome.localeCompare(b.nome));
}

export function CategoriasProdutosGrid({
  categorias,
  countSemCategoria,
  pastaId = null,
  onSelectCategoria,
  onSelectSemCategoria,
  onVerTodos,
  onExcluirCategoria,
}: CategoriasProdutosGridProps) {
  const ordenadas = ordenarCategorias(categorias).filter((cat) => {
    const nestaPasta = pastaId ? cat.pai === pastaId : !cat.pai;
    if (!nestaPasta) return false;
    if (pastaId) return totalNaPasta(cat, categorias) > 0;
    return true;
  });

  return (
    <div className="space-y-6">
      {!pastaId && (
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={onVerTodos}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border-2 border-dashed border-[#0176d3] text-[#0176d3] hover:bg-blue-50 dark:hover:bg-blue-950/30 text-sm font-medium transition-colors"
        >
          <Layers className="w-5 h-5" aria-hidden />
          Ver todos os produtos e serviços
        </button>
      </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {ordenadas.map((cat) => {
          const total = totalNaPasta(cat, categorias);
          return (
          <div
            key={cat.id}
            className="relative text-left rounded-xl border border-gray-200 dark:border-[#0d1f3c] bg-white dark:bg-[#16325c] shadow-sm hover:shadow-md hover:border-[#0176d3]/50 transition-all group"
          >
            <button
              type="button"
              onClick={() => onSelectCategoria(cat.id)}
              className="w-full text-left p-5 pr-12"
            >
            <div className="flex items-start gap-3">
              <span
                className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg text-white shadow-inner"
                style={{ backgroundColor: cat.cor || '#6B7280' }}
              >
                <FolderOpen className="w-6 h-6 opacity-90" aria-hidden />
              </span>
              <div className="min-w-0 flex-1">
                <h3 className="font-semibold text-gray-900 dark:text-white group-hover:text-[#0176d3] dark:group-hover:text-blue-300 transition-colors truncate">
                  {cat.nome}
                </h3>
                {cat.descricao ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 mt-1">{cat.descricao}</p>
                ) : null}
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                  {typeof cat.produtos_count === 'number' ? (
                    <>
                      <Package className="inline w-3.5 h-3.5 mr-1 -mt-0.5" aria-hidden />
                      {total} {total === 1 ? 'item' : 'itens'}
                    </>
                  ) : (
                    'Toque para ver itens'
                  )}
                </p>
              </div>
            </div>
            </button>
            <button
              type="button"
              onClick={() => onExcluirCategoria(cat)}
              className="absolute top-3 right-3 p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
              aria-label={`Excluir ${cat.nome}`}
              title="Excluir categoria"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
          );
        })}

        {!pastaId && countSemCategoria !== null && countSemCategoria > 0 && (
          <button
            type="button"
            onClick={onSelectSemCategoria}
            className="text-left rounded-xl border border-amber-200 dark:border-amber-900/50 bg-amber-50/80 dark:bg-amber-950/20 p-5 shadow-sm hover:shadow-md transition-all"
          >
            <div className="flex items-start gap-3">
              <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-amber-200 dark:bg-amber-900/40 text-amber-900 dark:text-amber-100">
                <Package className="w-6 h-6" aria-hidden />
              </span>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">Sem categoria</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Produtos ou serviços ainda sem classificação
                </p>
                <p className="text-xs text-amber-800 dark:text-amber-200/80 mt-2">
                  {countSemCategoria} {countSemCategoria === 1 ? 'item' : 'itens'}
                </p>
              </div>
            </div>
          </button>
        )}
      </div>

      {ordenadas.length === 0 && (countSemCategoria === 0 || countSemCategoria === null) && (
        <div className="rounded-xl border border-dashed border-gray-300 dark:border-gray-600 p-10 text-center text-gray-500 dark:text-gray-400">
          <FolderOpen className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p className="font-medium">Nenhuma categoria cadastrada</p>
          <p className="text-sm mt-1">Use &quot;Categorias&quot; para criar ou cadastre itens em &quot;Ver todos&quot;.</p>
        </div>
      )}
    </div>
  );
}
