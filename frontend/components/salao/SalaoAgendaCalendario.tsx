"use client";

import { lazy, Suspense, useEffect, useMemo, useState, type CSSProperties } from "react";
import { makeAgendaFcEventContent } from "@/hooks/clinica-beleza/agenda-data/agenda-fc-event-content";
import { eventosParaFullCalendar } from "@/hooks/clinica-beleza/agenda-data/agenda-event-mappers";
import {
  agendaVisualStyleVars,
  loadAgendaVisualTheme,
  type AgendaVisualId,
} from "@/lib/clinica-agenda-visual";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import {
  businessHoursFromHorarios,
  intervalosEventsFromHorarios,
  type HorarioTrabalho,
} from "@/lib/clinica-beleza-work-hours";
import { duracaoSlotAgenda, intervaloAgendaMinutos } from "@/lib/intervalo-agenda";
import type { AgendamentoSalao, BloqueioSalao, JornadaDia, ProfissionalSalao } from "@/lib/salao-api";

const FullCalendar = lazy(() => import("@fullcalendar-v7/react"));

type Vista = "dia" | "semana" | "mes";

function comoHorario(dias: JornadaDia[]): HorarioTrabalho[] {
  return dias.map((dia) => ({
    dia_semana: dia.dia_semana,
    hora_entrada: dia.hora_entrada,
    hora_saida: dia.hora_saida,
    intervalo_inicio: dia.intervalo_inicio || null,
    intervalo_fim: dia.intervalo_fim || null,
    ativo: dia.ativo,
  }));
}

function isoDia(data: Date) {
  const mes = String(data.getMonth() + 1).padStart(2, "0");
  const dia = String(data.getDate()).padStart(2, "0");
  return `${data.getFullYear()}-${mes}-${dia}`;
}

function vistaDoCalendario(tipo: string): Vista {
  if (tipo === "timeGridWeek") return "semana";
  if (tipo === "dayGridMonth") return "mes";
  return "dia";
}

function vistaInicial(modo: Vista) {
  if (modo === "semana") return "timeGridWeek";
  if (modo === "mes") return "dayGridMonth";
  return "timeGridDay";
}

export function SalaoAgendaCalendario({
  modo,
  cursor,
  visual,
  filtroProfissional,
  profissionais,
  jornadas,
  eventos,
  bloqueios,
  statusCores,
  onVista,
  onCursor,
  onAbrir,
  onAbrirBloqueio,
  onNovo,
  onMover,
  onRedimensionar,
}: {
  modo: Vista;
  cursor: Date;
  visual: AgendaVisualId;
  filtroProfissional: string;
  profissionais: ProfissionalSalao[];
  jornadas: Record<number, JornadaDia[]>;
  eventos: AgendamentoSalao[];
  bloqueios: BloqueioSalao[];
  statusCores: Record<string, string>;
  onVista: (vista: Vista) => void;
  onCursor: (data: Date) => void;
  onAbrir: (item: AgendamentoSalao) => void;
  onAbrirBloqueio: (item: BloqueioSalao) => void;
  onNovo: (data: Date, profissionalId: string) => void;
  onMover: (id: number, inicio: Date) => void;
  onRedimensionar: (id: number, minutos: number) => void;
}) {
  const [plugins, setPlugins] = useState<unknown[]>([]);
  const [locale, setLocale] = useState<unknown>(null);
  const pessoas = filtroProfissional === "todos"
    ? profissionais
    : profissionais.filter((pessoa) => String(pessoa.id) === filtroProfissional);
  const horarios = pessoas.flatMap((pessoa) => comoHorario(jornadas[pessoa.id] || []));
  const passo = intervaloAgendaMinutos(
    filtroProfissional === "todos" ? null : pessoas[0],
  );
  const slot = duracaoSlotAgenda(passo);
  const umProfissional = filtroProfissional !== "todos";

  useEffect(() => {
    let vivo = true;
    void (async () => {
      const [dayGrid, timeGrid, interaction, ptBr] = await Promise.all([
        import("@fullcalendar-v7/react/daygrid"),
        import("@fullcalendar-v7/react/timegrid"),
        import("@fullcalendar-v7/react/interaction"),
        import("@fullcalendar-v7/react/locales/pt-br"),
      ]);
      await import("@fullcalendar-v7/react/skeleton.css");
      const theme = await loadAgendaVisualTheme(visual);
      if (!vivo) return;
      setPlugins([dayGrid.default, timeGrid.default, interaction.default, theme]);
      setLocale(ptBr.default);
    })();
    return () => { vivo = false; };
  }, [visual]);

  const eventosFc = useMemo(() => {
    const cartoes: AgendaEventData[] = eventos
      .filter((item) => item.status !== "CANCELLED" && (filtroProfissional === "todos" || String(item.profissional) === filtroProfissional))
      .map((item) => {
        const cor = statusCores[item.status] || "#7a3044";
        return {
          id: String(item.id),
          title: item.cliente_nome,
          start: item.inicio,
          end: item.fim,
          color: cor,
          contrastColor: "#fff",
          backgroundColor: cor,
          borderColor: cor,
          textColor: "#fff",
          editable: !item.recebido,
          durationEditable: !item.recebido,
          startEditable: !item.recebido,
          extendedProps: {
            dbId: item.id,
            status: item.status,
            patient_name: item.cliente_nome,
            professional: item.profissional,
            professional_name: item.profissional_nome,
            procedure_name: item.servico_nome,
          },
        };
      });
    const folgas: AgendaEventData[] = bloqueios.filter((item) => filtroProfissional === "todos" || !item.profissional || String(item.profissional) === filtroProfissional).map((item) => {
      const diaInteiro = !item.horario_inicio || !item.horario_fim;
      const inicio = diaInteiro ? "08:00" : (item.horario_inicio || "08:00").slice(0, 5);
      const fim = diaInteiro ? "20:00" : (item.horario_fim || "20:00").slice(0, 5);
      return {
        id: `bloqueio-${item.id}`,
        title: item.titulo,
        start: `${item.data_inicio}T${inicio}:00`,
        end: `${item.data_fim}T${fim}:00`,
        allDay: false,
        display: "background",
        color: "#f6e4e8",
        contrastColor: "#7a3044",
        backgroundColor: "#f6e4e8",
        borderColor: "#7a3044",
        textColor: "#7a3044",
        editable: false,
        className: "fc-event-bloqueio",
        extendedProps: {
          isBloqueio: true,
          bloqueioId: item.id,
          motivo: item.titulo,
          professional: item.profissional ?? undefined,
          professional_name: item.profissional_nome,
        },
      };
    });
    const almoco = pessoas.flatMap((pessoa) => intervalosEventsFromHorarios(
      String(pessoa.id),
      comoHorario(jornadas[pessoa.id] || []),
      pessoa.nome,
    ));
    return eventosParaFullCalendar([...cartoes, ...folgas, ...almoco], umProfissional ? filtroProfissional : "");
  }, [bloqueios, eventos, filtroProfissional, jornadas, pessoas, statusCores, umProfissional]);

  const eventContent = useMemo(
    () => makeAgendaFcEventContent({ showProfessional: !umProfissional }),
    [umProfissional],
  );

  const horas = horarios.filter((item) => item.ativo);
  const slotMinTime = horas.length
    ? `${horas.reduce((min, item) => (item.hora_entrada.slice(0, 5) < min ? item.hora_entrada.slice(0, 5) : min), "23:59")}:00`
    : "08:00:00";
  const slotMaxTime = horas.length
    ? `${horas.reduce((max, item) => (item.hora_saida.slice(0, 5) > max ? item.hora_saida.slice(0, 5) : max), "00:00")}:00`
    : "20:00:00";
  const diaFc = (backend: number) => (backend === 6 ? 0 : backend + 1);
  const hiddenDays = horas.length
    ? [0, 1, 2, 3, 4, 5, 6].filter((dia) => !horas.some((item) => diaFc(item.dia_semana) === dia))
    : [];

  return (
    <div
      className="flex min-h-[70vh] flex-col overflow-hidden border bg-white"
      data-agenda-visual={visual}
      style={{ ...agendaVisualStyleVars(visual), borderColor: "var(--agenda-border, #e5e7eb)", borderRadius: "var(--agenda-radius, 16px)" } as CSSProperties}
    >
      <div className="fc-agenda-calendar-root agenda-v7-root min-h-0 flex-1 overflow-y-auto p-2 sm:p-3">
        {plugins.length > 0 && locale ? (
          <Suspense fallback={<p className="py-10 text-center text-sm text-[#8a6e74]">Carregando calendário...</p>}>
            <FullCalendar
              key={`${vistaInicial(modo)}-${isoDia(cursor)}-${filtroProfissional}-${visual}-${slot}`}
              plugins={plugins as never[]}
              initialView={vistaInicial(modo)}
              initialDate={isoDia(cursor)}
              locale={locale as never}
              editable
              eventStartEditable
              eventDurationEditable
              selectable
              selectMirror
              dayMaxEvents={3}
              moreLinkClick="popover"
              eventMinHeight={28}
              eventShortHeight={28}
              eventMaxStack={3}
              nowIndicator
              weekends
              events={eventosFc}
              eventContent={eventContent as never}
              eventClassNames={(arg: { event: { extendedProps?: Record<string, unknown> } }) => {
                const props = arg.event.extendedProps || {};
                const classes = ["agenda-fc-event"];
                if (props.isBloqueio) classes.push("agenda-fc-event-bloqueio");
                if (props.isIntervalo) classes.push("agenda-fc-event-intervalo");
                return classes;
              }}
              eventClick={(info: { event: { id: string; extendedProps?: Record<string, unknown> }; jsEvent: { preventDefault: () => void } }) => {
                info.jsEvent.preventDefault();
                const props = info.event.extendedProps || {};
                if (props.isIntervalo) return;
                if (props.isBloqueio) {
                  const folga = bloqueios.find((item) => item.id === Number(props.bloqueioId));
                  if (folga) onAbrirBloqueio(folga);
                  return;
                }
                const item = eventos.find((agenda) => String(agenda.id) === info.event.id);
                if (item) onAbrir(item);
              }}
              dateClick={(info: { date: Date }) => onNovo(info.date, umProfissional ? filtroProfissional : "")}
              eventDrop={(info: { event: { id: string; start: Date | null; extendedProps?: Record<string, unknown> } }) => {
                const props = info.event.extendedProps || {};
                if (props.isBloqueio || props.isIntervalo || !info.event.start) return;
                onMover(Number(info.event.id), info.event.start);
              }}
              eventResize={(info: { event: { id: string; start: Date | null; end: Date | null; extendedProps?: Record<string, unknown> } }) => {
                const props = info.event.extendedProps || {};
                if (props.isBloqueio || props.isIntervalo || !info.event.start || !info.event.end) return;
                const minutos = Math.max(5, Math.round((info.event.end.getTime() - info.event.start.getTime()) / 60000));
                onRedimensionar(Number(info.event.id), minutos);
              }}
              datesSet={(arg: { view: { type: string; calendar: { getDate: () => Date } } }) => {
                const data = arg.view.calendar.getDate();
                if (isoDia(data) !== isoDia(cursor)) onCursor(data);
                const vista = vistaDoCalendario(arg.view.type);
                if (vista !== modo) onVista(vista);
              }}
              height="auto"
              headerToolbar={{
                left: "prev,next today",
                center: "title",
                right: "timeGridDay,timeGridWeek,dayGridMonth",
              }}
              buttonText={{ today: "Hoje", month: "Mês", week: "Semana", day: "Dia" }}
              slotMinTime={slotMinTime}
              slotMaxTime={slotMaxTime}
              allDaySlot={false}
              slotDuration={slot}
              slotLabelInterval={slot}
              snapDuration={slot}
              businessHours={businessHoursFromHorarios(horarios) as never}
              hiddenDays={hiddenDays}
            />
          </Suspense>
        ) : (
          <p className="py-10 text-center text-sm text-[#8a6e74]">Carregando calendário...</p>
        )}
      </div>
    </div>
  );
}
