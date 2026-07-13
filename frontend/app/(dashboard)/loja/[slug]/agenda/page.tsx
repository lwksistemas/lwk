"use client";

/**
 * Página de Agenda - Clínica da Beleza
 * Calendário fullscreen com drag & drop + Bloqueio de Horários
 */

import { useCallback, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import { useAgendaMutations } from "@/hooks/useAgendaMutations";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { searchClinicaPatients } from "@/lib/clinica-beleza-cadastros-api";
import { useClinicaBelezaDark } from "@/hooks/useClinicaBelezaDark";
import { useAgendaData } from "@/hooks/clinica-beleza/useAgendaData";
import { useAgendaCalendarConfig } from "@/hooks/clinica-beleza/useAgendaCalendarConfig";
import { useAgendaPageEffects } from "@/hooks/clinica-beleza/useAgendaPageEffects";
import { useAgendaPageHandlers } from "@/hooks/clinica-beleza/useAgendaPageHandlers";
import { AgendaCalendarSection } from "./components/AgendaCalendarSection";
import { AgendaPageHeaderActions } from "./components/AgendaPageHeaderActions";
import { AgendaPageModals } from "./components/AgendaPageModals";

export default function AgendaPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const slug = params.slug as string;

  const [selectedProfessional, setSelectedProfessional] = useState<string>("");
  const [showModal, setShowModal] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<AgendaEventData | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [showModalBloqueio, setShowModalBloqueio] = useState(false);
  const [selectedBloqueio, setSelectedBloqueio] = useState<{
    id: number;
    motivo: string;
    professional_name: string;
  } | null>(null);
  const [modoAgenda, setModoAgenda] = useState<"grade" | "lista">("grade");

  useClinicaBelezaDark();

  const {
    eventos,
    setEventos,
    loading,
    professionals,
    horariosTrabalho,
    patients,
    setPatients,
    procedures,
    nomesAgenda,
    locaisAtendimento,
    bloqueios,
    carregarDados,
  } = useAgendaData(selectedProfessional);

  const { calendarPlugins, ptBrLocale, isMobile } = useAgendaPageEffects({
    searchParams,
    selectedProfessional,
    carregarDados,
    showModal,
    selectedEvent,
    eventos,
    setSelectedEvent,
    setSelectedDate,
    setShowCreateModal,
  });

  const {
    temHorarioExpediente,
    businessHours,
    hiddenDays,
    slotMinTime,
    slotMaxTime,
  } = useAgendaCalendarConfig(selectedProfessional, horariosTrabalho);

  const searchPatients = useCallback((query: string) => searchClinicaPatients(query), []);

  const {
    updatingStatus,
    reenviandoMensagem,
    conflictData,
    conflictResolving,
    moverEvento,
    redimensionarEvento,
    deletarEvento,
    atualizarStatusAgendamento,
    reenviarMensagemWhatsApp,
    handleConflitoUseServer,
    handleConflitoUseLocal,
    closeConflictModal,
  } = useAgendaMutations({
    onReload: carregarDados,
    selectedEvent,
    setSelectedEvent,
    setShowModal,
  });

  const { handleEventClick, handleEventClickArg, abrirEventoDaLista, handleDateClick } = useAgendaPageHandlers({
    selectedProfessional,
    horariosTrabalho,
    bloqueios,
    setSelectedEvent,
    setShowModal,
    setSelectedBloqueio,
    setSelectedDate,
    setShowCreateModal,
  });

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center min-h-[320px]">
        <div className="text-center">
          <div
            className="w-12 h-12 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4"
            style={{ borderColor: 'var(--cb-primary, #8B3D52) transparent transparent transparent' }}
          />
          <p className="text-sm text-gray-600 dark:text-gray-300">Carregando agenda...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <ClinicaBelezaStandardPageHeader
        title="Agenda"
        subtitle="Calendário de agendamentos"
        backHref={`/loja/${slug}/dashboard`}
        showOffline={false}
        extraActions={
          <AgendaPageHeaderActions
            modoAgenda={modoAgenda}
            onToggleModo={() => setModoAgenda((m) => (m === "grade" ? "lista" : "grade"))}
            selectedProfessional={selectedProfessional}
            onSelectProfessional={setSelectedProfessional}
            professionals={professionals}
            onBloquear={() => setShowModalBloqueio(true)}
            onNovo={() => {
              setSelectedDate(new Date());
              setShowCreateModal(true);
            }}
          />
        }
      />

      <div className="flex flex-col flex-1 min-h-0 p-3 sm:p-4 lg:p-6">
        <div className="flex flex-col flex-1 min-h-0 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
          <AgendaCalendarSection
            modoAgenda={modoAgenda}
            eventos={eventos}
            calendarPlugins={calendarPlugins}
            ptBrLocale={ptBrLocale}
            isMobile={isMobile}
            selectedProfessional={selectedProfessional}
            temHorarioExpediente={temHorarioExpediente}
            businessHours={businessHours}
            hiddenDays={hiddenDays}
            slotMinTime={slotMinTime}
            slotMaxTime={slotMaxTime}
            onAbrirLista={abrirEventoDaLista}
            onEventClick={handleEventClickArg}
            onDateClick={handleDateClick}
            onEventDrop={(info) => {
              void moverEvento(info);
            }}
            onEventResize={(info) => {
              void redimensionarEvento(info);
            }}
          />
        </div>
      </div>

      <AgendaPageModals
        selectedBloqueio={selectedBloqueio}
        onCloseBloqueio={() => setSelectedBloqueio(null)}
        showModal={showModal}
        selectedEvent={selectedEvent}
        onCloseDetalhe={() => setShowModal(false)}
        onReload={carregarDados}
        onUpdateStatus={atualizarStatusAgendamento}
        onDelete={deletarEvento}
        onReenviarWhatsApp={reenviarMensagemWhatsApp}
        updatingStatus={updatingStatus}
        reenviandoMensagem={reenviandoMensagem}
        showCreateModal={showCreateModal}
        onCloseCreate={() => setShowCreateModal(false)}
        selectedDate={selectedDate}
        defaultProfessionalId={selectedProfessional}
        professionals={professionals}
        patients={patients}
        procedures={procedures}
        nomesAgenda={nomesAgenda}
        locaisAtendimento={locaisAtendimento}
        onPatientsChange={setPatients}
        onSearchPatients={searchPatients}
        onOfflineEventCreated={(evt) => setEventos((prev) => [...prev, evt as AgendaEventData])}
        showModalBloqueio={showModalBloqueio}
        onCloseModalBloqueio={() => setShowModalBloqueio(false)}
        conflictData={conflictData}
        onCloseConflict={closeConflictModal}
        onUseServer={handleConflitoUseServer}
        onUseLocal={handleConflitoUseLocal}
        conflictResolving={conflictResolving}
      />
    </div>
  );
}
