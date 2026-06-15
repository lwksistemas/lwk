'use client';

import { CrmVendasShell } from '@/components/crm-vendas/CrmVendasShell';

export default function CrmVendasLayout({ children }: { children: React.ReactNode }) {
  return <CrmVendasShell>{children}</CrmVendasShell>;
}
