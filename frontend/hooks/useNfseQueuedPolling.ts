'use client';

import { useEffect } from 'react';
import { fetchCrmPaginatedPage } from '@/lib/crm-utils';
import { DEFAULT_PAGE_SIZE } from '@/hooks/usePaginatedList';

type QueryParams = Record<string, string | number | undefined | null>;

function cleanQueryParams(params: QueryParams): Record<string, string | number> {
  const cleaned: Record<string, string | number> = {};
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      cleaned[key] = value;
    }
  }
  return cleaned;
}

/** Atualiza a lista enquanto aguarda o worker concluir emissão enfileirada (202). */
export function useNfseQueuedPolling(options: {
  active: boolean;
  countBefore: number;
  queryParams: QueryParams;
  onTick: () => void;
  onFound: () => void;
  onTimeout: () => void;
  intervalMs?: number;
  maxAttempts?: number;
}) {
  const {
    active,
    countBefore,
    queryParams,
    onTick,
    onFound,
    onTimeout,
    intervalMs = 3000,
    maxAttempts = 12,
  } = options;

  const paramsKey = JSON.stringify(queryParams);

  useEffect(() => {
    if (!active) return;

    let attempts = 0;
    const cleaned = cleanQueryParams(queryParams);

    const timer = setInterval(async () => {
      attempts++;
      onTick();
      try {
        const data = await fetchCrmPaginatedPage('/nfse/', 1, DEFAULT_PAGE_SIZE, cleaned);
        if (data.count > countBefore) {
          clearInterval(timer);
          onFound();
          return;
        }
      } catch {
        // tenta de novo no próximo intervalo
      }
      if (attempts >= maxAttempts) {
        clearInterval(timer);
        onTimeout();
      }
    }, intervalMs);

    return () => clearInterval(timer);
  }, [active, countBefore, paramsKey, intervalMs, maxAttempts, onTick, onFound, onTimeout]);
}
