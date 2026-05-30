"use client";

/**
 * Página de Agenda - Clínica da Beleza
 * Calendário fullscreen com drag & drop + Bloqueio de Horários
 */

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { Plus, Lock } from "lucide-react";
import apiClient from "@/lib/api-client";
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
import { ModalConflitoAgenda, type ConflitoAgendaData } from "@/components/clinica-beleza/ModalConflitoAgenda";
import { OfflineIndicator } from "@/components/clinica-beleza/OfflineIndicator";
import { getClinicaBelezaBaseUrl, getClinicaBelezaHeaders, clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import {
  salvarPacientesOffline, buscarPacientesOffline,
  salvarProfissionaisOffline, buscarProfissionaisOffline,
  salvarProcedimentosOffline, buscarProcedimentosOffline,
  salvarAgendamentosOffline, buscarAgendamentosOffline, obterFilaSync,
} from "@/lib/offline-db";
import { logger } from "@/lib/logger";
import {
  type HorarioTrabalho,
  workHoursRejectionMessage,
} from "@/lib/clinica-beleza-work-hours";
import { ModalDetalheAgendamento, type AgendaEventData } from "./components/ModalDetalheAgendamento";
import { ModalCriarAgendamento } from "./components/ModalCriarAgendamento";
import { ModalBloqueio } from "./components/ModalBloqueio";

const CORES_STATUS: Record<string, { bg: string; border: string }> = {
  SCHEDULED: { bg: "#a855f7", border: "#9333ea" },
  CONFIRMED: { bg: "#22c55e", border: "#16a34a" },
  PENDING: { bg: "#f59e0b", border: "#d97706" },
  IN_PROGRESS: { bg: "#3b82f6", border: "#2563eb" },
  COMPLETED: { bg: "#0d9488", border: "#0f766e" },
  CANCELLED: { bg: "#dc2626", border: "#b91c1c" },
  NO_SHOW: { bg: "#b45309", border: "#92400e" },
};
const COR_BLOQUEIO = { bg: "#4f46e5", border: "#4338ca" };

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

function gName(o: { name?: string; nome?: string }): string { return o.name || o.nome || ''; }

/** Gera eventos de intervalo (almoço) para os próximos 30 dias */
function criarIntervalosEvents(profId: string, horarios: HorarioTrabalhoRow[], profName: string): any[] {
  const result: any[] = [];
  const hoje = new Date();
  for (let i = 0; i < 30; i++) {
    const data = new Date(hoje);
    data.setDate(hoje.getDate() + i);
    const diaBackend = data.getDay() === 0 ? 6 : data.getDay() - 1;
    const horario = horarios.find(h => h.ativo && h.dia_semana === diaBackend);
    if (horario?.intervalo_inicio && horario?.intervalo_fim) {
      const y = data.getFullYear();
      const m = String(data.getMonth() + 1).padStart(2, "0");
      const d = String(data.getDate()).padStart(2, "0");
      const ini = typeof horario.intervalo_inicio === 'string' ? horario.intervalo_inicio.slice(0, 5) : '12:00';
      const fim = typeof horario.intervalo_fim === 'string' ? horario.intervalo_fim.slice(0, 5) : '13:00';
      result.push({
        id: `intervalo-${profId}-${y}${m}${d}`, title: "🍽️ Intervalo",
        start: `${y}-${m}-${d}T${ini}:00`, end: `${y}-${m}-${d}T${fim}:00`,
        allDay: false, backgroundColor: "#f59e0b", borderColor: "#d97706", textColor: "#fff", editable: false,
        extendedProps: { isIntervalo: true, professional_name: profName },
      });
    }
  }
  return result;
}

export default function AgendaPage() {
  const params = useParams();
  const router = useRouter();
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
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [reenviandoMensagem, setReenviandoMensagem] = useState(false);
  const [conflictData, setConflictData] = useState<(ConflitoAgendaData & { appointmentId: number; payloadForResolve: { status?: string; date?: string } }) | null>(null);
  const [conflictResolving, setConflictResolving] = useState(false);
  const [consultaId, setConsultaId] = useState<number | null>(null);
  const [calendarPlugins, setCalendarPlugins] = useState<any[]>([]);
  const [ptBrLocale, setPtBrLocale] = useState<any>(null);
  useClinicaBelezaDark();
  const [isMobile, setIsMobile] = useState(false);

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
      .then((res) => setLoja(res.data as LojaInfo))
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

  // Carregar nome da loja
  useEffect(() => {
    if (!slug) return;
    (async () => {
      try {
        const api = (await import("@/lib/api-client")).default;
        const res = await api.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
        if (res.data?.id != null && typeof window !== "undefined") {
          sessionStorage.setItem("current_loja_id", String(res.data.id));
          if (res.data.slug) sessionStorage.setItem("loja_slug", res.data.slug);
        }
      } catch { /* ignora */ }
    })();
  }, [slug]);

  useEffect(() => { if (calendarPlugins.length > 0) carregarDados(); // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedProfessional, calendarPlugins]);

  useEffect(() => {
    if (!selectedProfessional) { setHorariosTrabalho([]); return; }
    (async () => {
      try {
        const res = await clinicaBelezaFetch(`/professionals/${selectedProfessional}/horarios-trabalho/`);
        setHorariosTrabalho(res.ok ? (await res.json()) : []);
      } catch { setHorariosTrabalho([]); }
    })();
  }, [selectedProfessional]);

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

  const formatarEvento = (e: any): AgendaEventData => {
    const cores = CORES_STATUS[e.status] || { bg: "#a855f7", border: "#9333ea" };
    const titulo = [e.patient_name, e.procedure_name].filter(Boolean).join(" • ") || e.title || "Agendamento";
    return {
      id: String(e.id), title: titulo, start: e.start, end: e.end,
      backgroundColor: cores.bg, borderColor: cores.border, textColor: "#fff",
      extendedProps: {
        dbId: e.id, status: e.status, patient_name: e.patient_name, patient_phone: e.patient_phone,
        professional_name: e.professional_name, procedure_name: e.procedure_name,
        procedure_duration: e.procedure_duration, procedure_price: e.procedure_price,
        notes: e.notes, version: e.version, updated_at: e.updated_at,
      },
    };
  };

  const getBusinessHours = () => {
    if (!selectedProfessional || horariosTrabalho.length === 0) {
      return { daysOfWeek: [1, 2, 3, 4, 5], startTime: "08:00", endTime: "18:00" };
    }
    const ativos = horariosTrabalho.filter((h) => h.ativo);
    if (!ativos.length) {
      return { daysOfWeek: [1, 2, 3, 4, 5], startTime: "08:00", endTime: "18:00" };
    }
    return ativos.map((h) => {
      const fcDay = h.dia_semana === 6 ? 0 : h.dia_semana + 1;
      return { daysOfWeek: [fcDay], startTime: (h.hora_entrada || '08:00').slice(0, 5), endTime: (h.hora_saida || '18:00').slice(0, 5) };
    });
  };

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
        const [resEv, resBl, resProf, resPat, resProc] = await Promise.all([
          clinicaBelezaFetch(agendaPath), clinicaBelezaFetch(bloqueiosPath),
          clinicaBelezaFetch("/professionals/?with_schedule=true"),
          clinicaBelezaFetch("/patients/"), clinicaBelezaFetch("/procedures/"),
        ]);
        const profs: Professional[] = resProf.ok ? await resProf.json() : [];
        const pacs: Patient[] = resPat.ok ? await resPat.json() : [];
        const procs: Procedure[] = resProc.ok ? await resProc.json() : [];
        if (profs.length) { setProfessionals(profs); await salvarProfissionaisOffline(profs); }
        if (pacs.length) { setPatients(pacs); await salvarPacientesOffline(pacs); }
        if (procs.length) { setProcedures(procs); await salvarProcedimentosOffline(procs); }

        let eventosFormatados: AgendaEventData[] = [];
        if (resEv.ok) { const data = await resEv.json(); await salvarAgendamentosOffline(data); eventosFormatados = data.map(formatarEvento); }

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
              allDay: false, backgroundColor: COR_BLOQUEIO.bg, borderColor: COR_BLOQUEIO.border, textColor: "#fff", editable: false,
              extendedProps: { isBloqueio: true, bloqueioId: b.id, motivo: b.motivo, professional_name: b.professional_name || "Todos" },
            };
          });
        }

        const profName = professionals.find(p => p.id === Number(selectedProfessional))?.name || "Profissional";
        const intervalos = selectedProfessional && horariosTrabalho.length > 0
          ? criarIntervalosEvents(selectedProfessional, horariosTrabalho, profName) : [];

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
            id: `offline-${item.id}`, title: [gName(patient || {}), gName(procedure || {})].filter(Boolean).join(" • ") || "Agendamento (pendente sync)",
            start: date.toISOString(), end: endDate.toISOString(),
            backgroundColor: "#a855f7", borderColor: "#9333ea", textColor: "#fff",
            extendedProps: { dbId: `offline-${item.id}`, status: p.status || "SCHEDULED", patient_name: gName(patient || {}), patient_phone: "", professional_name: professional?.name ?? "", procedure_name: gName(procedure || {}), procedure_duration: duration, procedure_price: procedure?.price ?? "", notes: p.notes ?? "" },
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
        const profName = (profs as Professional[]).find(p => p.id === Number(selectedProfessional))?.name || "Profissional";
        const intervalos = selectedProfessional && horariosTrabalho.length > 0
          ? criarIntervalosEvents(selectedProfessional, horariosTrabalho, profName) : [];
        if (Array.isArray(agendaRaw) && agendaRaw.length > 0) {
          let list = agendaRaw as any[];
          if (selectedProfessional) list = list.filter((e: any) => String(e.professional) === selectedProfessional);
          setEventos([...list.map(formatarEvento), ...intervalos]);
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

  const moverEvento = async (info: any) => {
    if (info.event.extendedProps?.isBloqueio) return;
    const { version, updated_at } = info.event.extendedProps || {};
    const body: any = { date: info.event.start.toISOString() };
    if (version != null) body.version = version;
    if (updated_at) body.updated_at = updated_at;
    try {
      const baseURL = getClinicaBelezaBaseUrl();
      const headers = getClinicaBelezaHeaders();
      const res = await fetch(`${baseURL}/agenda/${info.event.id}/update/`, { method: "PATCH", headers: { ...headers, "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const data = await res.json().catch(() => ({}));
      if (res.status === 409 && data.conflict) {
        info.revert();
        setConflictData({ server: data.server, local: data.local, resolution_hint: data.resolution_hint, appointmentId: Number(info.event.id), payloadForResolve: { date: info.event.start.toISOString() } });
        return;
      }
      if (!res.ok) { alert(data.error || "Não foi possível mover. Horário pode estar bloqueado."); info.revert(); return; }
      carregarDados();
    } catch (error) { logger.warn("Erro ao mover evento:", error); alert("Erro ao mover evento. Tente novamente."); info.revert(); }
  };

  const handleEventClick = (info: any) => {
    if (info.event.extendedProps?.isIntervalo) return;
    if (info.event.extendedProps?.isBloqueio) {
      setSelectedBloqueio({ id: info.event.extendedProps.bloqueioId, motivo: info.event.extendedProps.motivo || info.event.title, professional_name: info.event.extendedProps.professional_name || "Todos" });
      return;
    }
    setSelectedEvent({ id: info.event.id, title: info.event.title, start: info.event.start, end: info.event.end, backgroundColor: info.event.backgroundColor, borderColor: info.event.borderColor, textColor: info.event.textColor, extendedProps: info.event.extendedProps });
    setConsultaId(null);
    setShowModal(true);
    const dbId = info.event.extendedProps?.dbId;
    const st = info.event.extendedProps?.status;
    if (dbId && (st === "IN_PROGRESS" || st === "COMPLETED" || st === "CONFIRMED")) {
      clinicaBelezaFetch(`/consultas/?appointment=${dbId}`)
        .then((r) => r.json())
        .then((data) => {
          const arr = Array.isArray(data) ? data : [];
          if (arr[0]?.id) setConsultaId(arr[0].id);
        })
        .catch(() => {});
    }
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

  const deletarEvento = async () => {
    if (!selectedEvent) return;
    const dbId = selectedEvent.extendedProps.dbId;
    if (typeof dbId === "string" && dbId.startsWith("offline-")) { alert("Agendamento criado offline. Aguarde a sincronização para excluir."); return; }
    if (!confirm("Deseja realmente deletar este agendamento?")) return;
    try {
      const res = await fetch(`${getClinicaBelezaBaseUrl()}/agenda/${dbId}/delete/`, { method: "DELETE", headers: getClinicaBelezaHeaders() });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.error || "Erro ao deletar agendamento"); }
      setShowModal(false); setSelectedEvent(null); carregarDados();
    } catch (error) { logger.warn("Erro ao deletar evento:", error); alert(error instanceof Error ? error.message : "Erro ao deletar agendamento."); }
  };

  const atualizarStatusAgendamento = async (novoStatus: string) => {
    if (!selectedEvent) return;
    const dbId = selectedEvent.extendedProps.dbId;
    if (typeof dbId === "string" && dbId.startsWith("offline-")) { alert("Agendamento criado offline. Aguarde a sincronização para alterar status."); return; }
    setUpdatingStatus(true);
    try {
      const baseURL = getClinicaBelezaBaseUrl();
      const headers = getClinicaBelezaHeaders();
      const body: any = { status: novoStatus };
      if (selectedEvent.extendedProps.version != null) body.version = selectedEvent.extendedProps.version;
      if (selectedEvent.extendedProps.updated_at) body.updated_at = selectedEvent.extendedProps.updated_at;
      const res = await fetch(`${baseURL}/agenda/${dbId}/update/`, { method: "PATCH", headers: { ...headers, "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const data = await res.json().catch(() => ({}));
      if (res.status === 409 && data.conflict) {
        setConflictData({ server: data.server, local: data.local, resolution_hint: data.resolution_hint, appointmentId: Number(dbId), payloadForResolve: { status: novoStatus } });
        setUpdatingStatus(false); return;
      }
      if (!res.ok) throw new Error(data.error || "Erro ao atualizar status");
      setSelectedEvent((prev) => prev ? { ...prev, extendedProps: { ...prev.extendedProps, status: novoStatus } } : null);
      if (data.consulta_error) {
        alert(data.consulta_error);
      }
      if (data.consulta_id) {
        setConsultaId(data.consulta_id);
        if (novoStatus === "IN_PROGRESS") {
          const abrir = confirm("Consulta iniciada. Deseja abrir a tela de atendimento agora?");
          if (abrir) router.push(`/loja/${slug}/clinica-beleza/consultas?id=${data.consulta_id}`);
        }
      }
      carregarDados();
    } catch (error) { logger.warn("Erro ao atualizar status:", error); alert(error instanceof Error ? error.message : "Erro ao atualizar status."); }
    finally { setUpdatingStatus(false); }
  };

  const reenviarMensagemWhatsApp = async () => {
    if (!selectedEvent) return;
    const dbId = selectedEvent.extendedProps.dbId;
    if (typeof dbId === "string" && dbId.startsWith("offline-")) { alert("Agendamento offline. Sincronize antes de reenviar mensagem."); return; }
    setReenviandoMensagem(true);
    try {
      const res = await clinicaBelezaFetch(`/agenda/${dbId}/reenviar-mensagem/`, { method: "POST" });
      const data = await res.json().catch(() => ({}));
      alert(data.sent ? "Mensagem reenviada com sucesso para o paciente." : (data.message || "Não foi possível reenviar a mensagem."));
    } catch (e) { if (e instanceof Error && e.message === "SESSION_ENDED") return; logger.warn("Erro ao reenviar mensagem:", e); alert("Erro ao reenviar mensagem. Tente novamente."); }
    finally { setReenviandoMensagem(false); }
  };

  const handleConflitoUseServer = () => { setConflictData(null); setShowModal(false); carregarDados(); };
  const handleConflitoUseLocal = async () => {
    if (!conflictData) return;
    setConflictResolving(true);
    try {
      const res = await fetch(`${getClinicaBelezaBaseUrl()}/agenda/${conflictData.appointmentId}/update/`, {
        method: "PATCH", headers: { ...getClinicaBelezaHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ ...conflictData.payloadForResolve, resolve_use_local: true }),
      });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.error || "Erro ao aplicar sua versão"); }
      setConflictData(null); setShowModal(false); carregarDados();
    } catch (e) { logger.warn("Erro ao resolver conflito:", e); alert(e instanceof Error ? e.message : "Erro ao aplicar sua versão."); }
    finally { setConflictResolving(false); }
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
            <select
              value={selectedProfessional}
              onChange={(e) => setSelectedProfessional(e.target.value)}
              className="px-2.5 sm:px-3 py-1.5 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-[#8B3D52]/30 max-w-[120px] sm:max-w-none"
            >
              <option value="">Todos</option>
              {professionals.map((prof) => (
                <option key={prof.id} value={prof.id}>{gName(prof)}</option>
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
        <div className="flex flex-wrap items-center gap-3 sm:gap-4 text-xs sm:text-sm text-gray-600 dark:text-gray-400">
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-[#a855f7]" aria-hidden />Agendado</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-[#22c55e]" aria-hidden />Confirmado</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-[#b45309]" aria-hidden />Faltou</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-[#6b7280]" aria-hidden />Cancelado</span>
        </div>
      </ClinicaBelezaPageHeaderFooter>

      <div className="flex flex-col flex-1 min-h-0 p-3 sm:p-4 lg:p-6">
        <div className="flex flex-col flex-1 min-h-0 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
          <div className="flex-1 min-h-0 p-2 sm:p-3 overflow-hidden fc-agenda-mobile">
          {calendarPlugins.length > 0 && ptBrLocale && (
            <FullCalendar
              key={`${isMobile ? "mobile" : "desktop"}-${selectedProfessional}-${horariosTrabalho.length}`}
              plugins={calendarPlugins}
              initialView={isMobile ? "timeGridDay" : "timeGridWeek"}
              locale={ptBrLocale}
              editable
              eventStartEditable={true}
              eventDurationEditable={false}
              selectable={!!selectedProfessional}
              selectMirror
              selectConstraint={selectedProfessional && horariosTrabalho.some((h) => h.ativo) ? "businessHours" : undefined}
              eventConstraint={selectedProfessional && horariosTrabalho.some((h) => h.ativo) ? "businessHours" : undefined}
              dayMaxEvents={isMobile ? 6 : true}
              weekends
              events={eventos}
              eventDrop={moverEvento}
              eventClick={handleEventClick}
              dateClick={handleDateClick}
              height="100%"
              headerToolbar={isMobile ? { left: "prev,next", center: "title", right: "today" } : { left: "prev,next today", center: "title", right: "timeGridDay,timeGridWeek,dayGridMonth" }}
              buttonText={isMobile ? { today: "Hoje" } : undefined}
              slotMinTime={getSlotMinTime()}
              slotMaxTime={getSlotMaxTime()}
              allDaySlot={false}
              slotDuration="00:30:00"
              businessHours={getBusinessHours()}
              hiddenDays={getHiddenDays()}
            />
          )}
          </div>
        </div>
      </div>

      <ModalBloqueio open={selectedBloqueio != null} onClose={() => setSelectedBloqueio(null)} onSuccess={carregarDados} bloqueio={selectedBloqueio} />
      <ModalDetalheAgendamento
        open={showModal && selectedEvent != null} onClose={() => setShowModal(false)} onSuccess={carregarDados}
        event={selectedEvent!} onUpdateStatus={atualizarStatusAgendamento} onDelete={deletarEvento}
        onReenviarWhatsApp={reenviarMensagemWhatsApp} updatingStatus={updatingStatus} reenviandoMensagem={reenviandoMensagem}
        consultaDisponivel={consultaId != null}
        onAbrirConsulta={() => {
          if (consultaId) router.push(`/loja/${slug}/clinica-beleza/consultas?id=${consultaId}`);
        }}
      />
      <ModalCriarAgendamento
        open={showCreateModal} onClose={() => setShowCreateModal(false)} onSuccess={carregarDados}
        selectedDate={selectedDate} defaultProfessionalId={selectedProfessional}
        professionals={professionals} patients={patients} procedures={procedures}
        onOfflineEventCreated={(evt) => setEventos((prev) => [...prev, evt as AgendaEventData])}
      />
      <ModalBloqueioHorario isOpen={showModalBloqueio} onClose={() => setShowModalBloqueio(false)} onSuccess={() => carregarDados()} professionals={professionals as any} defaultProfessionalId={selectedProfessional} />
      <ModalConflitoAgenda open={conflictData != null} onClose={() => setConflictData(null)} data={conflictData} onUseServer={handleConflitoUseServer} onUseLocal={handleConflitoUseLocal} resolving={conflictResolving} />
    </>
  );

  return (
    <ClinicaBelezaShell loja={loja} onLogout={handleLogout} mainClassName="overflow-hidden !overflow-y-hidden flex flex-col">
      {agendaBody}
    </ClinicaBelezaShell>
  );
}
