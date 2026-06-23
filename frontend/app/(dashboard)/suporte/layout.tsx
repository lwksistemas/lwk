'use client';

import RouteGuard from '@/components/RouteGuard';
import { useSessionMonitor } from '@/hooks/useSessionMonitor';
import { useInactivityLogout } from '@/hooks/useInactivityLogout';

export default function SuporteLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useSessionMonitor();
  useInactivityLogout();

  return (
    <RouteGuard allowedUserType="suporte">
      {children}
    </RouteGuard>
  );
}
