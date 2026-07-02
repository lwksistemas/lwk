'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Plus, FileText } from 'lucide-react';
import SkeletonTable from '@/components/crm-vendas/SkeletonTable';
import CrmPaginationBar from '@/components/crm-vendas/CrmPaginationBar';
import { CrmDocumentoListPageShell } from '@/components/crm-vendas/documentos/CrmDocumentoListPageShell';
import { useCrmPropostasPage } from '@/hooks/crm-vendas/useCrmPropostasPage';
import { PropostasTable } from './components/PropostasTable';
import { PropostasPageModals } from './components/PropostasPageModals';

export default function CrmVendasPropostasPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';

  const {
    propostas,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    error,
    filtroStatus,
    setFiltroStatus,
    filtroOpcoes,
    exibirColunaAssinatura,
    propostaWhatsappHabilitada,
    enviandoId,
    handleEnviarCliente,
    handleDownloadPdf,
    handleDownloadDocx,
    modalType,
    selected,
    submitting,
    alterandoStatus,
    menuAberto,
    setMenuAberto,
    openModal,
    closeModal,
    irParaEditarProposta,
    handleDelete,
    handleMarcarComoAssinado,
    handleConfirmarPedido,
    handleCancelarProposta,
    confirmAction,
    confirmando,
    closeConfirm,
    executeConfirm,
  } = useCrmPropostasPage(slug);

  if (loading && propostas.length === 0) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-48 animate-pulse" />
        <SkeletonTable rows={5} columns={6} />
      </div>
    );
  }

  return (
    <>
      <CrmDocumentoListPageShell
        titulo="Criar Propostas"
        subtitulo="Crie e gerencie propostas comerciais vinculadas às oportunidades"
        slug={slug}
        error={error}
        filtroStatus={filtroStatus}
        onFiltroChange={setFiltroStatus}
        filtroOpcoes={filtroOpcoes}
        headerActions={
          <>
            <Link
              href={`/loja/${slug}/crm-vendas/proposta-templates`}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 rounded text-sm font-medium transition-colors shadow-sm"
            >
              <FileText size={18} />
              <span>Gerenciar Templates</span>
            </Link>
            <Link
              href={`/loja/${slug}/crm-vendas/propostas/nova`}
              className="flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded text-sm font-medium transition-colors shadow-sm"
            >
              <Plus size={18} />
              <span>Nova Proposta</span>
            </Link>
          </>
        }
      >
        <PropostasTable
          slug={slug}
          propostas={propostas}
          exibirColunaAssinatura={exibirColunaAssinatura}
          propostaWhatsappHabilitada={propostaWhatsappHabilitada}
          enviandoId={enviandoId}
          alterandoStatus={alterandoStatus}
          menuAberto={menuAberto}
          setMenuAberto={setMenuAberto}
          onEnviarCliente={handleEnviarCliente}
          onDownloadPdf={handleDownloadPdf}
          onDownloadDocx={handleDownloadDocx}
          onView={(p) => openModal('view', p)}
          onEditar={irParaEditarProposta}
          onMarcarComoAssinado={handleMarcarComoAssinado}
          onConfirmarPedido={handleConfirmarPedido}
          onCancelar={(p) => openModal('cancelar', p)}
          onExcluir={(p) => openModal('delete', p)}
        />
        <CrmPaginationBar
          page={page}
          totalPages={totalPages}
          totalCount={totalCount}
          pageSize={pageSize}
          loading={loading}
          itemLabel="propostas"
          onPageChange={setPage}
        />
      </CrmDocumentoListPageShell>

      <div className="px-4 py-3 bg-gray-50 dark:bg-[#0d1f3c]/30 rounded-lg border border-gray-200 dark:border-[#0d1f3c]">
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
          Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, com
          registro de data, hora e endereço IP.
        </p>
      </div>

      <PropostasPageModals
        modalType={modalType}
        selected={selected}
        submitting={submitting}
        confirmAction={confirmAction}
        confirmando={confirmando}
        onClose={closeModal}
        onDelete={handleDelete}
        onCancelar={handleCancelarProposta}
        onCloseConfirm={closeConfirm}
        onExecuteConfirm={executeConfirm}
      />
    </>
  );
}
