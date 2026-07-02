/**
 * Página de Produtos e Serviços — grade de categorias e lista filtrada.
 */
'use client';

import SkeletonTable from '@/components/crm-vendas/SkeletonTable';
import CrmPaginationBar from '@/components/crm-vendas/CrmPaginationBar';
import { useCrmProdutosServicosPage } from '@/hooks/crm-vendas/useCrmProdutosServicosPage';
import { ProdutoServicoFilters } from './components/ProdutoServicoFilters';
import { ProdutoServicoTable } from './components/ProdutoServicoTable';
import { ProdutoServicoModal } from './components/ProdutoServicoModal';
import { CategoriasModal } from './components/CategoriasModal';
import { CategoriasProdutosGrid } from './components/CategoriasProdutosGrid';
import { ProdutosServicosCategoriasSkeleton } from './components/ProdutosServicosCategoriasSkeleton';

export default function CrmVendasProdutosServicosPage() {
  const p = useCrmProdutosServicosPage();

  if (p.viewMode === 'categorias' && p.loadingCategorias) {
    return <ProdutosServicosCategoriasSkeleton />;
  }

  return (
    <div className="space-y-4">
      <ProdutoServicoFilters
        variant={p.viewMode === 'categorias' ? 'grid' : 'lista'}
        filtroCategoria={p.filtroCategoria}
        filtroTipo={p.filtroTipo}
        categorias={p.categorias}
        onCategoriaChange={p.setFiltroCategoria}
        onTipoChange={p.setFiltroTipo}
        onNovoClick={() => p.openModal('create')}
        onGerenciarCategoriasClick={() => p.setModalCategoriasAberto(true)}
        onVoltarCategorias={p.voltarCategorias}
        subtituloLista={p.subtituloLista}
      />

      {p.error && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">
          {p.error}
        </div>
      )}

      {p.viewMode === 'categorias' ? (
        <CategoriasProdutosGrid
          categorias={p.categorias}
          countSemCategoria={p.countSemCategoria}
          onSelectCategoria={p.irParaCategoria}
          onSelectSemCategoria={p.irSemCategoria}
          onVerTodos={p.irVerTodos}
        />
      ) : p.loadingItens ? (
        <SkeletonTable rows={5} columns={5} />
      ) : (
        <>
          <ProdutoServicoTable
            itens={p.itens}
            onView={(item) => p.openModal('view', item)}
            onEdit={(item) => p.openModal('edit', item)}
            onDelete={(item) => p.openModal('delete', item)}
          />
          <CrmPaginationBar
            page={p.page}
            totalPages={p.totalPages}
            totalCount={p.totalCount}
            pageSize={p.pageSize}
            loading={p.loadingItens}
            itemLabel="itens"
            onPageChange={p.setPage}
          />
        </>
      )}

      <ProdutoServicoModal
        modalType={p.modalType}
        selected={p.selected}
        formData={p.formData}
        categorias={p.categorias}
        submitting={p.submitting}
        onClose={p.closeModal}
        onFormChange={p.handleFormChange}
        onSubmit={p.handleSubmit}
        onDelete={p.handleDelete}
      />

      <CategoriasModal
        isOpen={p.modalCategoriasAberto}
        categorias={p.categorias}
        onClose={() => p.setModalCategoriasAberto(false)}
        onCriar={p.criarCategoria}
        onEditar={p.atualizarCategoria}
        onExcluir={p.deletarCategoria}
      />
    </div>
  );
}
