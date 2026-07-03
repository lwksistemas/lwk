"use client";

import { useState } from "react";
import { Printer } from "lucide-react";
import { ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import type { ProntuarioDocItem } from "@/lib/clinica-beleza-api";
import { logger } from "@/lib/logger";
import { printProntuarioDocument } from "./prontuario-document-print";
import { formatProntuarioDate, prontuarioTipoLabel } from "./prontuario-utils";

interface ProntuarioDocumentoCardProps {
  doc: ProntuarioDocItem;
}

export function ProntuarioDocumentoCard({ doc }: ProntuarioDocumentoCardProps) {
  const [printing, setPrinting] = useState(false);

  const handlePrintDocument = async () => {
    if (printing) return;
    setPrinting(true);
    try {
      await printProntuarioDocument(doc);
    } catch (e) {
      logger.warn("Erro ao imprimir documento:", e);
    } finally {
      setPrinting(false);
    }
  };

  return (
    <ClinicaBelezaPanel className="p-5">
      <div className="flex items-start justify-between gap-4 mb-2">
        <div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            {doc.titulo || prontuarioTipoLabel(doc.tipo)}
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {doc.professional_name && <span>{doc.professional_name} · </span>}
            {doc.created_at ? formatProntuarioDate(doc.created_at) : "—"}
            {doc.consulta_id && <span className="ml-2">Consulta #{doc.consulta_id}</span>}
            {doc.source === "memed" && (
              <span className="ml-2 px-1.5 py-0.5 rounded text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                Memed
              </span>
            )}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void handlePrintDocument()}
          disabled={printing}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-neutral-700 transition-colors disabled:opacity-50"
          title="Imprimir documento (PDF)"
        >
          <Printer size={14} />
          {printing ? "Gerando..." : "Imprimir"}
        </button>
      </div>
      <div className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
        {doc.conteudo}
      </div>
    </ClinicaBelezaPanel>
  );
}
