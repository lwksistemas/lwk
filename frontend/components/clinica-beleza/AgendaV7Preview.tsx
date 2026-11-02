'use client';

/**
 * Escolha do visual da agenda (FullCalendar 7). Prévia oculta até o admin abrir.
 */
import { useEffect, useMemo, useState, type ComponentType } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import {
  CLINICA_AGENDA_STATUS_COLORS,
  CLINICA_AGENDA_STATUS_LABEL,
  type AgendaStatusColorMap,
} from '@/lib/clinica-beleza-constants';
import {
  AGENDA_VISUAIS,
  AGENDA_VISUAL_DEFAULT,
  loadAgendaVisualTheme,
  normalizeAgendaVisual,
  type AgendaVisualId,
} from '@/lib/clinica-agenda-visual';

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
          Vale para Dia, Semana e Mês. Dia e Semana mantêm as colunas por profissional, com o visual
          escolhido. A prévia do calendário fica oculta até você abrir.
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
            <div className="agenda-v7-preview-root min-h-[280px]">
              <mods.FullCalendar
                key={visual}
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
      ) : null}
    </section>
  );
}
