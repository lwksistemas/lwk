'use client';

import { useEffect } from 'react';
import { fetchCrmPaginatedPage } from '@/lib/crm-utils';
import { DEFAULT_PAGE_SIZE } from '@/hooks/usePaginatedList';
import { emissaoConcluida, notaRecemEmitida, type NotaListaEmissao } from '@/lib/nfse-helpers';

type QueryParams = Record<string, string | number | undefined | null>;

export type PaginaNfse<T> = {
  results: T[];
  count: number;
  totalPages: number;
};

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
export function useNfseQueuedPolling<T extends NotaListaEmissao>(options: {
  active: boolean;
  idsAntes: number[];
  capturarBase: boolean;
  queryParams: QueryParams;
  onPage: (data: PaginaNfse<T>) => void;
  onResolved: (nota: T) => void;
  onTimeout: () => void;
  intervalMs?: number;
  maxAttempts?: number;
}) {
  const {
    active,
    idsAntes,
    capturarBase,
    queryParams,
    onPage,
    onResolved,
    onTimeout,
    intervalMs = 4000,
    // ISSNet/nacional pode demorar > 1 min; ~4 min de polling
    maxAttempts = 60,
  } = options;

  const paramsKey = JSON.stringify(queryParams);
  const idsKey = idsAntes.join(',');

  useEffect(() => {
    if (!active) return;

    let attempts = 0;
    let cancelled = false;
    let basePendente = capturarBase;
    let conhecidos = idsAntes;
    const cleaned = cleanQueryParams(queryParams);

    const tick = async () => {
      if (cancelled) return false;
      attempts++;
      try {
        const data = await fetchCrmPaginatedPage<T>('/nfse/', 1, DEFAULT_PAGE_SIZE, cleaned);
        if (cancelled) return false;
        onPage({ results: data.results, count: data.count, totalPages: data.totalPages });
        if (basePendente) {
          conhecidos = data.results.map((nota) => nota.id);
          basePendente = false;
          return false;
        }
        const nota = notaRecemEmitida(data.results, conhecidos);
        if (nota && emissaoConcluida(nota)) {
          onResolved(nota);
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
  }, [active, idsKey, capturarBase, paramsKey, intervalMs, maxAttempts, onPage, onResolved, onTimeout]);
}
