'use client';

import Link from 'next/link';
import type { CrmSidebarNavItem } from '@/lib/crm-sidebar-nav';
import { isCrmSidebarNavActive } from '@/lib/crm-sidebar-nav';

interface Props {
  item: CrmSidebarNavItem;
  currentPath: string;
  collapsed: boolean;
}

export function SidebarCrmNavLink({ item, currentPath, collapsed }: Props) {
  const active = isCrmSidebarNavActive(currentPath, item);
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      className={`flex items-center gap-3 px-3 py-2 rounded text-sm font-medium transition-all ${
        active
          ? 'bg-[#0176d3] text-white shadow-sm'
          : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-[#0d1f3c]'
      }`}
      title={collapsed ? item.label : undefined}
    >
      <Icon size={18} className="shrink-0" />
      {!collapsed && <span>{item.label}</span>}
    </Link>
  );
}
