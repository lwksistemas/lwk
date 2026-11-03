'use client';

/**
 * Escolha do visual da agenda (FullCalendar 7). Prévia oculta até o admin abrir.
 * Usa amostras fictícias — não altera agendamentos reais.
 */
import { useEffect, useMemo, useState, type ComponentType, type CSSProperties } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import {
  CLINICA_AGENDA_BLOQUEIO_COLORS,
  CLINICA_AGENDA_STATUS_COLORS,
  type AgendaStatusColorMap,
} from '@/lib/clinica-beleza-constants';
import {
  AGENDA_VISUAIS,
  AGENDA_VISUAL_DEFAULT,
  agendaVisualStyleVars,
  loadAgendaVisualTheme,
  normalizeAgendaVisual,
  type AgendaVisualId,
} from '@/lib/clinica-agenda-visual';
import { makeAgendaFcEventContent } from '@/hooks/clinica-beleza/agenda-data/agenda-fc-event-content';

type CalendarProps = Record<string, unknown>;

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

  const cor = (key: string) =>
    statusColors[key] || CLINICA_AGENDA_STATUS_COLORS[key] || { bg: '#a855f7', border: '#9333ea' };

  const ev = (
    id: string,
    start: string,
    end: string,
    title: string,
    extra: Record<string, unknown>,
  ) => {
    const status = String(extra.status || 'SCHEDULED');
    const colors = extra.isBloqueio
      ? CLINICA_AGENDA_BLOQUEIO_COLORS
      : cor(status);
    return {
      id,
      title,
      start: `${dia}T${start}`,
      end: `${dia}T${end}`,
      color: colors.bg,
      contrastColor: '#fff',
      backgroundColor: colors.bg,
      borderColor: colors.border,
      extendedProps: extra,
    };
  };

  return [
    ev('p-15', '08:00:00', '08:15:00', 'ANA SILVA', {
      status: 'SCHEDULED',
      patient_name: 'Ana Silva',
      professional: 1,
      professional_name: 'Dra. Marina Garcia',
      procedure_name: 'Avaliação',
    }),
    ev('p-30', '09:00:00', '09:30:00', 'BRUNO COSTA', {
      status: 'CLIENT_CONFIRMED',
      patient_name: 'Bruno Costa',
      professional: 1,
      professional_name: 'Dra. Marina Garcia',
      procedure_name: 'Protocolo',
    }),
    // Simultâneos de profissionais diferentes (não conflito)
    ev('p-sim-a', '10:00:00', '11:00:00', 'CARLA MENDES', {
      status: 'CONFIRMED',
      patient_name: 'Carla Mendes',
      professional: 1,
      professional_name: 'Dra. Marina Garcia',
      procedure_name: 'Laser',
    }),
    ev('p-sim-b', '10:00:00', '10:45:00', 'DIEGO ALVES', {
      status: 'PHONE_CONFIRMED',
      patient_name: 'Diego Alves',
      professional: 2,
      professional_name: 'Bruna Tucci',
      procedure_name: 'Limpeza',
    }),
    // Conflito real (mesmo profissional)
    ev('p-cf-1', '14:00:00', '15:00:00', 'ELENA ROCHA', {
      status: 'SCHEDULED',
      patient_name: 'Elena Rocha',
      professional: 2,
      professional_name: 'Bruna Tucci',
      procedure_name: 'Peeling',
    }),
    ev('p-cf-2', '14:30:00', '15:30:00', 'FÁBIO NUNES', {
      status: 'IN_PROGRESS',
      patient_name: 'Fábio Nunes',
      professional: 2,
      professional_name: 'Bruna Tucci',
      procedure_name: 'Microagulhamento',
    }),
    ev('p-done', '16:00:00', '17:00:00', 'GISELE PRADO', {
      status: 'COMPLETED',
      patient_name: 'Gisele Prado',
      professional: 1,
      professional_name: 'Dra. Marina Garcia',
      procedure_name: 'Retorno',
    }),
    ev('p-bloq', '12:00:00', '13:00:00', 'Almoço / bloqueio', {
      isBloqueio: true,
      motivo: 'Intervalo',
      professional: 1,
      professional_name: 'Dra. Marina Garcia',
    }),
  ];
}

async function loadPreview(visual: AgendaVisualId): Promise<LoadedMods> {
  const [{ default: FullCalendar }, { default: dayGridPlugin }, { default: timeGridPlugin }, { default: ptBr }] =
    await Promise.all([
      import('@fullcalendar-v7/react'),
      import('@fullcalendar-v7/react/daygrid'),
      import('@fullcalendar-v7/react/timegrid'),
      import('@fullcalendar-v7/react/locales/pt-br'),
    ]);
  await import('@fullcalendar-v7/react/skeleton.css');
  const theme = await loadAgendaVisualTheme(visual);
  return {
    FullCalendar: FullCalendar as ComponentType<CalendarProps>,
    plugins: [dayGridPlugin, timeGridPlugin, theme],
    locale: ptBr,
  };
}

type Props = {
  statusColors?: AgendaStatusColorMap;
  accentColor?: string;
  value?: string | null;
  onChange?: (visual: AgendaVisualId) => void;
};

export function AgendaV7Preview({
  statusColors = CLINICA_AGENDA_STATUS_COLORS,
  accentColor = '#8B3D52',
  value,
  onChange,
}: Props) {
  const [visual, setVisual] = useState<AgendaVisualId>(() =>
    normalizeAgendaVisual(value ?? AGENDA_VISUAL_DEFAULT),
  );
  const [mostrarPrevia, setMostrarPrevia] = useState(false);
  const [mods, setMods] = useState<LoadedMods | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  const events = useMemo(() => buildSampleEvents(statusColors), [statusColors]);
  const eventContent = useMemo(
    () => makeAgendaFcEventContent({ showProfessional: true }),
    [],
  );

  useEffect(() => {
    setVisual(normalizeAgendaVisual(value ?? AGENDA_VISUAL_DEFAULT));
  }, [value]);

  useEffect(() => {
    if (!mostrarPrevia) {
      setMods(null);
      return;
    }
    let cancelado = false;
    setCarregando(true);
    setErro(null);
    setMods(null);

    loadPreview(visual)
      .then((loaded) => {
        if (!cancelado) {
          setMods(loaded);
          setCarregando(false);
        }
      })
      .catch((e: unknown) => {
        if (!cancelado) {
          setErro(e instanceof Error ? e.message : 'Falha ao carregar a prévia.');
          setCarregando(false);
        }
      });

    return () => {
      cancelado = true;
    };
  }, [mostrarPrevia, visual]);

  const escolher = (id: AgendaVisualId) => {
    setVisual(id);
    onChange?.(id);
  };

  const ativo = AGENDA_VISUAIS.find((v) => v.id === visual);

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-gray-900 dark:text-white">
          Visual da agenda
        </h2>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          O tema vale para Dia, Semana e Mês. Com todos os profissionais no Dia, a grade por
          coluna continua disponível. A prévia usa dados fictícios e não altera a agenda real.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {AGENDA_VISUAIS.map((opcao) => {
          const selected = visual === opcao.id;
          return (
            <button
              key={opcao.id}
              type="button"
              onClick={() => escolher(opcao.id)}
              className={`max-w-[11rem] text-left px-3 py-2 rounded-lg border text-xs transition-colors ${
                selected
                  ? 'border-current'
                  : 'border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300'
              }`}
              style={
                selected
                  ? {
                      borderColor: accentColor,
                      backgroundColor: `${accentColor}15`,
                      color: accentColor,
                    }
                  : undefined
              }
            >
              <span className="block font-semibold">{opcao.nome}</span>
              <span className="block mt-0.5 opacity-80 font-normal text-[11px] leading-snug">
                {opcao.descricao}
              </span>
            </button>
          );
        })}
      </div>

      <p className="text-[11px] text-gray-500 dark:text-gray-400">
        Em uso: <strong>{ativo?.nome || 'Pulse'}</strong>
        {mostrarPrevia ? null : ' · prévia oculta'}
      </p>

      <button
        type="button"
        onClick={() => setMostrarPrevia((v) => !v)}
        className="inline-flex items-center gap-1.5 text-xs font-medium hover:underline"
        style={{ color: accentColor }}
      >
        {mostrarPrevia ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        {mostrarPrevia ? 'Ocultar prévia' : 'Ver prévia do calendário'}
      </button>

      {mostrarPrevia ? (
        <div className="rounded-xl border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 p-3 overflow-hidden">
          {carregando ? (
            <div className="flex items-center justify-center h-56 text-sm text-gray-500">
              Carregando prévia…
            </div>
          ) : erro ? (
            <div className="flex items-center justify-center h-56 text-sm text-red-600 dark:text-red-400 px-4 text-center">
              {erro}
            </div>
          ) : mods ? (
            <div
              className="agenda-v7-preview-root agenda-v7-root min-h-[280px]"
              data-agenda-visual={visual}
              style={agendaVisualStyleVars(visual) as CSSProperties}
            >
              <mods.FullCalendar
                key={visual}
                plugins={mods.plugins}
                locale={mods.locale}
                initialView="timeGridWeek"
                headerToolbar={{
                  left: 'prev,next today',
                  center: 'title',
                  right: 'timeGridDay,timeGridWeek,dayGridMonth',
                }}
                buttonText={{
                  today: 'Hoje',
                  month: 'Mês',
                  week: 'Semana',
                  day: 'Dia',
                }}
                height={520}
                weekends
                dayMaxEvents={3}
                moreLinkClick="popover"
                eventMinHeight={28}
                eventMaxStack={3}
                eventContent={eventContent}
                allDaySlot={false}
                slotMinTime="07:00:00"
                slotMaxTime="21:00:00"
                nowIndicator
                events={events}
                editable={false}
                selectable={false}
              />
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
