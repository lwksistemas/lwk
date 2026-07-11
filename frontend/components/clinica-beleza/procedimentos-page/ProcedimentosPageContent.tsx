"use client";

import { ArrowLeft, Stethoscope } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaRelatedLinks } from "@/components/clinica-beleza/ClinicaBelezaRelatedLinks";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { ProcedimentoFormView } from "./ProcedimentoFormView";
import { ProcedimentosCategoriasGrid } from "./ProcedimentosCategoriasGrid";
import { ProcedimentosListView } from "./ProcedimentosListView";
import type { ProcedimentosPageContentProps } from "./procedimentos-page-types";
import { useProcedimentosPage } from "./useProcedimentosPage";

export type { ProcedimentosPageContentProps } from "./procedimentos-page-types";

export function ProcedimentosPageContent({
  title = "Procedimentos",
  subtitle = "Serviços e valores praticados por convênio",
  defaultCategoria = "",
  backHref,
  relatedLinks = [],
}: ProcedimentosPageContentProps) {
  const page = useProcedimentosPage({ defaultCategoria });
  const emLista = page.viewMode === "lista";

  if (page.isFormView) {
    return (
      <ProcedimentoFormView
        editing={page.form.editing}
        form={page.form.form}
        convenios={page.matrix.convenios}
        precosConvenio={page.form.precosConvenio}
        error={page.form.error}
        saving={page.form.saving}
        accentColor={page.accentColor}
        onFormChange={(patch) => page.form.setForm((f) => ({ ...f, ...patch }))}
        onPrecoChange={(convenioId, value) =>
          page.form.setPrecosConvenio((prev) => ({ ...prev, [convenioId]: value }))
        }
        onCancel={page.voltarLista}
        onSave={() => void page.form.save()}
      />
    );
  }

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={title}
        subtitle={
          emLista && page.categoriaAtualLabel
            ? `${subtitle} · ${page.categoriaAtualLabel}`
            : subtitle
        }
        backHref={backHref}
        icon={Stethoscope}
        newLabel="Novo Procedimento"
        onNew={page.abrirNovo}
        extraActions={
          emLista ? (
            <button
              type="button"
              onClick={page.voltarCategorias}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs sm:text-sm font-medium rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700"
            >
              <ArrowLeft size={16} />
              <span className="hidden sm:inline">Categorias</span>
            </button>
          ) : null
        }
      />

      {page.viewMode === "categorias" ? (
        <ClinicaBelezaPageContent>
          {page.moduleKey && (
            <div className="mb-4 flex flex-wrap items-center gap-2 text-sm">
              <span className="px-2 py-1 rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200">
                Filtro: {page.moduleKey === "soroterapia" ? "Soroterapia" : "Estética"}
              </span>
              {page.hiddenByCategoryCount > 0 && (
                <button
                  type="button"
                  onClick={() => page.setShowAllCategories(!page.showAllCategories)}
                  className="text-purple-700 dark:text-purple-300 underline"
                >
                  {page.showAllCategories
                    ? "Mostrar só deste módulo"
                    : `Incluir outras categorias na grade (${page.activeList.length} cadastrados)`}
                </button>
              )}
            </div>
          )}
          <ProcedimentosCategoriasGrid
            categorias={page.categoriaCards}
            loading={page.loading}
            totalProcedimentos={page.activeList.length}
            onSelect={page.selecionarCategoria}
            onVerTodos={page.verTodos}
          />
          <ClinicaBelezaRelatedLinks slug={page.slug} items={relatedLinks} />
        </ClinicaBelezaPageContent>
      ) : (
        <ProcedimentosListView
          slug={page.slug}
          title={title}
          subtitle={subtitle}
          backHref={backHref}
          relatedLinks={relatedLinks}
          moduleKey={page.moduleKey}
          showAllCategories={page.showAllCategories}
          hiddenByCategoryCount={page.hiddenByCategoryCount}
          activeList={page.activeList}
          filteredList={page.filteredList}
          convenios={page.matrix.convenios}
          loading={page.loading}
          matrixLoading={page.matrix.matrixLoading}
          page={page.page}
          totalPages={page.totalPages}
          totalCount={page.totalCount ?? 0}
          pageSize={page.pageSize}
          precoCelula={page.matrix.precoCelula}
          hideHeader
          onToggleShowAll={() => page.setShowAllCategories(!page.showAllCategories)}
          onNew={page.abrirNovo}
          onEdit={page.abrirEditar}
          onExclude={(p) => void page.form.exclude(p)}
          onPageChange={page.setPage}
        />
      )}
    </>
  );
}
