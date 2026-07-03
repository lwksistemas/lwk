import { useCallback, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ClinicaBelezaAPI, type DocumentTemplateItem } from "@/lib/clinica-beleza-api";
import { useClinicaBelezaPaginatedList } from "@/hooks/clinica-beleza/useClinicaBelezaPaginatedList";
import { buildTemplateNovoPath } from "./templates-page-utils";

export function useTemplatesPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  const [filtroTipo, setFiltroTipo] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<DocumentTemplateItem | null>(null);
  const [deleting, setDeleting] = useState(false);

  const queryParams = useMemo(() => ({ tipo: filtroTipo || undefined }), [filtroTipo]);

  const { list: templates, loading, load, page, setPage, totalPages, pageSize, totalCount } =
    useClinicaBelezaPaginatedList<DocumentTemplateItem>({
      path: "/templates/",
      queryParams,
      reloadDeps: [filtroTipo],
    });

  const openNew = useCallback(() => {
    router.push(buildTemplateNovoPath(slug));
  }, [router, slug]);

  const openEdit = useCallback(
    (t: DocumentTemplateItem) => {
      router.push(buildTemplateNovoPath(slug, t.id));
    },
    [router, slug],
  );

  const confirmDelete = useCallback(async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await ClinicaBelezaAPI.templates.delete(deleteTarget.id);
      setDeleteTarget(null);
      load();
    } catch {
      alert("Erro ao desativar template.");
    } finally {
      setDeleting(false);
    }
  }, [deleteTarget, load]);

  return {
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
  };
}
