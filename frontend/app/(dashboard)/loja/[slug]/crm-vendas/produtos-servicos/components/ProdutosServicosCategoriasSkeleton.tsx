/** Skeleton da grade de categorias (produtos/serviços). */
export function ProdutosServicosCategoriasSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-48 animate-pulse" />
        <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-40 animate-pulse" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div
            key={i}
            className="h-32 rounded-xl bg-gray-100 dark:bg-gray-800 animate-pulse"
          />
        ))}
      </div>
    </div>
  );
}
