'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { EnviarFotoPublicaClient } from '@/components/clinica-beleza/EnviarFotoPublicaClient';

function EnviarFotoQueryPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get('t') || searchParams.get('token');
  return <EnviarFotoPublicaClient token={token} />;
}

export default function EnviarFotoPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
          <p className="text-gray-600">Carregando…</p>
        </div>
      }
    >
      <EnviarFotoQueryPage />
    </Suspense>
  );
}
