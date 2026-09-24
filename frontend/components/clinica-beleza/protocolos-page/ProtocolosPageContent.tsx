"use client";

import { useToast } from "@/components/ui/Toast";
import { ProtocoloAgendarModal } from "./ProtocoloAgendarModal";
import { ProtocoloFormView } from "./ProtocoloFormView";
import { ProtocolosListView } from "./ProtocolosListView";
import type { ProtocolosPageContentProps } from "./protocolos-page-types";
import { useProtocolosPage } from "./useProtocolosPage";

export type { ProtocolosPageContentProps } from "./protocolos-page-types";

export function ProtocolosPageContent({
  title = "Protocolos",
  subtitle = "Padronize procedimentos com etapas, materiais e cuidados",
  defaultCategoria = "",
  backHref,
  relatedLinks = [],
}: ProtocolosPageContentProps) {
  const toast = useToast();
  const {
    slug,
    accentColor,
    isFormView,
    loading,
    list,
    page,
    setPage,
    totalPages,
    pageSize,
    totalCount,
    procedures,
    produtos,
    agendando,
    setAgendando,
    abrirNovo,
    abrirEditar,
    voltarLista,
    form,
  } = useProtocolosPage({ defaultCategoria });

  if (isFormView) {
    return (
      <ProtocoloFormView
        editing={form.editing}
        form={form.form}
        procedures={procedures}
        produtos={produtos}
        error={form.error}
        saving={form.saving}
        accentColor={accentColor}
        onFormChange={(patch) => form.setForm((f) => ({ ...f, ...patch }))}
        onCancel={voltarLista}
        onSave={() => void form.save()}
      />
    );
  }

  return (
    <>
    <ProtocolosListView
      slug={slug}
      title={title}
      subtitle={subtitle}
      backHref={backHref}
      relatedLinks={relatedLinks}
      list={list}
      loading={loading}
      page={page}
      totalPages={totalPages}
      totalCount={totalCount ?? 0}
      pageSize={pageSize}
      onNew={abrirNovo}
      onEdit={abrirEditar}
      onExclude={(p) => void form.exclude(p)}
      onAgendar={setAgendando}
      onPageChange={setPage}
    />
    {agendando && (
      <ProtocoloAgendarModal
        protocol={agendando}
        onClose={() => setAgendando(null)}
        onSaved={(mensagem) => {
          setAgendando(null);
          toast.success(mensagem);
        }}
      />
    )}
  </>
  );
}
