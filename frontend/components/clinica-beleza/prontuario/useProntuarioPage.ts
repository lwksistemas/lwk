import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ClinicaBelezaAPI, type ProntuarioData } from "@/lib/clinica-beleza-api";
import { fetchClinicaSchedulingProfessionals, fetchHistoricoPaciente } from "@/lib/clinica-beleza-cadastros-api";
import { formatApiErrorBody } from "@/lib/api-errors";
import { logger } from "@/lib/logger";
import { useToast } from "@/components/ui/Toast";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import { buildConsultaDetailHref } from "@/components/clinica-beleza/consultas-page/consultas-page-utils";
import { buildProntuarioHubPath } from "./prontuario-paths";
import { buildProntuarioConsultasResumo } from "./prontuario-consultas-utils";
import { imprimirProntuarioPdf } from "./prontuario-document-print";
import { isProntuarioLocalTab, resolvePatientDisplayName } from "./prontuario-utils";
import type { ProntuarioTabId } from "./prontuario-types";

export function useProntuarioPage() {
  const params = useParams();
  const router = useRouter();
  const toast = useToast();
  const slug = params.slug as string;
  const patientId = Number(params.id);

  const [activeTab, setActiveTab] = useState<ProntuarioTabId>("resumo");
  const [data, setData] = useState<ProntuarioData | null>(null);
  const [loading, setLoading] = useState(false);
  const [patientName, setPatientName] = useState("");
  const [consultas, setConsultas] = useState<Consulta[]>([]);
  const [consultasLoading, setConsultasLoading] = useState(true);
  const [printando, setPrintando] = useState<"secao" | "completo" | null>(null);
  const [iniciandoId, setIniciandoId] = useState<number | null>(null);
  const [excluindoId, setExcluindoId] = useState<number | null>(null);
  const [receberConsulta, setReceberConsulta] = useState<Consulta | null>(null);
  const [abrindoReceberId, setAbrindoReceberId] = useState<number | null>(null);
  const [showProfessionalModal, setShowProfessionalModal] = useState(false);
  const [consultaParaIniciar, setConsultaParaIniciar] = useState<Consulta | null>(null);
  const [profissionaisDisponiveis, setProfissionaisDisponiveis] = useState<
    { id: number; nome?: string; name?: string }[]
  >([]);

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

  const handlePrintSecao = async () => {
    if (isProntuarioLocalTab(activeTab) || printando) return;
    setPrintando("secao");
    try {
      await imprimirProntuarioPdf(patientId, activeTab);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erro ao gerar PDF da seção.");
    } finally {
      setPrintando(null);
    }
  };

  const handlePrintCompleto = async () => {
    if (printando) return;
    setPrintando("completo");
    try {
      await imprimirProntuarioPdf(patientId);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erro ao gerar PDF do prontuário.");
    } finally {
      setPrintando(null);
    }
  };

  const executarInicio = useCallback(
    async (consulta: Consulta, professionalId?: number) => {
      setIniciandoId(consulta.id);
      try {
        const body = professionalId ? { professional: professionalId } : undefined;
        await ClinicaBelezaAPI.consultas.iniciar(consulta.id, body);
        toast.success("Consulta iniciada.");
        router.push(buildConsultaDetailHref(slug, consulta.id));
      } catch (e: unknown) {
        toast.error(formatApiErrorBody(e) || "Erro ao iniciar consulta.");
      } finally {
        setIniciandoId(null);
      }
    },
    [router, slug, toast],
  );

  const iniciarConsulta = useCallback(
    async (consulta: Consulta, professionalId?: number) => {
      if (!consulta.professional && !professionalId) {
        try {
          const profs = await fetchClinicaSchedulingProfessionals();
          setProfissionaisDisponiveis(Array.isArray(profs) ? profs : []);
        } catch {
          setProfissionaisDisponiveis([]);
        }
        setConsultaParaIniciar(consulta);
        setShowProfessionalModal(true);
        return;
      }
      await executarInicio(consulta, professionalId);
    },
    [executarInicio],
  );

  const confirmarProfissional = useCallback(
    (professionalId: number) => {
      const consulta = consultaParaIniciar;
      setShowProfessionalModal(false);
      setConsultaParaIniciar(null);
      if (consulta) void iniciarConsulta(consulta, professionalId);
    },
    [consultaParaIniciar, iniciarConsulta],
  );

  const abrirReceber = useCallback(async (consulta: Consulta) => {
    setAbrindoReceberId(consulta.id);
    try {
      const fresh = await ClinicaBelezaAPI.consultas.get(consulta.id);
      setReceberConsulta(fresh);
    } catch {
      setReceberConsulta(consulta);
    } finally {
      setAbrindoReceberId(null);
    }
  }, []);

  const aposRecebimento = useCallback(async (atualizada: Partial<Consulta>) => {
    setReceberConsulta((prev) => (prev ? { ...prev, ...atualizada } : null));
    await loadConsultas();
  }, [loadConsultas]);

  const excluirConsulta = useCallback(
    async (consulta: Consulta) => {
      if (!confirm("Excluir esta consulta? O agendamento vinculado será cancelado.")) return;
      setExcluindoId(consulta.id);
      try {
        await ClinicaBelezaAPI.consultas.excluir(consulta.id);
        toast.success("Consulta excluída.");
        await loadConsultas();
      } catch (e: unknown) {
        toast.error(formatApiErrorBody(e) || "Erro ao excluir consulta.");
      } finally {
        setExcluindoId(null);
      }
    },
    [loadConsultas, toast],
  );

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
    printando,
    iniciandoId,
    excluindoId,
    receberConsulta,
    abrindoReceberId,
    showProfessionalModal,
    profissionaisDisponiveis,
    handleTabChange,
    voltarHub,
    abrirConsulta,
    handlePrintSecao,
    handlePrintCompleto,
    iniciarConsulta,
    confirmarProfissional,
    fecharProfessionalModal: () => {
      setShowProfessionalModal(false);
      setConsultaParaIniciar(null);
    },
    abrirReceber,
    fecharReceber: () => setReceberConsulta(null),
    aposRecebimento,
    excluirConsulta,
  };
}
