"use client";

/**
 * Página de Agenda - Clínica da Beleza
 * Calendário fullscreen com drag & drop + Bloqueio de Horários
 * Integrado com API Django
 */

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import Link from "next/link";
import { X, Plus, Lock, Moon, Sun, ArrowLeft, MessageCircle } from "lucide-react";
import { useClinicaBelezaDark } from "@/hooks/useClinicaBelezaDark";
import { ModalBloqueioHorario } from "@/components/clinica-beleza/ModalBloqueioHorario";
import { ModalConflitoAgenda, type ConflitoAgendaData } from "@/components/clinica-beleza/ModalConflitoAgenda";
import { OfflineIndicator } from "@/components/clinica-beleza/OfflineIndicator";
import { getClinicaBelezaBaseUrl, getClinicaBelezaHeaders, clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import {
  salvarPacientesOffline,
  buscarPacientesOffline,
  salvarProfissionaisOffline,
  buscarProfissionaisOffline,
  salvarProcedimentosOffline,
  buscarProcedimentosOffline,
  salvarAgendamentosOffline,
  buscarAgendamentosOffline,
  adicionarNaFilaSync,
  obterFilaSync,
} from "@/lib/offline-db";
import { notificarFilaAtualizada } from "@/hooks/useSyncPending";

/** Cores por status (uma cor diferente para cada; concluído e faltou bem distintas) */
const CORES_STATUS: Record<string, { bg: string; border: string }> = {
  SCHEDULED: { bg: "#a855f7", border: "#9333ea" },    // 🟣 Agendado
  CONFIRMED: { bg: "#22c55e", border: "#16a34a" },    // 🟢 Confirmado
  PENDING: { bg: "#f59e0b", border: "#d97706" },      // 🟠 Pendente
  IN_PROGRESS: { bg: "#3b82f6", border: "#2563eb" },  // 🔵 Em atendimento
  COMPLETED: { bg: "#0d9488", border: "#0f766e" },   // 🩵 Concluído (teal)
  CANCELLED: { bg: "#dc2626", border: "#b91c1c" },   // 🔴 Cancelado
  NO_SHOW: { bg: "#b45309", border: "#92400e" },      // 🟤 Faltou (âmbar escuro)
};

/** Cor do evento de bloqueio de horário (distinta do vermelho cancelado) */
const COR_BLOQUEIO = { bg: "#4f46e5", border: "#4338ca" }; // Índigo

// Importar FullCalendar dinamicamente (client-side only)
const FullCalendar = dynamic(() => import("@fullcalendar/react"), {
  ssr: false,
  loading: () => <div className="flex items-center justify-center h-full">Carregando calendário...</div>,
});

interface AgendaEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  backgroundColor: string;
  borderColor: string;
  textColor: string;
  extendedProps: {
    dbId: number | string;
    status: string;
    patient_name: string;
    patient_phone: string;
    professional_name: string;
    procedure_name: string;
    procedure_duration: number;
    procedure_price: string;
    notes: string;
    version?: number;
    updated_at?: string;
  };
}

interface Professional {
  id: number;
  name: string;
  specialty: string;
}

interface HorarioTrabalho {
  id: number;
  dia_semana: number;
  hora_entrada: string;
  hora_saida: string;
  intervalo_inicio: string | null;
  intervalo_fim: string | null;
  ativo: boolean;
}

interface Patient {
  id: number;
  name: string;
  phone: string;
}

interface Procedure {
  id: number;
  name: string;
  duration: number;
  price: string;
}

interface BloqueioHorario {
  id: number;
  professional: number | null;
  professional_name: string | null;
  data_inicio: string;
  data_fim: string;
  motivo: string;
  observacoes: string | null;
  criado_em: string;
}

export default function AgendaPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const [lojaNome, setLojaNome] = useState<string>("");
  const [eventos, setEventos] = useState<AgendaEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProfessional, setSelectedProfessional] = useState<string>("");
  const [professionals, setProfessionals] = useState<Professional[]>([]);
  const [horariosTrabalho, setHorariosTrabalho] = useState<HorarioTrabalho[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<AgendaEvent | null>(null);
  
  // Dados para criar novo agendamento
  const [patients, setPatients] = useState<Patient[]>([]);
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [bloqueios, setBloqueios] = useState<BloqueioHorario[]>([]);
  const [showModalBloqueio, setShowModalBloqueio] = useState(false);
  const [selectedBloqueio, setSelectedBloqueio] = useState<{ id: number; motivo: string; professional_name: string } | null>(null);
  const [deletingBloqueio, setDeletingBloqueio] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [reenviandoMensagem, setReenviandoMensagem] = useState(false);
  const [conflictData, setConflictData] = useState<(ConflitoAgendaData & { appointmentId: number; payloadForResolve: { status?: string; date?: string } }) | null>(null);
  const [conflictResolving, setConflictResolving] = useState(false);
  const [createForm, setCreateForm] = useState({
    patientId: "",
    professionalId: "",
    procedureId: "",
    time: "09:00",
    notes: "",
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState("");
  
  // Plugins do FullCalendar (carregados dinamicamente)
  const [calendarPlugins, setCalendarPlugins] = useState<any[]>([]);
  const [ptBrLocale, setPtBrLocale] = useState<any>(null);
  const [darkMode, setDarkMode] = useClinicaBelezaDark();
  const [isMobile, setIsMobile] = useState(false);

  // Abrir modal "Novo Agendamento" quando ?novo=1 na URL
  useEffect(() => {
    if (searchParams.get("novo") === "1") {
      setSelectedDate(new Date());
      setShowCreateModal(true);
    }
  }, [searchParams]);

  // Redirecionar para login se não houver token (evita 401 em bloqueios, agenda, etc.)
  useEffect(() => {
    if (typeof window === "undefined" || !slug) return;
    const token = sessionStorage.getItem("access_token") || localStorage.getItem("token");
    if (!token) {
      window.location.href = `/loja/${slug}/login`;
      return;
    }
    // Garantir current_loja_id e loja_slug para as requisições da API (podem estar vazios se abriu direto a agenda)
    const lojaId = sessionStorage.getItem("current_loja_id");
    const lojaSlug = sessionStorage.getItem("loja_slug");
    if (!lojaId || !lojaSlug) {
      sessionStorage.setItem("loja_slug", slug);
      // current_loja_id será preenchido ao carregar info_publica ou nas requisições via X-Tenant-Slug
    }
  }, [slug]);

  useEffect(() => {
    // Carregar plugins do FullCalendar no client-side
    const loadPlugins = async () => {
      const dayGridPlugin = (await import("@fullcalendar/daygrid")).default;
      const timeGridPlugin = (await import("@fullcalendar/timegrid")).default;
      const interactionPlugin = (await import("@fullcalendar/interaction")).default;
      const ptBr = (await import("@fullcalendar/core/locales/pt-br")).default;
      
      setCalendarPlugins([dayGridPlugin, timeGridPlugin, interactionPlugin]);
      setPtBrLocale(ptBr);
    };
    
    loadPlugins();
  }, []);
  
  // Carregar nome da loja (definido em Nova Loja no superadmin)
  useEffect(() => {
    if (!slug) return;
    const fetchLoja = async () => {
      try {
        const api = (await import("@/lib/api-client")).default;
        const res = await api.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
        const data = res.data;
        if (data?.nome) setLojaNome(data.nome);
        if (data?.id != null && typeof window !== "undefined") {
          sessionStorage.setItem("current_loja_id", String(data.id));
          if (data.slug) sessionStorage.setItem("loja_slug", data.slug);
        }
      } catch {
        // ignora; subtítulo fica vazio ou genérico
      }
    };
    fetchLoja();
  }, [slug]);

  useEffect(() => {
    if (calendarPlugins.length > 0) {
      carregarDados();
    }
  }, [selectedProfessional, calendarPlugins]);

  // Carregar horários de trabalho quando selecionar profissional
  useEffect(() => {
    const carregarHorarios = async () => {
      if (!selectedProfessional) {
        setHorariosTrabalho([]);
        return;
      }
      try {
        const res = await clinicaBelezaFetch(`/professionals/${selectedProfessional}/horarios-trabalho/`);
        if (res.ok) {
          const data = await res.json();
          console.log('📅 Horários de trabalho carregados:', data);
          setHorariosTrabalho(Array.isArray(data) ? data : []);
        } else {
          console.error('❌ Erro ao carregar horários:', res.status);
          setHorariosTrabalho([]);
        }
      } catch (err) {
        console.error('❌ Erro ao carregar horários:', err);
        setHorariosTrabalho([]);
      }
    };
    carregarHorarios();
  }, [selectedProfessional]);

  // Layout responsivo: no celular usar view do dia e toolbar compacta
  useEffect(() => {
    const check = () => setIsMobile(typeof window !== "undefined" && window.innerWidth < 640);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  // Após sync da fila (registrado no layout da loja), recarregar dados para refletir agendamentos enviados
  useEffect(() => {
    const handler = () => {
      console.log("🔄 [agenda] Sincronização concluída, recarregando dados...");
      // Delay para o backend persistir e a lista GET /agenda/ trazer o novo agendamento
      setTimeout(() => carregarDados(), 1200);
    };
    window.addEventListener("offline-sync-done", handler);
    return () => window.removeEventListener("offline-sync-done", handler);
  }, []);

  const formatarEvento = (e: any) => {
    const cores = CORES_STATUS[e.status] || { bg: "#a855f7", border: "#9333ea" };
    const titulo = [e.patient_name, e.procedure_name].filter(Boolean).join(" • ") || e.title || "Agendamento";
    return {
      id: String(e.id),
      title: titulo,
      start: e.start,
      end: e.end,
      allDay: false,
      backgroundColor: cores.bg,
      borderColor: cores.border,
      textColor: "#fff",
      editable: e.status !== "CANCELLED",
      extendedProps: {
        dbId: e.id,
        status: e.status,
        patient_name: e.patient_name,
        patient_phone: e.patient_phone,
        professional_name: e.professional_name,
        procedure_name: e.procedure_name,
        procedure_duration: e.procedure_duration,
        procedure_price: e.procedure_price,
        notes: e.notes,
        version: e.version,
        updated_at: e.updated_at,
      },
    };
  };

  // Converter horários de trabalho para formato businessHours do FullCalendar
  const getBusinessHours = () => {
    if (!selectedProfessional || horariosTrabalho.length === 0) {
      // Padrão: segunda a sábado, 8h às 18h
      return {
        daysOfWeek: [1, 2, 3, 4, 5, 6],
        startTime: "08:00",
        endTime: "18:00",
      };
    }

    // Converter horários de trabalho para formato do FullCalendar
    return horariosTrabalho
      .filter((h) => h.ativo)
      .map((h) => ({
        daysOfWeek: [h.dia_semana === 6 ? 0 : h.dia_semana + 1], // FullCalendar: 0=domingo, 1=segunda
        startTime: h.hora_entrada.slice(0, 5),
        endTime: h.hora_saida.slice(0, 5),
      }));
  };

  // Obter dias ocultos (dias que o profissional NÃO trabalha)
  const getHiddenDays = () => {
    if (!selectedProfessional || horariosTrabalho.length === 0) {
      return [0]; // Ocultar apenas domingo por padrão
    }

    const diasAtivos = horariosTrabalho
      .filter((h) => h.ativo)
      .map((h) => (h.dia_semana === 6 ? 0 : h.dia_semana + 1));

    // Retornar dias que NÃO estão na lista de dias ativos
    const todosDias = [0, 1, 2, 3, 4, 5, 6];
    return todosDias.filter((dia) => !diasAtivos.includes(dia));
  };

  // Obter horário mínimo e máximo baseado nos horários de trabalho
  const getSlotMinTime = () => {
    if (!selectedProfessional || horariosTrabalho.length === 0) {
      return "07:00:00";
    }
    const horariosAtivos = horariosTrabalho.filter((h) => h.ativo);
    if (horariosAtivos.length === 0) return "07:00:00";
    
    const menorHorario = horariosAtivos.reduce((min, h) => {
      const hora = h.hora_entrada.slice(0, 5);
      return hora < min ? hora : min;
    }, "23:59");
    
    console.log('⏰ Horário mínimo calculado:', menorHorario);
    return menorHorario + ":00";
  };

  const getSlotMaxTime = () => {
    if (!selectedProfessional || horariosTrabalho.length === 0) {
      return "20:00:00";
    }
    const horariosAtivos = horariosTrabalho.filter((h) => h.ativo);
    if (horariosAtivos.length === 0) return "20:00:00";
    
    const maiorHorario = horariosAtivos.reduce((max, h) => {
      const hora = h.hora_saida.slice(0, 5);
      return hora > max ? hora : max;
    }, "00:00");
    
    console.log('⏰ Horário máximo calculado:', maiorHorario);
    return maiorHorario + ":00";
  };

  const carregarDados = async () => {
    try {
      const online = typeof navigator !== "undefined" && navigator.onLine;

      if (online) {
        // --- ONLINE: buscar da API e salvar no IndexedDB; mesclar agendamentos pendentes da fila para não sumirem
        const agendaPath = selectedProfessional ? `/agenda/?professional=${selectedProfessional}` : "/agenda/";
        const bloqueiosPath = selectedProfessional ? `/bloqueios/?professional=${selectedProfessional}` : "/bloqueios/";
        const [resEventos, resBloqueios, resProfessionals, resPatients, resProcedures] = await Promise.all([
          clinicaBelezaFetch(agendaPath),
          clinicaBelezaFetch(bloqueiosPath),
          clinicaBelezaFetch("/professionals/"),
          clinicaBelezaFetch("/patients/"),
          clinicaBelezaFetch("/procedures/"),
        ]);

        const profs: Professional[] = resProfessionals.ok ? await resProfessionals.json() : [];
        const pacs: Patient[] = resPatients.ok ? await resPatients.json() : [];
        const procs: Procedure[] = resProcedures.ok ? await resProcedures.json() : [];
        if (profs.length) {
          setProfessionals(profs);
          await salvarProfissionaisOffline(profs);
        }
        if (pacs.length) {
          setPatients(pacs);
          await salvarPacientesOffline(pacs);
        }
        if (procs.length) {
          setProcedures(procs);
          await salvarProcedimentosOffline(procs);
        }

        let eventosFormatados: any[] = [];
        let bloqueiosAsEvents: any[] = [];
        if (resEventos.ok) {
          const data = await resEventos.json();
          await salvarAgendamentosOffline(data);
          eventosFormatados = data.map((e: any) => formatarEvento(e));
        }
        let bloqueiosList: BloqueioHorario[] = [];
        if (resBloqueios.ok) {
          bloqueiosList = await resBloqueios.json();
          setBloqueios(bloqueiosList);
          bloqueiosAsEvents = bloqueiosList.map((b: BloqueioHorario) => {
            const rawStart = b.data_inicio ?? "";
            const rawEnd = b.data_fim ?? "";
            let startStr: string;
            let endStr: string;
            
            // Sempre usar os horários originais do bloqueio
            if (typeof rawStart === "string" && rawStart.includes("T") && typeof rawEnd === "string" && rawEnd.includes("T")) {
              startStr = rawStart;
              endStr = rawEnd;
            } else {
              // Fallback se não tiver horário (improvável)
              const datePart = rawStart ? String(rawStart).slice(0, 10) : "";
              startStr = datePart ? `${datePart}T00:00:00` : "";
              endStr = datePart ? `${datePart}T23:59:59` : "";
            }
            
            return {
              id: `bloqueio-${b.id}`,
              title: `🚫 ${b.motivo}`,
              start: startStr,
              end: endStr,
              allDay: false,
              backgroundColor: COR_BLOQUEIO.bg,
              borderColor: COR_BLOQUEIO.border,
              textColor: "#fff",
              editable: false,
              extendedProps: {
                isBloqueio: true,
                bloqueioId: b.id,
                motivo: b.motivo,
                professional_name: b.professional_name || "Todos",
              },
            };
          });
        }

        // Criar eventos de intervalo (almoço) baseados nos horários de trabalho
        const intervalosAsEvents: any[] = [];
        if (selectedProfessional && horariosTrabalho.length > 0) {
          console.log('🍽️ Criando intervalos para profissional:', selectedProfessional);
          console.log('📋 Horários disponíveis:', horariosTrabalho);
          
          const hoje = new Date();
          const diasParaMostrar = 30; // Mostrar intervalos para os próximos 30 dias
          
          for (let i = 0; i < diasParaMostrar; i++) {
            const data = new Date(hoje);
            data.setDate(hoje.getDate() + i);
            const diaSemana = data.getDay(); // 0=domingo, 1=segunda, etc.
            
            // Converter dia da semana do JS para o formato do backend (0=segunda, 6=domingo)
            const diaBackend = diaSemana === 0 ? 6 : diaSemana - 1;
            
            // Buscar horário de trabalho para este dia
            const horario = horariosTrabalho.find(h => h.ativo && h.dia_semana === diaBackend);
            
            if (horario && horario.intervalo_inicio && horario.intervalo_fim) {
              const y = data.getFullYear();
              const m = String(data.getMonth() + 1).padStart(2, "0");
              const d = String(data.getDate()).padStart(2, "0");
              
              // Garantir que os horários estão no formato correto (HH:MM)
              const intervaloInicio = typeof horario.intervalo_inicio === 'string' 
                ? horario.intervalo_inicio.slice(0, 5) 
                : '12:00';
              const intervaloFim = typeof horario.intervalo_fim === 'string' 
                ? horario.intervalo_fim.slice(0, 5) 
                : '13:00';
              
              const intervalo = {
                id: `intervalo-${selectedProfessional}-${y}${m}${d}`,
                title: "🍽️ Intervalo",
                start: `${y}-${m}-${d}T${intervaloInicio}:00`,
                end: `${y}-${m}-${d}T${intervaloFim}:00`,
                allDay: false,
                backgroundColor: "#f59e0b",
                borderColor: "#d97706",
                textColor: "#fff",
                editable: false,
                extendedProps: {
                  isIntervalo: true,
                  professional_name: professionals.find(p => p.id === Number(selectedProfessional))?.name || "Profissional",
                },
              };
              
              console.log(`✅ Intervalo criado para ${y}-${m}-${d}:`, intervalo);
              intervalosAsEvents.push(intervalo);
            }
          }
          
          console.log(`📊 Total de intervalos criados: ${intervalosAsEvents.length}`);
        }

        // Mesclar agendamentos ainda na fila de sync (criados offline) para não sumirem ao recarregar
        const fila = await obterFilaSync();
        const pendentesAgenda = fila.filter((f) => f.tipo === "agendamento") as Array<{ id: number; payload: { date?: string; status?: string; patient?: number; professional?: number; procedure?: number; notes?: string | null } }>;
        const pendingEvents = pendentesAgenda.map((item) => {
          const p = item.payload;
          const date = p.date ? new Date(p.date) : new Date();
          const patient = pacs.find((x) => x.id === p.patient);
          const procedure = procs.find((x) => x.id === p.procedure);
          const professional = profs.find((x) => x.id === p.professional);
          const duration = procedure?.duration ?? 30;
          const endDate = new Date(date);
          endDate.setMinutes(endDate.getMinutes() + duration);
          const titulo = [patient?.name, procedure?.name].filter(Boolean).join(" • ") || "Agendamento (pendente sync)";
          return {
            id: `offline-${item.id}`,
            title: titulo,
            start: date.toISOString(),
            end: endDate.toISOString(),
            backgroundColor: "#a855f7",
            borderColor: "#9333ea",
            textColor: "#fff",
            editable: false,
            extendedProps: {
              dbId: `offline-${item.id}`,
              status: p.status || "SCHEDULED",
              patient_name: patient?.name ?? "",
              patient_phone: "",
              professional_name: professional?.name ?? "",
              procedure_name: procedure?.name ?? "",
              procedure_duration: duration,
              procedure_price: procedure?.price ?? "",
              notes: p.notes ?? "",
              isBloqueio: false,
            },
          };
        });

        setEventos([...eventosFormatados, ...bloqueiosAsEvents, ...intervalosAsEvents, ...pendingEvents]);
      } else {
        // --- OFFLINE: ler do IndexedDB
        const [agendaRaw, profs, pacs, procs] = await Promise.all([
          buscarAgendamentosOffline(),
          buscarProfissionaisOffline(),
          buscarPacientesOffline(),
          buscarProcedimentosOffline(),
        ]);
        if (Array.isArray(profs)) setProfessionals(profs as Professional[]);
        if (Array.isArray(pacs)) setPatients(pacs as Patient[]);
        if (Array.isArray(procs)) setProcedures(procs as Procedure[]);
        
        // Criar eventos de intervalo mesmo offline
        const intervalosAsEvents: any[] = [];
        if (selectedProfessional && horariosTrabalho.length > 0) {
          const hoje = new Date();
          const diasParaMostrar = 30;
          
          for (let i = 0; i < diasParaMostrar; i++) {
            const data = new Date(hoje);
            data.setDate(hoje.getDate() + i);
            const diaSemana = data.getDay();
            const diaBackend = diaSemana === 0 ? 6 : diaSemana - 1;
            const horario = horariosTrabalho.find(h => h.ativo && h.dia_semana === diaBackend);
            
            if (horario && horario.intervalo_inicio && horario.intervalo_fim) {
              const y = data.getFullYear();
              const m = String(data.getMonth() + 1).padStart(2, "0");
              const d = String(data.getDate()).padStart(2, "0");
              
              // Garantir que os horários estão no formato correto (HH:MM)
              const intervaloInicio = typeof horario.intervalo_inicio === 'string' 
                ? horario.intervalo_inicio.slice(0, 5) 
                : '12:00';
              const intervaloFim = typeof horario.intervalo_fim === 'string' 
                ? horario.intervalo_fim.slice(0, 5) 
                : '13:00';
              
              intervalosAsEvents.push({
                id: `intervalo-${selectedProfessional}-${y}${m}${d}`,
                title: "🍽️ Intervalo",
                start: `${y}-${m}-${d}T${intervaloInicio}:00`,
                end: `${y}-${m}-${d}T${intervaloFim}:00`,
                allDay: false,
                backgroundColor: "#f59e0b",
                borderColor: "#d97706",
                textColor: "#fff",
                editable: false,
                extendedProps: {
                  isIntervalo: true,
                  professional_name: (profs as Professional[]).find(p => p.id === Number(selectedProfessional))?.name || "Profissional",
                },
              });
            }
          }
        }
        
        if (Array.isArray(agendaRaw) && agendaRaw.length > 0) {
          let list = agendaRaw as any[];
          if (selectedProfessional) {
            list = list.filter((e: any) => String(e.professional) === selectedProfessional);
          }
          const eventosFormatados = list.map((e: any) => formatarEvento(e));
          setEventos([...eventosFormatados, ...intervalosAsEvents]);
        } else {
          setEventos(intervalosAsEvents);
        }
      }

      setLoading(false);
    } catch (error) {
      console.error("Erro ao carregar dados:", error);
      setLoading(false);
    }
  };

  const moverEvento = async (info: any) => {
    if (info.event.extendedProps?.isBloqueio) return;
    const version = info.event.extendedProps?.version;
    const updated_at = info.event.extendedProps?.updated_at;
    const body: { date: string; version?: number; updated_at?: string } = {
      date: info.event.start.toISOString(),
    };
    if (version != null) body.version = version;
    if (updated_at) body.updated_at = updated_at;
    try {
      const baseURL = getClinicaBelezaBaseUrl();
      const headers = getClinicaBelezaHeaders();
      const res = await fetch(`${baseURL}/agenda/${info.event.id}/update/`, {
        method: "PATCH",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (res.status === 409 && data.conflict) {
        info.revert();
        setConflictData({
          server: data.server,
          local: data.local,
          resolution_hint: data.resolution_hint,
          appointmentId: Number(info.event.id),
          payloadForResolve: { date: info.event.start.toISOString() },
        });
        return;
      }
      if (!res.ok) {
        const msg = data.error || "Não foi possível mover. Horário pode estar bloqueado.";
        alert(msg);
        info.revert();
        return;
      }

      carregarDados();
    } catch (error) {
      console.error("Erro ao mover evento:", error);
      alert("Erro ao mover evento. Tente novamente.");
      info.revert();
    }
  };

  const handleEventClick = (info: any) => {
    // Não permitir clicar em intervalos
    if (info.event.extendedProps?.isIntervalo) {
      return;
    }
    
    if (info.event.extendedProps?.isBloqueio) {
      setSelectedBloqueio({
        id: info.event.extendedProps.bloqueioId,
        motivo: info.event.extendedProps.motivo || info.event.title,
        professional_name: info.event.extendedProps.professional_name || "Todos",
      });
      return;
    }
    setSelectedEvent({
      id: info.event.id,
      title: info.event.title,
      start: info.event.start,
      end: info.event.end,
      backgroundColor: info.event.backgroundColor,
      borderColor: info.event.borderColor,
      textColor: info.event.textColor,
      extendedProps: info.event.extendedProps,
    });
    setShowModal(true);
  };

  /** Verifica se o horário está bloqueado (bloqueio geral ou do profissional selecionado). */
  const conflitoComBloqueio = (date: Date): boolean => {
    return bloqueios.some((b) => {
      const dentro = date >= new Date(b.data_inicio) && date <= new Date(b.data_fim);
      if (!dentro) return false;
      if (!b.professional) return true; // bloqueio geral
      return selectedProfessional === String(b.professional);
    });
  };

  const handleDateClick = (info: any) => {
    const date = info.date as Date;
    if (conflitoComBloqueio(date)) {
      alert("Horário bloqueado. Escolha outro horário ou gerencie bloqueios no botão \"Bloquear horário\".");
      return;
    }
    setSelectedDate(date);
    setCreateForm({
      patientId: "",
      professionalId: "",
      procedureId: "",
      time: date.getHours().toString().padStart(2, "0") + ":" + date.getMinutes().toString().padStart(2, "0"),
      notes: "",
    });
    setCreateError("");
    setShowCreateModal(true);
  };

  const deletarEvento = async () => {
    if (!selectedEvent) return;
    const dbId = selectedEvent.extendedProps.dbId;
    if (typeof dbId === "string" && dbId.startsWith("offline-")) {
      alert("Agendamento criado offline. Aguarde a sincronização para excluir.");
      return;
    }
    if (!confirm("Deseja realmente deletar este agendamento?")) return;

    try {
      const baseURL = getClinicaBelezaBaseUrl();
      const headers = getClinicaBelezaHeaders();
      const res = await fetch(`${baseURL}/agenda/${dbId}/delete/`, {
        method: "DELETE",
        headers,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || "Erro ao deletar agendamento");
      }
      setShowModal(false);
      setSelectedEvent(null);
      carregarDados();
    } catch (error) {
      console.error("Erro ao deletar evento:", error);
      alert(error instanceof Error ? error.message : "Erro ao deletar agendamento.");
    }
  };

  const excluirBloqueio = async () => {
    if (!selectedBloqueio) return;
    if (!confirm(`Excluir o bloqueio "${selectedBloqueio.motivo}"?`)) return;
    setDeletingBloqueio(true);
    try {
      const baseURL = getClinicaBelezaBaseUrl();
      const headers = getClinicaBelezaHeaders();
      const res = await fetch(`${baseURL}/bloqueios/${selectedBloqueio.id}/`, { method: "DELETE", headers });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || "Erro ao excluir bloqueio");
      }
      setSelectedBloqueio(null);
      carregarDados();
    } catch (error) {
      console.error("Erro ao excluir bloqueio:", error);
      alert(error instanceof Error ? error.message : "Erro ao excluir bloqueio.");
    } finally {
      setDeletingBloqueio(false);
    }
  };

  const atualizarStatusAgendamento = async (novoStatus: string) => {
    if (!selectedEvent) return;
    const dbId = selectedEvent.extendedProps.dbId;
    if (typeof dbId === "string" && dbId.startsWith("offline-")) {
      alert("Agendamento criado offline. Aguarde a sincronização para alterar status.");
      return;
    }
    setUpdatingStatus(true);
    try {
      const baseURL = getClinicaBelezaBaseUrl();
      const headers = getClinicaBelezaHeaders();
      const body: { status: string; version?: number; updated_at?: string } = { status: novoStatus };
      if (selectedEvent.extendedProps.version != null) body.version = selectedEvent.extendedProps.version;
      if (selectedEvent.extendedProps.updated_at) body.updated_at = selectedEvent.extendedProps.updated_at;
      const res = await fetch(`${baseURL}/agenda/${dbId}/update/`, {
        method: "PATCH",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (res.status === 409 && data.conflict) {
        setConflictData({
          server: data.server,
          local: data.local,
          resolution_hint: data.resolution_hint,
          appointmentId: Number(dbId),
          payloadForResolve: { status: novoStatus },
        });
        setUpdatingStatus(false);
        return;
      }
      if (!res.ok) throw new Error(data.error || "Erro ao atualizar status");
      setSelectedEvent((prev) =>
        prev ? { ...prev, extendedProps: { ...prev.extendedProps, status: novoStatus } } : null
      );
      carregarDados();
    } catch (error) {
      console.error("Erro ao atualizar status:", error);
      alert(error instanceof Error ? error.message : "Erro ao atualizar status.");
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleConflitoUseServer = () => {
    setConflictData(null);
    setShowModal(false);
    carregarDados();
  };

  const reenviarMensagemWhatsApp = async () => {
    if (!selectedEvent) return;
    const dbId = selectedEvent.extendedProps.dbId;
    if (typeof dbId === "string" && dbId.startsWith("offline-")) {
      alert("Agendamento offline. Sincronize antes de reenviar mensagem.");
      return;
    }
    setReenviandoMensagem(true);
    try {
      const baseURL = getClinicaBelezaBaseUrl();
      const headers = getClinicaBelezaHeaders();
      const res = await clinicaBelezaFetch(`/agenda/${dbId}/reenviar-mensagem/`, { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (data.sent) {
        alert("Mensagem reenviada com sucesso para o paciente.");
      } else {
        alert(data.message || "Não foi possível reenviar a mensagem.");
      }
    } catch (e) {
      if (e instanceof Error && e.message === "SESSION_ENDED") return;
      console.error("Erro ao reenviar mensagem:", e);
      alert("Erro ao reenviar mensagem. Tente novamente.");
    } finally {
      setReenviandoMensagem(false);
    }
  };

  const handleConflitoUseLocal = async () => {
    if (!conflictData) return;
    setConflictResolving(true);
    try {
      const baseURL = getClinicaBelezaBaseUrl();
      const headers = getClinicaBelezaHeaders();
      const res = await fetch(`${baseURL}/agenda/${conflictData.appointmentId}/update/`, {
        method: "PATCH",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({
          ...conflictData.payloadForResolve,
          resolve_use_local: true,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || "Erro ao aplicar sua versão");
      }
      setConflictData(null);
      setShowModal(false);
      carregarDados();
    } catch (e) {
      console.error("Erro ao resolver conflito:", e);
      alert(e instanceof Error ? e.message : "Erro ao aplicar sua versão.");
    } finally {
      setConflictResolving(false);
    }
  };

  if (loading) {
    return (
      <div className="w-screen h-screen flex items-center justify-center bg-gradient-to-br from-pink-100 via-purple-50 to-white dark:from-neutral-900 dark:via-neutral-800 dark:to-neutral-900">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300">Carregando agenda...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-screen h-screen flex flex-col bg-gradient-to-br from-pink-100 via-purple-50 to-white dark:from-neutral-900 dark:via-neutral-800 dark:to-neutral-900 text-gray-800 dark:text-gray-100 overflow-hidden">
      {/* HEADER: compacto no celular, com wrap para não quebrar */}
      <div className="bg-white/70 dark:bg-neutral-800/70 backdrop-blur-xl shadow-sm p-3 sm:p-4 flex flex-wrap items-center justify-between gap-2 shrink-0">
        <div className="flex items-center gap-2 sm:gap-3 min-w-0">
          <Link
            href={`/loja/${slug}/dashboard`}
            className="flex items-center gap-1.5 p-2 rounded-lg hover:bg-purple-50 dark:hover:bg-neutral-700 transition-colors text-gray-700 dark:text-gray-300 font-medium shrink-0"
            aria-label="Voltar ao dashboard"
          >
            <ArrowLeft className="w-5 h-5 shrink-0" />
            <span className="hidden sm:inline">Voltar</span>
          </Link>
          <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-pink-200 dark:bg-pink-900 flex items-center justify-center text-lg sm:text-xl shrink-0">
            💆‍♀️
          </div>
          <div className="min-w-0">
            <h1 className="text-base sm:text-xl font-bold text-gray-800 dark:text-gray-100 truncate">Agenda</h1>
            <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 truncate">{lojaNome || "Agenda"}</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 sm:gap-3 flex-wrap justify-end">
          <OfflineIndicator />
          <button
            type="button"
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-lg hover:bg-purple-50 dark:hover:bg-neutral-700 transition-colors shrink-0"
            title={darkMode ? "Modo claro" : "Modo escuro"}
            aria-label={darkMode ? "Modo claro" : "Modo escuro"}
          >
            {darkMode ? <Sun className="w-5 h-5 text-purple-600" /> : <Moon className="w-5 h-5 text-purple-600" />}
          </button>
          <select
            value={selectedProfessional}
            onChange={(e) => setSelectedProfessional(e.target.value)}
            className="px-2 sm:px-4 py-1.5 sm:py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 max-w-[120px] sm:max-w-none"
          >
            <option value="">Todos</option>
            {professionals.map((prof) => (
              <option key={prof.id} value={prof.id}>
                {prof.name}
              </option>
            ))}
          </select>
          <button
            onClick={() => setShowModalBloqueio(true)}
            className="flex items-center gap-1.5 px-2.5 sm:px-4 py-1.5 sm:py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors shrink-0 text-sm"
            title="Bloquear horário"
          >
            <Lock size={18} className="sm:w-5 sm:h-5" />
            <span className="hidden sm:inline">Bloquear</span>
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-1.5 px-2.5 sm:px-4 py-1.5 sm:py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors shrink-0 text-sm"
            title="Novo agendamento"
          >
            <Plus size={18} className="sm:w-5 sm:h-5" />
            <span className="hidden sm:inline">Novo</span>
          </button>
        </div>
      </div>

      {/* Legenda: mais compacta no celular */}
      <div className="px-3 sm:px-4 py-1.5 sm:py-2 flex flex-wrap items-center gap-2 sm:gap-4 text-xs sm:text-sm bg-white/50 dark:bg-neutral-800/50 rounded-lg mx-3 sm:mx-4 mb-1 sm:mb-2 text-gray-700 dark:text-gray-300 shrink-0">
        <span className="font-medium text-gray-600 dark:text-gray-400">Status:</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-[#22c55e]" aria-hidden />Confirmado</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-[#a855f7]" aria-hidden />Agendado</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-[#f59e0b]" aria-hidden />Intervalo</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-[#6b7280]" aria-hidden />Cancelado</span>
      </div>

      {/* CALENDÁRIO: no celular view do dia, toolbar compacta, mais área útil */}
      <div className="flex-1 min-h-0 p-2 sm:p-4 overflow-hidden">
        <div className="bg-white/70 dark:bg-neutral-800/70 backdrop-blur-xl rounded-xl sm:rounded-2xl shadow-lg h-full p-2 sm:p-4 fc-agenda-mobile">
          {calendarPlugins.length > 0 && ptBrLocale && (
            <FullCalendar
              key={`${isMobile ? "mobile" : "desktop"}-${selectedProfessional}-${horariosTrabalho.length}`}
              plugins={calendarPlugins}
              initialView={isMobile ? "timeGridDay" : "timeGridWeek"}
              locale={ptBrLocale}
              editable
              eventStartEditable={true}
              eventDurationEditable={false}
              selectable
              selectMirror
              dayMaxEvents={isMobile ? 6 : true}
              weekends
              events={eventos}
              eventDrop={moverEvento}
              eventClick={handleEventClick}
              dateClick={handleDateClick}
              height="100%"
              headerToolbar={
                isMobile
                  ? { left: "prev,next", center: "title", right: "today" }
                  : { left: "prev,next today", center: "title", right: "timeGridDay,timeGridWeek,dayGridMonth" }
              }
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

      {/* MODAL DETALHES BLOQUEIO - Excluir */}
      {selectedBloqueio && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-md w-full p-6">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Bloqueio de horário</h2>
              <button
                onClick={() => setSelectedBloqueio(null)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-2">{selectedBloqueio.motivo}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Profissional: {selectedBloqueio.professional_name}</p>
            <div className="mt-6 flex gap-3">
              <button
                type="button"
                onClick={excluirBloqueio}
                disabled={deletingBloqueio}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {deletingBloqueio ? "Excluindo..." : "Excluir bloqueio"}
              </button>
              <button
                onClick={() => setSelectedBloqueio(null)}
                className="flex-1 px-4 py-2 bg-gray-200 dark:bg-neutral-600 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-neutral-500"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL DE DETALHES */}
      {showModal && selectedEvent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-md w-full p-6">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Detalhes do Agendamento</h2>
              <button
                onClick={() => setShowModal(false)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Paciente</p>
                <p className="font-semibold text-gray-900 dark:text-gray-100">{selectedEvent.extendedProps.patient_name}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">{selectedEvent.extendedProps.patient_phone}</p>
              </div>

              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Procedimento</p>
                <p className="font-semibold text-gray-900 dark:text-gray-100">{selectedEvent.extendedProps.procedure_name}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {selectedEvent.extendedProps.procedure_duration} min - R${" "}
                  {selectedEvent.extendedProps.procedure_price}
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Profissional</p>
                <p className="font-semibold text-gray-900 dark:text-gray-100">{selectedEvent.extendedProps.professional_name}</p>
              </div>

              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Data e Hora</p>
                <p className="font-semibold text-gray-900 dark:text-gray-100">
                  {new Date(selectedEvent.start).toLocaleString("pt-BR")}
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Status {updatingStatus && <span className="text-xs">(salvando…)</span>}</p>
                <div className="flex items-center gap-2">
                  <span
                    className="shrink-0 w-3 h-3 rounded-full border-2 border-gray-900/10"
                    style={{
                      backgroundColor: CORES_STATUS[selectedEvent.extendedProps.status]?.bg ?? "#a855f7",
                      borderColor: CORES_STATUS[selectedEvent.extendedProps.status]?.border ?? "#9333ea",
                    }}
                    aria-hidden
                  />
                  <select
                    value={selectedEvent.extendedProps.status}
                    onChange={(e) => atualizarStatusAgendamento(e.target.value)}
                    disabled={updatingStatus}
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm disabled:opacity-70"
                  >
                    <option value="SCHEDULED">🟣 Agendado</option>
                    <option value="CONFIRMED">🟢 Confirmado</option>
                    <option value="PENDING">🟠 Pendente</option>
                    <option value="IN_PROGRESS">🔵 Em Atendimento</option>
                    <option value="COMPLETED">⚫ Concluído</option>
                    <option value="CANCELLED">🔴 Cancelado</option>
                    <option value="NO_SHOW">⬜ Faltou</option>
                  </select>
                </div>
              </div>

              {selectedEvent.extendedProps.notes && (
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Observações</p>
                  <p className="text-sm text-gray-800 dark:text-gray-200">{selectedEvent.extendedProps.notes}</p>
                </div>
              )}
            </div>

            <div className="mt-4 flex flex-col gap-2">
              <button
                type="button"
                onClick={reenviarMensagemWhatsApp}
                disabled={reenviandoMensagem || !selectedEvent.extendedProps.patient_phone}
                className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                title="Reenviar confirmação por WhatsApp ao paciente"
              >
                <MessageCircle size={18} />
                {reenviandoMensagem ? "Enviando…" : "Reenviar mensagem WhatsApp"}
              </button>
              {!selectedEvent.extendedProps.patient_phone && (
                <p className="text-xs text-gray-500 dark:text-gray-400">Paciente sem telefone; não é possível reenviar.</p>
              )}
            </div>
            <div className="mt-4 flex gap-3">
              <button
                onClick={deletarEvento}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Deletar
              </button>
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 px-4 py-2 bg-gray-200 dark:bg-neutral-600 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-neutral-500 transition-colors"
              >
                Salvar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL NOVO AGENDAMENTO */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center p-4 border-b dark:border-neutral-700">
              <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Novo Agendamento</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            <form
              className="p-4 space-y-3"
              onSubmit={async (e) => {
                e.preventDefault();
                if (!createForm.patientId || !createForm.professionalId || !createForm.procedureId) {
                  setCreateError("Selecione paciente, profissional e procedimento.");
                  return;
                }
                if (!selectedDate) {
                  setCreateError("Data não definida.");
                  return;
                }
                const [h, m] = createForm.time.split(":").map(Number);
                const date = new Date(selectedDate);
                date.setHours(h, m, 0, 0);
                setCreateLoading(true);
                setCreateError("");
                const payload = {
                  date: date.toISOString(),
                  status: "SCHEDULED",
                  patient: parseInt(createForm.patientId, 10),
                  professional: parseInt(createForm.professionalId, 10),
                  procedure: parseInt(createForm.procedureId, 10),
                  notes: createForm.notes.trim() || null,
                };
                try {
                  if (!navigator.onLine) {
                    await adicionarNaFilaSync({ tipo: "agendamento", payload });
                    notificarFilaAtualizada();
                    const patient = patients.find((p) => p.id === parseInt(createForm.patientId, 10));
                    const professional = professionals.find((p) => p.id === parseInt(createForm.professionalId, 10));
                    const procedure = procedures.find((p) => p.id === parseInt(createForm.procedureId, 10));
                    const titulo = [patient?.name, procedure?.name].filter(Boolean).join(" • ") || "Agendamento (offline)";
                    const tempId = `offline-${Date.now()}`;
                    const endDate = new Date(date);
                    endDate.setMinutes(endDate.getMinutes() + (procedure?.duration ?? 30));
                    setEventos((prev) => [
                      ...prev,
                      {
                        id: tempId,
                        title: titulo,
                        start: date.toISOString(),
                        end: endDate.toISOString(),
                        backgroundColor: "#a855f7",
                        borderColor: "#9333ea",
                        textColor: "#fff",
                        editable: false,
                        extendedProps: {
                          dbId: tempId,
                          status: "SCHEDULED",
                          patient_name: patient?.name ?? "",
                          patient_phone: "",
                          professional_name: professional?.name ?? "",
                          procedure_name: procedure?.name ?? "",
                          procedure_duration: procedure?.duration ?? 30,
                          procedure_price: procedure?.price ?? "",
                          notes: createForm.notes.trim() || "",
                          isBloqueio: false,
                        },
                      },
                    ]);
                    setShowCreateModal(false);
                    setCreateForm({ patientId: "", professionalId: "", procedureId: "", time: "09:00", notes: "" });
                    setCreateLoading(false);
                    return;
                  }
                  const baseURL = getClinicaBelezaBaseUrl();
                  const headers = getClinicaBelezaHeaders();
                  const res = await fetch(`${baseURL}/agenda/create/`, {
                    method: "POST",
                    headers,
                    body: JSON.stringify(payload),
                  });
                  if (!res.ok) {
                    const data = await res.json().catch(() => ({}));
                    throw new Error(data.error || "Erro ao criar agendamento");
                  }
                  setShowCreateModal(false);
                  setCreateForm({ patientId: "", professionalId: "", procedureId: "", time: "09:00", notes: "" });
                  carregarDados();
                } catch (err: unknown) {
                  setCreateError(err instanceof Error ? err.message : "Erro ao criar agendamento");
                } finally {
                  setCreateLoading(false);
                }
              }}
            >
              {createError && (
                <div className="p-2 rounded bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm">{createError}</div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data</label>
                <p className="text-gray-800 dark:text-gray-200 font-medium">
                  {selectedDate ? selectedDate.toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit", month: "short" }) : "—"}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Horário</label>
                <input
                  type="time"
                  value={createForm.time}
                  onChange={(e) => setCreateForm((f) => ({ ...f, time: e.target.value }))}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Paciente *</label>
                <select
                  value={createForm.patientId}
                  onChange={(e) => setCreateForm((f) => ({ ...f, patientId: e.target.value }))}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                  required
                >
                  <option value="">Selecione o paciente</option>
                  {patients.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Profissional *</label>
                <select
                  value={createForm.professionalId}
                  onChange={(e) => setCreateForm((f) => ({ ...f, professionalId: e.target.value }))}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                  required
                >
                  <option value="">Selecione o profissional</option>
                  {professionals.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Procedimento *</label>
                <select
                  value={createForm.procedureId}
                  onChange={(e) => setCreateForm((f) => ({ ...f, procedureId: e.target.value }))}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                  required
                >
                  <option value="">Selecione o procedimento</option>
                  {procedures.map((p) => (
                    <option key={p.id} value={p.id}>{p.name} ({p.duration} min)</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Observações</label>
                <textarea
                  value={createForm.notes}
                  onChange={(e) => setCreateForm((f) => ({ ...f, notes: e.target.value }))}
                  rows={2}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 resize-none"
                  placeholder="Opcional"
                />
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 text-gray-700 dark:text-gray-300"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={createLoading}
                  className="flex-1 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50"
                >
                  {createLoading ? "Agendando..." : "Agendar"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Bloqueio de Horários */}
      <ModalBloqueioHorario
        isOpen={showModalBloqueio}
        onClose={() => setShowModalBloqueio(false)}
        onSuccess={() => carregarDados()}
        professionals={professionals}
      />

      {/* Modal Conflito de Sincronização */}
      <ModalConflitoAgenda
        open={conflictData != null}
        onClose={() => setConflictData(null)}
        data={conflictData}
        onUseServer={handleConflitoUseServer}
        onUseLocal={handleConflitoUseLocal}
        resolving={conflictResolving}
      />
    </div>
  );
}
