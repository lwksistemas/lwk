'use client';

import { LojaModuleShellLayout } from '@/components/loja/LojaModuleShellLayout';

export default function SuporteLayout({ children }: { children: React.ReactNode }) {
  return <LojaModuleShellLayout>{children}</LojaModuleShellLayout>;
}
