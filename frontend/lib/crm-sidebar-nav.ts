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
  /** Codename Django (ex.: view_lead) */
  permission?: string;
  /** Somente owner / vendedor admin */
  requiresAcessoTotal?: boolean;
}

export function buildCrmSidebarNavItems(base: string): CrmSidebarNavItem[] {
  return [
    { href: base, label: 'Home', icon: LayoutDashboard, exact: true },
    { href: `${base}/leads`, label: 'Leads', icon: Users, permission: 'view_lead' },
    { href: `${base}/pipeline`, label: 'Oportunidades', icon: DollarSign, permission: 'view_oportunidade' },
    { href: `${base}/customers`, label: 'Contas', icon: User, modulo: 'contas', permission: 'view_conta' },
    { href: `${base}/contatos`, label: 'Contatos', icon: User, modulo: 'contatos', permission: 'view_contato' },
    { href: `${base}/calendario`, label: 'Calendário', icon: Calendar, permission: 'view_atividade' },
    { href: `${base}/financeiro`, label: 'Financeiro', icon: Wallet, requiresAcessoTotal: true },
    { href: `${base}/relatorios`, label: 'Relatórios', icon: FileText, permission: 'view_oportunidade' },
    { href: `${base}/nfse`, label: 'NFS-e', icon: FileText, requiresAcessoTotal: true },
    { href: `${base}/propostas`, label: 'Criar Propostas', icon: ClipboardList, permission: 'view_proposta' },
    { href: `${base}/contratos`, label: 'Criar Contrato', icon: FileSignature, permission: 'view_contrato' },
    {
      href: `${base}/produtos-servicos`,
      label: 'Cadastrar Serviço e Produto',
      icon: Package,
      permission: 'view_produtoservico',
    },
  ];
}

export function isCrmSidebarNavActive(currentPath: string, item: CrmSidebarNavItem): boolean {
  if (item.exact) {
    return currentPath === item.href || currentPath === `${item.href}/`;
  }
  return currentPath.startsWith(item.href);
}

export function filterCrmSidebarNavItems(
  items: CrmSidebarNavItem[],
  opts: {
    moduloAtivo: (modulo: CrmSidebarModuloKey) => boolean;
    hasAcessoTotal: () => boolean;
    temPermissao: (codename: string | undefined) => boolean;
  },
): CrmSidebarNavItem[] {
  return items.filter((item) => {
    if (item.modulo && !opts.moduloAtivo(item.modulo)) return false;
    if (item.requiresAcessoTotal && !opts.hasAcessoTotal()) return false;
    if (item.permission && !opts.temPermissao(item.permission)) return false;
    return true;
  });
}
