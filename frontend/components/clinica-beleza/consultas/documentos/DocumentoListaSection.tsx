import { Loader2, Trash2 } from "lucide-react";
import type { DocumentoClinicoItem, PrescricaoMemedItem } from "@/lib/clinica-beleza-api";
import { imprimirDocumentoPdfLazy } from "@/lib/consulta-print-lazy";
import { abrirPdfPrescricaoMemed } from "@/lib/memed-prescricao-pdf";
import { ConsultaPrintButton } from "../ConsultaPrintButton";
import { labelPrescricaoMemed, TIPO_LABELS } from "../historico/historico-utils";

function formatarDataHora(iso: string) {
  return new Date(iso).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function DocumentoListaSection({
  loading,
  documentos,
  prescricoesMemed,
  consultaAtiva,
  confirmDeleteId,
  deletingId,
  onConfirmDelete,
  onCancelDelete,
  onDelete,
  onPrescricaoPdfUrl,
}: {
  loading: boolean;
  documentos: DocumentoClinicoItem[];
  prescricoesMemed: PrescricaoMemedItem[];
  consultaAtiva: boolean;
  confirmDeleteId: number | null;
  deletingId: number | null;
  onConfirmDelete: (id: number) => void;
  onCancelDelete: () => void;
  onDelete: (id: number) => void;
  onPrescricaoPdfUrl: (prescricaoId: number, url: string) => void;
}) {
  return (
    <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 md:p-6">
      <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Documentos da consulta</h3>

      {loading ? (
        <div className="flex items-center gap-2 py-4 justify-center text-gray-400">
          <Loader2 size={16} className="animate-spin" />
          <span className="text-sm">Carregando documentos…</span>
        </div>
      ) : documentos.length === 0 && prescricoesMemed.length === 0 ? (
        <p className="text-sm text-gray-400 dark:text-gray-500 italic">Nenhum documento criado nesta consulta.</p>
      ) : (
        <div className="space-y-3">
          {prescricoesMemed.map((p) => (
            <div
              key={`memed-${p.id}`}
              className="flex items-start gap-3 p-3 rounded-lg border border-purple-100 dark:border-purple-900/40 bg-purple-50/50 dark:bg-purple-950/20"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="inline-block text-xs font-medium px-2 py-0.5 rounded-full bg-purple-200 dark:bg-purple-900/50 text-purple-900 dark:text-purple-200">
                    {labelPrescricaoMemed(p)}
                  </span>
                  <span className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                    {p.resumo?.split("\n")[0]?.replace(/^- /, "") || "Prescrição Memed"}
                  </span>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {p.created_at ? formatarDataHora(p.created_at) : "—"}
                  {p.professional_name ? ` · ${p.professional_name}` : ""}
                </p>
                {p.resumo && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2 whitespace-pre-line">
                    {p.resumo}
                  </p>
                )}
              </div>
              <div className="flex-shrink-0 flex items-center gap-1">
                <ConsultaPrintButton
                  onPrint={async () => {
                    const url = await abrirPdfPrescricaoMemed(p);
                    onPrescricaoPdfUrl(p.id, url);
                  }}
                />
              </div>
            </div>
          ))}
          {documentos.map((doc) => (
            <div
              key={doc.id}
              className="flex items-start gap-3 p-3 rounded-lg border border-gray-100 dark:border-neutral-700 bg-gray-50 dark:bg-neutral-750"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="inline-block text-xs font-medium px-2 py-0.5 rounded-full bg-gray-200 dark:bg-neutral-600 text-gray-700 dark:text-gray-300">
                    {TIPO_LABELS[doc.tipo] || doc.tipo}
                  </span>
                  {doc.titulo && (
                    <span className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">{doc.titulo}</span>
                  )}
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{formatarDataHora(doc.created_at)}</p>
                {doc.conteudo && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                    {doc.conteudo.length > 120 ? `${doc.conteudo.slice(0, 120)}…` : doc.conteudo}
                  </p>
                )}
              </div>

              <div className="flex-shrink-0 flex items-center gap-1">
                <ConsultaPrintButton onPrint={() => imprimirDocumentoPdfLazy(doc)} />
                {consultaAtiva && (
                  <>
                    {confirmDeleteId === doc.id ? (
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => onDelete(doc.id)}
                          disabled={deletingId === doc.id}
                          className="text-xs px-2 py-1 rounded bg-red-500 text-white hover:bg-red-600 disabled:opacity-50 transition-colors"
                        >
                          {deletingId === doc.id ? <Loader2 size={12} className="animate-spin" /> : "Confirmar"}
                        </button>
                        <button
                          type="button"
                          onClick={onCancelDelete}
                          className="text-xs px-2 py-1 rounded bg-gray-200 dark:bg-neutral-600 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-neutral-500 transition-colors"
                        >
                          Cancelar
                        </button>
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={() => onConfirmDelete(doc.id)}
                        title="Excluir documento"
                        className="p-1.5 rounded text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                      >
                        <Trash2 size={15} />
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
