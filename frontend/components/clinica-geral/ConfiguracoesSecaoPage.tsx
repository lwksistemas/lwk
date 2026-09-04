'use client';

import { ConfiguracoesLayout } from '@/components/clinica-geral/ConfiguracoesLayout';

export function ConfiguracoesSecaoPage({ titulo, texto }: { titulo: string; texto: string }) {
  return (
    <ConfiguracoesLayout>
      <h2 className="mb-2 text-lg font-medium text-slate-800 dark:text-slate-100">{titulo}</h2>
      <p className="max-w-lg text-sm text-slate-500 dark:text-slate-400">{texto}</p>
    </ConfiguracoesLayout>
  );
}
