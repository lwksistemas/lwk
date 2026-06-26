"use client";

/**
 * Página de Agenda - Clínica da Beleza
 * Calendário fullscreen com drag & drop + Bloqueio de Horários
 */

import { useCallback, useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { Plus, Lock, List, CalendarDays } from "lucide-react";
import { entityName } from "@/lib/clinica-beleza-entities";
import {
  CLINICA_AGENDA_SLOT_DURATION,
  CLINICA_AGENDA_SLOT_LABEL_INTERVAL,
  CLINICA_AGENDA_SNAP_DURATION,
} from "@/lib/clinica-beleza-constants";
import { parseEventDate } from "@/lib/clinica-beleza-datetime";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import { useAgendaMutations } from "@/hooks/useAgendaMutations";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ModalBloqueioHorario } from "@/components/clinica-beleza/ModalBloqueioHorario";
import { ModalConflitoAgenda } from "@/components/clinica-beleza/ModalConflitoAgenda";
import { ModalCriarAgendamento } from "@/components/clinica-beleza/ModalCriarAgendamento";
import { OfflineIndicator } from "@/components/clinica-beleza/OfflineIndicator";
import { searchClinicaPatients } from "@/lib/clinica-beleza-cadastros-api";
import type { BloqueioHorario } from "@/lib/clinica-beleza-entities";
import {
  type HorarioTrabalho,
  workHoursRejectionMessage,
} from "@/lib/clinica-beleza-work-hours";
import { useClinicaBelezaDark } from "@/hooks/useClinicaBelezaDark";
import { useAgendaData } from "@/hooks/clinica-beleza/useAgendaData";
import { useAgendaCalendarConfig } from "@/hooks/clinica-beleza/useAgendaCalendarConfig";
import { ModalDetalheAgendamento } from "./components/ModalDetalheAgendamento";
import { ModalBloqueio } from "./components/ModalBloqueio";
import { AgendaListaColunas } from "./components/AgendaListaColunas";

const FullCalendar = dynamic(() => import("@fullcalendar/react"), {
  ssr: false,
  loading: () => <div className="flex items-center justify-center h-full">Carregando calendário...</div>,
});

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
  const [calendarPlugins, setCalendarPlugins] = useState<unknown[]>([]);
  const [ptBrLocale, setPtBrLocale] = useState<unknown>(null);
  const [isMobile, setIsMobile] = useState(false);
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

  const {
    temHorarioExpediente,
    businessHours,
    hiddenDays,
    slotMinTime,
    slotMaxTime,
  } = useAgendaCalendarConfig(selectedProfessional, horariosTrabalho);

  const searchPatients = useCallback((query: string) => searchClinicaPatients(query), []);

  useEffect(() => {
    if (searchParams.get("novo") === "1") {
      setSelectedDate(new Date());
      setShowCreateModal(true);
    }
  }, [searchParams]);

  useEffect(() => {
    const loadPlugins = async () => {
      const [dayGrid, timeGrid, interaction, ptBr] = await Promise.all([
        import("@fullcalendar/daygrid"),
        import("@fullcalendar/timegrid"),
        import("@fullcalendar/interaction"),
        import("@fullcalendar/core/locales/pt-br"),
      ]);
      setCalendarPlugins([dayGrid.default, timeGrid.default, interaction.default]);
      setPtBrLocale(ptBr.default);
    };
    loadPlugins();
  }, []);

  useEffect(() => {
    if (calendarPlugins.length > 0) carregarDados();
  }, [selectedProfessional, calendarPlugins, carregarDados]);

  useEffect(() => {
    const check = () => setIsMobile(typeof window !== "undefined" && window.innerWidth < 640);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  useEffect(() => {
    const handler = () => setTimeout(() => carregarDados(), 1200);
    window.addEventListener("offline-sync-done", handler);
    return () => window.removeEventListener("offline-sync-done", handler);
  }, [carregarDados]);

  useEffect(() => {
    if (!calendarPlugins.length) return;
    if (typeof navigator !== "undefined" && !navigator.onLine) return;
    const aguardando =
      showModal &&
      (selectedEvent?.extendedProps.status === "SCHEDULED" ||
        selectedEvent?.extendedProps.status === "PENDING");
    const intervalMs = aguardando ? 5000 : 15000;
    const timer = window.setInterval(() => carregarDados(), intervalMs);
    return () => window.clearInterval(timer);
  }, [
    calendarPlugins.length,
    selectedProfessional,
    showModal,
    selectedEvent?.extendedProps.status,
    carregarDados,
  ]);

  useEffect(() => {
    if (!showModal || !selectedEvent?.extendedProps?.dbId) return;
    const dbId = String(selectedEvent.extendedProps.dbId);
    const atualizado = eventos.find((e) => String(e.extendedProps.dbId) === dbId);
    if (!atualizado) return;
    if (
      atualizado.extendedProps.status !== selectedEvent.extendedProps.status ||
      atualizado.backgroundColor !== selectedEvent.backgroundColor
    ) {
      setSelectedEvent(atualizado);
    }
  }, [eventos, showModal, selectedEvent?.extendedProps?.dbId, selectedEvent?.extendedProps.status, selectedEvent?.backgroundColor]);

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

  const handleEventClick = (info: {
    event: {
      id: string;
      title: string;
      start: Date | null;
      end: Date | null;
      backgroundColor: string;
      borderColor: string;
      textColor: string;
      extendedProps: AgendaEventData["extendedProps"] & { isIntervalo?: boolean; isBloqueio?: boolean; bloqueioId?: number; motivo?: string; professional_name?: string };
    };
  }) => {
    if (info.event.extendedProps?.isIntervalo) return;
    if (info.event.extendedProps?.isBloqueio) {
      setSelectedBloqueio({
        id: info.event.extendedProps.bloqueioId!,
        motivo: info.event.extendedProps.motivo || info.event.title,
        professional_name: info.event.extendedProps.professional_name || "Todos",
      });
      return;
    }
    setSelectedEvent({
      id: info.event.id,
      title: info.event.title,
      start: info.event.start!,
      end: info.event.end!,
      backgroundColor: info.event.backgroundColor,
      borderColor: info.event.borderColor,
      textColor: info.event.textColor,
      extendedProps: info.event.extendedProps,
    });
    setShowModal(true);
  };

  const abrirEventoDaLista = (evt: AgendaEventData) => {
    handleEventClick({
      event: {
        id: evt.id,
        title: evt.title,
        start: parseEventDate(evt.start),
        end: parseEventDate(evt.end),
        backgroundColor: evt.backgroundColor,
        borderColor: evt.borderColor,
        textColor: evt.textColor,
        extendedProps: evt.extendedProps,
      },
    });
  };

  const conflitoComBloqueio = (date: Date, durationMin = 30) => {
    const apptEnd = new Date(date.getTime() + durationMin * 60000);
    return bloqueios.some((b: BloqueioHorario) => {
      const profMatch = !b.professional || selectedProfessional === String(b.professional);
      if (!profMatch) return false;
      const bStart = new Date(b.data_inicio);
      const bEnd = new Date(b.data_fim);
      if (Number.isNaN(bStart.getTime()) || Number.isNaN(bEnd.getTime())) return false;
      return date < bEnd && apptEnd > bStart;
    });
  };

  const handleDateClick = (info: { date: Date }) => {
    const date = info.date;
    if (selectedProfessional) {
      const msg = workHoursRejectionMessage(date, 30, horariosTrabalho as HorarioTrabalho[]);
      if (msg) {
        alert(msg);
        return;
      }
      if (conflitoComBloqueio(date)) {
        alert('Horário bloqueado. Escolha outro horário ou gerencie bloqueios no botão "Bloquear horário".');
        return;
      }
    }
    setSelectedDate(date);
    setShowCreateModal(true);
  };

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center min-h-[320px]">
        <div className="text-center">
          <div
            className="w-12 h-12 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4"
            style={{ borderColor: `${CLINICA_BELEZA_PRIMARY} transparent transparent transparent` }}
          />
          <p className="text-sm text-gray-600 dark:text-gray-300">Carregando agenda...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Agenda"
        subtitle="Calendário de agendamentos"
        backHref={`/loja/${slug}/dashboard`}
        showOffline={false}
        extraActions={
          <>
            <OfflineIndicator />
            <button
              type="button"
              onClick={() => setModoAgenda((m) => (m === "grade" ? "lista" : "grade"))}
              className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 text-xs sm:text-sm hover:bg-gray-50 dark:hover:bg-gray-600 shrink-0 transition-colors"
              title={modoAgenda === "grade" ? "Ver agenda em lista" : "Ver agenda em calendário"}
            >
              {modoAgenda === "grade" ? <List size={16} className="sm:w-4 sm:h-4" /> : <CalendarDays size={16} className="sm:w-4 sm:h-4" />}
              <span className="hidden sm:inline">{modoAgenda === "grade" ? "Lista" : "Calendário"}</span>
            </button>
            <select
              value={selectedProfessional}
              onChange={(e) => setSelectedProfessional(e.target.value)}
              className="px-2.5 sm:px-3 py-1.5 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-[#8B3D52]/30 max-w-[120px] sm:max-w-none"
            >
              <option value="">Todos</option>
              {professionals.map((prof) => (
                <option key={prof.id} value={prof.id}>{entityName(prof)}</option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => setShowModalBloqueio(true)}
              className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors shrink-0 text-xs sm:text-sm"
              title="Bloquear horário"
            >
              <Lock size={16} className="sm:w-4 sm:h-4" />
              <span className="hidden sm:inline">Bloquear</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setSelectedDate(new Date());
                setShowCreateModal(true);
              }}
              className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 text-white rounded-lg hover:opacity-90 transition-opacity shrink-0 text-xs sm:text-sm font-medium"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
              title="Novo agendamento"
            >
              <Plus size={16} className="sm:w-4 sm:h-4" />
              <span className="hidden sm:inline">Novo</span>
            </button>
          </>
        }
      />

      <div className="flex flex-col flex-1 min-h-0 p-3 sm:p-4 lg:p-6">
        <div className="flex flex-col flex-1 min-h-0 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
          <div className={`flex-1 min-h-0 p-2 sm:p-3 ${modoAgenda === "grade" ? "overflow-hidden fc-agenda-mobile" : "overflow-y-auto"}`}>
            {modoAgenda === "lista" ? (
              <AgendaListaColunas eventos={eventos} onAbrir={abrirEventoDaLista} />
            ) : calendarPlugins.length > 0 && ptBrLocale ? (
              <FullCalendar
                key={`${isMobile ? "mobile" : "desktop"}-${selectedProfessional}-${horariosTrabalho.length}`}
                plugins={calendarPlugins as never[]}
                initialView={isMobile ? "timeGridDay" : "timeGridWeek"}
                locale={ptBrLocale as never}
                editable
                eventStartEditable
                eventDurationEditable
                selectable
                selectMirror
                selectConstraint={temHorarioExpediente ? "businessHours" : undefined}
                dayMaxEvents={isMobile ? 6 : true}
                weekends
                events={eventos}
                eventDrop={(info) => { void moverEvento(info); }}
                eventResize={(info) => { void redimensionarEvento(info); }}
                eventClick={handleEventClick}
                dateClick={handleDateClick}
                height="100%"
                headerToolbar={
                  isMobile
                    ? { left: "prev,next", center: "title", right: "today" }
                    : { left: "prev,next today", center: "title", right: "timeGridDay,timeGridWeek,dayGridMonth" }
                }
                buttonText={isMobile ? { today: "Hoje" } : undefined}
                slotMinTime={slotMinTime}
                slotMaxTime={slotMaxTime}
                allDaySlot={false}
                slotDuration={CLINICA_AGENDA_SLOT_DURATION}
                slotLabelInterval={CLINICA_AGENDA_SLOT_LABEL_INTERVAL}
                snapDuration={CLINICA_AGENDA_SNAP_DURATION}
                businessHours={businessHours}
                hiddenDays={hiddenDays}
              />
            ) : null}
          </div>
        </div>
      </div>

      <ModalBloqueio
        open={selectedBloqueio != null}
        onClose={() => setSelectedBloqueio(null)}
        onSuccess={carregarDados}
        bloqueio={selectedBloqueio}
      />
      <ModalDetalheAgendamento
        open={showModal && selectedEvent != null}
        onClose={() => setShowModal(false)}
        onSuccess={carregarDados}
        event={selectedEvent!}
        onUpdateStatus={atualizarStatusAgendamento}
        onDelete={deletarEvento}
        onReenviarWhatsApp={reenviarMensagemWhatsApp}
        updatingStatus={updatingStatus}
        reenviandoMensagem={reenviandoMensagem}
      />
      <ModalCriarAgendamento
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={carregarDados}
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
      />
      <ModalBloqueioHorario
        isOpen={showModalBloqueio}
        onClose={() => setShowModalBloqueio(false)}
        onSuccess={carregarDados}
        professionals={professionals}
        defaultProfessionalId={selectedProfessional}
      />
      <ModalConflitoAgenda
        open={conflictData != null}
        onClose={closeConflictModal}
        data={conflictData}
        onUseServer={handleConflitoUseServer}
        onUseLocal={handleConflitoUseLocal}
        resolving={conflictResolving}
      />
    </>
  );
}
