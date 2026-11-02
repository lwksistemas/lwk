'use client';

/**
 * Prévia do visual Pulse (FullCalendar 7) — o mesmo tema usado na visão Mês da agenda.
 */
import { useEffect, useMemo, useState, type ComponentType } from 'react';
import {
  CLINICA_AGENDA_STATUS_COLORS,
  CLINICA_AGENDA_STATUS_LABEL,
  type AgendaStatusColorMap,
} from '@/lib/clinica-beleza-constants';

type CalendarProps = {
  plugins: unknown[];
  initialView: string;
  locale?: unknown;
  headerToolbar: Record<string, string>;
  height: number | string;
  weekends: boolean;
  dayMaxEvents: boolean;
  allDaySlot?: boolean;
  slotMinTime?: string;
  slotMaxTime?: string;
  nowIndicator?: boolean;
  events: Array<{
    id: string;
    title: string;
    start: string;
    end?: string;
    backgroundColor?: string;
    borderColor?: string;
  }>;
};

type LoadedMods = {
  FullCalendar: ComponentType<CalendarProps>;
  plugins: unknown[];
  locale: unknown;
};

function buildSampleEvents(statusColors: AgendaStatusColorMap) {
  const today = new Date();
  const y = today.getFullYear();
  const m = String(today.getMonth() + 1).padStart(2, '0');
  const d = String(today.getDate()).padStart(2, '0');
  const dia = `${y}-${m}-${d}`;

  const amostras: Array<{ key: string; hora: string; titulo: string }> = [
    { key: 'SCHEDULED', hora: '09:00', titulo: 'Ana — consulta' },
    { key: 'CLIENT_CONFIRMED', hora: '10:30', titulo: 'Bruno — protocolo' },
    { key: 'PHONE_CONFIRMED', hora: '14:00', titulo: 'Carla — retorno' },
    { key: 'CONFIRMED', hora: '16:00', titulo: 'Diana — presente' },
  ];

  return amostras.map((item, i) => {
    const colors =
      statusColors[item.key] || CLINICA_AGENDA_STATUS_COLORS[item.key] || {
        bg: '#a855f7',
        border: '#9333ea',
      };
    const [hh, mm] = item.hora.split(':').map(Number);
    const startH = String(hh).padStart(2, '0');
    const endH = String(hh + 1).padStart(2, '0');
    return {
      id: `preview-${i}`,
      title: `${item.titulo} (${CLINICA_AGENDA_STATUS_LABEL[item.key] || item.key})`,
      start: `${dia}T${startH}:${String(mm).padStart(2, '0')}:00`,
      end: `${dia}T${endH}:${String(mm).padStart(2, '0')}:00`,
      backgroundColor: colors.bg,
      borderColor: colors.border,
    };
  });
}

async function loadPulse(): Promise<LoadedMods> {
  const [
    { default: FullCalendar },
    { default: dayGridPlugin },
    { default: timeGridPlugin },
    { default: pulseTheme },
    { default: ptBr },
  ] = await Promise.all([
    import('@fullcalendar-v7/react'),
    import('@fullcalendar-v7/react/daygrid'),
    import('@fullcalendar-v7/react/timegrid'),
    import('@fullcalendar-v7/react/themes/pulse'),
    import('@fullcalendar-v7/react/locales/pt-br'),
  ]);
  await Promise.all([
    import('@fullcalendar-v7/react/skeleton.css'),
    import('@fullcalendar-v7/react/themes/pulse/theme.css'),
    import('@fullcalendar-v7/react/themes/pulse/palettes/purple.css'),
  ]);
  return {
    FullCalendar: FullCalendar as ComponentType<CalendarProps>,
    plugins: [dayGridPlugin, timeGridPlugin, pulseTheme],
    locale: ptBr,
  };
}

type Props = {
  statusColors?: AgendaStatusColorMap;
};

export function AgendaV7Preview({
  statusColors = CLINICA_AGENDA_STATUS_COLORS,
}: Props) {
  const [mods, setMods] = useState<LoadedMods | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);

  const events = useMemo(() => buildSampleEvents(statusColors), [statusColors]);

  useEffect(() => {
    let cancelado = false;
    setCarregando(true);
    setErro(null);

    loadPulse()
      .then((loaded) => {
        if (!cancelado) {
          setMods(loaded);
          setCarregando(false);
        }
      })
      .catch((e: unknown) => {
        if (!cancelado) {
          setErro(e instanceof Error ? e.message : 'Falha ao carregar o calendário Pulse.');
          setCarregando(false);
        }
      });

    return () => {
      cancelado = true;
    };
  }, []);

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-gray-900 dark:text-white">
          Agenda — visual Pulse (FullCalendar 7)
        </h2>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Este visual já está na visão <strong>Mês</strong> da agenda. Dia e Semana continuam com as
          colunas por profissional. Abaixo é só uma prévia rápida com Dia / Semana / Mês.
        </p>
      </div>

      <div className="rounded-xl border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 p-3 overflow-hidden">
        {carregando ? (
          <div className="flex items-center justify-center h-56 text-sm text-gray-500">
            Carregando prévia Pulse…
          </div>
        ) : erro ? (
          <div className="flex items-center justify-center h-56 text-sm text-red-600 dark:text-red-400 px-4 text-center">
            {erro}
          </div>
        ) : mods ? (
          <div className="agenda-v7-preview-root min-h-[280px]">
            <mods.FullCalendar
              plugins={mods.plugins}
              locale={mods.locale}
              initialView="timeGridDay"
              headerToolbar={{
                left: 'prev,next today',
                center: 'title',
                right: 'timeGridDay,timeGridWeek,dayGridMonth',
              }}
              height={520}
              weekends
              dayMaxEvents
              allDaySlot={false}
              slotMinTime="07:00:00"
              slotMaxTime="21:00:00"
              nowIndicator
              events={events}
            />
          </div>
        ) : null}
      </div>
    </section>
  );
}
