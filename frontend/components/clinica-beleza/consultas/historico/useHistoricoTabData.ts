import { useEffect, useMemo, useState } from "react";
import apiClient from "@/lib/api-client";
import { ClinicaBelezaAPI, type DocumentoClinicoItem, type PacienteFotoItem, type PrescricaoMemedItem } from "@/lib/clinica-beleza-api";
import type { Orcamento } from "../tab-panels/orcamento-tab/types";
import type { Anamnese, Consulta } from "../consultas-types";
import { ANAMNESE_FIELDS } from "../consultas-types";
import type { HistoricoSection, HistoricoSectionConfig } from "./historico-types";
import { HISTORICO_SECTION_ICONS } from "./historico-types";
import { parseListaDocumentos } from "./historico-utils";

export function useHistoricoTabData({
  historico,
  selectedId,
  consultaId,
  patientId,
  anamnese,
  prescricoes = [],
  observacoesAtual = "",
  protocoloNotasAtual,
  section,
}: {
  historico: Consulta[];
  selectedId: number;
  consultaId: number;
  patientId?: number | null;
  anamnese: Anamnese;
  prescricoes?: PrescricaoMemedItem[];
  observacoesAtual?: string;
  protocoloNotasAtual?: string | null;
  section: HistoricoSection;
}) {
  const [fotos, setFotos] = useState<PacienteFotoItem[]>([]);
  const [loadingFotos, setLoadingFotos] = useState(false);
  const [documentosPorConsulta, setDocumentosPorConsulta] = useState<Record<number, DocumentoClinicoItem[]>>({});
  const [loadingDocumentos, setLoadingDocumentos] = useState(false);
  const [orcamentos, setOrcamentos] = useState<Orcamento[]>([]);
  const [loadingOrcamentos, setLoadingOrcamentos] = useState(false);

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

  useEffect(() => {
    if (!patientId) {
      setOrcamentos([]);
      return;
    }
    let cancelled = false;
    setLoadingOrcamentos(true);
    apiClient
      .get<Orcamento[]>(`/clinica-beleza/orcamentos/?patient_id=${patientId}`)
      .then((res) => {
        if (!cancelled) setOrcamentos(Array.isArray(res.data) ? res.data : []);
      })
      .catch(() => {
        if (!cancelled) setOrcamentos([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingOrcamentos(false);
      });
    return () => {
      cancelled = true;
    };
  }, [patientId]);

  const consultaAtual = historicoEnriquecido.find((h) => h.id === selectedId);
  const totalDocumentos =
    Object.values(documentosPorConsulta).reduce((sum, docs) => sum + docs.length, 0) + prescricoes.length;
  const totalEvolucoes = historicoEnriquecido.reduce((sum, h) => sum + (h.total_evolucoes || 0), 0);
  const camposAnamnesePreenchidos = ANAMNESE_FIELDS.filter(([key]) => {
    const val = anamnese[key as keyof Anamnese];
    return val != null && String(val).trim() !== "";
  }).length;

  const sections: HistoricoSectionConfig[] = [
    { id: "atendimentos", label: "Atendimentos", icon: HISTORICO_SECTION_ICONS.atendimentos, count: historicoEnriquecido.length },
    { id: "anamnese", label: "Anamnese", icon: HISTORICO_SECTION_ICONS.anamnese, count: camposAnamnesePreenchidos },
    { id: "fotos", label: "Fotos", icon: HISTORICO_SECTION_ICONS.fotos, count: fotos.length },
    { id: "documentos", label: "Documentos", icon: HISTORICO_SECTION_ICONS.documentos, count: totalDocumentos },
    { id: "orcamentos", label: "Orçamentos", icon: HISTORICO_SECTION_ICONS.orcamentos, count: orcamentos.length },
    { id: "evolucoes", label: "Evoluções", icon: HISTORICO_SECTION_ICONS.evolucoes, count: totalEvolucoes },
  ];

  return {
    historicoEnriquecido,
    consultaAtual,
    fotos,
    loadingFotos,
    documentosPorConsulta,
    loadingDocumentos,
    orcamentos,
    loadingOrcamentos,
    sections,
  };
}
