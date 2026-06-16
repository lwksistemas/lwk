"use client";

import { useEffect, useState } from "react";
import { X, Layers, Eye, Loader2 } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI, type DocumentTemplateItem, type DocumentoClinicoItem } from "@/lib/clinica-beleza-api";
import { logger } from "@/lib/logger";
import type { DocumentoTipo } from "./ConsultaDocumentosTab";

const TIPO_LABEL: Record<DocumentoTipo, string> = {
  receituario: "Receituário",
  pedido_exame: "Pedido de Exame",
  atestado: "Atestado",
  documento_personalizado: "Documento",
};

/**
 * UsarTemplateModal — Modal para selecionar um template e criar documento na consulta.
 *
 * Fluxo:
 * 1. Carrega templates filtrados por tipo
 * 2. Profissional seleciona um template
 * 3. Mostra preview do conteúdo (com placeholders visíveis)
 * 4. Ao confirmar, POST cria o documento (backend renderiza placeholders)
 * 5. Sucesso → fecha modal e dispara refresh
 */
export function UsarTemplateModal({
  open,
  tipo,
  consultaId,
  professionalId,
  onClose,
  onSuccess,
}: {
  open: boolean;
  tipo: DocumentoTipo;
  consultaId: number;
  professionalId?: number;
  onClose: () => void;
  /** Chamado após criação com sucesso — para recarregar lista de documentos. */
  onSuccess?: (created?: DocumentoClinicoItem) => void | Promise<void>;
}) {
  const [templates, setTemplates] = useState<DocumentTemplateItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<DocumentTemplateItem | null>(null);
  const [criando, setCriando] = useState(false);
  const [erro, setErro] = useState("");

  // Carrega templates ao abrir o modal
  useEffect(() => {
    if (!open) return;
    setSelectedTemplate(null);
    setErro("");
    setLoading(true);
    (async () => {
      try {
        const params: Record<string, string | number> = { tipo, page_size: 100 };
        if (professionalId) params.professional = professionalId;
        const data = await ClinicaBelezaAPI.templates.list(params);
        const lista = Array.isArray(data) ? data : data?.results ?? [];
        setTemplates(lista);
      } catch (e) {
        logger.warn("Erro ao carregar templates:", e);
        setTemplates([]);
      } finally {
        setLoading(false);
      }
    })();
  }, [open, tipo, professionalId]);

  const handleConfirmar = async () => {
    if (!selectedTemplate) return;
    setCriando(true);
    setErro("");
    try {
      const created = await ClinicaBelezaAPI.documentos.create(consultaId, {
        tipo,
        template_id: selectedTemplate.id,
      });
      onClose();
      await onSuccess?.(created);
    } catch (e: unknown) {
      logger.warn("Erro ao criar documento a partir de template:", e);
      const msg =
        e && typeof e === "object" && "error" in e && typeof (e as { error: unknown }).error === "string"
          ? (e as { error: string }).error
          : "Erro ao criar documento. Tente novamente.";
      setErro(msg);
    } finally {
      setCriando(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b dark:border-neutral-700">
          <div className="flex items-center gap-2">
            <Layers size={18} className="text-purple-500" />
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              Usar Template — {TIPO_LABEL[tipo]}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {loading ? (
            <div className="flex items-center justify-center py-8 text-gray-500">
              <Loader2 size={20} className="animate-spin mr-2" />
              Carregando templates...
            </div>
          ) : templates.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 dark:text-gray-400 text-sm">
                Nenhum template de {TIPO_LABEL[tipo].toLowerCase()} disponível.
              </p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                Crie templates em Configurações → Templates.
              </p>
            </div>
          ) : (
            <>
              {/* Seleção de template */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Selecione um template
                </label>
                <div className="space-y-2">
                  {templates.map((tpl) => (
                    <button
                      key={tpl.id}
                      type="button"
                      onClick={() => setSelectedTemplate(tpl)}
                      className={`w-full text-left px-3 py-2.5 rounded-lg border transition-colors ${
                        selectedTemplate?.id === tpl.id
                          ? "border-[var(--cb-primary)] bg-[var(--cb-primary-light)] text-gray-900 dark:text-gray-100"
                          : "border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 text-gray-700 dark:text-gray-300"
                      }`}
                      style={
                        {
                          "--cb-primary": CLINICA_BELEZA_PRIMARY,
                          "--cb-primary-light": "#F5E6EA",
                        } as React.CSSProperties
                      }
                    >
                      <span className="font-medium text-sm">{tpl.nome}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Preview do template selecionado */}
              {selectedTemplate && (
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <Eye size={14} className="text-gray-500" />
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Preview
                    </span>
                  </div>
                  <div className="bg-gray-50 dark:bg-neutral-900 border border-gray-200 dark:border-neutral-700 rounded-lg p-3 max-h-48 overflow-y-auto">
                    <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">
                      {selectedTemplate.conteudo}
                    </pre>
                  </div>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-1.5">
                    Os placeholders (ex: {"{{paciente_nome}}"}) serão substituídos automaticamente ao criar o documento.
                  </p>
                </div>
              )}
            </>
          )}

          {erro && (
            <p className="text-sm text-red-600 dark:text-red-400">{erro}</p>
          )}
        </div>

        {/* Footer */}
        <div className="flex gap-2 p-4 border-t dark:border-neutral-700">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleConfirmar}
            disabled={!selectedTemplate || criando}
            className="flex-1 py-2 rounded-lg text-white text-sm font-medium disabled:opacity-50 transition-colors"
            style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
          >
            {criando ? "Criando..." : "Confirmar"}
          </button>
        </div>
      </div>
    </div>
  );
}
