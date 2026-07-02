'use client';

import { Bell, X } from 'lucide-react';
import type { CrmSidebarNotificacao } from '@/hooks/crm-vendas/useCrmSidebar';

interface Props {
  open: boolean;
  onClose: () => void;
  notificacoes: CrmSidebarNotificacao[];
  loading: boolean;
  erro: string | null;
}

export function SidebarCrmNotificationsPanel({ open, onClose, notificacoes, loading, erro }: Props) {
  if (!open) return null;

  return (
    <div className="fixed top-4 right-4 z-50 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 p-4 max-w-sm animate-slide-in max-h-[80vh] overflow-hidden flex flex-col">
      <div className="flex items-start gap-3 shrink-0">
        <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 shrink-0">
          <Bell size={20} />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 dark:text-white text-sm">Notificações</h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            Sincronizado com o sistema (agendamentos, tarefas, lembretes, financeiro)
          </p>
        </div>
        <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 shrink-0">
          <X size={16} />
        </button>
      </div>
      <div className="mt-3 overflow-y-auto flex-1 min-h-0">
        {loading ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">Carregando...</p>
        ) : erro ? (
          <p className="text-sm text-amber-600 dark:text-amber-400">{erro}</p>
        ) : notificacoes.length === 0 ? (
          <p className="text-sm text-gray-600 dark:text-gray-400">Você não tem novas notificações no momento.</p>
        ) : (
          <ul className="space-y-2">
            {notificacoes.slice(0, 10).map((n) => (
              <li
                key={n.id}
                className={`text-sm p-2 rounded border-l-2 ${
                  n.read_at
                    ? 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400'
                    : 'border-[#0176d3] bg-blue-50/50 dark:bg-blue-900/10 text-gray-900 dark:text-white'
                }`}
              >
                <span className="font-medium">{n.titulo}</span>
                <p className="text-xs mt-0.5 line-clamp-2">{n.mensagem}</p>
              </li>
            ))}
            {notificacoes.length > 10 && (
              <li className="text-xs text-gray-500 dark:text-gray-400">+{notificacoes.length - 10} mais</li>
            )}
          </ul>
        )}
      </div>
    </div>
  );
}
