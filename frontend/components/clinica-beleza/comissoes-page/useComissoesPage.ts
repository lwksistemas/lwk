import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import {
  buildRelatorioPdfFilename,
  downloadBlob,
  getDefaultRelatorioPeriod,
} from "@/components/clinica-beleza/relatorios-shared/relatorios-shared-utils";
import { useRelatorioProfessionals } from "@/components/clinica-beleza/relatorios-shared/useRelatorioProfessionals";
import { downloadComissoesCsv, ensureComissoesPrintStyles } from "./comissoes-page-utils";
import type { RelatorioComissoesData } from "./comissoes-page-types";

export function useComissoesPage() {
  const params = useParams();
  const slug = params.slug as string;

  const defaultPeriod = getDefaultRelatorioPeriod();
  const [dataInicio, setDataInicio] = useState(defaultPeriod.dataInicio);
  const [dataFim, setDataFim] = useState(defaultPeriod.dataFim);
  const [professionalId, setProfessionalId] = useState("");

  const [data, setData] = useState<RelatorioComissoesData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [logoUrl, setLogoUrl] = useState<string | null>(null);
  const [clinicaNome, setClinicaNome] = useState("");
  const [temTimbrado, setTemTimbrado] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);

  const professionals = useRelatorioProfessionals();

  const profissionalNome = useMemo(() => {
    if (!professionalId) return null;
    return professionals.find((x) => String(x.id) === professionalId)?.nome ?? null;
  }, [professionalId, professionals]);

  useEffect(() => {
    ensureComissoesPrintStyles();
  }, []);

  useEffect(() => {
    clinicaBelezaFetch("/loja-info/")
      .then(async (res) => {
        if (res.ok) {
          const info = await res.json();
          setClinicaNome(info.nome || info.owner_username || "");
        }
      })
      .catch(() => {});
    fetch(`/api/superadmin/lojas/info_publica/?slug=${slug}`)
      .then(async (res) => {
        if (res.ok) {
          const info = await res.json();
          if (info.logo) setLogoUrl(info.logo);
          else if (info.login_logo) setLogoUrl(info.login_logo);
          if (info.nome) setClinicaNome(info.nome);
        }
      })
      .catch(() => {});
    clinicaBelezaFetch("/memed/timbrado/")
      .then(async (res) => {
        if (res.ok) {
          const t = await res.json();
          setTemTimbrado(Boolean(t.tem_timbrado));
        }
      })
      .catch(() => {});
  }, [slug]);

  const buscar = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const qp = new URLSearchParams({ data_inicio: dataInicio, data_fim: dataFim });
      if (professionalId) qp.set("professional_id", professionalId);
      const res = await clinicaBelezaFetch(`/relatorios/comissoes/?${qp.toString()}`);
      if (res.ok) {
        setData(await res.json());
      } else {
        setError("Erro ao carregar dados. Tente novamente.");
        setData(null);
      }
    } catch {
      setError("Erro ao carregar dados. Tente novamente.");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [dataInicio, dataFim, professionalId]);

  useEffect(() => {
    void buscar();
  }, [buscar]);

  const exportarCSV = useCallback(() => {
    if (!data) return;
    downloadComissoesCsv(data, dataInicio, dataFim);
  }, [data, dataInicio, dataFim]);

  const exportarPDF = useCallback(async () => {
    setPdfLoading(true);
    setError("");
    try {
      const qp = new URLSearchParams({ data_inicio: dataInicio, data_fim: dataFim });
      if (professionalId) qp.set("professional_id", professionalId);
      const res = await clinicaBelezaFetch(`/relatorios/comissoes/pdf/?${qp.toString()}`);
      if (!res.ok) {
        setError("Não foi possível gerar o PDF. Tente novamente.");
        return;
      }
      const blob = await res.blob();
      downloadBlob(
        blob,
        buildRelatorioPdfFilename("comissoes", profissionalNome, dataInicio, dataFim),
      );
    } catch {
      setError("Não foi possível gerar o PDF. Tente novamente.");
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
    profissionalNome,
    data,
    loading,
    error,
    logoUrl,
    clinicaNome,
    temTimbrado,
    pdfLoading,
    buscar,
    exportarCSV,
    exportarPDF,
  };
}
