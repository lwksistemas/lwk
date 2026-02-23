'use client';

import { useState, useRef } from 'react';
import { createPortal } from 'react-dom';
import type { Agendamento } from '@/types/dashboard';
import { STATUS_AGENDAMENTO_CLINICA } from '@/constants/status';

interface AgendamentoCardProps {
  agendamento: Agendamento;
  cor: string;
  onDelete?: (id: number) => void;
  onStatusChange?: (id: number, novoStatus: string) => void;
}

/** Card de agendamento com menu de status em portal (evita corte por overflow). Usado no dashboard Clínica de Estética. */
export function AgendamentoCard({ agendamento, cor, onDelete, onStatusChange }: AgendamentoCardProps) {
  const [showStatusMenu, setShowStatusMenu] = useState(false);
  const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0, openUp: false });
  const buttonRef = useRef<HTMLButtonElement>(null);
  const openTimeRef = useRef(0);

  const status = STATUS_AGENDAMENTO_CLINICA.find(s => s.value === agendamento.status)
    ?? { bg: 'bg-gray-100 dark:bg-gray-700', text: 'text-gray-800 dark:text-gray-300', label: agendamento.status };

  const handleDelete = () => {
    if (confirm(`Tem certeza que deseja excluir o agendamento de ${agendamento.cliente_nome}?`)) {
      onDelete?.(agendamento.id);
    }
  };

  const handleToggleMenu = () => {
    if (!showStatusMenu && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const menuHeight = 6 * 40 + 16;
      const spaceBelow = window.innerHeight - rect.bottom;
      const openUp = spaceBelow < menuHeight && rect.top > menuHeight;
      setMenuPosition({
        top: openUp ? rect.top - 8 : rect.bottom + 4,
        left: Math.max(8, Math.min(rect.right - 160, window.innerWidth - 168)),
        openUp,
      });
      openTimeRef.current = Date.now();
    }
    setShowStatusMenu((prev) => !prev);
  };

  const handleCloseMenu = () => {
    if (Date.now() - openTimeRef.current < 200) return;
    setShowStatusMenu(false);
  };

  const handleStatusChange = (novoStatus: string) => {
    onStatusChange?.(agendamento.id, novoStatus);
    setShowStatusMenu(false);
  };

  return (
    <div
      className="flex flex-col sm:flex-row sm:items-center justify-between p-3 sm:p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl
                    hover:bg-gray-100 dark:hover:bg-gray-700 transition-all duration-200
                    group card-hover gap-3 sm:gap-4 relative"
    >
      <div className="flex items-center space-x-3 sm:space-x-4 flex-1 min-w-0">
        <div
          className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl flex items-center justify-center text-white font-bold text-base sm:text-lg flex-shrink-0
                     transform group-hover:scale-105 transition-transform duration-200 shadow-md"
          style={{ backgroundColor: cor }}
        >
          {agendamento.cliente_nome.charAt(0)}
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-gray-900 dark:text-white text-sm sm:text-base truncate">{agendamento.cliente_nome}</p>
          <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 truncate">{agendamento.procedimento_nome}</p>
          <p className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 truncate">Prof: {agendamento.profissional_nome}</p>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
        <div className="sm:text-right">
          <p className="font-bold text-base sm:text-lg" style={{ color: cor }}>
            {agendamento.horario}
          </p>
          <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">{agendamento.data}</p>
        </div>

        <div className="relative">
          <button
            ref={buttonRef}
            type="button"
            onClick={handleToggleMenu}
            className={`text-[10px] sm:text-xs px-2 sm:px-3 py-1.5 min-h-[36px] rounded-full font-medium whitespace-nowrap ${status.bg} ${status.text} hover:opacity-80 transition-opacity`}
            title="Clique para alterar status"
            aria-haspopup="true"
            aria-expanded={showStatusMenu}
          >
            {status.label}
          </button>

          {showStatusMenu && typeof document !== 'undefined' && createPortal(
            <>
              <div
                className="fixed inset-0 z-[9998]"
                onClick={handleCloseMenu}
                aria-hidden="true"
              />
              <div
                className="fixed z-[9999] bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 min-w-[160px] py-1 max-h-[85vh] overflow-y-auto"
                style={{
                  top: menuPosition.openUp ? undefined : menuPosition.top,
                  bottom: menuPosition.openUp ? window.innerHeight - menuPosition.top : undefined,
                  left: menuPosition.left,
                }}
                role="menu"
              >
                {STATUS_AGENDAMENTO_CLINICA.map((item) => (
                  <button
                    key={item.value}
                    type="button"
                    role="menuitem"
                    onClick={() => handleStatusChange(item.value)}
                    className={`w-full text-left px-4 py-3 min-h-[44px] text-sm hover:bg-gray-100 dark:hover:bg-gray-700 first:rounded-t-lg last:rounded-b-lg flex items-center ${
                      item.value === agendamento.status ? 'font-bold bg-gray-50 dark:bg-gray-700/50' : ''
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </>,
            document.body
          )}
        </div>

        <button
          onClick={handleDelete}
          className="p-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors active:scale-95 flex-shrink-0"
          title="Excluir agendamento"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>
  );
}
