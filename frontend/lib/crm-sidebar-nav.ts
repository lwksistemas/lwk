import type { LucideIcon } from 'lucide-react';
import {
  Calendar,
  ClipboardList,
  DollarSign,
  FileSignature,
  FileText,
  LayoutDashboard,
  Package,
  User,
  Users,
  Wallet,
} from 'lucide-react';

export type CrmSidebarModuloKey = 'contas' | 'contatos';

export interface CrmSidebarNavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  exact?: boolean;
  modulo?: CrmSidebarModuloKey;
}

export function buildCrmSidebarNavItems(base: string): CrmSidebarNavItem[] {
  return [
    { href: base, label: 'Home', icon: LayoutDashboard, exact: true },
    { href: `${base}/leads`, label: 'Leads', icon: Users },
    { href: `${base}/pipeline`, label: 'Oportunidades', icon: DollarSign },
    { href: `${base}/customers`, label: 'Contas', icon: User, modulo: 'contas' },
    { href: `${base}/contatos`, label: 'Contatos', icon: User, modulo: 'contatos' },
    { href: `${base}/calendario`, label: 'Calendário', icon: Calendar },
    { href: `${base}/financeiro`, label: 'Financeiro', icon: Wallet },
    { href: `${base}/relatorios`, label: 'Relatórios', icon: FileText },
    { href: `${base}/nfse`, label: 'NFS-e', icon: FileText },
    { href: `${base}/propostas`, label: 'Criar Propostas', icon: ClipboardList },
    { href: `${base}/contratos`, label: 'Criar Contrato', icon: FileSignature },
    { href: `${base}/produtos-servicos`, label: 'Cadastrar Serviço e Produto', icon: Package },
  ];
}

export function isCrmSidebarNavActive(currentPath: string, item: CrmSidebarNavItem): boolean {
  if (item.exact) {
    return currentPath === item.href || currentPath === `${item.href}/`;
  }
  return currentPath.startsWith(item.href);
}
