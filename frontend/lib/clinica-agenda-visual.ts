/** Visuais FullCalendar 7 da agenda (visão Mês). */

export const AGENDA_VISUAIS = [
  {
    id: 'pulse',
    nome: 'Pulse',
    descricao: 'Limpo e minimalista (estilo Apple).',
  },
  {
    id: 'breezy',
    nome: 'Breezy',
    descricao: 'Moderno, com contraste (estilo Tailwind).',
  },
  {
    id: 'monarch',
    nome: 'Monarch',
    descricao: 'Material Design 3, mais marcante.',
  },
  {
    id: 'forma',
    nome: 'Forma',
    descricao: 'Fluent UI, botões e cantos suaves.',
  },
  {
    id: 'classic',
    nome: 'Clássico',
    descricao: 'Visual próximo ao calendário antigo.',
  },
] as const;

export type AgendaVisualId = (typeof AGENDA_VISUAIS)[number]['id'];

export const AGENDA_VISUAL_DEFAULT: AgendaVisualId = 'pulse';

const IDS = new Set<string>(AGENDA_VISUAIS.map((v) => v.id));

export function normalizeAgendaVisual(raw: unknown): AgendaVisualId {
  if (typeof raw === 'string' && IDS.has(raw)) return raw as AgendaVisualId;
  return AGENDA_VISUAL_DEFAULT;
}

/** Carrega plugin + CSS do tema FC7 escolhido. */
export async function loadAgendaVisualTheme(visual: AgendaVisualId): Promise<unknown> {
  switch (visual) {
    case 'breezy': {
      const { default: theme } = await import('@fullcalendar-v7/react/themes/breezy');
      await import('@fullcalendar-v7/react/themes/breezy/theme.css');
      await import('@fullcalendar-v7/react/themes/breezy/palettes/indigo.css');
      return theme;
    }
    case 'monarch': {
      const { default: theme } = await import('@fullcalendar-v7/react/themes/monarch');
      await import('@fullcalendar-v7/react/themes/monarch/theme.css');
      await import('@fullcalendar-v7/react/themes/monarch/palettes/purple.css');
      return theme;
    }
    case 'forma': {
      const { default: theme } = await import('@fullcalendar-v7/react/themes/forma');
      await import('@fullcalendar-v7/react/themes/forma/theme.css');
      await import('@fullcalendar-v7/react/themes/forma/palettes/purple.css');
      return theme;
    }
    case 'classic': {
      const { default: theme } = await import('@fullcalendar-v7/react/themes/classic');
      await import('@fullcalendar-v7/react/themes/classic/theme.css');
      await import('@fullcalendar-v7/react/themes/classic/palette.css');
      return theme;
    }
    case 'pulse':
    default: {
      const { default: theme } = await import('@fullcalendar-v7/react/themes/pulse');
      await import('@fullcalendar-v7/react/themes/pulse/theme.css');
      await import('@fullcalendar-v7/react/themes/pulse/palettes/purple.css');
      return theme;
    }
  }
}
