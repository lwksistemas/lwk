import type { LucideIcon } from 'lucide-react';
import {
  LayoutDashboard,
  CalendarDays,
  Users,
  Scissors,
  UserCog,
  DollarSign,
  Settings,
  Headphones,
} from 'lucide-react';

export const SALAO_PRIMARY = '#4A3042';
export const SALAO_ACCENT = '#C4A4B0';
export const SALAO_PAGE_BG = '#F7F0F3';

export interface SalaoNavItem {
  label: string;
  icon: LucideIcon;
  path: string;
}

export const SALAO_NAV_ITEMS: SalaoNavItem[] = [
  { label: 'Visão geral', icon: LayoutDashboard, path: 'dashboard' },
  { label: 'Agenda', icon: CalendarDays, path: 'cabeleireiro/agenda' },
  { label: 'Clientes', icon: Users, path: 'cabeleireiro/clientes' },
  { label: 'Serviços', icon: Scissors, path: 'cabeleireiro/servicos' },
  { label: 'Profissionais', icon: UserCog, path: 'cabeleireiro/profissionais' },
  { label: 'Financeiro', icon: DollarSign, path: 'cabeleireiro/financeiro' },
  { label: 'Configurações', icon: Settings, path: 'cabeleireiro/configuracoes' },
  { label: 'Suporte', icon: Headphones, path: 'suporte' },
];

export function getSalaoNavHref(slug: string, path: string): string {
  return `/loja/${slug}/${path}`;
}

export function isSalaoNavActive(pathname: string, slug: string, path: string): boolean {
  const href = getSalaoNavHref(slug, path).replace(/\/$/, '');
  const current = pathname.replace(/\/$/, '');
  if (path === 'dashboard') return current === href;
  return current === href || current.startsWith(`${href}/`);
}
