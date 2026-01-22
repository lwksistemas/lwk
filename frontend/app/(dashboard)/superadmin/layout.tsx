'use client';

import RouteGuard from '@/components/RouteGuard';

export default function SuperAdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RouteGuard allowedUserType="superadmin">
      {children}
    </RouteGuard>
  );
}
