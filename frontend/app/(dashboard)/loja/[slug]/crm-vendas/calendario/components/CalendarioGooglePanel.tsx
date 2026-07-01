'use client';

interface CalendarioGooglePanelProps {
  googleStatus: { connected: boolean; email: string | null };
  googleLoading: boolean;
  syncError: string | null;
  googleSyncResult: { pushed: number; pulled: number } | null;
  googleErrorParam: boolean;
  onConnect: () => void;
  onSync: () => void;
  onDisconnect: () => void;
}

export function CalendarioGooglePanel({
  googleStatus,
  googleLoading,
  onConnect,
  onSync,
  onDisconnect,
}: Omit<CalendarioGooglePanelProps, 'syncError' | 'googleSyncResult' | 'googleErrorParam'>) {
  return (
    <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 shrink-0">
        {googleStatus.connected ? (
          <>
            <span
              className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 truncate max-w-[120px] sm:max-w-none"
              title={googleStatus.email ?? undefined}
            >
              {googleStatus.email ? `Google: ${googleStatus.email}` : 'Google conectado'}
            </span>
            <button
              type="button"
              onClick={onSync}
              disabled={googleLoading}
              className="px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm font-medium bg-[#0176d3] hover:bg-[#0159a8] text-white disabled:opacity-50 touch-manipulation"
            >
              {googleLoading ? '...' : 'Sincronizar'}
            </button>
            <button
              type="button"
              onClick={onDisconnect}
              disabled={googleLoading}
              className="px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm font-medium border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 touch-manipulation"
            >
              Desconectar
            </button>
          </>
        ) : (
          <div className="flex flex-col gap-2">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Para sincronizar, conecte sua conta Google e autorize o acesso ao calendário.
            </p>
            <details className="text-xs text-gray-500 dark:text-gray-400 group">
              <summary className="cursor-pointer hover:text-gray-700 dark:hover:text-gray-300 list-none [&::-webkit-details-marker]:hidden">
                <span className="inline-flex items-center gap-1">
                  <span className="group-open:rotate-90 transition-transform">▶</span>
                  Ver aviso sobre a tela do Google
                </span>
              </summary>
              <p className="mt-2 pl-4 border-l-2 border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400">
                O Google pode exibir &quot;O app não foi verificado&quot; — isso é normal. O LWK Sistemas usa a integração de forma segura apenas para sincronizar seu calendário. Clique em <strong>Continuar</strong> ou <strong>Avançado → Acessar</strong> para autorizar.
              </p>
            </details>
            <button
              type="button"
              onClick={onConnect}
              disabled={googleLoading}
              className="px-3 py-2 rounded-lg text-sm font-medium bg-[#4285f4] hover:bg-[#3367d6] text-white disabled:opacity-50 flex items-center gap-2 w-fit"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" aria-hidden>
                <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              Conectar Google Calendar
            </button>
          </div>
        )}
    </div>
  );
}
