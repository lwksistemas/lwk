"use client";

import { FileUp, Package } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { ClinicaBelezaRelatedLinks } from "@/components/clinica-beleza/ClinicaBelezaRelatedLinks";
import { EstoqueFilters } from "@/components/clinica-beleza/estoque/EstoqueFilters";
import { EstoqueHistoricoModal } from "@/components/clinica-beleza/estoque/EstoqueHistoricoModal";
import { EstoqueMovimentacaoModal } from "@/components/clinica-beleza/estoque/EstoqueMovimentacaoModal";
import { EstoqueProdutoModal } from "@/components/clinica-beleza/estoque/EstoqueProdutoModal";
import { EstoqueProdutosTable } from "@/components/clinica-beleza/estoque/EstoqueProdutosTable";
import { EstoqueResumoCards } from "@/components/clinica-beleza/estoque/EstoqueResumoCards";
import { EstoqueImportarXmlModal } from "@/components/clinica-beleza/EstoqueImportarXmlModal";
import { useEstoquePage } from "@/hooks/clinica-beleza/useEstoquePage";

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

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={title}
        subtitle={subtitle}
        backHref={backHref}
        icon={Package}
        newLabel="Novo Produto"
        onNew={page.abrirNovoProduto}
        extraActions={
          <button
            type="button"
            onClick={() => page.setShowImportXmlModal(true)}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs sm:text-sm font-medium rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700"
          >
            <FileUp size={16} />
            <span className="hidden sm:inline">Importar XML</span>
          </button>
        }
      />
      <ClinicaBelezaPageContent>
        {page.loading && !page.resumo ? (
          <div className="flex justify-center py-12">
            <div className="w-10 h-10 border-4 border-purple-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <>
            <EstoqueResumoCards resumo={page.resumo} />
            <EstoqueFilters
              categoriaFilter={page.categoriaFilter}
              searchTerm={page.searchTerm}
              onSearchChange={page.setSearchTerm}
              onCategoriaChange={page.setCategoriaFilterAndUrl}
            />
            {page.listError && (
              <div className="mb-4 px-4 py-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300">
                Erro ao carregar produtos: {page.listError}
              </div>
            )}
            <EstoqueProdutosTable
              produtos={page.produtos}
              resumo={page.resumo}
              onHistorico={page.abrirHistorico}
              onEditar={page.abrirEditarProduto}
              onEntrada={(p) => page.abrirMovimentacao(p, "entrada")}
              onSaida={(p) => page.abrirMovimentacao(p, "saida")}
              onExcluir={page.handleExcluirProduto}
            />
          </>
        )}
        <ClinicaBelezaRelatedLinks slug={page.slug} items={relatedLinks} />
      </ClinicaBelezaPageContent>

      {page.showProdutoModal && (
        <EstoqueProdutoModal
          key={page.editingProduto?.id ?? "new"}
          produto={page.editingProduto}
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
