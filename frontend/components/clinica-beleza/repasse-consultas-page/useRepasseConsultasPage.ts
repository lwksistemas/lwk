import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import {
  buildRelatorioPdfFilename,
  downloadBlob,
  getDefaultRelatorioPeriod,
} from "@/components/clinica-beleza/relatorios-shared/relatorios-shared-utils";
import { useRelatorioProfessionals } from "@/components/clinica-beleza/relatorios-shared/useRelatorioProfessionals";
import type { RelatorioRepasseData } from "./repasse-consultas-page-types";

export function useRepasseConsultasPage() {
  const params = useParams();
  const slug = params.slug as string;
  const defaultPeriod = getDefaultRelatorioPeriod();

  const [dataInicio, setDataInicio] = useState(defaultPeriod.dataInicio);
  const [dataFim, setDataFim] = useState(defaultPeriod.dataFim);
  const [professionalId, setProfessionalId] = useState("");
  const [data, setData] = useState<RelatorioRepasseData | null>(null);
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [error, setError] = useState("");

  const professionals = useRelatorioProfessionals();

  const profissionalNome = useMemo(() => {
    if (!professionalId) return null;
    return professionals.find((x) => String(x.id) === professionalId)?.nome ?? null;
  }, [professionalId, professionals]);

  const buscar = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const qp = new URLSearchParams({ data_inicio: dataInicio, data_fim: dataFim });
      if (professionalId) qp.set("professional_id", professionalId);
      const res = await clinicaBelezaFetch(`/relatorios/repasse-consultas/?${qp.toString()}`);
      if (res.ok) {
        setData(await res.json());
      } else {
        setError("Erro ao carregar dados.");
        setData(null);
      }
    } catch {
      setError("Erro ao carregar dados.");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [dataInicio, dataFim, professionalId]);

  useEffect(() => {
    void buscar();
  }, [buscar]);

  const exportarPDF = useCallback(async () => {
    setPdfLoading(true);
    setError("");
    try {
      const qp = new URLSearchParams({ data_inicio: dataInicio, data_fim: dataFim });
      if (professionalId) qp.set("professional_id", professionalId);
      const res = await clinicaBelezaFetch(`/relatorios/repasse-consultas/pdf/?${qp.toString()}`);
      if (!res.ok) {
        setError("Não foi possível gerar o PDF.");
        return;
      }
      const blob = await res.blob();
      const nome = profissionalNome
        ? buildRelatorioPdfFilename("repasse", profissionalNome, dataInicio, dataFim)
        : `repasse_consultas_${dataInicio}_${dataFim}.pdf`;
      downloadBlob(blob, nome);
    } catch {
      setError("Não foi possível gerar o PDF.");
    } finally {
      setPdfLoading(false);
    }
  }, [dataFim, dataInicio, profissionalNome, professionalId]);

  return {
    slug,
    dataInicio,
    setDataInicio,
    dataFim,
    setDataFim,
    professionalId,
    setProfessionalId,
    professionals,
    data,
    loading,
    error,
    pdfLoading,
    buscar,
    exportarPDF,
  };
}
