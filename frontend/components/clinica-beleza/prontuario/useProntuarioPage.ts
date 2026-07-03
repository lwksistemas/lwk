import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ClinicaBelezaAPI, type ProntuarioData } from "@/lib/clinica-beleza-api";
import { logger } from "@/lib/logger";
import { resolvePatientDisplayName } from "./prontuario-utils";
import type { ProntuarioTabId } from "./prontuario-types";

export function useProntuarioPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;
  const patientId = Number(params.id);

  const [activeTab, setActiveTab] = useState<ProntuarioTabId>("receituario");
  const [data, setData] = useState<ProntuarioData | null>(null);
  const [loading, setLoading] = useState(true);
  const [patientName, setPatientName] = useState("");

  const loadProntuario = useCallback(
    async (secao?: string) => {
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

  useEffect(() => {
    void loadPatientName();
    void loadProntuario(activeTab);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- carrega ao montar / mudar paciente
  }, [loadPatientName, patientId]);

  const handleTabChange = (tabId: ProntuarioTabId) => {
    setActiveTab(tabId);
    void loadProntuario(tabId);
  };

  const voltarPacientes = () => {
    router.push(`/loja/${slug}/clinica-beleza/pacientes`);
  };

  const handlePrintSecao = () => {
    const url = ClinicaBelezaAPI.prontuario.pdfUrl(patientId, activeTab);
    window.open(url, "_blank");
  };

  const handlePrintCompleto = () => {
    const url = ClinicaBelezaAPI.prontuario.pdfUrl(patientId);
    window.open(url, "_blank");
  };

  return {
    slug,
    patientId,
    activeTab,
    data,
    loading,
    patientName,
    handleTabChange,
    voltarPacientes,
    handlePrintSecao,
    handlePrintCompleto,
  };
}
