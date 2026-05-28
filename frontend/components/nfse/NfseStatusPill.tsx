'use client';

import { nfseStatusTailwindClass } from '@/lib/nfse-helpers';

type NfseStatusPillProps = {
  status: string;
  label?: string;
  erro?: string | null;
};

/** Badge de status estilo pill (listagem NFS-e da loja CRM). */
export function NfseStatusPill({ status, label, erro }: NfseStatusPillProps) {
  return (
    <>
      <span
        className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${nfseStatusTailwindClass(status)}`}
      >
        {label ?? status}
      </span>
      {status === 'erro' && erro && (
        <p className="text-xs text-amber-700 dark:text-amber-300 mt-1 max-w-[200px] truncate" title={erro}>
          {erro}
        </p>
      )}
    </>
  );
}
