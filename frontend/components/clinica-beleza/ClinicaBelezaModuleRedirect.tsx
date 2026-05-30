'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

type ModuleSegment = 'soroterapia' | 'estetica';

const MODULE_DEFAULT_PATH: Record<ModuleSegment, string> = {
  soroterapia: 'clinica-beleza/estoque?categoria=soroterapia',
  estetica: 'clinica-beleza/procedimentos',
};

export function ClinicaBelezaModuleRedirect({ module: moduleSegment }: { module: ModuleSegment }) {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  useEffect(() => {
    router.replace(`/loja/${slug}/${MODULE_DEFAULT_PATH[moduleSegment]}`);
  }, [slug, moduleSegment, router]);

  return (
    <div className="flex min-h-[40vh] items-center justify-center text-gray-500 dark:text-gray-400 text-sm">
      Redirecionando…
    </div>
  );
}
