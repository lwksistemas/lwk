'use client';

import type { LucideIcon } from 'lucide-react';
import { Plus } from 'lucide-react';
import type { ReactNode } from 'react';
import { SALAO_PRIMARY } from './salao-nav';

type Props = {
  title: string;
  subtitle?: string;
  icon?: LucideIcon;
  onNew?: () => void;
  newLabel?: string;
  primary?: string;
  children?: ReactNode;
};

export function SalaoPageHeader({
  title,
  subtitle,
  icon: Icon,
  onNew,
  newLabel = 'Novo',
  primary = SALAO_PRIMARY,
  children,
}: Props) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-4 md:px-6 py-4 border-b border-[#E8D5DC] bg-white/80">
      <div className="flex items-center gap-3 min-w-0">
        {Icon && (
          <div className="p-2 rounded-lg text-white shrink-0" style={{ backgroundColor: primary }}>
            <Icon size={20} />
          </div>
        )}
        <div className="min-w-0">
          <h1 className="text-lg font-semibold text-gray-900 truncate">{title}</h1>
          {subtitle && <p className="text-xs text-gray-500 truncate">{subtitle}</p>}
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {children}
        {onNew && (
          <button
            type="button"
            onClick={onNew}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-white"
            style={{ backgroundColor: primary }}
          >
            <Plus size={16} />
            {newLabel}
          </button>
        )}
      </div>
    </div>
  );
}
