'use client';

/**
 * Prévia isolada do FullCalendar 7 (não altera a agenda de produção, ainda em v6).
 * Duas opções de visual: Pulse e Breezy.
 */
import { useEffect, useMemo, useState, type ComponentType } from 'react';
import {
  CLINICA_AGENDA_STATUS_COLORS,
  CLINICA_AGENDA_STATUS_LABEL,
  type AgendaStatusColorMap,
} from '@/lib/clinica-beleza-constants';

export type AgendaV7Visual = 'pulse' | 'breezy';

const VISUAIS: Array<{
  id: AgendaV7Visual;
  nome: string;
  descricao: string;
}> = [
  {
    id: 'pulse',
    nome: 'Pulse',
    descricao: 'Visual limpo e minimalista (estilo Apple).',
  },
  {
    id: 'breezy',
    nome: 'Breezy',
    descricao: 'Visual moderno com cantos e contraste (estilo Tailwind).',
  },
];

type CalendarProps = {
  plugins: unknown[];
  initialView: string;
  locale?: unknown;
  headerToolbar: Record<string, string>;
  height: number | string;
  weekends: boolean;
  dayMaxEvents: boolean;
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

async function loadVisual(visual: AgendaV7Visual): Promise<LoadedMods> {
  const [{ default: FullCalendar }, { default: dayGridPlugin }, { default: ptBr }] =
    await Promise.all([
      import('@fullcalendar-v7/react'),
      import('@fullcalendar-v7/react/daygrid'),
      import('@fullcalendar-v7/react/locales/pt-br'),
    ]);
  await import('@fullcalendar-v7/react/skeleton.css');

  if (visual === 'pulse') {
    const { default: pulseTheme } = await import('@fullcalendar-v7/react/themes/pulse');
    await import('@fullcalendar-v7/react/themes/pulse/theme.css');
    await import('@fullcalendar-v7/react/themes/pulse/palettes/purple.css');
    return {
      FullCalendar: FullCalendar as ComponentType<CalendarProps>,
      plugins: [dayGridPlugin, pulseTheme],
      locale: ptBr,
    };
  }

  const { default: breezyTheme } = await import('@fullcalendar-v7/react/themes/breezy');
  await import('@fullcalendar-v7/react/themes/breezy/theme.css');
  await import('@fullcalendar-v7/react/themes/breezy/palettes/indigo.css');
  return {
    FullCalendar: FullCalendar as ComponentType<CalendarProps>,
    plugins: [dayGridPlugin, breezyTheme],
    locale: ptBr,
  };
}

type Props = {
  statusColors?: AgendaStatusColorMap;
  accentColor?: string;
};

export function AgendaV7Preview({
  statusColors = CLINICA_AGENDA_STATUS_COLORS,
  accentColor = '#8B3D52',
}: Props) {
  const [visual, setVisual] = useState<AgendaV7Visual>('pulse');
  const [mods, setMods] = useState<LoadedMods | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);

  const events = useMemo(() => buildSampleEvents(statusColors), [statusColors]);

  useEffect(() => {
    let cancelado = false;
    setCarregando(true);
    setErro(null);
    setMods(null);

    loadVisual(visual)
      .then((loaded) => {
        if (!cancelado) {
          setMods(loaded);
          setCarregando(false);
        }
      })
      .catch((e: unknown) => {
        if (!cancelado) {
          setErro(e instanceof Error ? e.message : 'Falha ao carregar o calendário v7.');
          setCarregando(false);
        }
      });

    return () => {
      cancelado = true;
    };
  }, [visual]);

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-gray-900 dark:text-white">
          Prévia da agenda (FullCalendar 7)
        </h2>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Teste dois visuais novos sem mudar a agenda das lojas (ainda usa a versão 6). Escolha uma
          opção e compare no calendário abaixo.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {VISUAIS.map((opcao) => {
          const selected = visual === opcao.id;
          return (
            <button
              key={opcao.id}
              type="button"
              onClick={() => setVisual(opcao.id)}
              className={`max-w-xs text-left px-3 py-2 rounded-lg border text-xs transition-colors ${
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

      <div className="rounded-xl border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 p-3 overflow-hidden">
        <p className="text-[11px] text-gray-500 dark:text-gray-400 mb-2">
          Visual ativo: <strong>{VISUAIS.find((v) => v.id === visual)?.nome}</strong> · eventos de
          exemplo usam as cores de status acima
        </p>
        {carregando ? (
          <div className="flex items-center justify-center h-56 text-sm text-gray-500">
            Carregando prévia v7…
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
              initialView="dayGridMonth"
              headerToolbar={{
                left: 'prev,next today',
                center: 'title',
                right: '',
              }}
              height="auto"
              weekends
              dayMaxEvents
              events={events}
            />
          </div>
        ) : null}
      </div>
    </section>
  );
}
