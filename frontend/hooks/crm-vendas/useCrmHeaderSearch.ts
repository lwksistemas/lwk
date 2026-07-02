'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import apiClient from '@/lib/api-client';
import {
  CRM_HEADER_SEARCH_DEBOUNCE_MS,
  CRM_HEADER_SEARCH_MIN_LEN,
  type CrmHeaderBuscaResult,
} from '@/lib/crm-header';

export function useCrmHeaderSearch() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<CrmHeaderBuscaResult | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [showSearchDropdown, setShowSearchDropdown] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchBusca = useCallback(async (q: string) => {
    if (!q || q.length < CRM_HEADER_SEARCH_MIN_LEN) {
      setSearchResults(null);
      return;
    }
    setSearchLoading(true);
    try {
      const res = await apiClient.get<CrmHeaderBuscaResult>('/crm-vendas/busca/', {
        params: { q: q.trim(), limit: 5 },
      });
      setSearchResults(res.data);
    } catch {
      setSearchResults({ leads: [], oportunidades: [], contas: [], propostas: [] });
    } finally {
      setSearchLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (searchQuery.length < CRM_HEADER_SEARCH_MIN_LEN) {
      setSearchResults(null);
      setShowSearchDropdown(false);
      return;
    }
    debounceRef.current = setTimeout(() => {
      void fetchBusca(searchQuery);
      setShowSearchDropdown(true);
      debounceRef.current = null;
    }, CRM_HEADER_SEARCH_DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchQuery, fetchBusca]);

  const clearSearch = useCallback(() => {
    setSearchQuery('');
    setSearchResults(null);
    setShowSearchDropdown(false);
  }, []);

  return {
    searchQuery,
    setSearchQuery,
    searchResults,
    searchLoading,
    showSearchDropdown,
    setShowSearchDropdown,
    clearSearch,
  };
}
