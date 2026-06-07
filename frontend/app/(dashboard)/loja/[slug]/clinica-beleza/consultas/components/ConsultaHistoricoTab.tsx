"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ChevronRight, ChevronDown, Pill, FlaskConical, ClipboardList, Activity, FolderOpen } from "lucide-react";
import { ClinicaBelezaAPI, type DocumentoClinicoItem } from "@/lib/clinica-beleza-api";
import { imprimirConsultaPdf, imprimirDocumentoPdf, type ConsultaPrintMeta } from "@/lib/consulta-print";
import type { Consulta, Evolucao } from "./consultas-types";
import type { PrescricaoMemedItem } from "@/lib/clinica-beleza-api";
import { ConsultaPrintButton } from "./ConsultaPrintButton";

type HistoricoSection = "atendimentos" | "receituarios" | "exames" | "documentos" | "evolucoes";

const TIPO_LABELS: Record<string, string> = {
  receituario: "Receituário",
  pedido_exame: "Pedido de Exame",
  atestado: "Atestado",
  documento_personalizado: "Documento",
};

function parseListaDocumentos(data: unknown): DocumentoClinicoItem[] {
  if (Array.isArray(data)) return data;
  if (data && typeof data === "object" && Array.isArray((data as { results?: unknown }).results)) {
    return (data as { results: DocumentoClinicoItem[] }).results;
  }
  return [];
}

export function ConsultaHistoricoTab({
  historico,
  selectedId,
  prescricoes = [],
  observacoesAtual = "",
  protocoloNotasAtual,
  formatData,
  onSelect,
  printMeta,
}: {
  historico: Consulta[];
  selectedId: number;
  prescricoes?: PrescricaoMemedItem[];
  observacoesAtual?: string;
  protocoloNotasAtual?: string | null;
  formatData: (d?: string | null) => string;
  onSelect: (c: Consulta) => void;
  printMeta: ConsultaPrintMeta;
}) {
  const [section, setSection] = useState<HistoricoSection>("atendimentos");

  const historicoEnriquecido = useMemo(
    () =>
      historico.map((h) => {
        if (h.id !== selectedId) return h;
        const notas = observacoesAtual || h.observacoes_gerais || "";
        const protocolo = protocoloNotasAtual ?? h.protocolo_notas ?? "";
        return {
          ...h,
          observacoes_gerais: notas || h.observacoes_gerais,
          protocolo_notas: protocolo || h.protocolo_notas,
        };
      }),
    [historico, selectedId, observacoesAtual, protocoloNotasAtual],
  );
  const [documentosPorConsulta, setDocumentosPorConsulta] = useState<Record<number, DocumentoClinicoItem[]>>({});
  const [loadingDocumentos, setLoadingDocumentos] = useState(false);

  useEffect(() => {
    if (historicoEnriquecido.length === 0) {
      setDocumentosPorConsulta({});
      return;
    }
    let cancelled = false;
    setLoadingDocumentos(true);
    Promise.all(
      historicoEnriquecido.map((h) =>
        ClinicaBelezaAPI.documentos
          .list(h.id)
          .then((data) => ({ id: h.id, docs: parseListaDocumentos(data) }))
          .catch(() => ({ id: h.id, docs: [] as DocumentoClinicoItem[] })),
      ),
    )
      .then((results) => {
        if (cancelled) return;
        const map: Record<number, DocumentoClinicoItem[]> = {};
        for (const r of results) map[r.id] = r.docs;
        setDocumentosPorConsulta(map);
      })
      .finally(() => {
        if (!cancelled) setLoadingDocumentos(false);
      });
    return () => {
      cancelled = true;
    };
  }, [historicoEnriquecido, selectedId]);

  const totalDocumentos = Object.values(documentosPorConsulta).reduce((sum, docs) => sum + docs.length, 0);
  const documentosDestaConsulta = documentosPorConsulta[selectedId]?.length ?? 0;

  const prescricoesDestaConsulta = prescricoes.filter((p) => p.consulta === selectedId);

  // Separar prescrições em receituários e exames (prioriza desta consulta)
  const receituarios = prescricoesDestaConsulta.filter(
    (p) => !p.itens?.every((it) => it.tipo === "exame"),
  );
  const exames = prescricoesDestaConsulta.filter(
    (p) => p.itens?.some((it) => it.tipo === "exame"),
  );

  const consultaAtual = historicoEnriquecido.find((h) => h.id === selectedId);
  const evolucoesDestaConsulta = consultaAtual?.total_evolucoes ?? 0;

  const sections: { id: HistoricoSection; label: string; icon: typeof Pill; count: number }[] = [
    { id: "atendimentos", label: "Atendimentos", icon: ClipboardList, count: historicoEnriquecido.length },
    { id: "receituarios", label: "Receituários", icon: Pill, count: receituarios.length },
    { id: "exames", label: "Exames", icon: FlaskConical, count: exames.length },
    { id: "documentos", label: "Documentos", icon: FolderOpen, count: documentosDestaConsulta || totalDocumentos },
    { id: "evolucoes", label: "Evoluções", icon: Activity, count: evolucoesDestaConsulta || historicoEnriquecido.reduce((sum, h) => sum + (h.total_evolucoes || 0), 0) },
  ];

  return (
    <div className="space-y-4">
      {consultaAtual && (
        <div className="rounded-xl border border-[#8B3D52]/30 bg-[#F5E6EA]/30 dark:bg-neutral-800/80 p-4">
          <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Consulta atual — {consultaAtual.procedure_name}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {formatData(consultaAtual.data_inicio)}
            {consultaAtual.professional_name ? ` · ${consultaAtual.professional_name}` : ""}
            {consultaAtual.protocol_name ? ` · ${consultaAtual.protocol_name}` : ""}
          </p>
          <div className="flex flex-wrap gap-2 mt-3">
            {sections.map(({ id, label, count }) => (
              count > 0 ? (
                <button
                  key={id}
                  type="button"
                  onClick={() => setSection(id)}
                  className="text-xs px-2.5 py-1 rounded-full bg-white dark:bg-neutral-700 border border-gray-200 dark:border-neutral-600 text-gray-700 dark:text-gray-300 hover:border-[#8B3D52]"
                >
                  {label} ({count})
                </button>
              ) : null
            ))}
          </div>
        </div>
      )}

      {/* Sub-tabs */}
      <div className="flex flex-wrap gap-2">
        {sections.map(({ id, label, icon: Icon, count }) => (
          <button
            key={id}
            type="button"
            onClick={() => setSection(id)}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              section === id
                ? "bg-[#8B3D52] text-white"
                : "bg-gray-100 dark:bg-neutral-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-neutral-700"
            }`}
          >
            <Icon size={14} />
            {label}
            {count > 0 && (
              <span className={`ml-1 px-1.5 py-0.5 rounded-full text-[10px] ${
                section === id ? "bg-white/20 text-white" : "bg-gray-200 dark:bg-neutral-700 text-gray-600 dark:text-gray-400"
              }`}>
                {count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Conteúdo da seção */}
      <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 md:p-5">
        {section === "atendimentos" && (
          <HistoricoAtendimentos
            historico={historicoEnriquecido}
            selectedId={selectedId}
            formatData={formatData}
            onSelect={onSelect}
            printMeta={printMeta}
          />
        )}
        {section === "receituarios" && (
          <HistoricoPrescricoes
            items={receituarios}
            formatData={formatData}
            emptyMsg="Nenhum receituário nesta consulta."
            titulo="Receituário"
            printMeta={printMeta}
          />
        )}
        {section === "exames" && (
          <HistoricoPrescricoes
            items={exames}
            formatData={formatData}
            emptyMsg="Nenhum exame nesta consulta."
            titulo="Pedido de exame"
            printMeta={printMeta}
          />
        )}
        {section === "documentos" && (
          <HistoricoDocumentos
            historico={historicoEnriquecido}
            selectedId={selectedId}
            documentosPorConsulta={documentosPorConsulta}
            loading={loadingDocumentos}
            formatData={formatData}
            somenteConsultaAtual
          />
        )}
        {section === "evolucoes" && (
          <HistoricoEvolucoes
            historico={historicoEnriquecido.filter((h) => h.id === selectedId)}
            formatData={formatData}
            printMeta={printMeta}
            emptyMsg="Nenhuma evolução nesta consulta."
          />
        )}
      </div>
    </div>
  );
}

function HistoricoAtendimentos({
  historico, selectedId, formatData, onSelect, printMeta,
}: {
  historico: Consulta[]; selectedId: number;
  formatData: (d?: string | null) => string;
  onSelect: (c: Consulta) => void;
  printMeta: ConsultaPrintMeta;
}) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  if (historico.length === 0) return <p className="text-gray-500 text-sm">Nenhuma consulta anterior.</p>;
  return (
    <div className="space-y-2">
      {historico.map((h) => {
        const isExpanded = expandedId === h.id;
        const conteudo = h.observacoes_gerais || h.protocolo_notas;
        return (
          <div key={h.id} className={`rounded-lg border transition-colors ${
            h.id === selectedId
              ? "border-[#8B3D52] bg-[#F5E6EA]/40 dark:bg-neutral-700"
              : "border-gray-200 dark:border-neutral-600"
          }`}>
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
                  <ConsultaPrintButton
                    onPrint={() => imprimirConsultaPdf(h.id, "atendimento")}
                  />
                )}
                {h.id !== selectedId && (
                  conteudo ? (
                    isExpanded ? <ChevronDown size={16} className="text-gray-400 shrink-0" /> : <ChevronRight size={16} className="text-gray-400 shrink-0" />
                  ) : (
                    <button type="button" onClick={(e) => { e.stopPropagation(); onSelect(h); }} className="text-xs text-purple-600 dark:text-purple-400 hover:underline">
                      Abrir
                    </button>
                  )
                )}
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
                <pre className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">{conteudo}</pre>
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

function HistoricoPrescricoes({
  items, formatData, emptyMsg, titulo, printMeta,
}: {
  items: PrescricaoMemedItem[];
  formatData: (d?: string | null) => string;
  emptyMsg: string;
  titulo: string;
  printMeta: ConsultaPrintMeta;
}) {
  if (items.length === 0) return <p className="text-gray-500 text-sm">{emptyMsg}</p>;
  return (
    <div className="space-y-3">
      {items.map((p) => (
        <div key={p.id} className="p-3 rounded-lg border border-gray-200 dark:border-neutral-600">
          <div className="flex items-start justify-between gap-2">
            <p className="text-xs text-gray-500">
              {formatData(p.created_at)}
              {p.professional_name ? ` · ${p.professional_name}` : ""}
            </p>
            <div className="flex items-center gap-2 shrink-0">
              <ConsultaPrintButton
                onPrint={() => {
                  if (p.pdf_url) {
                    window.open(p.pdf_url, "_blank");
                    return;
                  }
                  alert("Receituário sem PDF. Use a aba Documentos ou Memed para imprimir com timbrado.");
                }}
              />
            </div>
          </div>
          {p.itens && p.itens.length > 0 ? (
            <ul className="mt-1.5 space-y-1">
              {p.itens.map((it, idx) => (
                <li key={idx} className="text-sm text-gray-800 dark:text-gray-200">
                  <span className="font-medium">{it.nome}</span>
                  {it.posologia ? <span className="text-gray-500"> — {it.posologia}</span> : null}
                </li>
              ))}
            </ul>
          ) : (
            p.resumo && <p className="mt-1.5 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line">{p.resumo}</p>
          )}
        </div>
      ))}
    </div>
  );
}

function HistoricoDocumentos({
  historico,
  selectedId,
  documentosPorConsulta,
  loading,
  formatData,
  somenteConsultaAtual = false,
}: {
  historico: Consulta[];
  selectedId: number;
  documentosPorConsulta: Record<number, DocumentoClinicoItem[]>;
  loading: boolean;
  formatData: (d?: string | null) => string;
  somenteConsultaAtual?: boolean;
}) {
  const lista = somenteConsultaAtual
    ? historico.filter((h) => h.id === selectedId)
    : historico;
  const consultasComDocs = lista.filter((h) => (documentosPorConsulta[h.id]?.length ?? 0) > 0);

  if (loading) return <p className="text-gray-500 text-sm">Carregando documentos…</p>;
  if (consultasComDocs.length === 0) {
    return (
      <p className="text-gray-500 text-sm">
        {somenteConsultaAtual
          ? "Nenhum documento registrado nesta consulta."
          : "Nenhum documento registrado nas consultas."}
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {consultasComDocs.map((h) => {
        const docs = documentosPorConsulta[h.id] ?? [];
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
                    <ConsultaPrintButton onPrint={() => imprimirDocumentoPdf(doc)} />
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

function HistoricoEvolucoes({
  historico, formatData, printMeta, emptyMsg = "Nenhuma evolução registrada.",
}: {
  historico: Consulta[];
  formatData: (d?: string | null) => string;
  printMeta: ConsultaPrintMeta;
  emptyMsg?: string;
}) {
  if (historico.length === 0) return <p className="text-gray-500 text-sm">{emptyMsg}</p>;

  return (
    <div className="space-y-4">
      {historico.map((h) => (
        <EvolucaoConsultaBlock key={h.id} consulta={h} formatData={formatData} printMeta={printMeta} />
      ))}
    </div>
  );
}

function EvolucaoConsultaBlock({
  consulta,
  formatData,
  printMeta,
}: {
  consulta: Consulta;
  formatData: (d?: string | null) => string;
  printMeta: ConsultaPrintMeta;
}) {
  const [evolucoes, setEvolucoes] = useState<Evolucao[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    ClinicaBelezaAPI.consultas.evolucoes.list(consulta.id).then((data) => {
      setEvolucoes(Array.isArray(data) ? data : []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [consulta.id]);

  return (
    <div className="border border-gray-200 dark:border-neutral-600 rounded-lg overflow-hidden">
      <div className="px-3 py-2 bg-gray-50 dark:bg-neutral-700/50 border-b border-gray-200 dark:border-neutral-600 flex items-center justify-between gap-2">
        <p className="text-xs font-medium text-gray-800 dark:text-gray-200">
          {consulta.procedure_name} · {formatData(consulta.data_inicio)}
          {consulta.professional_name ? ` · ${consulta.professional_name}` : ""}
        </p>
        {!loading && evolucoes.length > 0 && (
          <ConsultaPrintButton
            label="Imprimir"
            onPrint={() => imprimirConsultaPdf(consulta.id, "evolucao")}
          />
        )}
      </div>
      <div className="p-3 space-y-2">
        {loading ? (
          <p className="text-xs text-gray-400">Carregando...</p>
        ) : evolucoes.length === 0 ? (
          <p className="text-xs text-gray-400">Sem evoluções.</p>
        ) : (
          evolucoes.map((ev, idx) => (
            <div key={ev.id} className="text-sm space-y-1">
              <div className="flex items-start justify-between gap-2">
                <p className="text-xs text-gray-500">
                  {formatData(ev.created_at)}
                  {ev.professional_name ? ` · ${ev.professional_name}` : ""}
                </p>
                <ConsultaPrintButton
                  onPrint={() => imprimirConsultaPdf(consulta.id, "evolucao")}
                />
              </div>
              {ev.descricao && <p className="text-gray-800 dark:text-gray-200">{ev.descricao}</p>}
              {ev.procedimento_realizado && (
                <p className="text-gray-600 dark:text-gray-400"><span className="font-medium">Procedimento:</span> {ev.procedimento_realizado}</p>
              )}
              {ev.produtos_utilizados && (
                <p className="text-gray-600 dark:text-gray-400"><span className="font-medium">Produtos:</span> {ev.produtos_utilizados}</p>
              )}
              {ev.orientacoes && (
                <p className="text-gray-600 dark:text-gray-400"><span className="font-medium">Orientações:</span> {ev.orientacoes}</p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
