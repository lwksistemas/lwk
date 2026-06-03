"use client";

/**
 * Listagem de Templates de Documentos Clínicos — Clínica da Beleza
 * Filtro por tipo: receituário, pedido de exame, atestado, documento personalizado
 */

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Pencil, Trash2, FileText, X } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI, type DocumentTemplateItem } from "@/lib/clinica-beleza-api";

const TIPO_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "Todos os tipos" },
  { value: "receituario", label: "Receituário" },
  { value: "pedido_exame", label: "Pedido de Exame" },
  { value: "atestado", label: "Atestado" },
  { value: "documento_personalizado", label: "Documento Personalizado" },
];

function tipoLabel(tipo: string): string {
  const found = TIPO_OPTIONS.find((o) => o.value === tipo);
  return found?.label ?? tipo;
}

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
  } catch {
    return dateStr;
  }
}

export default function TemplatesPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  const [templates, setTemplates] = useState<DocumentTemplateItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtroTipo, setFiltroTipo] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<DocumentTemplateItem | null>(null);
  const [deleting, setDeleting] = useState(false);

  const loadTemplates = useCallback(async () => {
    setLoading(true);
    try {
      const params: { tipo?: string } = {};
      if (filtroTipo) params.tipo = filtroTipo;
      const data = await ClinicaBelezaAPI.templates.list(params);
      setTemplates(data.results ?? []);
    } catch {
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  }, [filtroTipo]);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  const openNew = () => {
    router.push(`/loja/${slug}/clinica-beleza/templates/novo`);
  };

  const openEdit = (t: DocumentTemplateItem) => {
    router.push(`/loja/${slug}/clinica-beleza/templates/novo?id=${t.id}`);
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await ClinicaBelezaAPI.templates.delete(deleteTarget.id);
      setDeleteTarget(null);
      loadTemplates();
    } catch {
      alert("Erro ao desativar template.");
    } finally {
      setDeleting(false);
    }
  };

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
        {/* Filtro por tipo */}
        <div className="mb-4 flex items-center gap-3">
          <label className="text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap">
            Filtrar por tipo:
          </label>
          <select
            value={filtroTipo}
            onChange={(e) => setFiltroTipo(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100"
          >
            {TIPO_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Lista */}
        {loading ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : templates.length === 0 ? (
          <div className="bg-white/80 dark:bg-neutral-800/70 rounded-xl p-8 text-center text-gray-500 dark:text-gray-400">
            {filtroTipo
              ? "Nenhum template encontrado para este tipo."
              : 'Nenhum template cadastrado. Clique em "Novo Template" para começar.'}
          </div>
        ) : (
          <div className="bg-white/80 dark:bg-neutral-800/70 rounded-xl shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-100 dark:bg-neutral-700 text-gray-600 dark:text-gray-300">
                  <tr>
                    <th className="text-left p-3">Nome</th>
                    <th className="text-left p-3">Tipo</th>
                    <th className="text-left p-3 hidden md:table-cell">Atualizado em</th>
                    <th className="w-28 p-3">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {templates.map((t) => (
                    <tr key={t.id} className="border-t border-gray-100 dark:border-neutral-700">
                      <td className="p-3 font-medium text-gray-800 dark:text-gray-200">
                        {t.nome}
                      </td>
                      <td className="p-3 text-gray-700 dark:text-gray-300">
                        <span
                          className="inline-block px-2 py-0.5 text-xs rounded-full"
                          style={{
                            backgroundColor: `${CLINICA_BELEZA_PRIMARY}15`,
                            color: CLINICA_BELEZA_PRIMARY,
                          }}
                        >
                          {tipoLabel(t.tipo)}
                        </span>
                      </td>
                      <td className="p-3 hidden md:table-cell text-gray-700 dark:text-gray-300">
                        {formatDate(t.updated_at)}
                      </td>
                      <td className="p-3">
                        <div className="flex gap-2">
                          <button
                            onClick={() => openEdit(t)}
                            className="p-2 text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/30 rounded"
                            title="Editar"
                          >
                            <Pencil size={18} />
                          </button>
                          <button
                            onClick={() => setDeleteTarget(t)}
                            className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                            title="Desativar"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </ClinicaBelezaPageContent>

      {/* Modal de confirmação de exclusão (soft-delete) */}
      {deleteTarget && (
        <>
          <div className="fixed inset-0 bg-black/50 z-[80]" onClick={() => !deleting && setDeleteTarget(null)} />
          <div className="fixed inset-0 z-[81] flex items-center justify-center p-4">
            <div className="bg-white dark:bg-neutral-800 rounded-lg shadow-xl max-w-lg w-full">
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-neutral-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Excluir Template</h2>
                <button
                  type="button"
                  onClick={() => !deleting && setDeleteTarget(null)}
                  className="p-1 rounded hover:bg-gray-100 dark:hover:bg-neutral-700"
                >
                  <X size={20} className="text-gray-500 dark:text-gray-400" />
                </button>
              </div>
              <div className="p-6">
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Deseja excluir o template &quot;{deleteTarget.nome}&quot;? Ele será desativado e não aparecerá mais na listagem, mas ficará preservado para referência histórica.
                </p>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => !deleting && setDeleteTarget(null)}
                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700"
                  >
                    Cancelar
                  </button>
                  <button
                    type="button"
                    onClick={confirmDelete}
                    disabled={deleting}
                    className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-50"
                  >
                    {deleting ? "Excluindo..." : "Excluir"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
