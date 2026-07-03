"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ChevronRight,
  ChevronDown,
  ClipboardList,
  Activity,
  FolderOpen,
  FileText,
  Camera,
} from "lucide-react";
import { ClinicaBelezaAPI, type DocumentoClinicoItem, type PacienteFotoItem } from "@/lib/clinica-beleza-api";
import { imprimirConsultaPdfLazy, imprimirDocumentoPdfLazy, type ConsultaPrintMeta } from "@/lib/consulta-print-lazy";
import type { Anamnese, Consulta, Evolucao } from "./consultas-types";
import { ANAMNESE_FIELDS } from "./consultas-types";
import type { PrescricaoMemedItem } from "@/lib/clinica-beleza-api";
import { abrirPdfPrescricaoMemed } from "@/lib/memed-prescricao-pdf";
import { ConsultaPrintButton } from "./ConsultaPrintButton";
import { PacienteFotoZoomModal } from "./PacienteFotoZoomModal";

type HistoricoSection =
  | "atendimentos"
  | "anamnese"
  | "fotos"
  | "documentos"
  | "evolucoes";

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
  consultaId,
  anamnese,
  prescricoes = [],
  observacoesAtual = "",
  protocoloNotasAtual,
  formatData,
  onSelect,
  printMeta,
}: {
  historico: Consulta[];
  selectedId: number;
  consultaId: number;
  anamnese: Anamnese;
  prescricoes?: PrescricaoMemedItem[];
  observacoesAtual?: string;
  protocoloNotasAtual?: string | null;
  formatData: (d?: string | null) => string;
  onSelect: (c: Consulta) => void;
  printMeta: ConsultaPrintMeta;
}) {
  const [section, setSection] = useState<HistoricoSection>("atendimentos");
  const [fotos, setFotos] = useState<PacienteFotoItem[]>([]);
  const [loadingFotos, setLoadingFotos] = useState(false);
  const [zoomFoto, setZoomFoto] = useState<PacienteFotoItem | null>(null);

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
    if (section !== "documentos") return;
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
  }, [section, historicoEnriquecido]);

  useEffect(() => {
    if (!consultaId) return;
    let cancelled = false;
    setLoadingFotos(true);
    ClinicaBelezaAPI.consultas.fotos
      .list(consultaId)
      .then((res) => {
        if (!cancelled) setFotos(res.fotos || []);
      })
      .catch(() => {
        if (!cancelled) setFotos([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingFotos(false);
      });
    return () => {
      cancelled = true;
    };
  }, [consultaId]);

  const totalDocumentos =
    Object.values(documentosPorConsulta).reduce((sum, docs) => sum + docs.length, 0) + prescricoes.length;

  const consultaAtual = historicoEnriquecido.find((h) => h.id === selectedId);
  const totalEvolucoes = historicoEnriquecido.reduce((sum, h) => sum + (h.total_evolucoes || 0), 0);
  const camposAnamnesePreenchidos = ANAMNESE_FIELDS.filter(([key]) => {
    const val = anamnese[key as keyof Anamnese];
    return val != null && String(val).trim() !== "";
  }).length;

  const sections: { id: HistoricoSection; label: string; icon: typeof FolderOpen; count: number }[] = [
    { id: "atendimentos", label: "Atendimentos", icon: ClipboardList, count: historicoEnriquecido.length },
    { id: "anamnese", label: "Anamnese", icon: FileText, count: camposAnamnesePreenchidos },
    { id: "fotos", label: "Fotos", icon: Camera, count: fotos.length },
    { id: "documentos", label: "Documentos", icon: FolderOpen, count: totalDocumentos },
    { id: "evolucoes", label: "Evoluções", icon: Activity, count: totalEvolucoes },
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
        {section === "anamnese" && <HistoricoAnamnese anamnese={anamnese} printMeta={printMeta} />}
        {section === "fotos" && (
          <HistoricoFotos
            fotos={fotos}
            loading={loadingFotos}
            onZoom={setZoomFoto}
          />
        )}
        {section === "documentos" && (
          <HistoricoDocumentos
            historico={historicoEnriquecido}
            selectedId={selectedId}
            documentosPorConsulta={documentosPorConsulta}
            prescricoes={prescricoes}
            loading={loadingDocumentos}
            formatData={formatData}
          />
        )}
        {section === "evolucoes" && (
          <HistoricoEvolucoes
            historico={historicoEnriquecido}
            formatData={formatData}
            printMeta={printMeta}
            emptyMsg="Nenhuma evolução registrada no histórico."
          />
        )}
      </div>

      {zoomFoto && (
        <PacienteFotoZoomModal
          foto={zoomFoto}
          fotos={fotos}
          onClose={() => setZoomFoto(null)}
          onChangeFoto={setZoomFoto}
        />
      )}
    </div>
  );
}

function HistoricoAnamnese({
  anamnese,
  printMeta,
}: {
  anamnese: Anamnese;
  printMeta: ConsultaPrintMeta;
}) {
  const preenchidos = ANAMNESE_FIELDS.filter(([key]) => {
    const val = anamnese[key as keyof Anamnese];
    return val != null && String(val).trim() !== "";
  });

  if (preenchidos.length === 0) {
    return <p className="text-gray-500 text-sm">Nenhum dado de anamnese registrado para este paciente.</p>;
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <ConsultaPrintButton onPrint={() => imprimirConsultaPdfLazy(printMeta.consultaId, "anamnese")} />
      </div>
      {preenchidos.map(([key, label]) => (
        <div key={key}>
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">{label}</p>
          <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap mt-0.5">
            {String(anamnese[key as keyof Anamnese])}
          </p>
        </div>
      ))}
      {(anamnese.peso || anamnese.altura) && (
        <div className="flex gap-6 text-sm text-gray-700 dark:text-gray-300">
          {anamnese.peso ? <span><strong>Peso:</strong> {anamnese.peso} kg</span> : null}
          {anamnese.altura ? <span><strong>Altura:</strong> {anamnese.altura} m</span> : null}
        </div>
      )}
    </div>
  );
}

function HistoricoFotos({
  fotos,
  loading,
  onZoom,
}: {
  fotos: PacienteFotoItem[];
  loading: boolean;
  onZoom: (foto: PacienteFotoItem) => void;
}) {
  if (loading) return <p className="text-gray-500 text-sm">Carregando fotos…</p>;
  if (fotos.length === 0) {
    return <p className="text-gray-500 text-sm">Nenhuma foto de acompanhamento registrada.</p>;
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
      {fotos.map((foto) => (
        <button
          key={foto.id}
          type="button"
          onClick={() => onZoom(foto)}
          className="text-left rounded-lg border border-gray-200 dark:border-neutral-600 overflow-hidden hover:border-[#8B3D52] transition-colors"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={foto.cloudinary_url}
            alt={`Foto ${foto.consulta_data}`}
            className="w-full aspect-square object-cover cursor-zoom-in"
          />
          <p className="text-[10px] text-gray-500 dark:text-gray-400 px-2 py-1.5 truncate">
            {foto.consulta_data || "—"} · {foto.origem_display}
          </p>
        </button>
      ))}
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

  if (historico.length === 0) {
    return <p className="text-gray-500 text-sm">Nenhuma consulta encontrada para este paciente.</p>;
  }
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
                    onPrint={() => imprimirConsultaPdfLazy(h.id, "atendimento")}
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

function labelPrescricaoMemed(p: PrescricaoMemedItem): string {
  const ehExame = p.itens?.some((it) => it.tipo === "exame");
  return ehExame ? "Exames (Memed)" : "Receituário (Memed)";
}

function HistoricoDocumentos({
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
  const prescricoesPorConsulta = prescricoes.reduce<Record<number, PrescricaoMemedItem[]>>((acc, p) => {
    if (p.consulta == null) return acc;
    if (!acc[p.consulta]) acc[p.consulta] = [];
    acc[p.consulta].push(p);
    return acc;
  }, {});

  const lista = somenteConsultaAtual
    ? historico.filter((h) => h.id === selectedId)
    : historico;
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
            label={evolucoes.length > 1 ? "Imprimir todas" : "Imprimir"}
            onPrint={() => imprimirConsultaPdfLazy(consulta.id, "evolucao")}
          />
        )}
      </div>
      <div className="p-3 space-y-2">
        {loading ? (
          <p className="text-xs text-gray-400">Carregando...</p>
        ) : evolucoes.length === 0 ? (
          <p className="text-xs text-gray-400">Sem evoluções.</p>
        ) : (
          evolucoes.map((ev) => (
            <div key={ev.id} className="text-sm space-y-1">
              <p className="text-xs text-gray-500">
                {formatData(ev.created_at)}
                {ev.professional_name ? ` · ${ev.professional_name}` : ""}
              </p>
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
