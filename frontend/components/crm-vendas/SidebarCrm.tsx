'use client';

import Link from 'next/link';
import { useParams, usePathname, useRouter } from 'next/navigation';
import { useCRMUIStore } from '@/store/crm-ui';
import {
  LayoutDashboard,
  Users,
  DollarSign,
  User,
  Menu,
  LogOut,
  ArrowLeft,
} from 'lucide-react';

interface SidebarCrmProps {
  lojaNome?: string;
  onLogout?: () => void;
}

export default function SidebarCrm({ lojaNome, onLogout }: SidebarCrmProps) {
  const { collapsed, toggle } = useCRMUIStore();
  const router = useRouter();
  const params = useParams();
  const pathname = usePathname();
  const slug = (params?.slug as string) || (typeof pathname === 'string' && pathname.startsWith('/loja/') ? pathname.split('/')[2] : '') || '';
  const base = `/loja/${slug}/crm-vendas`;

  return (
    <aside
      className={`bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transition-all duration-200 h-full flex flex-col shrink-0 ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      <div className="p-4 flex items-center justify-between border-b border-gray-200 dark:border-gray-800 min-h-[4rem]">
        {!collapsed && (
          <span className="font-bold text-xl text-gray-900 dark:text-white truncate" title={lojaNome}>
            {lojaNome || 'LWK CRM'}
          </span>
        )}
        <button
          type="button"
          onClick={toggle}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-gray-600 dark:text-gray-300"
          aria-label={collapsed ? 'Expandir menu' : 'Recolher menu'}
        >
          <Menu size={20} />
        </button>
      </div>

      <nav className="space-y-1 p-2 flex-1 overflow-y-auto">
        <Link href={base} className="crm-menu-item">
          <LayoutDashboard size={20} className="shrink-0" />
          {!collapsed && <span>Dashboard</span>}
        </Link>
        <Link href={`${base}/leads`} className="crm-menu-item">
          <Users size={20} className="shrink-0" />
          {!collapsed && <span>Leads</span>}
        </Link>
        <Link href={`${base}/pipeline`} className="crm-menu-item">
          <DollarSign size={20} className="shrink-0" />
          {!collapsed && <span>Vendas</span>}
        </Link>
        <Link href={`${base}/customers`} className="crm-menu-item">
          <User size={20} className="shrink-0" />
          {!collapsed && <span>Clientes</span>}
        </Link>
      </nav>

      <div className="p-2 border-t border-gray-200 dark:border-gray-800 space-y-1">
        <button
          type="button"
          onClick={() => slug && router.push(`/loja/${slug}/dashboard`)}
          className="crm-menu-item w-full text-left text-gray-500 dark:text-gray-400"
          disabled={!slug}
          title={slug ? 'Voltar ao dashboard da loja' : 'Carregando...'}
        >
          <ArrowLeft size={20} className="shrink-0" />
          {!collapsed && <span>Voltar à loja</span>}
        </button>
        {onLogout && (
          <button
            type="button"
            onClick={onLogout}
            className="crm-menu-item w-full text-left text-gray-500 dark:text-gray-400"
          >
            <LogOut size={20} className="shrink-0" />
            {!collapsed && <span>Sair</span>}
          </button>
        )}
      </div>
    </aside>
  );
}
