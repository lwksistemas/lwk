'use client';

import type { LojaInfo } from '@/types/dashboard';
import { SalaoDashboardContent } from '@/components/cabeleireiro/SalaoDashboardContent';

export default function DashboardCabeleireiro({
  loja,
  onLogout,
}: {
  loja: LojaInfo;
  onLogout?: () => void;
}) {
  return <SalaoDashboardContent loja={loja} onLogout={onLogout} wrapShell />;
}
