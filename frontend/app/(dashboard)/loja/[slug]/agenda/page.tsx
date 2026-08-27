"use client";

/**
 * Página de Agenda - Clínica da Beleza
 * Grade Dia/Semana própria, mês FullCalendar, bloqueio de horários.
 */

import { useCallback, useRef, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { Plus } from "lucide-react";
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
  const [createProfessionalId, setCreateProfessionalId] = useState("");

  useClinicaBelezaDark();

  const isMutatingRef = useRef(false);
  const isDraggingRef = useRef(false);

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
    recarregarEventos,
  } = useAgendaData(selectedProfessional);

  const { calendarPlugins, ptBrLocale } = useAgendaPageEffects({
    searchParams,
    selectedProfessional,
    carregarDados,
    recarregarEventos,
    showModal,
    selectedEvent,
    eventos,
    setSelectedEvent,
    setSelectedDate,
    setShowCreateModal,
    isMutatingRef,
    isDraggingRef,
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
    salvandoDetalhe,
    conflictData,
    conflictResolving,
    moverEvento,
    moverAgendamentoGrade,
    redimensionarEvento,
    redimensionarAgendamentoGrade,
    deletarEvento,
    atualizarStatusAgendamento,
    atualizarDetalheAgendamento,
    reenviarMensagemWhatsApp,
    handleConflitoUseServer,
    handleConflitoUseLocal,
    closeConflictModal,
  } = useAgendaMutations({
    onReload: carregarDados,
    selectedProfessional,
    selectedEvent,
    setSelectedEvent,
    setShowModal,
    isMutatingRef,
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

  // IMPORTANTE: hooks antes de qualquer return — loading flip quebrava a página no Android.
  const abrirNovoAgendamento = useCallback(() => {
    const now = new Date();
    const step = 15;
    const rounded = new Date(now);
    const mins = rounded.getMinutes();
    const next = Math.ceil(mins / step) * step;
    if (next >= 60) {
      rounded.setHours(rounded.getHours() + 1, 0, 0, 0);
    } else {
      rounded.setMinutes(next, 0, 0);
    }
    setSelectedDate(rounded);
    setCreateProfessionalId(selectedProfessional);
    setShowCreateModal(true);
  }, [selectedProfessional]);

  if (loading && eventos.length === 0) {
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
    <div className="relative flex flex-col sm:flex-1 sm:min-h-0">
      <ClinicaBelezaStandardPageHeader
        title="Agenda"
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
            onNovo={abrirNovoAgendamento}
          />
        }
      />

      <div className="flex flex-col sm:flex-1 sm:min-h-0 min-w-0 p-3 sm:p-4 lg:p-6">
        <div className="flex flex-col sm:flex-1 sm:min-h-0 min-w-0 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm sm:overflow-hidden">
          <AgendaCalendarSection
            modoAgenda={modoAgenda}
            eventos={eventos}
            calendarPlugins={calendarPlugins}
            ptBrLocale={ptBrLocale}
            selectedProfessional={selectedProfessional}
            temHorarioExpediente={temHorarioExpediente}
            businessHours={businessHours}
            hiddenDays={hiddenDays}
            slotMinTime={slotMinTime}
            slotMaxTime={slotMaxTime}
            onAbrirLista={abrirEventoDaLista}
            onEventClick={handleEventClickArg}
            onDateClick={handleDateClick}
            onEventDrop={moverEvento}
            onEventResize={redimensionarEvento}
            isDraggingRef={isDraggingRef}
            professionals={professionals}
            onNovoHorario={(_date, professionalId) => {
              setCreateProfessionalId(professionalId > 0 ? String(professionalId) : "");
            }}
            onMoverGrade={moverAgendamentoGrade}
            onRedimensionarGrade={redimensionarAgendamentoGrade}
          />
        </div>
      </div>

      {/* FAB mobile — botão Novo some do topo lotado; fica fixo e visível */}
      <button
        type="button"
        onClick={abrirNovoAgendamento}
        className="sm:hidden fixed z-40 flex items-center justify-center gap-2 rounded-full text-white shadow-lg active:scale-95 transition-transform touch-manipulation px-4 h-14 bottom-[max(1.25rem,env(safe-area-inset-bottom))] right-4"
        style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
        aria-label="Novo agendamento"
        title="Novo agendamento"
      >
        <Plus size={22} strokeWidth={2.5} />
        <span className="text-sm font-semibold pr-0.5">Agendar</span>
      </button>

      <AgendaPageModals
        selectedBloqueio={selectedBloqueio}
        onCloseBloqueio={() => setSelectedBloqueio(null)}
        showModal={showModal}
        selectedEvent={selectedEvent}
        onCloseDetalhe={() => setShowModal(false)}
        onReload={carregarDados}
        onUpdateStatus={atualizarStatusAgendamento}
        onSalvarDetalhe={atualizarDetalheAgendamento}
        onDelete={deletarEvento}
        onReenviarWhatsApp={reenviarMensagemWhatsApp}
        updatingStatus={updatingStatus}
        salvandoDetalhe={salvandoDetalhe}
        reenviandoMensagem={reenviandoMensagem}
        showCreateModal={showCreateModal}
        onCloseCreate={() => {
          setShowCreateModal(false);
          setCreateProfessionalId("");
        }}
        selectedDate={selectedDate}
        defaultProfessionalId={createProfessionalId || selectedProfessional}
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
