"use client";

import { ArrowLeft, FileUp, Package, Settings2 } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { ClinicaBelezaRelatedLinks } from "@/components/clinica-beleza/ClinicaBelezaRelatedLinks";
import { EstoqueCategoriasGrid } from "@/components/clinica-beleza/estoque/EstoqueCategoriasGrid";
import { EstoqueCategoriasModal } from "@/components/clinica-beleza/estoque/EstoqueCategoriasModal";
import { EstoqueFilters } from "@/components/clinica-beleza/estoque/EstoqueFilters";
import { EstoqueHistoricoModal } from "@/components/clinica-beleza/estoque/EstoqueHistoricoModal";
import { EstoqueMovimentacaoModal } from "@/components/clinica-beleza/estoque/EstoqueMovimentacaoModal";
import { EstoqueProdutoModal } from "@/components/clinica-beleza/estoque/EstoqueProdutoModal";
import { EstoqueProdutosTable } from "@/components/clinica-beleza/estoque/EstoqueProdutosTable";
import { EstoqueResumoCards } from "@/components/clinica-beleza/estoque/EstoqueResumoCards";
import { EstoqueImportarXmlModal } from "@/components/clinica-beleza/estoque/EstoqueImportarXmlModal";
import { useEstoquePage } from "@/hooks/clinica-beleza/useEstoquePage";
import { useEstoqueColunas } from "@/hooks/clinica-beleza/useEstoqueColunas";

export interface EstoquePageContentProps {
  title?: string;
  subtitle?: string;
  defaultCategoria?: string;
  backHref?: string;
  relatedLinks?: { label: string; href: string }[];
}

export function EstoquePageContent({
  title = "Estoque",
  subtitle = "Produtos, insumos e movimentações da clínica",
  defaultCategoria = "",
  backHref,
  relatedLinks = [],
}: EstoquePageContentProps) {
  const page = useEstoquePage({ defaultCategoria });
  const { colunasKeys } = useEstoqueColunas();
  const emLista = page.viewMode === "lista";

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={title}
        subtitle={
          emLista && page.categoriaAtual
            ? `${subtitle} · ${page.categoriaAtual.nome}`
            : subtitle
        }
        backHref={backHref}
        icon={Package}
        newLabel="Novo Produto"
        onNew={page.abrirNovoProduto}
        extraActions={
          <div className="flex items-center gap-1.5">
            {emLista && (
              <button
                type="button"
                onClick={page.voltarCategorias}
                className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs sm:text-sm font-medium rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700"
              >
                <ArrowLeft size={16} />
                <span className="hidden sm:inline">Categorias</span>
              </button>
            )}
            <button
              type="button"
              onClick={() => page.setShowCategoriasModal(true)}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs sm:text-sm font-medium rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700"
            >
              <Settings2 size={16} />
              <span className="hidden sm:inline">Categorias</span>
            </button>
            <button
              type="button"
              onClick={() => page.setShowImportXmlModal(true)}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs sm:text-sm font-medium rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700"
            >
              <FileUp size={16} />
              <span className="hidden sm:inline">Importar XML</span>
            </button>
          </div>
        }
      />
      <ClinicaBelezaPageContent>
        {page.loading && !page.resumo && page.viewMode === "categorias" ? (
          <div className="flex justify-center py-12">
            <div
              className="w-10 h-10 border-4 border-t-transparent rounded-full animate-spin"
              style={{ borderColor: "var(--cb-primary, #8B3D52)", borderTopColor: "transparent" }}
            />
          </div>
        ) : (
          <>
            <EstoqueResumoCards resumo={page.resumo} />
            {page.viewMode === "categorias" ? (
              <EstoqueCategoriasGrid
                categorias={page.categorias}
                loading={page.loadingCategorias}
                totalProdutos={page.resumo?.total_produtos}
                onSelect={page.selecionarCategoria}
                onVerTodos={page.verTodos}
                onGerenciar={() => page.setShowCategoriasModal(true)}
              />
            ) : (
              <>
                <EstoqueFilters
                  categoriaFilter={page.categoriaFilter}
                  searchTerm={page.searchTerm}
                  onSearchChange={page.setSearchTerm}
                  onCategoriaChange={page.setCategoriaFilterAndUrl}
                  categorias={page.categorias}
                />
                {page.listError && (
                  <div className="mb-4 px-4 py-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300">
                    Erro ao carregar produtos: {page.listError}
                  </div>
                )}
                <EstoqueProdutosTable
                  produtos={page.produtos}
                  resumo={page.resumo}
                  categorias={page.categorias}
                  onHistorico={page.abrirHistorico}
                  onEditar={page.abrirEditarProduto}
                  onEntrada={(p) => page.abrirMovimentacao(p, "entrada")}
                  onSaida={(p) => page.abrirMovimentacao(p, "saida")}
                  onExcluir={page.handleExcluirProduto}
                  onMover={page.moverProduto}
                  colunasVisiveis={colunasKeys}
                />
              </>
            )}
          </>
        )}
        <ClinicaBelezaRelatedLinks slug={page.slug} items={relatedLinks} />
      </ClinicaBelezaPageContent>

      {page.showProdutoModal && (
        <EstoqueProdutoModal
          key={page.editingProduto?.id ?? "new"}
          produto={page.editingProduto}
          categorias={page.categorias}
          defaultCategoriaSlug={page.categoriaFilter || undefined}
          saving={page.saving}
          saveError={page.saveError}
          onClose={page.fecharProdutoModal}
          onSave={page.salvarProduto}
        />
      )}
      {page.showMovModal && page.movProduto && (
        <EstoqueMovimentacaoModal
          key={`${page.movProduto.id}-${page.movTipo}`}
          produto={page.movProduto}
          tipo={page.movTipo}
          saving={page.saving}
          onClose={page.fecharMovModal}
          onSubmit={page.registrarMovimentacao}
        />
      )}
      <EstoqueImportarXmlModal
        open={page.showImportXmlModal}
        onClose={() => page.setShowImportXmlModal(false)}
        onSuccess={page.loadAll}
        categorias={page.categorias}
        defaultCategoriaSlug={page.categoriaFilter || undefined}
      />
      <EstoqueCategoriasModal
        open={page.showCategoriasModal}
        onClose={() => page.setShowCategoriasModal(false)}
        onChanged={() => void page.loadAll()}
        lojaCtx={page.lojaCtx}
      />
      {page.showHistoricoModal && page.historicoProduto && (
        <EstoqueHistoricoModal
          produto={page.historicoProduto}
          historico={page.historicoData}
          onClose={() => page.setShowHistoricoModal(false)}
        />
      )}
    </>
  );
}
