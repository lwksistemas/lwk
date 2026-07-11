"use client";

import { useCallback, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { useClinicaBelezaPaginatedList } from "@/hooks/clinica-beleza";
import { useAgendamentoCadastros } from "@/hooks/clinica-beleza/useAgendamentoCadastros";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { ModalReceberConsulta } from "@/components/clinica-beleza/consultas/ModalReceberConsulta";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
import { entityName } from "@/lib/clinica-beleza-entities";
import { ConsultaDetailView, ConsultasListView } from "./ConsultasListView";
import { ConsultasPageModals } from "./ConsultasPageModals";
import {
  useConsultasAgendaModals,
  useConsultasDeepLink,
  useConsultasNovaConsulta,
} from "./useConsultasPage";
import { useConsultasColunas } from "@/hooks/clinica-beleza/useConsultasColunas";

export function ConsultasPageContent() {
  const params = useParams();
  const slug = params.slug as string;

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
  });

  const { colunasKeys } = useConsultasColunas();
  const cadastros = useAgendamentoCadastros(true);
  const agendaModals = useConsultasAgendaModals();
  const novaConsulta = useConsultasNovaConsulta(slug);
  const deepLink = useConsultasDeepLink(slug, consultas);

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
    async (atualizada: Consulta) => {
      setReceberConsulta(atualizada);
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
              deepLink.abrirConsulta(c as Consulta, true);
            })
            .catch(() => {});
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
