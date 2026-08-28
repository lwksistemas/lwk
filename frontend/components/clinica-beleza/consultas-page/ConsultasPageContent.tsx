"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useClinicaBelezaPaginatedList } from "@/hooks/clinica-beleza";
import { useAgendamentoCadastros } from "@/hooks/clinica-beleza/useAgendamentoCadastros";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { ModalReceberConsulta } from "@/components/clinica-beleza/consultas/ModalReceberConsulta";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
import { entityName } from "@/lib/clinica-beleza-entities";
import { buildProntuarioHubPath } from "@/components/clinica-beleza/prontuario/prontuario-paths";
import { ConsultaDetailView, ConsultasListView } from "./ConsultasListView";
import { ConsultasPageModals } from "./ConsultasPageModals";
import {
  useConsultasAgendaModals,
  useConsultasDeepLink,
  useConsultasNovaConsulta,
} from "./useConsultasPage";
import { useConsultasColunas } from "@/hooks/clinica-beleza/useConsultasColunas";
import { shouldRedirectConsultasList } from "./consultas-page-utils";

function ConsultasRedirectToProntuario({ slug }: { slug: string }) {
  const router = useRouter();
  useEffect(() => {
    router.replace(buildProntuarioHubPath(slug));
  }, [router, slug]);
  return (
    <div className="text-center py-16 text-gray-500">Redirecionando ao prontuário...</div>
  );
}

function ConsultasPageWorkspace({ slug }: { slug: string }) {
  const searchParams = useSearchParams();
  const consultaIdParam = searchParams.get("id");

  const [receberConsulta, setReceberConsulta] = useState<Consulta | null>(null);
  const [abrindoReceberId, setAbrindoReceberId] = useState<number | null>(null);
  const [filtroPaciente, setFiltroPaciente] = useState<PatientQuickOption | null>(null);

  const queryParams = useMemo(
    () => (filtroPaciente ? { patient: filtroPaciente.id } : undefined),
    [filtroPaciente],
  );

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
        recebendoConsultaId={abrindoReceberId}
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
    </>
  );
}

export function ConsultasPageContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const slug = params.slug as string;

  if (shouldRedirectConsultasList(searchParams)) {
    return <ConsultasRedirectToProntuario slug={slug} />;
  }

  return <ConsultasPageWorkspace slug={slug} />;
}
