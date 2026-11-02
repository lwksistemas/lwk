declare module '@fullcalendar-v7/react' {
  import type { ComponentType } from 'react';
  const FullCalendar: ComponentType<Record<string, unknown>>;
  export default FullCalendar;
}

declare module '@fullcalendar-v7/react/daygrid' {
  const plugin: unknown;
  export default plugin;
}

declare module '@fullcalendar-v7/react/timegrid' {
  const plugin: unknown;
  export default plugin;
}

declare module '@fullcalendar-v7/react/themes/pulse' {
  const plugin: unknown;
  export default plugin;
}

declare module '@fullcalendar-v7/react/themes/breezy' {
  const plugin: unknown;
  export default plugin;
}

declare module '@fullcalendar-v7/react/locales/pt-br' {
  const locale: unknown;
  export default locale;
}

declare module '@fullcalendar-v7/react/skeleton.css';
declare module '@fullcalendar-v7/react/themes/pulse/theme.css';
declare module '@fullcalendar-v7/react/themes/pulse/palettes/purple.css';
declare module '@fullcalendar-v7/react/themes/breezy/theme.css';
declare module '@fullcalendar-v7/react/themes/breezy/palettes/indigo.css';
