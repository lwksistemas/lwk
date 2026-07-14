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
    intervalMs = 2500,
    // ISSNet/nacional pode demorar > 1 min; ~3 min de polling
    maxAttempts = 72,
  } = options;

  const paramsKey = JSON.stringify(queryParams);

  useEffect(() => {
    if (!active) return;

    let attempts = 0;
    let cancelled = false;
    const cleaned = cleanQueryParams(queryParams);

    const tick = async () => {
      if (cancelled) return;
      attempts++;
      onTick();
      try {
        const data = await fetchCrmPaginatedPage('/nfse/', 1, DEFAULT_PAGE_SIZE, cleaned);
        if (cancelled) return;
        if (data.count > countBefore) {
          onFound();
          return true;
        }
      } catch {
        // tenta de novo no próximo intervalo
      }
      if (attempts >= maxAttempts) {
        onTimeout();
        return true;
      }
      return false;
    };

    let timer: ReturnType<typeof setInterval> | null = null;

    void (async () => {
      // Primeira checagem imediata (não espera o intervalo)
      const done = await tick();
      if (done || cancelled) return;
      timer = setInterval(() => {
        void tick().then((finished) => {
          if (finished && timer) clearInterval(timer);
        });
      }, intervalMs);
    })();

    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, countBefore, paramsKey, intervalMs, maxAttempts, onTick, onFound, onTimeout]);
}
