"use client";

import { useState, useEffect, useCallback } from "react";
import {
  FileText,
  Pill,
  FlaskConical,
  ClipboardCheck,
  File,
  ChevronDown,
  Layers,
  PenLine,
  ExternalLink,
  Trash2,
  Loader2,
} from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI, DocumentoClinicoItem } from "@/lib/clinica-beleza-api";

/**
 * Tipo de documento clínico — mapeia ao DocumentTemplate.TIPO_CHOICES do backend.
 */
export type DocumentoTipo = "receituario" | "pedido_exame" | "atestado" | "documento_personalizado";

/**
 * Sub-opção selecionada pelo profissional ao clicar em um tipo de documento.
 */
export type DocumentoAcao = "memed" | "template" | "manual";

interface DocumentoButtonConfig {
  tipo: DocumentoTipo;
  label: string;
  icon: typeof Pill;
  /** Se true, mostra a opção "Usar Memed" (apenas Receituário e Exames). */
  hasMemed: boolean;
}

const DOCUMENTO_BUTTONS: DocumentoButtonConfig[] = [
  { tipo: "receituario", label: "Receituário", icon: Pill, hasMemed: true },
  { tipo: "pedido_exame", label: "Exames", icon: FlaskConical, hasMemed: true },
  { tipo: "atestado", label: "Atestado", icon: ClipboardCheck, hasMemed: false },
  { tipo: "documento_personalizado", label: "Documento", icon: File, hasMemed: false },
];

/** Mapa de tipo → label amigável */
const TIPO_LABELS: Record<string, string> = {
  receituario: "Receituário",
  pedido_exame: "Pedido de Exame",
  atestado: "Atestado",
  documento_personalizado: "Documento",
};

/**
 * ConsultaDocumentosTab — Seção de documentos clínicos na consulta.
 *
 * Mostra 4 botões de tipo de documento com sub-opções:
 * - "Usar Memed" (Receituário e Exames — abre prescrição digital existente)
 * - "Usar Template" (abre seleção de template — implementado na task 11.3)
 * - "Digitar Manual" (abre editor de texto livre — implementado na task 11.4)
 *
 * Também lista documentos já criados com opção de excluir (task 11.5).
 */
export function ConsultaDocumentosTab({
  consultaId,
  consultaAtiva,
  onUsarMemed,
  onUsarTemplate,
  onDigitarManual,
}: {
  consultaId: number;
  consultaAtiva: boolean;
  /** Callback ao selecionar "Usar Memed" (receituário ou exames). */
  onUsarMemed?: () => void;
  /** Callback ao selecionar "Usar Template" com o tipo escolhido. */
  onUsarTemplate?: (tipo: DocumentoTipo) => void;
  /** Callback ao selecionar "Digitar Manual" com o tipo escolhido. */
  onDigitarManual?: (tipo: DocumentoTipo) => void;
}) {
  const [openDropdown, setOpenDropdown] = useState<DocumentoTipo | null>(null);
  const [documentos, setDocumentos] = useState<DocumentoClinicoItem[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);

  /** Carrega a lista de documentos da consulta */
  const fetchDocumentos = useCallback(async () => {
    try {
      setLoadingDocs(true);
      const data = await ClinicaBelezaAPI.documentos.list(consultaId);
      setDocumentos(Array.isArray(data) ? data : []);
    } catch {
      setDocumentos([]);
    } finally {
      setLoadingDocs(false);
    }
  }, [consultaId]);

  useEffect(() => {
    fetchDocumentos();
  }, [fetchDocumentos]);

  /** Exclui um documento após confirmação */
  const handleDelete = async (docId: number) => {
    setDeletingId(docId);
    try {
      await ClinicaBelezaAPI.documentos.delete(consultaId, docId);
      await fetchDocumentos();
    } catch {
      // erro silencioso — o documento pode já ter sido excluído
    } finally {
      setDeletingId(null);
      setConfirmDeleteId(null);
    }
  };

  const toggleDropdown = (tipo: DocumentoTipo) => {
    setOpenDropdown((prev) => (prev === tipo ? null : tipo));
  };

  const handleAcao = (tipo: DocumentoTipo, acao: DocumentoAcao) => {
    setOpenDropdown(null);
    switch (acao) {
      case "memed":
        onUsarMemed?.();
        break;
      case "template":
        onUsarTemplate?.(tipo);
        break;
      case "manual":
        onDigitarManual?.(tipo);
        break;
    }
  };

  return (
    <div className="space-y-5">
      {/* Seção: Criar novo documento */}
      <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 md:p-6">
        <div className="flex items-center gap-2 mb-4">
          <FileText size={18} className="text-gray-600 dark:text-gray-400" />
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">Documentos</h3>
        </div>

        {consultaAtiva ? (
          <>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              Crie receituários, pedidos de exame, atestados e outros documentos clínicos para esta consulta.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {DOCUMENTO_BUTTONS.map((btn) => {
                const Icon = btn.icon;
                const isOpen = openDropdown === btn.tipo;
                return (
                  <div key={btn.tipo} className="relative">
                    <button
                      type="button"
                      onClick={() => toggleDropdown(btn.tipo)}
                      className={`w-full flex items-center justify-center gap-2 px-3 py-3 rounded-lg text-sm font-medium transition-colors border ${
                        isOpen
                          ? "border-[var(--cb-primary)] bg-[var(--cb-primary-light)] text-[var(--cb-primary)]"
                          : "border-gray-200 dark:border-neutral-600 bg-gray-50 dark:bg-neutral-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-neutral-600"
                      }`}
                      style={
                        {
                          "--cb-primary": CLINICA_BELEZA_PRIMARY,
                          "--cb-primary-light": "#F5E6EA",
                        } as React.CSSProperties
                      }
                    >
                      <Icon size={16} />
                      <span className="hidden sm:inline">{btn.label}</span>
                      <span className="sm:hidden">{btn.label.length > 8 ? btn.label.slice(0, 6) + "…" : btn.label}</span>
                      <ChevronDown
                        size={14}
                        className={`transition-transform ${isOpen ? "rotate-180" : ""}`}
                      />
                    </button>

                    {/* Dropdown de sub-opções */}
                    {isOpen && (
                      <div className="absolute top-full left-0 right-0 z-20 mt-1 bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-600 rounded-lg shadow-lg overflow-hidden">
                        {btn.hasMemed && (
                          <button
                            type="button"
                            onClick={() => handleAcao(btn.tipo, "memed")}
                            className="w-full flex items-center gap-2 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors"
                          >
                            <ExternalLink size={14} className="text-blue-500" />
                            Usar Memed
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => handleAcao(btn.tipo, "template")}
                          className="w-full flex items-center gap-2 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors"
                        >
                          <Layers size={14} className="text-purple-500" />
                          Usar Template
                        </button>
                        <button
                          type="button"
                          onClick={() => handleAcao(btn.tipo, "manual")}
                          className="w-full flex items-center gap-2 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors"
                        >
                          <PenLine size={14} className="text-green-500" />
                          Digitar Manual
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </>
        ) : (
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Documentos só podem ser criados enquanto a consulta está em andamento.
          </p>
        )}
      </div>

      {/* Seção: Lista de documentos já criados */}
      <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 md:p-6">
        <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Documentos da consulta</h3>

        {loadingDocs ? (
          <div className="flex items-center gap-2 py-4 justify-center text-gray-400">
            <Loader2 size={16} className="animate-spin" />
            <span className="text-sm">Carregando documentos…</span>
          </div>
        ) : documentos.length === 0 ? (
          <p className="text-sm text-gray-400 dark:text-gray-500 italic">
            Nenhum documento criado nesta consulta.
          </p>
        ) : (
          <div className="space-y-3">
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
                      <span className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                        {doc.titulo}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {new Date(doc.created_at).toLocaleString("pt-BR", {
                      day: "2-digit",
                      month: "2-digit",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                  {doc.conteudo && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                      {doc.conteudo.length > 120
                        ? doc.conteudo.slice(0, 120) + "…"
                        : doc.conteudo}
                    </p>
                  )}
                </div>

                {/* Botão excluir — só se consulta ativa */}
                {consultaAtiva && (
                  <div className="flex-shrink-0">
                    {confirmDeleteId === doc.id ? (
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => handleDelete(doc.id)}
                          disabled={deletingId === doc.id}
                          className="text-xs px-2 py-1 rounded bg-red-500 text-white hover:bg-red-600 disabled:opacity-50 transition-colors"
                        >
                          {deletingId === doc.id ? (
                            <Loader2 size={12} className="animate-spin" />
                          ) : (
                            "Confirmar"
                          )}
                        </button>
                        <button
                          type="button"
                          onClick={() => setConfirmDeleteId(null)}
                          className="text-xs px-2 py-1 rounded bg-gray-200 dark:bg-neutral-600 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-neutral-500 transition-colors"
                        >
                          Cancelar
                        </button>
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={() => setConfirmDeleteId(doc.id)}
                        title="Excluir documento"
                        className="p-1.5 rounded text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                      >
                        <Trash2 size={15} />
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
