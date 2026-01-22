'use client';

import RouteGuard from '@/components/RouteGuard';

export default function SuporteLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RouteGuard allowedUserType="suporte">
      {children}
    </RouteGuard>
  );
}
