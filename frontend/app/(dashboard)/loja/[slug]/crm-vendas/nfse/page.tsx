'use client';

import { X } from 'lucide-react';
import CrmPaginationBar from '@/components/crm-vendas/CrmPaginationBar';
import { useCrmNfsePage } from '@/hooks/crm-vendas/useCrmNfsePage';
import { ModalEmitirNFSe } from './components/ModalEmitirNFSe';
import { ModalRecuperarNFSe } from './components/ModalRecuperarNFSe';
import ModalNfseEnviarWhatsapp from './components/ModalNfseEnviarWhatsapp';
import { NfseLojaEmptyState } from './components/NfseLojaEmptyState';
import { NfseLojaFilters } from './components/NfseLojaFilters';
import { NfseLojaHeader } from './components/NfseLojaHeader';
import { NfseLojaLoading } from './components/NfseLojaLoading';
import { NfseLojaSyncMessage } from './components/NfseLojaSyncMessage';
import { NfseLojaTable } from './components/NfseLojaTable';

export default function NFSePage() {
  const {
    lojaProvedor,
    whatsappAtivo,
    showModal,
    setShowModal,
    showRecuperarModal,
    setShowRecuperarModal,
    filtroStatus,
    setFiltroStatus,
    busca,
    setBusca,
    syncMsg,
    syncingId,
    deletingId,
    nfWhatsapp,
    setNfWhatsapp,
    nfses,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    confirmAction,
    setConfirmAction,
    confirmando,
    confirmCopy,
    executeConfirm,
    sincronizarStatus,
    requestExcluirNFSe,
    baixarPdfNFSe,
    cancelarNFSe,
    abrirModalWhatsapp,
    enviarWhatsappNFSe,
    requestReenviarEmail,
    handleEmitirSuccess,
    handleRecuperarSuccess,
  } = useCrmNfsePage();

  return (
    <div className="space-y-6">
      <NfseLojaHeader
        onEmitir={() => setShowModal(true)}
        onRecuperar={lojaProvedor === 'issnet' ? () => setShowRecuperarModal(true) : undefined}
      />

      {syncMsg && <NfseLojaSyncMessage type={syncMsg.type} text={syncMsg.text} />}

      <NfseLojaFilters
        busca={busca}
        setBusca={setBusca}
        filtroStatus={filtroStatus}
        setFiltroStatus={setFiltroStatus}
      />

      {loading ? (
        <NfseLojaLoading />
      ) : nfses.length === 0 ? (
        <NfseLojaEmptyState hasFiltros={!!busca || !!filtroStatus} onEmitir={() => setShowModal(true)} />
      ) : (
        <>
          <NfseLojaTable
            nfses={nfses}
            lojaProvedor={lojaProvedor}
            syncingId={syncingId}
            deletingId={deletingId}
            onSync={sincronizarStatus}
            onDelete={requestExcluirNFSe}
            onDownloadPdf={baixarPdfNFSe}
            onReenviarEmail={requestReenviarEmail}
            onEnviarWhatsapp={abrirModalWhatsapp}
            onCancelar={cancelarNFSe}
            whatsappHabilitado={whatsappAtivo}
          />
          <CrmPaginationBar
            page={page}
            totalPages={totalPages}
            totalCount={totalCount}
            pageSize={pageSize}
            loading={loading}
            itemLabel="notas"
            onPageChange={setPage}
          />
        </>
      )}

      {nfWhatsapp && (
        <ModalNfseEnviarWhatsapp
          nf={nfWhatsapp}
          onClose={() => setNfWhatsapp(null)}
          onEnviar={enviarWhatsappNFSe}
        />
      )}

      {showRecuperarModal && (
        <ModalRecuperarNFSe onClose={() => setShowRecuperarModal(false)} onSuccess={handleRecuperarSuccess} />
      )}

      {showModal && (
        <ModalEmitirNFSe onClose={() => setShowModal(false)} onSuccess={handleEmitirSuccess} />
      )}

      {confirmAction && confirmCopy && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-[80]"
            onClick={() => !confirmando && setConfirmAction(null)}
          />
          <div className="fixed inset-0 z-[81] flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full">
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{confirmCopy.title}</h2>
                <button
                  type="button"
                  onClick={() => !confirmando && setConfirmAction(null)}
                  className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <X size={20} />
                </button>
              </div>
              <div className="p-6 space-y-4">
                <p className="text-gray-600 dark:text-gray-400">{confirmCopy.message(confirmAction.nf)}</p>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setConfirmAction(null)}
                    disabled={confirmando}
                    className="flex-1 px-4 py-2 border rounded-lg disabled:opacity-50"
                  >
                    Cancelar
                  </button>
                  <button
                    type="button"
                    onClick={executeConfirm}
                    disabled={confirmando}
                    className={`flex-1 px-4 py-2 text-white rounded-lg disabled:opacity-50 ${
                      confirmCopy.variant === 'danger'
                        ? 'bg-red-600 hover:bg-red-700'
                        : 'bg-[#0176d3] hover:bg-[#0159a8]'
                    }`}
                  >
                    {confirmando ? 'Processando...' : confirmCopy.confirmLabel}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
