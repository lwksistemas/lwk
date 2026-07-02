'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import type { ReadonlyURLSearchParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import {
  API_GOOGLE_AUTH,
  API_GOOGLE_DISCONNECT,
  API_GOOGLE_STATUS,
  API_GOOGLE_SYNC,
  SYNC_RESULT_DISPLAY_MS,
} from '@/lib/crm-calendario';

export function useCrmCalendarioGoogle(
  searchParams: ReadonlyURLSearchParams,
  range: { start: Date; end: Date } | null,
  refreshAtividades: (start: Date, end: Date) => Promise<void>,
) {
  const [googleStatus, setGoogleStatus] = useState<{ connected: boolean; email: string | null }>({
    connected: false,
    email: null,
  });
  const [googleLoading, setGoogleLoading] = useState(false);
  const [googleSyncResult, setGoogleSyncResult] = useState<{ pushed: number; pulled: number } | null>(
    null,
  );
  const [syncError, setSyncError] = useState<string | null>(null);
  const syncingRef = useRef(false);

  const loadGoogleStatus = useCallback(async () => {
    try {
      const res = await apiClient.get<{ connected: boolean; email?: string | null }>(API_GOOGLE_STATUS);
      setGoogleStatus({ connected: !!res.data.connected, email: res.data.email ?? null });
    } catch {
      setGoogleStatus({ connected: false, email: null });
    }
  }, []);

  useEffect(() => {
    loadGoogleStatus();
  }, [loadGoogleStatus]);

  useEffect(() => {
    const connected = searchParams.get('google_connected');
    const err = searchParams.get('google_error');
    if (connected === '1') {
      setSyncError(null);
      loadGoogleStatus();
      if (typeof window !== 'undefined') {
        window.history.replaceState({}, '', window.location.pathname);
      }
    }
    if (err === '1' && typeof window !== 'undefined') {
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [searchParams, loadGoogleStatus]);

  const handleConnectGoogle = useCallback(async () => {
    setGoogleLoading(true);
    setSyncError(null);
    try {
      const res = await apiClient.get<{ auth_url: string }>(API_GOOGLE_AUTH);
      if (res.data?.auth_url) {
        window.location.href = res.data.auth_url;
        return;
      }
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Google Calendar não configurado. Entre em contato com o suporte.';
      setSyncError(msg);
    } finally {
      setGoogleLoading(false);
    }
  }, []);

  const handleSyncGoogle = useCallback(
    async (direction: 'push_only' | 'pull' | 'both' = 'both') => {
      if (syncingRef.current) return;
      syncingRef.current = true;
      setGoogleLoading(true);
      setGoogleSyncResult(null);
      setSyncError(null);
      try {
        const res = await apiClient.post<{ pushed: number; pulled: number }>(API_GOOGLE_SYNC, {
          direction,
        });
        setGoogleSyncResult({ pushed: res.data.pushed, pulled: res.data.pulled });
        if (range) await refreshAtividades(range.start, range.end);
        if (SYNC_RESULT_DISPLAY_MS > 0 && typeof window !== 'undefined') {
          window.setTimeout(() => setGoogleSyncResult(null), SYNC_RESULT_DISPLAY_MS);
        }
      } catch (e: unknown) {
        const err = e as { response?: { data?: { detail?: string }; status?: number } };
        let msg = err?.response?.data?.detail || 'Erro ao sincronizar com o Google Calendar.';
        if (msg.includes('Contexto de loja') || msg.includes('não identificado')) {
          msg += ' Atualize a página e tente novamente.';
        } else if (err?.response?.status === 502 || err?.response?.status === 503) {
          msg = 'Servidor temporariamente indisponível. Tente novamente em alguns segundos.';
        }
        setSyncError(msg);
        if (msg.includes('Token expirado') || msg.includes('inválido')) {
          setGoogleStatus({ connected: false, email: null });
          loadGoogleStatus();
        }
      } finally {
        syncingRef.current = false;
        setGoogleLoading(false);
      }
    },
    [range, refreshAtividades, loadGoogleStatus],
  );

  const executeDisconnectGoogle = useCallback(async () => {
    setGoogleLoading(true);
    setSyncError(null);
    try {
      await apiClient.delete(API_GOOGLE_DISCONNECT);
      setGoogleStatus({ connected: false, email: null });
      setGoogleSyncResult(null);
    } finally {
      setGoogleLoading(false);
    }
  }, []);

  const schedulePushToGoogle = useCallback(() => {
    if (googleStatus.connected && !syncingRef.current) {
      setTimeout(() => {
        handleSyncGoogle('push_only').catch(() => {});
      }, 100);
    }
  }, [googleStatus.connected, handleSyncGoogle]);

  return {
    googleStatus,
    googleLoading,
    googleSyncResult,
    syncError,
    syncingRef,
    handleConnectGoogle,
    handleSyncGoogle,
    executeDisconnectGoogle,
    schedulePushToGoogle,
  };
}
