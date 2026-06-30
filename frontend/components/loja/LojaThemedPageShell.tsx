'use client';

import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import type { LojaThemeColors } from '@/lib/loja-theme';
import { assinaturaBackPath } from '@/lib/loja-theme';

interface LojaThemedPageShellProps {
  slug: string;
  tipoLojaNome: string;
  theme: LojaThemeColors;
  title: string;
  subtitle?: string;
  backLabel?: string;
  hideBackButton?: boolean;
  headerActions?: React.ReactNode;
  children: React.ReactNode;
}

export function LojaThemedPageShell({
  slug,
  tipoLojaNome,
  theme,
  title,
  subtitle,
  backLabel,
  hideBackButton = false,
  headerActions,
  children,
}: LojaThemedPageShellProps) {
  const backHref = assinaturaBackPath(slug, tipoLojaNome);

  return (
    <div
      className="min-h-screen w-full text-gray-800 dark:text-gray-100 dark:bg-slate-950"
      style={{ ...theme.cssVars, backgroundColor: theme.pageBg }}
    >
      <nav
        className="text-white shadow-lg"
        style={{ backgroundColor: theme.corPrimaria }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row justify-between min-h-16 py-3 sm:py-0 gap-3 sm:gap-0 sm:items-center">
            <div className="min-w-0">
              <h1 className="text-xl sm:text-2xl font-bold truncate">{title}</h1>
              {subtitle ? (
                <p className="text-sm opacity-90 truncate">{subtitle}</p>
              ) : null}
            </div>
            <div className="flex flex-wrap items-center gap-2 shrink-0">
              {headerActions}
              {!hideBackButton && (
              <Link
                href={backHref}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors hover:opacity-90"
                style={{ backgroundColor: theme.corSecundaria }}
              >
                <ArrowLeft className="w-4 h-4" />
                {backLabel || 'Voltar'}
              </Link>
              )}
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
        {children}
      </main>
    </div>
  );
}
