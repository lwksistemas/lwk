import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ClinicaBelezaAPI, type ProntuarioData } from "@/lib/clinica-beleza-api";
import { fetchHistoricoPaciente } from "@/lib/clinica-beleza-cadastros-api";
import { logger } from "@/lib/logger";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import { buildConsultaDetailHref } from "@/components/clinica-beleza/consultas-page/consultas-page-utils";
import { buildProntuarioHubPath } from "./prontuario-paths";
import { buildProntuarioConsultasResumo } from "./prontuario-consultas-utils";
import { isProntuarioLocalTab, resolvePatientDisplayName } from "./prontuario-utils";
import type { ProntuarioTabId } from "./prontuario-types";

export function useProntuarioPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;
  const patientId = Number(params.id);

  const [activeTab, setActiveTab] = useState<ProntuarioTabId>("resumo");
  const [data, setData] = useState<ProntuarioData | null>(null);
  const [loading, setLoading] = useState(false);
  const [patientName, setPatientName] = useState("");
  const [consultas, setConsultas] = useState<Consulta[]>([]);
  const [consultasLoading, setConsultasLoading] = useState(true);

  const loadProntuario = useCallback(
    async (secao?: string) => {
      if (secao && isProntuarioLocalTab(secao as ProntuarioTabId)) return;
      setLoading(true);
      try {
        const result = await ClinicaBelezaAPI.prontuario.get(patientId, secao);
        setData(result);
      } catch (e) {
        logger.warn("Erro ao carregar prontuário:", e);
        setData(null);
      } finally {
        setLoading(false);
      }
    },
    [patientId],
  );

  const loadPatientName = useCallback(async () => {
    try {
      const patient = await ClinicaBelezaAPI.get<{ name?: string; nome?: string }>(
        `/patients/${patientId}/`,
      );
      setPatientName(resolvePatientDisplayName(patient));
    } catch {
      setPatientName("Paciente");
    }
  }, [patientId]);

  const loadConsultas = useCallback(async () => {
    setConsultasLoading(true);
    try {
      const rows = await fetchHistoricoPaciente(patientId);
      setConsultas(rows);
    } catch (e) {
      logger.warn("Erro ao carregar consultas do prontuário:", e);
      setConsultas([]);
    } finally {
      setConsultasLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    void loadPatientName();
    void loadConsultas();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- carrega ao montar / mudar paciente
  }, [loadPatientName, loadConsultas, patientId]);

  const handleTabChange = (tabId: ProntuarioTabId) => {
    setActiveTab(tabId);
    if (!isProntuarioLocalTab(tabId)) {
      setLoading(true);
      void loadProntuario(tabId);
    }
  };

  const voltarHub = () => {
    router.push(buildProntuarioHubPath(slug));
  };

  const abrirConsulta = (consultaId: number) => {
    router.push(buildConsultaDetailHref(slug, consultaId));
  };

  const handlePrintSecao = () => {
    if (isProntuarioLocalTab(activeTab)) return;
    const url = ClinicaBelezaAPI.prontuario.pdfUrl(patientId, activeTab);
    window.open(url, "_blank");
  };

  const handlePrintCompleto = () => {
    const url = ClinicaBelezaAPI.prontuario.pdfUrl(patientId);
    window.open(url, "_blank");
  };

  const { consultaParaFotosId } = buildProntuarioConsultasResumo(consultas);

  return {
    slug,
    patientId,
    activeTab,
    data,
    loading,
    patientName,
    consultas,
    consultasLoading,
    consultaParaFotosId,
    handleTabChange,
    voltarHub,
    abrirConsulta,
    handlePrintSecao,
    handlePrintCompleto,
  };
}
