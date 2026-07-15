'use client';

import { SalaoLojaLayout } from '@/components/cabeleireiro/SalaoLojaLayout';

export default function CabeleireiroLayout({ children }: { children: React.ReactNode }) {
  return <SalaoLojaLayout>{children}</SalaoLojaLayout>;
}
