'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

export default function ClinicaGeralRecursosPage() {
  const params = useParams();
  const slug = params.slug as string;
  const router = useRouter();

  useEffect(() => {
    router.replace(`/loja/${slug}/clinica-geral/configuracoes`);
  }, [router, slug]);

  return <p className="p-6 text-sm text-slate-500">Abrindo configurações...</p>;
}
