"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useClinicaBelezaPaginatedList } from "@/hooks/clinica-beleza";
import { useAgendamentoCadastros } from "@/hooks/clinica-beleza/useAgendamentoCadastros";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import { ModalPagamentoAgenda } from "@/app/(dashboard)/loja/[slug]/agenda/components/ModalPagamentoAgenda";
import { ConsultaDetailView, ConsultasListView } from "./ConsultasListView";
import { ConsultasPageModals } from "./ConsultasPageModals";
import {
  useConsultasAgendaModals,
  useConsultasDeepLink,
  useConsultasNovaConsulta,
} from "./useConsultasPage";

interface PagamentoNovaConsultaState {
  open: boolean;
  appointmentId: number;
  patientName: string;
  procedureName: string;
  procedurePrice: number | string;
}

const PAGAMENTO_INITIAL: PagamentoNovaConsultaState = {
  open: false,
  appointmentId: 0,
  patientName: "",
  procedureName: "",
  procedurePrice: "",
};

export function ConsultasPageContent() {
  const params = useParams();
  const slug = params.slug as string;
  const [pagamento, setPagamento] = useState<PagamentoNovaConsultaState>(PAGAMENTO_INITIAL);

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
          ClinicaBelezaAPI.consultas
            .get(consultaId)
            .then((c) => {
              const consulta = c as Consulta & { appointment?: number };
              deepLink.abrirConsulta(consulta, true);
              // Abrir modal de pagamento para nova consulta
              if (consulta.appointment || consultaId) {
                setPagamento({
                  open: true,
                  appointmentId: Number(consulta.appointment || consultaId),
                  patientName: consulta.patient_name || "",
                  procedureName: consulta.procedure_name || "",
                  procedurePrice: consulta.valor_pagamento || consulta.valor_consulta || "",
                });
              }
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
      <ModalPagamentoAgenda
        open={pagamento.open}
        onClose={() => setPagamento(PAGAMENTO_INITIAL)}
        onSuccess={() => {
          setPagamento(PAGAMENTO_INITIAL);
          void loadConsultas();
        }}
        appointmentId={pagamento.appointmentId}
        patientName={pagamento.patientName}
        procedureName={pagamento.procedureName}
        procedurePrice={pagamento.procedurePrice}
      />
    </>
  );
}
