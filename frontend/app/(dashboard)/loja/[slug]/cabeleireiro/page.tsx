'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

export default function CabeleireiroIndexPage() {
  const slug = useParams()?.slug as string;
  const router = useRouter();
  useEffect(() => {
    router.replace(`/loja/${slug}/dashboard`);
  }, [router, slug]);
  return (
    <div className="p-8 text-sm text-gray-500">Redirecionando ao dashboard...</div>
  );
}
