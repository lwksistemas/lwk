"use client";

import { useCallback, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useClinicaBelezaPaginatedList } from "@/hooks/clinica-beleza";
import { useAgendamentoCadastros } from "@/hooks/clinica-beleza/useAgendamentoCadastros";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { fetchClinicaSchedulingProfessionals } from "@/lib/clinica-beleza-cadastros-api";
import { formatApiErrorBody } from "@/lib/api-errors";
import { useToast } from "@/components/ui/Toast";
import { ModalReceberConsulta } from "@/components/clinica-beleza/consultas/ModalReceberConsulta";
import { ConsultaProfessionalSelectModal } from "@/components/clinica-beleza/consultas/ConsultaProfessionalSelectModal";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
import { entityName } from "@/lib/clinica-beleza-entities";
import { buildProntuarioPacientePath } from "@/components/clinica-beleza/prontuario/prontuario-paths";
import { ConsultaDetailView, ConsultasListView } from "./ConsultasListView";
import { ConsultasPageModals } from "./ConsultasPageModals";
import {
  useConsultasAgendaModals,
  useConsultasDeepLink,
  useConsultasNovaConsulta,
} from "./useConsultasPage";
import { useConsultasColunas } from "@/hooks/clinica-beleza/useConsultasColunas";
import { buildConsultaDetailHref } from "./consultas-page-utils";

function ConsultasPageWorkspace({ slug }: { slug: string }) {
  const router = useRouter();
  const toast = useToast();
  const searchParams = useSearchParams();
  const consultaIdParam = searchParams.get("id");

  const [receberConsulta, setReceberConsulta] = useState<Consulta | null>(null);
  const [abrindoReceberId, setAbrindoReceberId] = useState<number | null>(null);
  const [iniciandoId, setIniciandoId] = useState<number | null>(null);
  const [excluindoId, setExcluindoId] = useState<number | null>(null);
  const [filtroPaciente, setFiltroPaciente] = useState<PatientQuickOption | null>(null);
  const [consultaParaIniciar, setConsultaParaIniciar] = useState<Consulta | null>(null);
  const [showProfessionalModal, setShowProfessionalModal] = useState(false);
  const [profissionaisDisponiveis, setProfissionaisDisponiveis] = useState<
    Array<{ id: number; nome: string }>
  >([]);

  const queryParams = useMemo(() => {
    if (filtroPaciente) return { patient: filtroPaciente.id };
    return { fila: "iniciar" };
  }, [filtroPaciente]);

  const {
    list: consultas,
    loading,
    load: loadConsultas,
    page,
    setPage,
    totalPages,
    pageSize,
    totalCount,
  } = useClinicaBelezaPaginatedList<Consulta>({
    path: "/consultas/",
    queryParams,
    enabled: !consultaIdParam,
  });

  const { colunasKeys } = useConsultasColunas();
  const agendaModals = useConsultasAgendaModals();
  const novaConsulta = useConsultasNovaConsulta(slug);
  const deepLink = useConsultasDeepLink(slug, consultas);
  const cadastros = useAgendamentoCadastros(novaConsulta.showNovaConsultaModal);

  const limparFiltroPaciente = useCallback(() => {
    setFiltroPaciente(null);
  }, []);

  const abrirReceberNaLista = useCallback(async (c: Consulta) => {
    setAbrindoReceberId(c.id);
    try {
      const fresh = (await ClinicaBelezaAPI.consultas.get(c.id)) as Consulta;
      setReceberConsulta(fresh);
    } catch {
      setReceberConsulta(c);
    } finally {
      setAbrindoReceberId(null);
    }
  }, []);

  const aposRecebimentoLista = useCallback(
    async (atualizada: Partial<Consulta>) => {
      setReceberConsulta((prev) => (prev ? { ...prev, ...atualizada } : null));
      await loadConsultas();
    },
    [loadConsultas],
  );

  const executarInicio = useCallback(
    async (consulta: Consulta, professionalId?: number) => {
      setIniciandoId(consulta.id);
      try {
        const body = professionalId ? { professional: professionalId } : undefined;
        await ClinicaBelezaAPI.consultas.iniciar(consulta.id, body);
        toast.success("Consulta iniciada. Data e horário atualizados.");
        await loadConsultas();
        router.push(buildConsultaDetailHref(slug, consulta.id));
      } catch (e: unknown) {
        toast.error(formatApiErrorBody(e) || "Erro ao iniciar consulta.");
      } finally {
        setIniciandoId(null);
      }
    },
    [loadConsultas, router, slug, toast],
  );

  const iniciarNaLista = useCallback(
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
      if (consulta) void iniciarNaLista(consulta, professionalId);
    },
    [consultaParaIniciar, iniciarNaLista],
  );

  const excluirNaLista = useCallback(
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

  const verProntuario = useCallback(
    (consulta: Consulta) => {
      router.push(buildProntuarioPacientePath(slug, consulta.patient));
    },
    [router, slug],
  );

  if (deepLink.selected) {
    return (
      <ConsultaDetailView
        consulta={deepLink.selected}
        detailPreloaded={deepLink.detailPreloaded}
        onBack={deepLink.voltarLista}
        onSelectConsulta={(c) => deepLink.abrirConsulta(c, false)}
        onListRefresh={loadConsultas}
      />
    );
  }

  return (
    <>
      <ConsultasListView
        consultas={consultas}
        loading={loading}
        deepLinkError={deepLink.deepLinkError}
        page={page}
        totalPages={totalPages}
        totalCount={totalCount ?? 0}
        pageSize={pageSize}
        colunasVisiveis={colunasKeys}
        filtroPacienteNome={filtroPaciente ? entityName(filtroPaciente) : null}
        onLimparFiltroPaciente={limparFiltroPaciente}
        onFiltroPaciente={setFiltroPaciente}
        onNovaConsulta={novaConsulta.abrirNovaConsulta}
        onOpenConfigAgenda={() => agendaModals.setShowConfigAgendaMenu(true)}
        onSelectConsulta={(c) => deepLink.abrirConsulta(c, false)}
        onReceberConsulta={abrirReceberNaLista}
        onIniciarConsulta={iniciarNaLista}
        onExcluirConsulta={excluirNaLista}
        onVerProntuario={verProntuario}
        recebendoConsultaId={abrindoReceberId}
        iniciandoConsultaId={iniciandoId}
        excluindoConsultaId={excluindoId}
        onPageChange={setPage}
        onLimparDeepLinkError={deepLink.limparDeepLinkError}
      />
      <ConsultasPageModals
        showNovaConsultaModal={novaConsulta.showNovaConsultaModal}
        novaConsultaDate={novaConsulta.novaConsultaDate}
        onFecharNovaConsulta={novaConsulta.fecharNovaConsulta}
        onConsultaCreated={(consultaId) => {
          ClinicaBelezaAPI.consultas
            .get(consultaId)
            .then((c) => {
              void loadConsultas();
              setReceberConsulta(c as Consulta);
            })
            .catch(() => {
              void loadConsultas();
            });
        }}
        onAgendamentoSuccess={() => {
          void loadConsultas();
          void cadastros.reload();
        }}
        cadastros={cadastros}
        agendaModals={agendaModals}
      />
      {receberConsulta && (
        <ModalReceberConsulta
          open
          consulta={receberConsulta}
          onClose={() => setReceberConsulta(null)}
          onSuccess={(c) => void aposRecebimentoLista(c)}
        />
      )}
      <ConsultaProfessionalSelectModal
        open={showProfessionalModal}
        profissionais={profissionaisDisponiveis}
        onSelect={confirmarProfissional}
        onClose={() => {
          setShowProfessionalModal(false);
          setConsultaParaIniciar(null);
        }}
      />
    </>
  );
}

export function ConsultasPageContent() {
  const params = useParams();
  const slug = params.slug as string;
  return <ConsultasPageWorkspace slug={slug} />;
}
