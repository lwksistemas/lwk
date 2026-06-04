'use client';

import RouteGuard from '@/components/RouteGuard';
import { useSessionMonitor } from '@/hooks/useSessionMonitor';

export default function SuporteLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useSessionMonitor();

  return (
    <RouteGuard allowedUserType="suporte">
      {children}
    </RouteGuard>
  );
}
