"use client";

import { CampanhaFormView } from "./CampanhaFormView";
import { CampanhasListView } from "./CampanhasListView";
import { useCampanhasPage } from "./useCampanhasPage";

export function CampanhasPageContent() {
  const {
    basePath,
    isFormView,
    loading,
    list,
    page,
    setPage,
    totalPages,
    pageSize,
    totalCount,
    abrirNovo,
    abrirEditar,
    voltarLista,
    load,
    enviarCampanha,
    setEnviarCampanha,
    form,
    exclusao,
  } = useCampanhasPage();

  if (isFormView) {
    return (
      <CampanhaFormView
        basePath={basePath}
        editing={form.editing}
        form={form.form}
        error={form.error}
        saving={form.saving}
        onFormChange={(patch) => form.setForm((f) => ({ ...f, ...patch }))}
        onCancel={voltarLista}
        onSave={() => void form.save()}
      />
    );
  }

  return (
    <CampanhasListView
      list={list}
      loading={loading}
      page={page}
      totalPages={totalPages}
      totalCount={totalCount ?? 0}
      pageSize={pageSize}
      enviarCampanha={enviarCampanha}
      excluirCampanha={exclusao.excluirCampanha}
      excluindo={exclusao.excluindo}
      onNew={abrirNovo}
      onEdit={abrirEditar}
      onEnviar={setEnviarCampanha}
      onExcluir={exclusao.setExcluirCampanha}
      onCloseEnviar={() => setEnviarCampanha(null)}
      onCloseExcluir={() => exclusao.setExcluirCampanha(null)}
      onConfirmExcluir={() => void exclusao.confirmarExclusao()}
      onPageChange={setPage}
      onSent={load}
    />
  );
}
