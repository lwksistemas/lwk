"use client";

/**
 * Página de Agenda - Clínica da Beleza
 * Calendário fullscreen com drag & drop + Bloqueio de Horários
 * Integrado com API Django
 */

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import dynamic from "next/dynamic";
import { X, Plus, Lock } from "lucide-react";
import { ModalBloqueioHorario } from "@/components/clinica-beleza/ModalBloqueioHorario";
import { getClinicaBelezaBaseUrl, getClinicaBelezaHeaders } from "@/lib/clinica-beleza-api";

/** Cores por status (padrão comercial: recepção) */
const CORES_STATUS: Record<string, { bg: string; border: string }> = {
  CONFIRMED: { bg: "#22c55e", border: "#16a34a" },   // 🟢 Confirmado
  SCHEDULED: { bg: "#a855f7", border: "#9333ea" },    // 🟣 Agendado
  PENDING: { bg: "#a855f7", border: "#9333ea" },      // 🟣 Pendente
  IN_PROGRESS: { bg: "#3b82f6", border: "#2563eb" },  // Azul em atendimento
  COMPLETED: { bg: "#6b7280", border: "#4b5563" },    // Cinza concluído
  CANCELLED: { bg: "#6b7280", border: "#4b5563" },    // ⚫ Cancelado
  NO_SHOW: { bg: "#6b7280", border: "#4b5563" },     // Cinza faltou
};

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
    dbId: number;
    status: string;
    patient_name: string;
    patient_phone: string;
    professional_name: string;
    procedure_name: string;
    procedure_duration: number;
    procedure_price: string;
    notes: string;
  };
}

interface Professional {
  id: number;
  name: string;
  specialty: string;
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
  const [eventos, setEventos] = useState<AgendaEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProfessional, setSelectedProfessional] = useState<string>("");
  const [professionals, setProfessionals] = useState<Professional[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<AgendaEvent | null>(null);
  
  // Dados para criar novo agendamento
  const [patients, setPatients] = useState<Patient[]>([]);
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [bloqueios, setBloqueios] = useState<BloqueioHorario[]>([]);
  const [showModalBloqueio, setShowModalBloqueio] = useState(false);
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
  
  useEffect(() => {
    if (calendarPlugins.length > 0) {
      carregarDados();
    }
  }, [selectedProfessional, calendarPlugins]);

  const carregarDados = async () => {
    try {
      const baseURL = getClinicaBelezaBaseUrl();
      const headers = getClinicaBelezaHeaders();

      // Carregar eventos (agendamentos)
      let url = `${baseURL}/agenda/`;
      if (selectedProfessional) {
        url += `?professional=${selectedProfessional}`;
      }
      const resEventos = await fetch(url, { headers });
      if (resEventos.ok) {
        const data = await resEventos.json();
        const eventosFormatados = data.map((e: any) => {
          const cores = CORES_STATUS[e.status] || { bg: "#a855f7", border: "#9333ea" };
          const titulo = [e.patient_name, e.procedure_name].filter(Boolean).join(" • ") || e.title || "Agendamento";
          return {
            id: String(e.id),
            title: titulo,
            start: e.start,
            end: e.end,
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
              notes: e.notes || "",
              isBloqueio: false,
            },
          };
        });

        // Carregar bloqueios de horário
        let bloqueiosUrl = `${baseURL}/bloqueios/`;
        if (selectedProfessional) {
          bloqueiosUrl += `?professional=${selectedProfessional}`;
        }
        const resBloqueios = await fetch(bloqueiosUrl, { headers });
        let bloqueiosList: BloqueioHorario[] = [];
        if (resBloqueios.ok) {
          bloqueiosList = await resBloqueios.json();
          setBloqueios(bloqueiosList);
        }
        const bloqueiosAsEvents = bloqueiosList.map((b: BloqueioHorario) => ({
          id: `bloqueio-${b.id}`,
          title: `🚫 ${b.motivo}`,
          start: b.data_inicio,
          end: b.data_fim,
          backgroundColor: "#b91c1c",
          borderColor: "#991b1b",
          textColor: "#fff",
          editable: false,
          extendedProps: {
            isBloqueio: true,
            bloqueioId: b.id,
            motivo: b.motivo,
            professional_name: b.professional_name || "Todos",
          },
        }));
        setEventos([...eventosFormatados, ...bloqueiosAsEvents]);
      }

      // Carregar profissionais
      const resProfessionals = await fetch(`${baseURL}/professionals/`, { headers });

      if (resProfessionals.ok) {
        const data = await resProfessionals.json();
        setProfessionals(data);
      }

      // Carregar pacientes
      const resPatients = await fetch(`${baseURL}/patients/`, { headers });

      if (resPatients.ok) {
        const data = await resPatients.json();
        setPatients(data);
      }

      // Carregar procedimentos
      const resProcedures = await fetch(`${baseURL}/procedures/`, { headers });

      if (resProcedures.ok) {
        const data = await resProcedures.json();
        setProcedures(data);
      }

      setLoading(false);
    } catch (error) {
      console.error("Erro ao carregar dados:", error);
      setLoading(false);
    }
  };

  const moverEvento = async (info: any) => {
    if (info.event.extendedProps?.isBloqueio) return;
    try {
      const baseURL = getClinicaBelezaBaseUrl();
      const headers = getClinicaBelezaHeaders();
      const res = await fetch(`${baseURL}/agenda/${info.event.id}/update/`, {
        method: "PATCH",
        headers,
        body: JSON.stringify({
          date: info.event.start.toISOString(),
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
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
    if (info.event.extendedProps?.isBloqueio) {
      return; // Bloqueios não abrem modal de detalhe (só na tela de Bloquear horário)
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

    if (!confirm("Deseja realmente deletar este agendamento?")) return;

    try {
      const baseURL = getClinicaBelezaBaseUrl();
      const headers = getClinicaBelezaHeaders();
      await fetch(`${baseURL}/agenda/${selectedEvent.extendedProps.dbId}/delete/`, {
        method: "DELETE",
        headers,
      });

      setShowModal(false);
      setSelectedEvent(null);
      carregarDados();
    } catch (error) {
      console.error("Erro ao deletar evento:", error);
    }
  };

  if (loading) {
    return (
      <div className="w-screen h-screen flex items-center justify-center bg-gradient-to-br from-pink-100 via-purple-50 to-white">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando agenda...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-screen h-screen flex flex-col bg-gradient-to-br from-pink-100 via-purple-50 to-white">
      {/* HEADER */}
      <div className="bg-white/70 backdrop-blur-xl shadow-sm p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-pink-200 flex items-center justify-center text-xl">
            💆‍♀️
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-800">Agenda</h1>
            <p className="text-sm text-gray-500">Clínica da Beleza</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Filtro por Profissional */}
          <select
            value={selectedProfessional}
            onChange={(e) => setSelectedProfessional(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg bg-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="">Todos os Profissionais</option>
            {professionals.map((prof) => (
              <option key={prof.id} value={prof.id}>
                {prof.name}
              </option>
            ))}
          </select>

          <button
            onClick={() => setShowModalBloqueio(true)}
            className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
            title="Bloquear horário"
          >
            <Lock size={20} />
            <span className="hidden sm:inline">Bloquear horário</span>
          </button>

          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            <Plus size={20} />
            <span className="hidden sm:inline">Novo Agendamento</span>
          </button>
        </div>
      </div>

      {/* Legenda de status */}
      <div className="px-4 py-2 flex flex-wrap items-center gap-4 text-sm bg-white/50 rounded-lg mx-4 mb-2">
        <span className="font-medium text-gray-600">Status:</span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-[#22c55e]" aria-hidden />
          Confirmado
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-[#a855f7]" aria-hidden />
          Agendado
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-[#6b7280]" aria-hidden />
          Cancelado
        </span>
      </div>

      {/* CALENDÁRIO */}
      <div className="flex-1 p-4 overflow-hidden min-h-0">
        <div className="bg-white/70 backdrop-blur-xl rounded-2xl shadow-lg h-full p-4">
          {calendarPlugins.length > 0 && ptBrLocale && (
            <FullCalendar
              plugins={calendarPlugins}
              initialView="timeGridWeek"
              locale={ptBrLocale}
              editable
              eventStartEditable={true}
              eventDurationEditable={false}
              selectable
              selectMirror
              dayMaxEvents
              weekends
              events={eventos}
              eventDrop={moverEvento}
              eventClick={handleEventClick}
              dateClick={handleDateClick}
              height="100%"
              headerToolbar={{
                left: "prev,next today",
                center: "title",
                right: "timeGridDay,timeGridWeek,dayGridMonth",
              }}
              slotMinTime="07:00:00"
              slotMaxTime="20:00:00"
              allDaySlot={false}
              slotDuration="00:30:00"
              businessHours={{
                daysOfWeek: [1, 2, 3, 4, 5, 6],
                startTime: "08:00",
                endTime: "18:00",
              }}
            />
          )}
        </div>
      </div>

      {/* MODAL DE DETALHES */}
      {showModal && selectedEvent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-bold text-gray-800">Detalhes do Agendamento</h2>
              <button
                onClick={() => setShowModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-500">Paciente</p>
                <p className="font-semibold">{selectedEvent.extendedProps.patient_name}</p>
                <p className="text-sm text-gray-600">{selectedEvent.extendedProps.patient_phone}</p>
              </div>

              <div>
                <p className="text-sm text-gray-500">Procedimento</p>
                <p className="font-semibold">{selectedEvent.extendedProps.procedure_name}</p>
                <p className="text-sm text-gray-600">
                  {selectedEvent.extendedProps.procedure_duration} min - R${" "}
                  {selectedEvent.extendedProps.procedure_price}
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-500">Profissional</p>
                <p className="font-semibold">{selectedEvent.extendedProps.professional_name}</p>
              </div>

              <div>
                <p className="text-sm text-gray-500">Data e Hora</p>
                <p className="font-semibold">
                  {new Date(selectedEvent.start).toLocaleString("pt-BR")}
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-500">Status</p>
                <span
                  className="inline-block px-3 py-1 rounded-full text-xs font-medium"
                  style={{ backgroundColor: selectedEvent.backgroundColor, color: "#fff" }}
                >
                  {selectedEvent.extendedProps.status}
                </span>
              </div>

              {selectedEvent.extendedProps.notes && (
                <div>
                  <p className="text-sm text-gray-500">Observações</p>
                  <p className="text-sm">{selectedEvent.extendedProps.notes}</p>
                </div>
              )}
            </div>

            <div className="mt-6 flex gap-3">
              <button
                onClick={deletarEvento}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Deletar
              </button>
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL NOVO AGENDAMENTO */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center p-4 border-b">
              <h2 className="text-xl font-bold text-gray-800">Novo Agendamento</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
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
                try {
                  const baseURL = getClinicaBelezaBaseUrl();
                  const headers = getClinicaBelezaHeaders();
                  const res = await fetch(`${baseURL}/agenda/create/`, {
                    method: "POST",
                    headers,
                    body: JSON.stringify({
                      date: date.toISOString(),
                      status: "SCHEDULED",
                      patient: parseInt(createForm.patientId, 10),
                      professional: parseInt(createForm.professionalId, 10),
                      procedure: parseInt(createForm.procedureId, 10),
                      notes: createForm.notes.trim() || null,
                    }),
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
                <div className="p-2 rounded bg-red-50 text-red-700 text-sm">{createError}</div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Data</label>
                <p className="text-gray-800 font-medium">
                  {selectedDate ? selectedDate.toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit", month: "short" }) : "—"}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Horário</label>
                <input
                  type="time"
                  value={createForm.time}
                  onChange={(e) => setCreateForm((f) => ({ ...f, time: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Paciente *</label>
                <select
                  value={createForm.patientId}
                  onChange={(e) => setCreateForm((f) => ({ ...f, patientId: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-lg bg-white"
                  required
                >
                  <option value="">Selecione o paciente</option>
                  {patients.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Profissional *</label>
                <select
                  value={createForm.professionalId}
                  onChange={(e) => setCreateForm((f) => ({ ...f, professionalId: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-lg bg-white"
                  required
                >
                  <option value="">Selecione o profissional</option>
                  {professionals.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Procedimento *</label>
                <select
                  value={createForm.procedureId}
                  onChange={(e) => setCreateForm((f) => ({ ...f, procedureId: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-lg bg-white"
                  required
                >
                  <option value="">Selecione o procedimento</option>
                  {procedures.map((p) => (
                    <option key={p.id} value={p.id}>{p.name} ({p.duration} min)</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Observações</label>
                <textarea
                  value={createForm.notes}
                  onChange={(e) => setCreateForm((f) => ({ ...f, notes: e.target.value }))}
                  rows={2}
                  className="w-full px-3 py-2 border rounded-lg resize-none"
                  placeholder="Opcional"
                />
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 py-2 rounded-lg border border-gray-300 hover:bg-gray-50"
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
    </div>
  );
}
