'use client';

import { useState, useRef } from 'react';
import { createPortal } from 'react-dom';
import { STATUS_AGENDAMENTO_CLINICA } from '@/constants/status';
import type { Agendamento } from './types';

export function MenuStatus({ 
  agendamento, 
  onStatusChange 
}: { 
  agendamento: Agendamento; 
  onStatusChange: (agendamento: Agendamento, novoStatus: string) => void;
}) {
  const [showMenu, setShowMenu] = useState(false);
  const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0 });
  const buttonRef = useRef<HTMLButtonElement>(null);
  const openTimeRef = useRef<number>(0);

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (!showMenu && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setMenuPosition({
        top: rect.bottom + 4,
        left: Math.max(8, Math.min(rect.right - 180, window.innerWidth - 192)),
      });
      openTimeRef.current = Date.now();
    }
    setShowMenu((prev) => !prev);
  };

  const handleClose = () => {
    // No mobile, o mesmo toque pode abrir e fechar; ignorar fechamento nos primeiros 200ms
    if (Date.now() - openTimeRef.current < 250) return;
    setShowMenu(false);
  };

  const handleOptionClick = (e: React.MouseEvent, value: string) => {
    e.stopPropagation();
    e.preventDefault();
    onStatusChange(agendamento, value);
    setShowMenu(false);
  };

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        type="button"
        onClick={handleToggle}
        className="p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition-colors touch-manipulation"
        title="Mudar status"
        aria-haspopup="true"
        aria-expanded={showMenu}
      >
        <svg className="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      
      {showMenu && typeof document !== 'undefined' && createPortal(
        <>
          <div 
            className="fixed inset-0 z-[9998]" 
            onClick={handleClose}
            aria-hidden="true"
          />
          <div 
            className="fixed z-[9999] bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 min-w-[180px] py-1"
            style={{
              top: menuPosition.top,
              left: menuPosition.left,
            }}
            role="menu"
          >
            {STATUS_AGENDAMENTO_CLINICA.map((option) => (
              <button
                key={option.value}
                type="button"
                role="menuitem"
                onClick={(e) => handleOptionClick(e, option.value)}
                className={`w-full text-left px-4 py-3 min-h-[44px] text-sm hover:bg-gray-100 dark:hover:bg-gray-700 first:rounded-t-lg last:rounded-b-lg flex items-center gap-2 touch-manipulation ${
                  option.value === agendamento.status ? 'font-bold bg-gray-50 dark:bg-gray-700/50' : ''
                }`}
              >
                <span style={{ color: option.color }}>●</span>
                {option.label}
              </button>
            ))}
          </div>
        </>,
        document.body
      )}
    </div>
  );
}
