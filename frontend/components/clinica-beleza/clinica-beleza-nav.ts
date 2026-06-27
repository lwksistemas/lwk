import type { LucideIcon } from 'lucide-react';
import {
  LayoutDashboard,
  CalendarDays,
  Users,
  Stethoscope,
  ListChecks,
  ClipboardList,
  DollarSign,
  Package,
  Megaphone,
  BarChart3,
  Settings,
  Headphones,
  FileText,
  Handshake,
  Layers,
} from 'lucide-react';

/** Cor principal do app (mockup Beleza & Vitalidade) */
export const CLINICA_BELEZA_PRIMARY = '#8B3D52';
export const CLINICA_BELEZA_PRIMARY_LIGHT = '#F5E6EA';

export interface ClinicaBelezaNavChild {
  label: string;
  /** Segmento após `/loja/[slug]/` (pode incluir query) */
  path: string;
}

export interface ClinicaBelezaNavItem {
  label: string;
  icon: LucideIcon;
  /** Link direto — omitir se tiver `children` */
  path?: string;
  children?: ClinicaBelezaNavChild[];
}

export const CLINICA_BELEZA_NAV_ITEMS: ClinicaBelezaNavItem[] = [
  { label: 'Dashboard', icon: LayoutDashboard, path: 'dashboard' },
  { label: 'Agenda', icon: CalendarDays, path: 'agenda' },
  { label: 'Clientes', icon: Users, path: 'clinica-beleza/pacientes' },
  { label: 'Convênios', icon: Handshake, path: 'clinica-beleza/convenios' },
  { label: 'Consultas', icon: Stethoscope, path: 'clinica-beleza/consultas' },
  { label: 'Procedimentos', icon: ListChecks, path: 'clinica-beleza/procedimentos' },
  { label: 'Protocolos', icon: ClipboardList, path: 'clinica-beleza/protocolos' },
  {
    label: 'Módulos',
    icon: Layers,
    children: [
      { label: 'Estética', path: 'clinica-beleza/estetica/procedimentos' },
      { label: 'Soroterapia', path: 'clinica-beleza/soroterapia/procedimentos' },
    ],
  },
  { label: 'Templates', icon: FileText, path: 'clinica-beleza/templates' },
  { label: 'Estoque', icon: Package, path: 'clinica-beleza/estoque' },
  { label: 'Financeiro', icon: DollarSign, path: 'clinica-beleza/financeiro' },
  { label: 'Marketing', icon: Megaphone, path: 'clinica-beleza/campanhas' },
  { label: 'Relatórios', icon: BarChart3, path: 'relatorios' },
  { label: 'Configurações', icon: Settings, path: 'clinica-beleza/configuracoes' },
  { label: 'Suporte', icon: Headphones, path: 'suporte' },
];

export function getClinicaBelezaNavHref(slug: string, path: string): string {
  const [pathname, search] = path.split('?');
  const base = `/loja/${slug}/${pathname}`;
  return search ? `${base}?${search}` : base;
}

function normalizePath(p: string): string {
  return p.replace(/\/$/, '').split('?')[0];
}

/** Rotas de módulo que redirecionam para a primeira tela útil */
const MODULE_REDIRECT_PREFIXES = [
  'clinica-beleza/soroterapia',
  'clinica-beleza/estetica',
] as const;

export function isClinicaBelezaNavActive(pathname: string, slug: string, path: string): boolean {
  const pathOnly = normalizePath(getClinicaBelezaNavHref(slug, path));
  const current = normalizePath(pathname);
  if (path === 'dashboard') return current === pathOnly;
  if (MODULE_REDIRECT_PREFIXES.some((prefix) => path.startsWith(prefix))) {
    return current === pathOnly || current.startsWith(`${pathOnly}/`);
  }
  return current === pathOnly || current.startsWith(`${pathOnly}/`);
}

export function isClinicaBelezaNavGroupActive(pathname: string, slug: string, item: ClinicaBelezaNavItem): boolean {
  if (item.path && isClinicaBelezaNavActive(pathname, slug, item.path)) return true;
  return item.children?.some((c) => isClinicaBelezaNavActive(pathname, slug, c.path)) ?? false;
}
