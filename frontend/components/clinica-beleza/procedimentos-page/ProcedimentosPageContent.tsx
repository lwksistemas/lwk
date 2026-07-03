"use client";

import { ProcedimentoFormView } from "./ProcedimentoFormView";
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
  const {
    slug,
    accentColor,
    isFormView,
    moduleKey,
    showAllCategories,
    setShowAllCategories,
    activeList,
    filteredList,
    hiddenByCategoryCount,
    loading,
    page,
    setPage,
    totalPages,
    pageSize,
    totalCount,
    abrirNovo,
    abrirEditar,
    voltarLista,
    matrix,
    form,
  } = useProcedimentosPage({ defaultCategoria });

  if (isFormView) {
    return (
      <ProcedimentoFormView
        editing={form.editing}
        form={form.form}
        convenios={matrix.convenios}
        precosConvenio={form.precosConvenio}
        error={form.error}
        saving={form.saving}
        accentColor={accentColor}
        onFormChange={(patch) => form.setForm((f) => ({ ...f, ...patch }))}
        onPrecoChange={(convenioId, value) =>
          form.setPrecosConvenio((prev) => ({ ...prev, [convenioId]: value }))
        }
        onCancel={voltarLista}
        onSave={() => void form.save()}
      />
    );
  }

  return (
    <ProcedimentosListView
      slug={slug}
      title={title}
      subtitle={subtitle}
      backHref={backHref}
      relatedLinks={relatedLinks}
      moduleKey={moduleKey}
      showAllCategories={showAllCategories}
      hiddenByCategoryCount={hiddenByCategoryCount}
      activeList={activeList}
      filteredList={filteredList}
      convenios={matrix.convenios}
      loading={loading}
      matrixLoading={matrix.matrixLoading}
      page={page}
      totalPages={totalPages}
      totalCount={totalCount ?? 0}
      pageSize={pageSize}
      precoCelula={matrix.precoCelula}
      onToggleShowAll={() => setShowAllCategories(!showAllCategories)}
      onNew={abrirNovo}
      onEdit={abrirEditar}
      onExclude={(p) => void form.exclude(p)}
      onPageChange={setPage}
    />
  );
}
