"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useClinicaBelezaPaginatedList } from "@/hooks/clinica-beleza";
import { useAgendamentoCadastros } from "@/hooks/clinica-beleza/useAgendamentoCadastros";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import { ConsultaDetailView, ConsultasListView } from "./ConsultasListView";
import { ConsultasPageModals } from "./ConsultasPageModals";
import {
  useConsultasAgendaModals,
  useConsultasDeepLink,
  useConsultasNovaConsulta,
} from "./useConsultasPage";

export function ConsultasPageContent() {
  const params = useParams();
  const slug = params.slug as string;

  const {
    list: consultas,
    loading,
    load: loadConsultas,
    page,
    setPage,
    totalPages,
    pageSize,
    totalCount,
  } = useClinicaBelezaPaginatedList<Consulta>({ path: "/consultas/" });

  const cadastros = useAgendamentoCadastros(true);
  const agendaModals = useConsultasAgendaModals();
  const novaConsulta = useConsultasNovaConsulta(slug);
  const deepLink = useConsultasDeepLink(slug, consultas);
  const [autoAbrirReceber, setAutoAbrirReceber] = useState(false);

  if (deepLink.selected) {
    return (
      <ConsultaDetailView
        consulta={deepLink.selected}
        detailPreloaded={deepLink.detailPreloaded}
        autoAbrirReceber={autoAbrirReceber}
        onBack={() => {
          setAutoAbrirReceber(false);
          deepLink.voltarLista();
        }}
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
        onNovaConsulta={novaConsulta.abrirNovaConsulta}
        onOpenConfigAgenda={() => agendaModals.setShowConfigAgendaMenu(true)}
        onSelectConsulta={(c) => deepLink.abrirConsulta(c, false)}
        onPageChange={setPage}
        onLimparDeepLinkError={deepLink.limparDeepLinkError}
      />
      <ConsultasPageModals
        showNovaConsultaModal={novaConsulta.showNovaConsultaModal}
        novaConsultaDate={novaConsulta.novaConsultaDate}
        onFecharNovaConsulta={novaConsulta.fecharNovaConsulta}
        onConsultaCreated={(consultaId) => {
          setAutoAbrirReceber(true);
          ClinicaBelezaAPI.consultas
            .get(consultaId)
            .then((c) => {
              deepLink.abrirConsulta(c as Consulta, true);
            })
            .catch(() => {
              setAutoAbrirReceber(false);
            });
        }}
        onAgendamentoSuccess={() => {
          void loadConsultas();
          void cadastros.reload();
        }}
        cadastros={cadastros}
        agendaModals={agendaModals}
      />
    </>
  );
}
