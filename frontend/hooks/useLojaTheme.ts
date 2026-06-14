'use client';

import { useCallback, useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import { lojaThemeFromInfo, type LojaThemeColors } from '@/lib/loja-theme';
import type { LojaInfo } from '@/types/dashboard';

export function useLojaTheme(slug: string) {
  const [loja, setLoja] = useState<LojaInfo | null>(null);
  const [theme, setTheme] = useState<LojaThemeColors>(() => lojaThemeFromInfo(null));
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!slug) {
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const { data } = await apiClient.get<LojaInfo>(
        `/superadmin/lojas/info_publica/?slug=${encodeURIComponent(slug)}`,
      );
      setLoja(data);
      setTheme(lojaThemeFromInfo(data));
      if (data?.id && typeof window !== 'undefined') {
        sessionStorage.setItem('current_loja_id', String(data.id));
        if (data.slug) sessionStorage.setItem('loja_slug', data.slug);
      }
    } catch {
      setLoja(null);
      setTheme(lojaThemeFromInfo(null));
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    load();
  }, [load]);

  return { loja, theme, loading, reload: load };
}
