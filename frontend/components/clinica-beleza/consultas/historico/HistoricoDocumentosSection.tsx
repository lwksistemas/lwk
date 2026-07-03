import type { DocumentoClinicoItem, PrescricaoMemedItem } from "@/lib/clinica-beleza-api";
import { abrirPdfPrescricaoMemed } from "@/lib/memed-prescricao-pdf";
import { imprimirDocumentoPdfLazy } from "@/lib/consulta-print-lazy";
import type { Consulta } from "../consultas-types";
import { ConsultaPrintButton } from "../ConsultaPrintButton";
import { agruparPrescricoesPorConsulta, labelPrescricaoMemed, TIPO_LABELS } from "./historico-utils";

export function HistoricoDocumentosSection({
  historico,
  selectedId,
  documentosPorConsulta,
  prescricoes,
  loading,
  formatData,
  somenteConsultaAtual = false,
}: {
  historico: Consulta[];
  selectedId: number;
  documentosPorConsulta: Record<number, DocumentoClinicoItem[]>;
  prescricoes: PrescricaoMemedItem[];
  loading: boolean;
  formatData: (d?: string | null) => string;
  somenteConsultaAtual?: boolean;
}) {
  const prescricoesPorConsulta = agruparPrescricoesPorConsulta(prescricoes);
  const lista = somenteConsultaAtual ? historico.filter((h) => h.id === selectedId) : historico;
  const consultasComDocs = lista.filter(
    (h) =>
      (documentosPorConsulta[h.id]?.length ?? 0) > 0 ||
      (prescricoesPorConsulta[h.id]?.length ?? 0) > 0,
  );

  if (loading) return <p className="text-gray-500 text-sm">Carregando documentos…</p>;
  if (consultasComDocs.length === 0) {
    return (
      <p className="text-gray-500 text-sm">
        {somenteConsultaAtual
          ? "Nenhum documento registrado nesta consulta."
          : "Nenhum documento registrado nas consultas (receituários, exames, atestados ou Memed)."}
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {consultasComDocs.map((h) => {
        const docs = documentosPorConsulta[h.id] ?? [];
        const memed = prescricoesPorConsulta[h.id] ?? [];
        return (
          <div
            key={h.id}
            className={`rounded-lg border overflow-hidden ${
              h.id === selectedId
                ? "border-[#8B3D52] bg-[#F5E6EA]/20 dark:bg-neutral-700"
                : "border-gray-200 dark:border-neutral-600"
            }`}
          >
            <div className="px-3 py-2 bg-gray-50 dark:bg-neutral-700/50 border-b border-gray-200 dark:border-neutral-600">
              <p className="text-xs font-medium text-gray-800 dark:text-gray-200">
                {h.procedure_name} · {formatData(h.data_inicio)}
                {h.professional_name ? ` · ${h.professional_name}` : ""}
                {h.id === selectedId ? " · Consulta atual" : ""}
              </p>
            </div>
            <div className="p-3 space-y-3">
              {memed.map((p) => (
                <div
                  key={`memed-${p.id}`}
                  className="p-3 rounded-lg border border-purple-100 dark:border-purple-900/40 bg-purple-50/50 dark:bg-purple-950/20"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="inline-block text-xs font-medium px-2 py-0.5 rounded-full bg-purple-200 dark:bg-purple-900/50 text-purple-900 dark:text-purple-200">
                          {labelPrescricaoMemed(p)}
                        </span>
                        <span className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                          {p.resumo?.split("\n")[0]?.replace(/^- /, "") || "Prescrição Memed"}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {formatData(p.created_at)}
                        {p.professional_name ? ` · ${p.professional_name}` : ""}
                      </p>
                      {p.resumo && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 whitespace-pre-wrap line-clamp-4">
                          {p.resumo}
                        </p>
                      )}
                    </div>
                    <ConsultaPrintButton onPrint={() => abrirPdfPrescricaoMemed(p)} />
                  </div>
                </div>
              ))}
              {docs.map((doc) => (
                <div
                  key={doc.id}
                  className="p-3 rounded-lg border border-gray-100 dark:border-neutral-700 bg-white dark:bg-neutral-800/60"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
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
                        {formatData(doc.created_at)}
                        {doc.professional_name ? ` · ${doc.professional_name}` : ""}
                      </p>
                    </div>
                    <ConsultaPrintButton onPrint={() => imprimirDocumentoPdfLazy(doc)} />
                  </div>
                  {doc.conteudo && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 whitespace-pre-wrap line-clamp-4">
                      {doc.conteudo}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
