'use client';

import { Fragment } from 'react';
import Link from 'next/link';

interface LinkItem {
  label: string;
  href: string;
}

interface ClinicaBelezaRelatedLinksProps {
  slug: string;
  items: LinkItem[];
}

export function ClinicaBelezaRelatedLinks({ slug, items }: ClinicaBelezaRelatedLinksProps) {
  if (items.length === 0) return null;

  return (
    <p className="mt-8 pb-4 text-center text-sm text-gray-500 dark:text-gray-400 px-4">
      Também:{' '}
      {items.map((item, i) => (
        <Fragment key={item.href}>
          {i > 0 && ' · '}
          <Link
            href={item.href.startsWith('/') ? item.href : `/loja/${slug}/${item.href}`}
            className="font-medium hover:underline"
            style={{ color: 'var(--cb-primary, #8B3D52)' }}
          >
            {item.label}
          </Link>
        </Fragment>
      ))}
    </p>
  );
}
