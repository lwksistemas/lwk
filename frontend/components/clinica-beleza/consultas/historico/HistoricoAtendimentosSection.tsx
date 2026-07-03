"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { imprimirConsultaPdf } from "@/lib/consulta-print";
import type { Consulta } from "../consultas-types";
import { ConsultaPrintButton } from "../ConsultaPrintButton";

export function HistoricoAtendimentosSection({
  historico,
  selectedId,
  formatData,
  onSelect,
}: {
  historico: Consulta[];
  selectedId: number;
  formatData: (d?: string | null) => string;
  onSelect: (c: Consulta) => void;
}) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  if (historico.length === 0) {
    return <p className="text-gray-500 text-sm">Nenhuma consulta encontrada para este paciente.</p>;
  }

  return (
    <div className="space-y-2">
      {historico.map((h) => {
        const isExpanded = expandedId === h.id;
        const conteudo = h.observacoes_gerais || h.protocolo_notas;
        return (
          <div
            key={h.id}
            className={`rounded-lg border transition-colors ${
              h.id === selectedId
                ? "border-[#8B3D52] bg-[#F5E6EA]/40 dark:bg-neutral-700"
                : "border-gray-200 dark:border-neutral-600"
            }`}
          >
            <button
              type="button"
              onClick={() => {
                if (h.id === selectedId) return;
                setExpandedId(isExpanded ? null : h.id);
              }}
              className="w-full text-left p-3"
              disabled={h.id === selectedId}
            >
              <div className="flex justify-between items-center gap-2">
                <div>
                  <p className="font-medium text-sm text-gray-900 dark:text-gray-100">{h.procedure_name}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {formatData(h.data_inicio)}
                    {h.professional_name ? ` · ${h.professional_name}` : ""}
                    {h.protocol_name ? ` · ${h.protocol_name}` : ""}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {conteudo && (
                    <ConsultaPrintButton onPrint={() => imprimirConsultaPdf(h.id, "atendimento")} />
                  )}
                  {h.id !== selectedId &&
                    (conteudo ? (
                      isExpanded ? (
                        <ChevronDown size={16} className="text-gray-400 shrink-0" />
                      ) : (
                        <ChevronRight size={16} className="text-gray-400 shrink-0" />
                      )
                    ) : (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelect(h);
                        }}
                        className="text-xs text-purple-600 dark:text-purple-400 hover:underline"
                      >
                        Abrir
                      </button>
                    ))}
                </div>
              </div>
            </button>
            {(h.id === selectedId || isExpanded) && conteudo && (
              <div className="px-3 pb-3 border-t border-gray-100 dark:border-neutral-600 pt-2">
                {h.id === selectedId && (
                  <p className="text-[10px] uppercase tracking-wide text-[#8B3D52] font-medium mb-2">
                    Consulta atual
                  </p>
                )}
                <pre className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">
                  {conteudo}
                </pre>
                {h.id !== selectedId && (
                  <button
                    type="button"
                    onClick={() => onSelect(h)}
                    className="mt-2 text-xs text-purple-600 dark:text-purple-400 hover:underline"
                  >
                    Ver detalhes completos →
                  </button>
                )}
              </div>
            )}
            {h.id === selectedId && !conteudo && (
              <div className="px-3 pb-3 border-t border-gray-100 dark:border-neutral-600 pt-2">
                <p className="text-xs text-gray-400 italic">Nenhuma anotação registrada nesta consulta.</p>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
