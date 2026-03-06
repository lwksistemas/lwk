'use client';

import { useCRMUIStore } from '@/store/crm-ui';
import { Menu, Search } from 'lucide-react';

interface HeaderCrmProps {
  title?: string;
  userName?: string;
}

export default function HeaderCrm({ title = 'CRM Vendas', userName = 'Admin' }: HeaderCrmProps) {
  const { toggle } = useCRMUIStore();

  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center px-4 sm:px-6 justify-between gap-4 shrink-0">
      <button
        type="button"
        onClick={toggle}
        className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-600 dark:text-gray-300"
        aria-label="Alternar menu"
      >
        <Menu size={22} />
      </button>

      <div className="flex-1 max-w-xl hidden sm:block">
        <div className="relative">
          <Search
            size={18}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
          />
          <input
            type="search"
            placeholder="Buscar leads, clientes..."
            className="w-full pl-10 pr-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700/50 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-primary focus:border-transparent text-sm"
          />
        </div>
      </div>

      <div className="font-semibold text-gray-700 dark:text-gray-200 truncate text-sm">
        {userName}
      </div>
    </header>
  );
}
