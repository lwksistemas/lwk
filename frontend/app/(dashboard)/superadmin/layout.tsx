'use client';

import RouteGuard from '@/components/RouteGuard';
import { useSessionMonitor } from '@/hooks/useSessionMonitor';

export default function SuperAdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useSessionMonitor();

  return (
    <RouteGuard allowedUserType="superadmin">
      {children}
    </RouteGuard>
  );
}
