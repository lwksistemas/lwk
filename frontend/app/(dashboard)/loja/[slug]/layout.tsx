'use client';

import { useParams } from 'next/navigation';
import RouteGuard from '@/components/RouteGuard';

export default function LojaLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams();
  const slug = params.slug as string;
  
  return (
    <RouteGuard allowedUserType="loja" requiredSlug={slug}>
      {children}
    </RouteGuard>
  );
}
