"use client";

/**
 * Página de Agenda - Clínica da Beleza
 * Calendário fullscreen com drag & drop + Bloqueio de Horários
 */

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { Plus, Lock, List, CalendarDays } from "lucide-react";
import apiClient from "@/lib/api-client";
import { entityName } from "@/lib/clinica-beleza-entities";
import {
  CLINICA_AGENDA_BLOQUEIO_COLORS,
  CLINICA_AGENDA_STATUS_COLORS,
} from "@/lib/clinica-beleza-constants";
import { parseEventDate } from "@/lib/clinica-beleza-datetime";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import { useAgendaMutations } from "@/hooks/useAgendaMutations";
import { useLojaAuth } from "@/hooks/useLojaAuth";
import { ClinicaBelezaShell } from "@/components/clinica-beleza/ClinicaBelezaShell";
import {
  ClinicaBelezaPageHeaderFooter,
  ClinicaBelezaStandardPageHeader,
} from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import type { LojaInfo } from "@/types/dashboard";
import { useClinicaBelezaDark } from "@/hooks/useClinicaBelezaDark";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ModalBloqueioHorario } from "@/components/clinica-beleza/ModalBloqueioHorario";
import { ModalConflitoAgenda } from "@/components/clinica-beleza/ModalConflitoAgenda";
import { OfflineIndicator } from "@/components/clinica-beleza/OfflineIndicator";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import {
  salvarPacientesOffline, buscarPacientesOffline,
  salvarProfissionaisOffline, buscarProfissionaisOffline,
  salvarProcedimentosOffline, buscarProcedimentosOffline,
  salvarAgendamentosOffline, buscarAgendamentosOffline, obterFilaSync,
} from "@/lib/offline-db";
import { logger } from "@/lib/logger";
import {
  type HorarioTrabalho,
  businessHoursFromHorarios,
  intervalosEventsFromHorarios,
  workHoursRejectionMessage,
} from "@/lib/clinica-beleza-work-hours";
import { ModalDetalheAgendamento } from "./components/ModalDetalheAgendamento";
import { ModalCriarAgendamento } from "./components/ModalCriarAgendamento";
import { ModalBloqueio } from "./components/ModalBloqueio";
import { AgendaListaColunas } from "./components/AgendaListaColunas";
import { AgendaLegenda } from "./components/AgendaLegenda";

const FullCalendar = dynamic(() => import("@fullcalendar/react"), {
  ssr: false,
  loading: () => <div className="flex items-center justify-center h-full">Carregando calendário...</div>,
});

interface Professional { id: number; name?: string; nome?: string; specialty?: string; especialidade?: string; }
interface HorarioTrabalhoRow {
  id: number;
  dia_semana: number;
  hora_entrada: string;
  hora_saida: string;
  intervalo_inicio: string | null;
  intervalo_fim: string | null;
  ativo: boolean;
}
interface Patient { id: number; name?: string; nome?: string; phone?: string; telefone?: string; }
interface Procedure { id: number; name?: string; nome?: string; duration?: number; duracao_minutos?: number; price?: string; preco?: string; }
interface BloqueioHorario { id: number; professional: number | null; professional_name: string | null; data_inicio: string; data_fim: string; motivo: string; observacoes: string | null; criado_em: string; }

export default function AgendaPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const { handleLogout } = useLojaAuth(slug);
  const [loja, setLoja] = useState<LojaInfo | null>(null);
  const [lojaLoading, setLojaLoading] = useState(true);
  const [eventos, setEventos] = useState<AgendaEventData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProfessional, setSelectedProfessional] = useState<string>("");
  const [professionals, setProfessionals] = useState<Professional[]>([]);
  const [horariosTrabalho, setHorariosTrabalho] = useState<HorarioTrabalhoRow[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<AgendaEventData | null>(null);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [bloqueios, setBloqueios] = useState<BloqueioHorario[]>([]);
  const [showModalBloqueio, setShowModalBloqueio] = useState(false);
  const [selectedBloqueio, setSelectedBloqueio] = useState<{ id: number; motivo: string; professional_name: string } | null>(null);
  const [calendarPlugins, setCalendarPlugins] = useState<any[]>([]);
  const [ptBrLocale, setPtBrLocale] = useState<any>(null);
  useClinicaBelezaDark();
  const [isMobile, setIsMobile] = useState(false);
  const [modoAgenda, setModoAgenda] = useState<"grade" | "lista">("grade");

  // Abrir modal "Novo Agendamento" quando ?novo=1 na URL
  useEffect(() => {
    if (searchParams.get("novo") === "1") { setSelectedDate(new Date()); setShowCreateModal(true); }
  }, [searchParams]);

  // Redirecionar para login se não houver token
  useEffect(() => {
    if (typeof window === "undefined" || !slug) return;
    const token = sessionStorage.getItem("access_token");
    if (!token) { window.location.href = `/loja/${slug}/login`; return; }
    if (!sessionStorage.getItem("current_loja_id") || !sessionStorage.getItem("loja_slug")) {
      sessionStorage.setItem("loja_slug", slug);
    }
  }, [slug]);

  useEffect(() => {
    if (!slug) return;
    setLojaLoading(true);
    apiClient
      .get(`/superadmin/lojas/info_publica/?slug=${slug}`)
      .then((res) => {
        const data = res.data as LojaInfo;
        setLoja(data);
        if (typeof window !== "undefined" && data?.id != null) {
          sessionStorage.setItem("current_loja_id", String(data.id));
          if (data.slug) sessionStorage.setItem("loja_slug", data.slug);
        }
      })
      .catch(() => setLoja(null))
      .finally(() => setLojaLoading(false));
  }, [slug]);

  useEffect(() => {
    const loadPlugins = async () => {
      const [dayGrid, timeGrid, interaction, ptBr] = await Promise.all([
        import("@fullcalendar/daygrid"), import("@fullcalendar/timegrid"),
        import("@fullcalendar/interaction"), import("@fullcalendar/core/locales/pt-br"),
      ]);
      setCalendarPlugins([dayGrid.default, timeGrid.default, interaction.default]);
      setPtBrLocale(ptBr.default);
    };
    loadPlugins();
  }, []);

  useEffect(() => { if (calendarPlugins.length > 0) carregarDados(); // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedProfessional, calendarPlugins]);

  useEffect(() => {
    const check = () => setIsMobile(typeof window !== "undefined" && window.innerWidth < 640);
    check(); window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  useEffect(() => {
    const handler = () => setTimeout(() => carregarDados(), 1200);
    window.addEventListener("offline-sync-done", handler);
    return () => window.removeEventListener("offline-sync-done", handler);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const temHorarioExpediente = selectedProfessional && horariosTrabalho.some((h) => h.ativo);

  const formatarEvento = (e: any, comRestricaoExpediente = temHorarioExpediente): AgendaEventData => {
    const cores = CLINICA_AGENDA_STATUS_COLORS[e.status] || { bg: "#a855f7", border: "#9333ea" };
    const titulo = [e.patient_name, e.procedure_name].filter(Boolean).join(" • ") || e.title || "Agendamento";
    return {
      id: String(e.id), title: titulo, start: e.start, end: e.end,
      backgroundColor: cores.bg, borderColor: cores.border, textColor: "#fff",
      ...(comRestricaoExpediente ? { constraint: "businessHours" as const } : {}),
      extendedProps: {
        dbId: e.id, status: e.status, patient_name: e.patient_name, patient_phone: e.patient_phone,
        professional_name: e.professional_name, procedure_name: e.procedure_name,
        procedure_duration: e.procedure_duration, duracao_minutos: e.duracao_minutos, procedure_price: e.procedure_price,
        notes: e.notes, version: e.version, updated_at: e.updated_at,
      },
    };
  };

  const getBusinessHours = () => businessHoursFromHorarios(horariosTrabalho as HorarioTrabalho[]);

  const getHiddenDays = () => {
    if (!selectedProfessional || horariosTrabalho.length === 0) return [0];
    const diasAtivos = horariosTrabalho.filter((h) => h.ativo).map((h) => (h.dia_semana === 6 ? 0 : h.dia_semana + 1));
    return [0, 1, 2, 3, 4, 5, 6].filter((d) => !diasAtivos.includes(d));
  };

  const getSlotMinTime = () => {
    if (!selectedProfessional || horariosTrabalho.length === 0) return "07:00:00";
    const ativos = horariosTrabalho.filter((h) => h.ativo);
    if (!ativos.length) return "07:00:00";
    return ativos.reduce((min, h) => { const t = (h.hora_entrada || '07:00').slice(0, 5); return t < min ? t : min; }, "23:59") + ":00";
  };

  const getSlotMaxTime = () => {
    if (!selectedProfessional || horariosTrabalho.length === 0) return "20:00:00";
    const ativos = horariosTrabalho.filter((h) => h.ativo);
    if (!ativos.length) return "20:00:00";
    return ativos.reduce((max, h) => { const t = (h.hora_saida || '20:00').slice(0, 5); return t > max ? t : max; }, "00:00") + ":00";
  };

  const carregarDados = async () => {
    try {
      const online = typeof navigator !== "undefined" && navigator.onLine;
      if (online) {
        const agendaPath = selectedProfessional ? `/agenda/?professional=${selectedProfessional}` : "/agenda/";
        const bloqueiosPath = selectedProfessional ? `/bloqueios/?professional=${selectedProfessional}` : "/bloqueios/";
        const horariosReq = selectedProfessional
          ? clinicaBelezaFetch(`/professionals/${selectedProfessional}/horarios-trabalho/`)
          : Promise.resolve(null);
        const [resEv, resBl, resProf, resPat, resProc, resHor] = await Promise.all([
          clinicaBelezaFetch(agendaPath), clinicaBelezaFetch(bloqueiosPath),
          clinicaBelezaFetch("/professionals/?with_schedule=true"),
          clinicaBelezaFetch("/patients/"), clinicaBelezaFetch("/procedures/"),
          horariosReq,
        ]);
        const profs: Professional[] = resProf.ok ? await resProf.json() : [];
        const pacs: Patient[] = resPat.ok ? await resPat.json() : [];
        const procs: Procedure[] = resProc.ok ? await resProc.json() : [];
        let horariosAtivos: HorarioTrabalhoRow[] = [];
        if (resHor?.ok) {
          horariosAtivos = await resHor.json();
          setHorariosTrabalho(horariosAtivos);
        } else {
          setHorariosTrabalho([]);
        }
        if (profs.length) { setProfessionals(profs); await salvarProfissionaisOffline(profs); }
        if (pacs.length) { setPatients(pacs); await salvarPacientesOffline(pacs); }
        if (procs.length) { setProcedures(procs); await salvarProcedimentosOffline(procs); }

        const temExpedienteCarregado = Boolean(selectedProfessional && horariosAtivos.some((h) => h.ativo));

        let eventosFormatados: AgendaEventData[] = [];
        if (resEv.ok) { const data = await resEv.json(); await salvarAgendamentosOffline(data); eventosFormatados = data.map((ev: unknown) => formatarEvento(ev, temExpedienteCarregado)); }

        let bloqueiosAsEvents: any[] = [];
        if (resBl.ok) {
          const bloqueiosList: BloqueioHorario[] = await resBl.json();
          setBloqueios(bloqueiosList);
          bloqueiosAsEvents = bloqueiosList.map((b) => {
            const rawS = b.data_inicio ?? "", rawE = b.data_fim ?? "";
            const hasT = typeof rawS === "string" && rawS.includes("T") && typeof rawE === "string" && rawE.includes("T");
            const startStr = hasT ? rawS : (rawS.slice(0, 10) ? `${rawS.slice(0, 10)}T00:00:00` : "");
            const endStr = hasT ? rawE : (rawS.slice(0, 10) ? `${rawS.slice(0, 10)}T23:59:59` : "");
            return {
              id: `bloqueio-${b.id}`, title: `🚫 ${b.motivo}`, start: startStr, end: endStr,
              allDay: false, backgroundColor: CLINICA_AGENDA_BLOQUEIO_COLORS.bg, borderColor: CLINICA_AGENDA_BLOQUEIO_COLORS.border, textColor: "#fff",
              editable: true, durationEditable: true, startEditable: true,
              classNames: ["fc-event-bloqueio"],
              extendedProps: {
                isBloqueio: true,
                bloqueioId: b.id,
                motivo: b.motivo,
                professional: b.professional,
                professional_name: b.professional_name || "Todos",
              },
            };
          });
        }

        const profName = entityName(profs.find((p) => p.id === Number(selectedProfessional)) || {}) || "Profissional";
        const intervalos = selectedProfessional && horariosAtivos.length > 0
          ? intervalosEventsFromHorarios(selectedProfessional, horariosAtivos, profName) : [];

        // Mesclar agendamentos pendentes offline
        const fila = await obterFilaSync();
        const pendingEvents = fila.filter((f) => f.tipo === "agendamento").map((item: any) => {
          const p = item.payload;
          const date = p.date ? new Date(p.date) : new Date();
          const patient = pacs.find((x) => x.id === p.patient);
          const procedure = procs.find((x) => x.id === p.procedure);
          const professional = profs.find((x) => x.id === p.professional);
          const duration = procedure?.duration ?? 30;
          const endDate = new Date(date); endDate.setMinutes(endDate.getMinutes() + duration);
          return {
            id: `offline-${item.id}`, title: [entityName(patient || {}), entityName(procedure || {})].filter(Boolean).join(" • ") || "Agendamento (pendente sync)",
            start: date.toISOString(), end: endDate.toISOString(),
            backgroundColor: "#a855f7", borderColor: "#9333ea", textColor: "#fff",
            ...(temExpedienteCarregado ? { constraint: "businessHours" as const } : {}),
            extendedProps: { dbId: `offline-${item.id}`, status: p.status || "SCHEDULED", patient_name: entityName(patient || {}), patient_phone: "", professional_name: professional?.name ?? "", procedure_name: entityName(procedure || {}), procedure_duration: duration, procedure_price: procedure?.price ?? "", notes: p.notes ?? "" },
          };
        });
        setEventos([...eventosFormatados, ...bloqueiosAsEvents, ...intervalos, ...pendingEvents]);

      } else {
        // OFFLINE
        const [agendaRaw, profs, pacs, procs] = await Promise.all([
          buscarAgendamentosOffline(), buscarProfissionaisOffline(), buscarPacientesOffline(), buscarProcedimentosOffline(),
        ]);
        if (Array.isArray(profs)) setProfessionals(profs as Professional[]);
        if (Array.isArray(pacs)) setPatients(pacs as Patient[]);
        if (Array.isArray(procs)) setProcedures(procs as Procedure[]);
        const profName = entityName((profs as Professional[]).find((p) => p.id === Number(selectedProfessional)) || {}) || "Profissional";
        const intervalos = selectedProfessional && horariosTrabalho.length > 0
          ? intervalosEventsFromHorarios(selectedProfessional, horariosTrabalho, profName) : [];
        if (Array.isArray(agendaRaw) && agendaRaw.length > 0) {
          let list = agendaRaw as any[];
          if (selectedProfessional) list = list.filter((e: any) => String(e.professional) === selectedProfessional);
          setEventos([...list.map((e) => formatarEvento(e)), ...intervalos]);
        } else {
          setEventos(intervalos);
        }
      }
      setLoading(false);
    } catch (error) {
      logger.warn("Erro ao carregar dados:", error);
      setLoading(false);
    }
  };

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

  const handleEventClick = (info: any) => {
    if (info.event.extendedProps?.isIntervalo) return;
    if (info.event.extendedProps?.isBloqueio) {
      setSelectedBloqueio({ id: info.event.extendedProps.bloqueioId, motivo: info.event.extendedProps.motivo || info.event.title, professional_name: info.event.extendedProps.professional_name || "Todos" });
      return;
    }
    setSelectedEvent({ id: info.event.id, title: info.event.title, start: info.event.start, end: info.event.end, backgroundColor: info.event.backgroundColor, borderColor: info.event.borderColor, textColor: info.event.textColor, extendedProps: info.event.extendedProps });
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
    return bloqueios.some((b) => {
      const profMatch = !b.professional || selectedProfessional === String(b.professional);
      if (!profMatch) return false;
      const bStart = new Date(b.data_inicio);
      const bEnd = new Date(b.data_fim);
      if (Number.isNaN(bStart.getTime()) || Number.isNaN(bEnd.getTime())) return false;
      return date < bEnd && apptEnd > bStart;
    });
  };

  const handleDateClick = (info: any) => {
    const date = info.date as Date;
    if (!selectedProfessional) {
      alert("Selecione um profissional no filtro acima para agendar dentro do horário de trabalho.");
      return;
    }
    const msg = workHoursRejectionMessage(date, 30, horariosTrabalho as HorarioTrabalho[]);
    if (msg) {
      alert(msg);
      return;
    }
    if (conflitoComBloqueio(date)) { alert("Horário bloqueado. Escolha outro horário ou gerencie bloqueios no botão \"Bloquear horário\"."); return; }
    setSelectedDate(date);
    setShowCreateModal(true);
  };

  if (lojaLoading || !loja) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f8f9fa] dark:bg-gray-950">
        <div className="text-center">
          <div
            className="w-12 h-12 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4"
            style={{ borderColor: `${CLINICA_BELEZA_PRIMARY} transparent transparent transparent` }}
          />
          <p className="text-sm text-gray-600 dark:text-gray-300">Carregando...</p>
        </div>
      </div>
    );
  }

  const agendaBody = loading ? (
    <div className="flex flex-1 items-center justify-center min-h-[320px]">
      <div className="text-center">
        <div
          className="w-12 h-12 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4"
          style={{ borderColor: `${CLINICA_BELEZA_PRIMARY} transparent transparent transparent` }}
        />
        <p className="text-sm text-gray-600 dark:text-gray-300">Carregando agenda...</p>
      </div>
    </div>
  ) : (
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
      <ClinicaBelezaPageHeaderFooter>
        <AgendaLegenda />
      </ClinicaBelezaPageHeaderFooter>

      <div className="flex flex-col flex-1 min-h-0 p-3 sm:p-4 lg:p-6">
        <div className="flex flex-col flex-1 min-h-0 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
          <div className={`flex-1 min-h-0 p-2 sm:p-3 ${modoAgenda === "grade" ? "overflow-hidden fc-agenda-mobile" : "overflow-y-auto"}`}>
          {modoAgenda === "lista" ? (
            <AgendaListaColunas eventos={eventos} onAbrir={abrirEventoDaLista} />
          ) : calendarPlugins.length > 0 && ptBrLocale ? (
            <FullCalendar
              key={`${isMobile ? "mobile" : "desktop"}-${selectedProfessional}-${horariosTrabalho.length}`}
              plugins={calendarPlugins}
              initialView={isMobile ? "timeGridDay" : "timeGridWeek"}
              locale={ptBrLocale}
              editable
              eventStartEditable={true}
              eventDurationEditable
              selectable={!!selectedProfessional}
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
              headerToolbar={isMobile ? { left: "prev,next", center: "title", right: "today" } : { left: "prev,next today", center: "title", right: "timeGridDay,timeGridWeek,dayGridMonth" }}
              buttonText={isMobile ? { today: "Hoje" } : undefined}
              slotMinTime={getSlotMinTime()}
              slotMaxTime={getSlotMaxTime()}
              allDaySlot={false}
              slotDuration="00:05:00"
              slotLabelInterval="00:30:00"
              snapDuration="00:05:00"
              businessHours={getBusinessHours()}
              hiddenDays={getHiddenDays()}
            />
          ) : null}
          </div>
        </div>
      </div>

      <ModalBloqueio open={selectedBloqueio != null} onClose={() => setSelectedBloqueio(null)} onSuccess={carregarDados} bloqueio={selectedBloqueio} />
      <ModalDetalheAgendamento
        open={showModal && selectedEvent != null} onClose={() => setShowModal(false)} onSuccess={carregarDados}
        event={selectedEvent!} onUpdateStatus={atualizarStatusAgendamento} onDelete={deletarEvento}
        onReenviarWhatsApp={reenviarMensagemWhatsApp} updatingStatus={updatingStatus} reenviandoMensagem={reenviandoMensagem}
      />
      <ModalCriarAgendamento
        open={showCreateModal} onClose={() => setShowCreateModal(false)} onSuccess={carregarDados}
        selectedDate={selectedDate} defaultProfessionalId={selectedProfessional}
        professionals={professionals} patients={patients} procedures={procedures}
        onOfflineEventCreated={(evt) => setEventos((prev) => [...prev, evt as AgendaEventData])}
      />
      <ModalBloqueioHorario isOpen={showModalBloqueio} onClose={() => setShowModalBloqueio(false)} onSuccess={() => carregarDados()} professionals={professionals as any} defaultProfessionalId={selectedProfessional} />
      <ModalConflitoAgenda open={conflictData != null} onClose={closeConflictModal} data={conflictData} onUseServer={handleConflitoUseServer} onUseLocal={handleConflitoUseLocal} resolving={conflictResolving} />
    </>
  );

  return (
    <ClinicaBelezaShell loja={loja} onLogout={handleLogout} mainClassName="overflow-hidden !overflow-y-hidden flex flex-col">
      {agendaBody}
    </ClinicaBelezaShell>
  );
}
