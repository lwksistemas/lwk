'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { MOBILE_BREAKPOINT } from '@/lib/crm-calendario';
import {
  useCrmCalendarioAtividades,
  type CrmCalendarioGoogleHelpersRef,
} from '@/hooks/crm-vendas/useCrmCalendarioAtividades';
import { useCrmCalendarioGoogle } from '@/hooks/crm-vendas/useCrmCalendarioGoogle';

export function useCrmCalendarioPage() {
  const searchParams = useSearchParams();
  const [plugins, setPlugins] = useState<any[]>([]);
  const [locale, setLocale] = useState<any>(null);
  const [isMobile, setIsMobile] = useState(
    () => typeof window !== 'undefined' && window.innerWidth < MOBILE_BREAKPOINT,
  );
  const [confirmAction, setConfirmAction] = useState<'delete_atividade' | 'disconnect_google' | null>(
    null,
  );
  const [confirmando, setConfirmando] = useState(false);

  const googleHelpersRef = useRef({
    googleConnected: false,
    syncingRef: { current: false },
    schedulePushToGoogle: () => {},
    handleSyncGoogle: async (_direction: 'push_only' | 'pull' | 'both' = 'both') => {},
  }) as CrmCalendarioGoogleHelpersRef;

  const atividades = useCrmCalendarioAtividades(googleHelpersRef);
  const google = useCrmCalendarioGoogle(searchParams, atividades.range, atividades.fetchAtividades);

  googleHelpersRef.current = {
    googleConnected: google.googleStatus.connected,
    syncingRef: google.syncingRef,
    schedulePushToGoogle: google.schedulePushToGoogle,
    handleSyncGoogle: google.handleSyncGoogle,
  };

  const loadPlugins = useCallback(async () => {
    const [dayGrid, timeGrid, interaction, ptBr] = await Promise.all([
      import('@fullcalendar/daygrid').then((m) => m.default),
      import('@fullcalendar/timegrid').then((m) => m.default),
      import('@fullcalendar/interaction').then((m) => m.default),
      import('@fullcalendar/core/locales/pt-br').then((m) => m.default),
    ]);
    setPlugins([dayGrid, timeGrid, interaction]);
    setLocale(ptBr);
  }, []);

  useEffect(() => {
    loadPlugins();
  }, [loadPlugins]);

  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
    const handle = () => setIsMobile(mql.matches);
    mql.addEventListener('change', handle);
    handle();
    return () => mql.removeEventListener('change', handle);
  }, []);

  const handleDisconnectGoogle = useCallback(() => {
    setConfirmAction('disconnect_google');
  }, []);

  const handleDelete = useCallback(() => {
    if (!atividades.requestDeleteAtividade()) return;
    setConfirmAction('delete_atividade');
  }, [atividades.requestDeleteAtividade]);

  const closeConfirm = useCallback(() => {
    if (confirmando || atividades.saving) return;
    setConfirmAction(null);
  }, [confirmando, atividades.saving]);

  const executeConfirm = useCallback(async () => {
    if (!confirmAction) return;
    setConfirmando(true);
    try {
      if (confirmAction === 'delete_atividade') {
        await atividades.executeDeleteAtividade();
        setConfirmAction(null);
      } else {
        await google.executeDisconnectGoogle();
        setConfirmAction(null);
      }
    } finally {
      setConfirmando(false);
    }
  }, [confirmAction, atividades.executeDeleteAtividade, google.executeDisconnectGoogle]);

  return {
    searchParams,
    loading: atividades.loading,
    plugins,
    locale,
    isMobile,
    modalOpen: atividades.modalOpen,
    modalAtividade: atividades.modalAtividade,
    form: atividades.form,
    patchForm: atividades.patchForm,
    saving: atividades.saving,
    error: atividades.error,
    whatsappAtivo: atividades.whatsappAtivo,
    googleStatus: google.googleStatus,
    googleLoading: google.googleLoading,
    googleSyncResult: google.googleSyncResult,
    syncError: google.syncError,
    eventosComFeriados: atividades.eventosComFeriados,
    handleConnectGoogle: google.handleConnectGoogle,
    handleSyncGoogle: google.handleSyncGoogle,
    handleDisconnectGoogle,
    handleDatesSet: atividades.handleDatesSet,
    openNovaAtividade: atividades.openNovaAtividade,
    handleDateClick: atividades.handleDateClick,
    handleSelect: atividades.handleSelect,
    handleEventClick: atividades.handleEventClick,
    handleCloseModal: atividades.handleCloseModal,
    handleSave: atividades.handleSave,
    handleSaveAndWhatsapp: atividades.handleSaveAndWhatsapp,
    handleEnviarWhatsapp: atividades.handleEnviarWhatsapp,
    handleToggleConcluido: atividades.handleToggleConcluido,
    handleDelete,
    handleEventDrop: atividades.handleEventDrop,
    handleEventResize: atividades.handleEventResize,
    confirmAction,
    confirmando,
    closeConfirm,
    executeConfirm,
  };
}
