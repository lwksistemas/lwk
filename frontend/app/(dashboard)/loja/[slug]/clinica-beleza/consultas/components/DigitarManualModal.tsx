"use client";

import { useState } from "react";
import { X, PenLine } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import type { DocumentoTipo } from "./ConsultaDocumentosTab";

const TIPO_LABELS: Record<DocumentoTipo, string> = {
  receituario: "Receituário",
  pedido_exame: "Pedido de Exame",
  atestado: "Atestado",
  documento_personalizado: "Documento",
};

interface DigitarManualModalProps {
  open: boolean;
  tipo: DocumentoTipo;
  saving: boolean;
  onClose: () => void;
  onSave: (data: { tipo: DocumentoTipo; titulo: string; conteudo: string }) => void;
}

/**
 * Modal para criação de documento clínico com texto livre (Digitar Manual).
 * Permite inserir um título opcional e o conteúdo em textarea.
 */
export function DigitarManualModal({
  open,
  tipo,
  saving,
  onClose,
  onSave,
}: DigitarManualModalProps) {
  const [titulo, setTitulo] = useState("");
  const [conteudo, setConteudo] = useState("");

  if (!open) return null;

  const handleSave = () => {
    if (!conteudo.trim()) return;
    onSave({ tipo, titulo: titulo.trim(), conteudo: conteudo.trim() });
  };

  const handleClose = () => {
    setTitulo("");
    setConteudo("");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b dark:border-neutral-700">
          <div className="flex items-center gap-2">
            <PenLine size={18} className="text-green-500" />
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              {TIPO_LABELS[tipo]} — Texto Livre
            </h2>
          </div>
          <button
            type="button"
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 space-y-4 flex-1 overflow-y-auto">
          {/* Título (opcional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Título <span className="text-gray-400 font-normal">(opcional)</span>
            </label>
            <input
              type="text"
              value={titulo}
              onChange={(e) => setTitulo(e.target.value)}
              placeholder={`Ex: ${TIPO_LABELS[tipo]} - ${new Date().toLocaleDateString("pt-BR")}`}
              className="w-full px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[var(--cb-primary)] focus:border-transparent"
              style={{ "--cb-primary": CLINICA_BELEZA_PRIMARY } as React.CSSProperties}
            />
          </div>

          {/* Conteúdo */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Conteúdo <span className="text-red-500">*</span>
            </label>
            <textarea
              value={conteudo}
              onChange={(e) => setConteudo(e.target.value)}
              placeholder="Digite o conteúdo do documento..."
              rows={10}
              className="w-full px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 resize-y focus:outline-none focus:ring-2 focus:ring-[var(--cb-primary)] focus:border-transparent"
              style={{ "--cb-primary": CLINICA_BELEZA_PRIMARY } as React.CSSProperties}
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-2 p-4 border-t dark:border-neutral-700">
          <button
            type="button"
            onClick={handleClose}
            className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving || !conteudo.trim()}
            className="flex-1 py-2 rounded-lg text-white font-medium disabled:opacity-50 transition-colors"
            style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
          >
            {saving ? "Salvando..." : "Salvar documento"}
          </button>
        </div>
      </div>
    </div>
  );
}
