"use client";

import { useState } from "react";
import type { PacienteFotoItem, PrescricaoMemedItem } from "@/lib/clinica-beleza-api";
import type { ConsultaPrintMeta } from "@/lib/consulta-print";
import type { Anamnese, Consulta } from "./consultas-types";
import { PacienteFotoZoomModal } from "./PacienteFotoZoomModal";
import { HistoricoAnamneseSection } from "./historico/HistoricoAnamneseSection";
import { HistoricoAtendimentosSection } from "./historico/HistoricoAtendimentosSection";
import { HistoricoDocumentosSection } from "./historico/HistoricoDocumentosSection";
import { HistoricoEvolucoesSection } from "./historico/HistoricoEvolucoesSection";
import { HistoricoFotosSection } from "./historico/HistoricoFotosSection";
import { HistoricoSectionNav } from "./historico/HistoricoSectionNav";
import type { HistoricoSection } from "./historico/historico-types";
import { useHistoricoTabData } from "./historico/useHistoricoTabData";

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
  const [zoomFoto, setZoomFoto] = useState<PacienteFotoItem | null>(null);

  const {
    historicoEnriquecido,
    consultaAtual,
    fotos,
    loadingFotos,
    documentosPorConsulta,
    loadingDocumentos,
    sections,
  } = useHistoricoTabData({
    historico,
    selectedId,
    consultaId,
    anamnese,
    prescricoes,
    observacoesAtual,
    protocoloNotasAtual,
    section,
  });

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

      <HistoricoSectionNav sections={sections} active={section} onChange={setSection} />

      <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 md:p-5">
        {section === "atendimentos" && (
          <HistoricoAtendimentosSection
            historico={historicoEnriquecido}
            selectedId={selectedId}
            formatData={formatData}
            onSelect={onSelect}
          />
        )}
        {section === "anamnese" && <HistoricoAnamneseSection anamnese={anamnese} printMeta={printMeta} />}
        {section === "fotos" && (
          <HistoricoFotosSection fotos={fotos} loading={loadingFotos} onZoom={setZoomFoto} />
        )}
        {section === "documentos" && (
          <HistoricoDocumentosSection
            historico={historicoEnriquecido}
            selectedId={selectedId}
            documentosPorConsulta={documentosPorConsulta}
            prescricoes={prescricoes}
            loading={loadingDocumentos}
            formatData={formatData}
          />
        )}
        {section === "evolucoes" && (
          <HistoricoEvolucoesSection
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
