/** Visuais da agenda (Dia, Semana e Mês). Mês usa FullCalendar 7; Dia/Semana usam a grade própria com os mesmos tokens. */

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

/** Tokens CSS da grade Dia/Semana (espelham as paletas FC7). */
export type AgendaVisualTokens = {
  accent: string;
  accentFg: string;
  radius: string;
  cardRadius: string;
  cardShadow: string;
  border: string;
  todayBg: string;
  hoverBg: string;
  focusText: string;
  now: string;
};

export const AGENDA_VISUAL_TOKENS: Record<AgendaVisualId, AgendaVisualTokens> = {
  pulse: {
    accent: '#ad46ff',
    accentFg: '#ffffff',
    radius: '12px',
    cardRadius: '12px',
    cardShadow: '0 1px 3px rgb(0 0 0 / 0.08), 0 1px 2px rgb(0 0 0 / 0.06)',
    border: '#e5e7eb',
    todayBg: 'rgb(236 72 153 / 0.08)',
    hoverBg: 'rgb(173 70 255 / 0.08)',
    focusText: '#7e22ce',
    now: '#ef4444',
  },
  breezy: {
    accent: '#4f46e5',
    accentFg: '#ffffff',
    radius: '8px',
    cardRadius: '8px',
    cardShadow: '0 1px 2px rgb(0 0 0 / 0.06)',
    border: '#e5e7eb',
    todayBg: 'rgb(56 189 248 / 0.1)',
    hoverBg: 'rgb(79 70 229 / 0.08)',
    focusText: '#4338ca',
    now: '#f43f5e',
  },
  monarch: {
    accent: '#6750a4',
    accentFg: '#ffffff',
    radius: '16px',
    cardRadius: '16px',
    cardShadow: '0 2px 6px rgb(103 80 164 / 0.16)',
    border: '#e7e0ec',
    todayBg: 'rgb(234 221 255 / 0.55)',
    hoverBg: 'rgb(234 221 255 / 0.4)',
    focusText: '#4f378b',
    now: '#b3261e',
  },
  forma: {
    accent: '#742774',
    accentFg: '#ffffff',
    radius: '4px',
    cardRadius: '4px',
    cardShadow: '0 1px 2px rgb(0 0 0 / 0.1)',
    border: '#e0e0e0',
    todayBg: 'rgb(116 39 116 / 0.08)',
    hoverBg: 'rgb(116 39 116 / 0.06)',
    focusText: '#5d1f5d',
    now: '#ef4444',
  },
  classic: {
    accent: '#3788d8',
    accentFg: '#ffffff',
    radius: '3px',
    cardRadius: '3px',
    cardShadow: 'none',
    border: '#dddddd',
    todayBg: 'rgb(250 204 21 / 0.15)',
    hoverBg: 'rgb(55 136 216 / 0.08)',
    focusText: '#1d4ed8',
    now: '#ef4444',
  },
};

export function agendaVisualStyleVars(visual: AgendaVisualId): Record<string, string> {
  const t = AGENDA_VISUAL_TOKENS[visual] || AGENDA_VISUAL_TOKENS[AGENDA_VISUAL_DEFAULT];
  return {
    '--agenda-accent': t.accent,
    '--agenda-accent-fg': t.accentFg,
    '--agenda-radius': t.radius,
    '--agenda-card-radius': t.cardRadius,
    '--agenda-card-shadow': t.cardShadow,
    '--agenda-border': t.border,
    '--agenda-today-bg': t.todayBg,
    '--agenda-hover-bg': t.hoverBg,
    '--agenda-focus-text': t.focusText,
    '--agenda-now': t.now,
  };
}

/** Carrega plugin + CSS do tema FC7 escolhido (Dia/Semana/Mês). */
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
