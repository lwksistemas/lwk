'use client';

import { useState } from 'react';
import { Bell, Smartphone } from 'lucide-react';
import { useNotifications } from '@/hooks/useNotifications';
import { registerPush } from '@/services/push';

interface NotificationBellProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  className?: string;
}

export function NotificationBell({ open, onOpenChange, className = '' }: NotificationBellProps) {
  const { notifications, unreadCount, read, loading } = useNotifications();
  const [pushEnabling, setPushEnabling] = useState(false);
  const [pushEnabled, setPushEnabled] = useState(false);

  async function handleEnablePush() {
    if (pushEnabling || pushEnabled) return;
    setPushEnabling(true);
    try {
      const ok = await registerPush();
      if (ok) setPushEnabled(true);
      else alert('Não foi possível ativar. Verifique se permitiu notificações no navegador.');
    } catch {
      alert('Erro ao ativar notificações no celular.');
    } finally {
      setPushEnabling(false);
    }
  }

  return (
    <div className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => onOpenChange(!open)}
        className="p-2 hover:bg-purple-50 dark:hover:bg-neutral-700 rounded-lg transition-colors relative"
        title="Notificações"
        aria-expanded={open}
        aria-haspopup="true"
      >
        <Bell className="w-5 h-5 text-gray-700 dark:text-gray-200" />
        {unreadCount > 0 && (
          <span
            className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-xs min-w-[1.25rem] h-5 px-1 flex items-center justify-center rounded-full font-medium"
            aria-label={`${unreadCount} não lidas`}
          >
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => onOpenChange(false)}
            aria-hidden="true"
          />
          <div
            className="absolute right-0 top-full mt-1 z-50 w-80 md:w-96 max-h-96 bg-white dark:bg-neutral-800 rounded-xl shadow-lg border dark:border-neutral-700 py-2 overflow-hidden flex flex-col"
            role="dialog"
            aria-label="Lista de notificações"
          >
            <div className="px-4 py-2 border-b dark:border-neutral-700 shrink-0">
              <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">
                Notificações
              </h3>
            </div>
            {typeof window !== 'undefined' && 'Notification' in window && !pushEnabled && (
              <div className="px-4 py-2 border-b dark:border-neutral-700 shrink-0">
                <button
                  type="button"
                  onClick={handleEnablePush}
                  disabled={pushEnabling}
                  className="flex items-center gap-2 w-full text-left text-sm text-purple-600 dark:text-purple-400 hover:underline disabled:opacity-50"
                >
                  <Smartphone className="w-4 h-4 shrink-0" />
                  {pushEnabling ? 'Ativando…' : 'Ativar notificações no celular'}
                </button>
              </div>
            )}
            <div className="overflow-y-auto flex-1 min-h-0">
              {loading && notifications.length === 0 ? (
                <p className="p-4 text-sm text-gray-500 dark:text-gray-400 text-center">
                  Carregando…
                </p>
              ) : notifications.length === 0 ? (
                <p className="p-4 text-sm text-gray-500 dark:text-gray-400 text-center">
                  Nenhuma notificação no momento.
                </p>
              ) : (
                <ul className="divide-y dark:divide-neutral-700">
                  {notifications.map((n) => (
                    <li key={n.id}>
                      <button
                        type="button"
                        onClick={() => {
                          if (n.status !== 'lido') read(n.id);
                        }}
                        className={`w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-neutral-700/50 transition-colors ${
                          n.status !== 'lido'
                            ? 'bg-purple-50/50 dark:bg-purple-900/10'
                            : 'bg-white dark:bg-neutral-800'
                        }`}
                      >
                        <p className="font-medium text-sm text-gray-900 dark:text-gray-100">
                          {n.titulo}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mt-0.5">
                          {n.mensagem}
                        </p>
                        {n.created_at && (
                          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                            {new Date(n.created_at).toLocaleString('pt-BR', {
                              day: '2-digit',
                              month: '2-digit',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </p>
                        )}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
