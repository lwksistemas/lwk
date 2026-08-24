'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

export default function ClinicaGeralIndexPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  useEffect(() => {
    router.replace(`/loja/${slug}/clinica/agenda`);
  }, [router, slug]);

  return <p className="p-6 text-sm text-slate-500">Abrindo agenda...</p>;
}
