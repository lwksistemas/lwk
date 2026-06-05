'use client';

import { useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { enhanceResizableTables } from '@/lib/resizable-table-columns';

function isDashboardPath(pathname: string | null): boolean {
  if (!pathname) return false;
  if (pathname.startsWith('/superadmin')) return true;
  if (pathname.startsWith('/suporte/dashboard')) return true;
  if (pathname.startsWith('/loja/') && !pathname.includes('/login')) return true;
  return false;
}

/**
 * Ativa redimensionamento de colunas (arrastar) em tabelas de listagem.
 * Ignora calendários (.fc) e blocos com data-resizable-columns="off".
 */
export function TableColumnsResizer() {
  const pathname = usePathname();

  useEffect(() => {
    if (!isDashboardPath(pathname)) return;

    let debounceId: ReturnType<typeof setTimeout> | null = null;

    const run = () => {
      if (debounceId) clearTimeout(debounceId);
      debounceId = setTimeout(() => {
        enhanceResizableTables(pathname || '/');
      }, 80);
    };

    run();

    const observer = new MutationObserver(run);
    observer.observe(document.body, { childList: true, subtree: true });

    return () => {
      if (debounceId) clearTimeout(debounceId);
      observer.disconnect();
    };
  }, [pathname]);

  return null;
}
