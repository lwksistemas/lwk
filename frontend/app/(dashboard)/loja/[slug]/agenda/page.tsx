"use client";

/**
 * Página de Agenda - Clínica da Beleza
 * Calendário fullscreen com drag & drop
 * Integrado com API Django
 */

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import dynamic from "next/dynamic";
import { X, Plus } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import ProtectedRoute from "@/components/ProtectedRoute";
import { fetchWithAuth } from "@/lib/auth";

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

export default function AgendaPage() {
  const params = useParams();
  const { user, isAdmin, isRecepcao, isProfissional } = useAuth();
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
      const token = localStorage.getItem("token");
      const baseURL = process.env.NEXT_PUBLIC_API_URL;

      // Carregar eventos
      let url = `${baseURL}/clinica-beleza/agenda/`;
      if (selectedProfessional) {
        url += `?professional=${selectedProfessional}`;
      }

      const resEventos = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (resEventos.ok) {
        const data = await resEventos.json();
        const eventosFormatados = data.map((e: any) => ({
          id: String(e.id),
          title: e.title,
          start: e.start,
          end: e.end,
          backgroundColor: e.backgroundColor,
          borderColor: e.borderColor,
          textColor: e.textColor,
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
          },
        }));
        setEventos(eventosFormatados);
      }

      // Carregar profissionais
      const resProfessionals = await fetch(`${baseURL}/clinica-beleza/professionals/`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (resProfessionals.ok) {
        const data = await resProfessionals.json();
        setProfessionals(data);
      }

      // Carregar pacientes
      const resPatients = await fetch(`${baseURL}/clinica-beleza/patients/`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (resPatients.ok) {
        const data = await resPatients.json();
        setPatients(data);
      }

      // Carregar procedimentos
      const resProcedures = await fetch(`${baseURL}/clinica-beleza/procedures/`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

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
    try {
      const token = localStorage.getItem("token");
      const baseURL = process.env.NEXT_PUBLIC_API_URL;

      await fetch(`${baseURL}/clinica-beleza/agenda/${info.event.id}/update/`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          date: info.event.start.toISOString(),
        }),
      });

      // Recarregar eventos
      carregarDados();
    } catch (error) {
      console.error("Erro ao mover evento:", error);
      info.revert();
    }
  };

  const handleEventClick = (info: any) => {
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

  const handleDateClick = (info: any) => {
    setSelectedDate(info.date);
    setShowCreateModal(true);
  };

  const deletarEvento = async () => {
    if (!selectedEvent) return;

    if (!confirm("Deseja realmente deletar este agendamento?")) return;

    try {
      const token = localStorage.getItem("token");
      const baseURL = process.env.NEXT_PUBLIC_API_URL;

      await fetch(`${baseURL}/clinica-beleza/agenda/${selectedEvent.extendedProps.dbId}/delete/`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
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
    <ProtectedRoute>
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
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            <Plus size={20} />
            <span className="hidden sm:inline">Novo Agendamento</span>
          </button>
        </div>
      </div>

      {/* CALENDÁRIO */}
      <div className="flex-1 p-4 overflow-hidden">
        <div className="bg-white/70 backdrop-blur-xl rounded-2xl shadow-lg h-full p-4">
          {calendarPlugins.length > 0 && ptBrLocale && (
            <FullCalendar
              plugins={calendarPlugins}
              initialView="timeGridWeek"
              locale={ptBrLocale}
              editable
              selectable
              selectMirror
              dayMaxEvents
              weekends
              events={eventos}
              eventDrop={moverEvento}
              eventResize={moverEvento}
              eventClick={handleEventClick}
              dateClick={handleDateClick}
              height="100%"
              headerToolbar={{
                left: "prev,next today",
                center: "title",
                right: "dayGridMonth,timeGridWeek,timeGridDay",
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

      {/* MODAL DE CRIAR (Placeholder) */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-bold text-gray-800">Novo Agendamento</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <p className="text-center text-gray-600 py-8">
              Formulário de criação em desenvolvimento...
            </p>

            <button
              onClick={() => setShowCreateModal(false)}
              className="w-full px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Fechar
            </button>
          </div>
        </div>
      )}
    </div>
    </ProtectedRoute>
  );
}
