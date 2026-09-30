"use client";

import { useCallback, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useClinicaBelezaPaginatedList } from "@/hooks/clinica-beleza";
import { useAgendamentoCadastros } from "@/hooks/clinica-beleza/useAgendamentoCadastros";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import {
  clinicaBelezaQueryKeys,
  fetchClinicaSchedulingProfessionals,
} from "@/lib/clinica-beleza-cadastros-api";
import { formatApiErrorBody } from "@/lib/api-errors";
import { useToast } from "@/components/ui/Toast";
import { ModalReceberConsulta } from "@/components/clinica-beleza/consultas/ModalReceberConsulta";
import { ConsultaProfessionalSelectModal } from "@/components/clinica-beleza/consultas/ConsultaProfessionalSelectModal";
import { passoInicioConsulta, textoModalProfissional } from "@/components/clinica-beleza/consultas/consulta-acesso";
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
import { useClinicaPodeVerConsulta } from "@/hooks/clinica-beleza/useClinicaPodeVerConsulta";
import {
  buildConsultaDetailHref,
  buildConsultasListQueryParams,
  intervaloPeriodoConsultas,
  type ConsultasListaVista,
  type ConsultasPeriodo,
} from "./consultas-page-utils";
import { consultaPagamentoUi } from "@/hooks/clinica-beleza/consulta-detail-actions/consulta-detail-actions-utils";

function ConsultasPageWorkspace({ slug }: { slug: string }) {
  const router = useRouter();
  const toast = useToast();
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const consultaIdParam = searchParams.get("id");
  const { podeVerConsulta, loaded: acessoCarregado } = useClinicaPodeVerConsulta();
  const acessoClinico = acessoCarregado && podeVerConsulta;

  const [receberConsulta, setReceberConsulta] = useState<Consulta | null>(null);
  const [abrindoReceberId, setAbrindoReceberId] = useState<number | null>(null);
  const [iniciandoId, setIniciandoId] = useState<number | null>(null);
  const [excluindoId, setExcluindoId] = useState<number | null>(null);
  const [filtroPaciente, setFiltroPaciente] = useState<PatientQuickOption | null>(null);
  const [filtroProfissionalId, setFiltroProfissionalId] = useState<number | null>(null);
  const [vista, setVista] = useState<ConsultasListaVista>("iniciar");
  const [periodo, setPeriodo] = useState<ConsultasPeriodo>("mes_atual");
  const [periodoInicio, setPeriodoInicio] = useState("");
  const [periodoFim, setPeriodoFim] = useState("");
  const [consultaParaIniciar, setConsultaParaIniciar] = useState<Consulta | null>(null);
  const [showProfessionalModal, setShowProfessionalModal] = useState(false);
  const [profissionaisDisponiveis, setProfissionaisDisponiveis] = useState<
    Array<{ id: number; nome?: string; name?: string }>
  >([]);

  const intervalo = useMemo(
    () => intervaloPeriodoConsultas(periodo, { inicio: periodoInicio, fim: periodoFim }),
    [periodo, periodoInicio, periodoFim],
  );

  const queryParams = useMemo(
    () =>
      buildConsultasListQueryParams({
        patientId: filtroPaciente?.id ?? null,
        professionalId: filtroProfissionalId,
        vista,
        dataInicio: intervalo.data_inicio || null,
        dataFim: intervalo.data_fim || null,
      }),
    [filtroPaciente, filtroProfissionalId, vista, intervalo],
  );

  const resumoQuery = useQuery({
    queryKey: ["consultas-resumo-financeiro", queryParams],
    queryFn: () => ClinicaBelezaAPI.consultas.resumoFinanceiro(queryParams),
    enabled: !consultaIdParam,
  });

  const professionalsQuery = useQuery({
    queryKey: clinicaBelezaQueryKeys.schedulingProfessionals(),
    queryFn: fetchClinicaSchedulingProfessionals,
  });

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
      await queryClient.invalidateQueries({ queryKey: ["consultas-resumo-financeiro"] });
    },
    [loadConsultas, queryClient],
  );

  const executarInicio = useCallback(
    async (consulta: Consulta) => {
      setIniciandoId(consulta.id);
      try {
        await ClinicaBelezaAPI.consultas.iniciar(consulta.id);
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
      const me = await ClinicaBelezaAPI.me.get().catch(() => null);
      const passo = passoInicioConsulta(consulta, me?.professional_id ?? null, professionalId);
      if (passo.tipo === "modal") {
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
      if (passo.tipo === "trocar") {
        try {
          await ClinicaBelezaAPI.consultas.trocarProfissional(consulta.id, passo.professionalId);
          await loadConsultas();
          if (!passo.iniciarDepois) {
            toast.success("Profissional da agenda atualizado. Quem for atender inicia a consulta.");
            return;
          }
        } catch (e: unknown) {
          toast.error(formatApiErrorBody(e) || "Erro ao trocar o profissional.");
          return;
        }
      }
      await executarInicio(consulta);
    },
    [executarInicio, loadConsultas, toast],
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

  if (acessoClinico && deepLink.selected) {
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
        profissionais={professionalsQuery.data ?? []}
        filtroProfissionalId={filtroProfissionalId}
        onFiltroProfissional={setFiltroProfissionalId}
        periodo={periodo}
        onPeriodo={setPeriodo}
        periodoInicio={periodoInicio}
        periodoFim={periodoFim}
        onPeriodoInicio={setPeriodoInicio}
        onPeriodoFim={setPeriodoFim}
        totalPago={resumoQuery.data?.total_pago ?? 0}
        aReceber={resumoQuery.data?.a_receber ?? 0}
        vista={vista}
        onVista={setVista}
        onNovaConsulta={novaConsulta.abrirNovaConsulta}
        onOpenConfigAgenda={() => agendaModals.setShowConfigAgendaMenu(true)}
        onSelectConsulta={(c) => deepLink.abrirConsulta(c, false)}
        onReceberConsulta={abrirReceberNaLista}
        onIniciarConsulta={iniciarNaLista}
        onExcluirConsulta={excluirNaLista}
        onVerProntuario={acessoClinico ? verProntuario : undefined}
        acessoClinico={acessoClinico}
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
              const criada = c as Consulta;
              if (consultaPagamentoUi(criada).mostrarIsento) return;
              setReceberConsulta(criada);
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
        titulo={consultaParaIniciar ? textoModalProfissional(consultaParaIniciar).titulo : undefined}
        descricao={consultaParaIniciar ? textoModalProfissional(consultaParaIniciar).descricao : undefined}
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
