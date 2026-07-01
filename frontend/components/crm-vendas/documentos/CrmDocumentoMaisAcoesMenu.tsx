'use client';

import type { ReactNode } from 'react';
import { MoreVertical } from 'lucide-react';

interface Props {
  itemId: number;
  aberto: boolean;
  onToggle: () => void;
  onClose: () => void;
  children: ReactNode;
  placement?: 'fixed' | 'absolute';
  menuClassName?: string;
}

function menuPositionStyle(itemId: number, placement: 'fixed' | 'absolute') {
  if (placement === 'absolute') return undefined;
  const btn = document.querySelector(`[data-crm-menu-id="${itemId}"]`);
  if (!btn) return { top: '0px', right: '24px' as const };
  const rect = btn.getBoundingClientRect();
  const spaceBelow = window.innerHeight - rect.bottom;
  const flip = spaceBelow < 280;
  return {
    top: flip ? `${rect.top - 4}px` : `${rect.bottom + 4}px`,
    right: '24px',
    transform: flip ? 'translateY(-100%)' : 'none',
  };
}

export default function CrmDocumentoMaisAcoesMenu({
  itemId,
  aberto,
  onToggle,
  onClose,
  children,
  placement = 'absolute',
  menuClassName = 'w-56',
}: Props) {
  return (
    <div className="relative">
      <button
        type="button"
        onClick={onToggle}
        data-crm-menu-id={itemId}
        className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300"
        title="Mais ações"
      >
        <MoreVertical size={16} />
      </button>
      {aberto && (
        <>
          <div className="fixed inset-0 z-40" onClick={onClose} />
          <div
            className={`${placement === 'fixed' ? 'fixed' : 'absolute right-0 top-full mt-1'} z-50 ${menuClassName} bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 py-1 max-h-64 overflow-y-auto`}
            style={placement === 'fixed' ? menuPositionStyle(itemId, placement) : undefined}
          >
            {children}
          </div>
        </>
      )}
    </div>
  );
}
