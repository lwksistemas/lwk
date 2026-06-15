'use client';

import { useEffect, useMemo } from 'react';
import { LoginBackgroundLayer } from '@/components/auth/LoginBackgroundLayer';
import {
  getLoginBackgroundFallbackColor,
  getLoginBackgroundHintFromSlug,
  getLoginThemeColor,
  preloadLoginBackground,
  resolveLoginBackground,
} from '@/lib/login-default-backgrounds';

interface AuthScreenShellProps {
  children: React.ReactNode;
  loading?: boolean;
  /** URL fixa do fundo (superadmin/suporte) */
  backgroundUrl?: string;
  /** Slug da loja — heurística imediata antes da API */
  slug?: string;
  /** Nome do tipo de app (API) */
  tipoLojaNome?: string;
  /** Fundo customizado Cloudinary (opcional) */
  loginBackground?: string | null;
  loadingMessage?: string;
}

/**
 * Layout full-screen com foto padrão do tipo de app (arquivos locais em /public).
 * Usado em login, troca de senha e fluxos similares.
 */
export function AuthScreenShell({
  children,
  loading = false,
  backgroundUrl: backgroundUrlProp,
  slug,
  tipoLojaNome,
  loginBackground,
  loadingMessage = 'Carregando...',
}: AuthScreenShellProps) {
  const backgroundUrl = useMemo(() => {
    if (backgroundUrlProp) return backgroundUrlProp;
    if (tipoLojaNome) {
      return resolveLoginBackground(tipoLojaNome, loginBackground);
    }
    if (slug) {
      return getLoginBackgroundHintFromSlug(slug);
    }
    return '/login-backgrounds/default.jpg';
  }, [backgroundUrlProp, tipoLojaNome, loginBackground, slug]);

  const fallbackColor = getLoginBackgroundFallbackColor(backgroundUrl);
  const themeColor = tipoLojaNome ? getLoginThemeColor(tipoLojaNome) : undefined;

  useEffect(() => {
    preloadLoginBackground(backgroundUrl);
  }, [backgroundUrl]);

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      <LoginBackgroundLayer imageUrl={backgroundUrl} fallbackColor={fallbackColor} />
      {loading ? (
        <div className="relative z-10 text-white text-lg flex items-center drop-shadow-md">
          <svg className="animate-spin -ml-1 mr-3 h-6 w-6 text-white" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          {loadingMessage}
        </div>
      ) : (
        <div
          className="relative z-10 w-full max-w-md bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm rounded-2xl shadow-2xl p-6 sm:p-8"
          style={themeColor ? { borderTop: `4px solid ${themeColor}` } : undefined}
        >
          {children}
        </div>
      )}
    </div>
  );
}
