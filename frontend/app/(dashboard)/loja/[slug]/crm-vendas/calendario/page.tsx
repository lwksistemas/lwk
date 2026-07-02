'use client';

import { useCallback } from 'react';
import dynamic from 'next/dynamic';
import { useCrmCalendarioPage } from '@/hooks/crm-vendas/useCrmCalendarioPage';
import { AtividadeModal } from './components/AtividadeModal';
import { CalendarioEventContent } from './components/CalendarioEventContent';
import { CalendarioGooglePanel } from './components/CalendarioGooglePanel';
import CrmConfirmActionModal from '@/components/crm-vendas/CrmConfirmActionModal';

export type { Atividade } from '@/lib/crm-calendario';

const FullCalendar = dynamic(() => import('@fullcalendar/react'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center min-h-[400px] text-gray-500 dark:text-gray-400">
      Carregando calendário...
    </div>
  ),
});

export default function CalendarioCrmPage() {
  const {
    searchParams,
    loading,
    plugins,
    locale,
    isMobile,
    modalOpen,
    modalAtividade,
    form,
    patchForm,
    saving,
    error,
    whatsappAtivo,
    googleStatus,
    googleLoading,
    googleSyncResult,
    syncError,
    eventosComFeriados,
    handleConnectGoogle,
    handleSyncGoogle,
    handleDisconnectGoogle,
    handleDatesSet,
    openNovaAtividade,
    handleDateClick,
    handleSelect,
    handleEventClick,
    handleCloseModal,
    handleSave,
    handleSaveAndWhatsapp,
    handleEnviarWhatsapp,
    handleToggleConcluido,
    handleDelete,
    handleEventDrop,
    handleEventResize,
    confirmAction,
    confirmando,
    closeConfirm,
    executeConfirm,
  } = useCrmCalendarioPage();

  const confirmCopy =
    confirmAction === 'delete_atividade'
      ? {
          title: 'Excluir atividade',
          message: `Excluir "${modalAtividade?.titulo || 'esta atividade'}"?`,
          confirmLabel: 'Excluir',
          variant: 'danger' as const,
        }
      : confirmAction === 'disconnect_google'
        ? {
            title: 'Desconectar Google Calendar',
            message:
              'Desconectar o Google Calendar? Os eventos já enviados permanecem no Google.',
            confirmLabel: 'Desconectar',
            variant: 'danger' as const,
          }
        : null;

  const renderEventContent = useCallback(
    (eventInfo: Parameters<typeof CalendarioEventContent>[0]['eventInfo']) => (
      <CalendarioEventContent eventInfo={eventInfo} />
    ),
    [],
  );

  return (
    <div className="h-full min-h-0 flex flex-col">
      <div className="flex flex-wrap items-center justify-between gap-3 sm:gap-4 mb-3 sm:mb-4 shrink-0">
        <div className="min-w-0">
          <h1 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white truncate">
            Calendário
          </h1>
          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 hidden sm:block">
            Sincronizado com as atividades do CRM • Feriados nacionais exibidos
          </p>
        </div>
        <CalendarioGooglePanel
          googleStatus={googleStatus}
          googleLoading={googleLoading}
          onConnect={handleConnectGoogle}
          onSync={() => handleSyncGoogle('both')}
          onDisconnect={handleDisconnectGoogle}
        />
      </div>
      {(searchParams.get('google_error') === '1' || syncError) && (
        <p className="mb-3 text-sm text-amber-600 dark:text-amber-400">
          {syncError || 'Não foi possível conectar ao Google. Tente novamente.'}
        </p>
      )}
      {googleSyncResult && !syncError && (
        <p className="mb-3 text-sm text-green-600 dark:text-green-400">
          Sincronizado: {googleSyncResult.pushed} enviado(s) ao Google, {googleSyncResult.pulled} importado(s) do Google.
        </p>
      )}

      <div className="relative flex-1 min-h-[400px] sm:min-h-[500px] rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 overflow-hidden fc-agenda-mobile">
        {plugins.length > 0 && locale && (
          <FullCalendar
            key={isMobile ? 'mobile' : 'desktop'}
            plugins={plugins}
            locale={locale}
            themeSystem="standard"
            initialView={isMobile ? 'timeGridDay' : 'dayGridMonth'}
            headerToolbar={
              isMobile
                ? { left: 'prev,next', center: 'title', right: 'today' }
                : { left: 'prev,next today', center: 'title', right: 'dayGridMonth,timeGridWeek,timeGridDay' }
            }
            buttonText={
              isMobile
                ? { today: 'Hoje' }
                : { today: 'Hoje', month: 'Mês', week: 'Semana', day: 'Dia' }
            }
            slotMinTime="06:00:00"
            slotMaxTime="22:00:00"
            allDaySlot
            editable
            selectable
            selectMirror
            dateClick={handleDateClick}
            select={handleSelect}
            eventClick={handleEventClick}
            eventDrop={handleEventDrop}
            eventResize={handleEventResize}
            dayMaxEvents={isMobile ? 6 : 4}
            weekends
            events={eventosComFeriados}
            datesSet={handleDatesSet}
            height="100%"
            eventDisplay="block"
            nowIndicator
            navLinks
            eventTimeFormat={{ hour: '2-digit', minute: '2-digit', meridiem: false }}
            slotLabelFormat={{ hour: '2-digit', minute: '2-digit', meridiem: false }}
            eventContent={renderEventContent}
          />
        )}
        {loading && plugins.length === 0 && (
          <div className="flex items-center justify-center min-h-[400px] text-gray-500">
            Carregando...
          </div>
        )}
        <button
          type="button"
          onClick={openNovaAtividade}
          className="absolute bottom-4 right-4 z-30 flex items-center justify-center w-14 h-14 rounded-full bg-[#0176d3] hover:bg-[#0159a8] text-white shadow-lg active:scale-95 transition-transform touch-manipulation"
          aria-label="Nova atividade"
          title="Nova atividade"
        >
          <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>

      {modalOpen && (
        <AtividadeModal
          atividade={modalAtividade}
          form={form}
          saving={saving}
          error={error}
          whatsappHabilitado={whatsappAtivo}
          onChange={patchForm}
          onSave={handleSave}
          onSaveAndWhatsapp={whatsappAtivo ? handleSaveAndWhatsapp : undefined}
          onEnviarWhatsapp={whatsappAtivo && modalAtividade ? handleEnviarWhatsapp : undefined}
          onClose={handleCloseModal}
          onToggleConcluido={modalAtividade ? handleToggleConcluido : undefined}
          onDelete={modalAtividade ? handleDelete : undefined}
        />
      )}

      {confirmCopy && (
        <CrmConfirmActionModal
          open
          title={confirmCopy.title}
          message={confirmCopy.message}
          confirmLabel={confirmCopy.confirmLabel}
          variant={confirmCopy.variant}
          loading={confirmando || saving}
          onClose={closeConfirm}
          onConfirm={executeConfirm}
        />
      )}
    </div>
  );
}
