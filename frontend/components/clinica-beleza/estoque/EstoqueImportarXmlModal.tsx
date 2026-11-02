"use client";

import { AlertCircle, CheckCircle2, FileUp, Loader2, X } from "lucide-react";
import type { EstoqueImportarXmlModalProps } from "./estoque-importar-xml-types";
import { EstoqueImportarXmlForm } from "./EstoqueImportarXmlForm";
import { EstoqueImportarXmlPreview } from "./EstoqueImportarXmlPreview";
import { EstoqueImportarXmlResult } from "./EstoqueImportarXmlResult";
import { useEstoqueImportarXml } from "./useEstoqueImportarXml";

export function EstoqueImportarXmlModal({
  open,
  onClose,
  onSuccess,
  categorias,
  defaultCategoriaSlug,
}: EstoqueImportarXmlModalProps) {
  const {
    arquivo,
    categoria,
    setCategoria,
    loading,
    error,
    preview,
    resultado,
    pendentes,
    notaId,
    sincronizando,
    handleClose,
    handleFileChange,
    voltarPreview,
    enviarXml,
    updateProdutoCategoria,
    abrirPendente,
    confirmarPendente,
    ignorarPendente,
    sincronizar,
  } = useEstoqueImportarXml(open, onClose, onSuccess, { categorias, defaultCategoriaSlug });

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-2xl max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-neutral-700 shrink-0">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Importar XML (NF-e)</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Importe produtos da nota fiscal eletrônica
            </p>
          </div>
          <button
            type="button"
            onClick={handleClose}
            disabled={loading}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800"
          >
            <X size={20} className="text-gray-500" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm flex items-start gap-2">
              <AlertCircle size={16} className="shrink-0 mt-0.5" />
              {error}
            </div>
          )}

          {resultado && <EstoqueImportarXmlResult resultado={resultado} />}
          {preview && !resultado && (
            <EstoqueImportarXmlPreview
              preview={preview}
              categorias={categorias}
              onProdutoCategoriaChange={updateProdutoCategoria}
            />
          )}
          {!resultado && !preview && (
            <div className="space-y-4">
              <div className="rounded-lg border border-gray-200 dark:border-neutral-700 p-3 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-gray-800 dark:text-gray-100">Notas pendentes</p>
                  <button
                    type="button"
                    onClick={() => void sincronizar()}
                    disabled={loading || sincronizando}
                    className="text-xs font-medium px-2 py-1 rounded-md border border-gray-300 dark:border-neutral-600 disabled:opacity-50"
                  >
                    {sincronizando ? "Consultando..." : "Buscar na SEFAZ"}
                  </button>
                </div>
                {pendentes.length === 0 ? (
                  <p className="text-xs text-gray-500">Nenhuma nota aguardando. A busca usa o certificado A1 da clínica.</p>
                ) : (
                  <ul className="space-y-2">
                    {pendentes.map((nota) => (
                      <li key={nota.id} className="flex flex-wrap items-center justify-between gap-2 text-sm">
                        <span>
                          NF {nota.numero || "—"} — {nota.fornecedor || "Fornecedor"}
                          <span className="block text-xs text-gray-500">
                            {nota.status_display}
                            {nota.data_emissao ? ` · ${nota.data_emissao}` : ""}
                            {nota.ultimo_erro ? ` · ${nota.ultimo_erro}` : ""}
                          </span>
                        </span>
                        <span className="flex gap-2">
                          {nota.tem_xml && (
                            <button type="button" className="text-xs font-medium underline" onClick={() => void abrirPendente(nota.id)}>
                              Abrir
                            </button>
                          )}
                          <button type="button" className="text-xs text-gray-500 underline" onClick={() => void ignorarPendente(nota.id)}>
                            Ignorar
                          </button>
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            <EstoqueImportarXmlForm
              arquivo={arquivo}
              categoria={categoria}
              onCategoriaChange={setCategoria}
              onFileChange={handleFileChange}
              categorias={categorias}
            />
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-gray-200 dark:border-neutral-700 flex justify-between gap-3 shrink-0">
          {resultado ? (
            <button
              type="button"
              onClick={handleClose}
              className="ml-auto px-4 py-2 text-sm font-medium text-white rounded-lg"
              style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
            >
              Fechar
            </button>
          ) : preview ? (
            <>
              <button
                type="button"
                onClick={voltarPreview}
                className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800 rounded-lg"
              >
                Voltar
              </button>
              <button
                type="button"
                onClick={() => void (notaId ? confirmarPendente() : enviarXml(true))}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white rounded-lg disabled:opacity-50"
                style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
              >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
                Confirmar importação ({preview.total_produtos})
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800 rounded-lg"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={() => void enviarXml(false)}
                disabled={loading || !arquivo}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white rounded-lg disabled:opacity-50"
                style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
              >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <FileUp size={16} />}
                Visualizar produtos
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
