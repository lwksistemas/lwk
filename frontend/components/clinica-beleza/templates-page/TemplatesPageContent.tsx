"use client";

import { FileText } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { TemplatesDeleteModal } from "./TemplatesDeleteModal";
import { TemplatesListView } from "./TemplatesListView";
import { useTemplatesPage } from "./useTemplatesPage";

export function TemplatesPageContent() {
  const {
    filtroTipo,
    setFiltroTipo,
    templates,
    loading,
    page,
    setPage,
    totalPages,
    pageSize,
    totalCount,
    deleteTarget,
    setDeleteTarget,
    deleting,
    openNew,
    openEdit,
    confirmDelete,
  } = useTemplatesPage();

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Templates"
        subtitle="Templates de documentos clínicos reutilizáveis"
        icon={FileText}
        newLabel="Novo Template"
        onNew={openNew}
      />
      <ClinicaBelezaPageContent>
        <TemplatesListView
          filtroTipo={filtroTipo}
          onFiltroTipoChange={setFiltroTipo}
          templates={templates}
          loading={loading}
          page={page}
          totalPages={totalPages}
          pageSize={pageSize}
          totalCount={totalCount ?? 0}
          onPageChange={setPage}
          onEdit={openEdit}
          onDelete={setDeleteTarget}
        />
      </ClinicaBelezaPageContent>

      {deleteTarget && (
        <TemplatesDeleteModal
          target={deleteTarget}
          deleting={deleting}
          onClose={() => setDeleteTarget(null)}
          onConfirm={() => void confirmDelete()}
        />
      )}
    </>
  );
}
