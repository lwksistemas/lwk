'use client';

import { ReactNode } from 'react';
import { ThemeProvider } from '@/components/ui/ThemeProvider';
import { ToastProvider } from '@/components/ui/Toast';
import { TableColumnsResizer } from '@/components/ui/TableColumnsResizer';

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <ToastProvider>
        <TableColumnsResizer />
        {children}
      </ToastProvider>
    </ThemeProvider>
  );
}
