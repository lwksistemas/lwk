import type { LucideIcon } from 'lucide-react';
import {
  LayoutDashboard,
  CalendarDays,
  Users,
  UserCog,
  ClipboardList,
  Activity,
  DollarSign,
  Settings,
} from 'lucide-react';

export interface ClinicaBelezaNavItem {
  label: string;
  icon: LucideIcon;
  /** Segmento após `/loja/[slug]/` */
  path: string;
}

export const CLINICA_BELEZA_NAV_ITEMS: ClinicaBelezaNavItem[] = [
  { label: 'Dashboard', icon: LayoutDashboard, path: 'dashboard' },
  { label: 'Agenda', icon: CalendarDays, path: 'agenda' },
  { label: 'Pacientes', icon: Users, path: 'clinica-beleza/pacientes' },
  { label: 'Profissionais', icon: UserCog, path: 'clinica-beleza/profissionais' },
  { label: 'Procedimentos', icon: ClipboardList, path: 'clinica-beleza/procedimentos' },
  { label: 'Estoque', icon: Activity, path: 'clinica-beleza/estoque' },
  { label: 'Financeiro', icon: DollarSign, path: 'clinica-beleza/financeiro' },
  { label: 'Configurações', icon: Settings, path: 'clinica-beleza/configuracoes' },
];

export function getClinicaBelezaNavHref(slug: string, path: string): string {
  return `/loja/${slug}/${path}`;
}

export function isClinicaBelezaNavActive(pathname: string, slug: string, path: string): boolean {
  const href = getClinicaBelezaNavHref(slug, path);
  if (path === 'dashboard') {
    return pathname === href || pathname === `${href}/`;
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}
