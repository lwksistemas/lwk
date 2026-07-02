'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  CRM_CONTRATO_STATUS_LABEL as STATUS_LABEL,
  CRM_STATUS_ASSINATURA_LABEL as STATUS_ASSINATURA_LABEL,
} from '@/lib/crm-constants';
import { Plus, Eye, Edit2, Trash2, FileSignature, Ban } from 'lucide-react';
import SkeletonTable from '@/components/crm-vendas/SkeletonTable';
import CrmEnviarAssinaturaColuna from '@/components/crm-vendas/CrmEnviarAssinaturaColuna';
import CrmConfirmDeleteModal from '@/components/crm-vendas/CrmConfirmDeleteModal';
import CrmConfirmActionModal from '@/components/crm-vendas/CrmConfirmActionModal';
import CrmCancelarModal from '@/components/crm-vendas/CrmCancelarModal';
import CrmDocumentoStatusBadge from '@/components/crm-vendas/CrmDocumentoStatusBadge';
import CrmDocumentoDetalhesModal from '@/components/crm-vendas/CrmDocumentoDetalhesModal';
import {
  CrmDocumentoEmptyState,
  CrmDocumentoListPageShell,
} from '@/components/crm-vendas/documentos/CrmDocumentoListPageShell';
import CrmDocumentoMaisAcoesMenu from '@/components/crm-vendas/documentos/CrmDocumentoMaisAcoesMenu';
import CrmDocumentoArquivoAcoes from '@/components/crm-vendas/documentos/CrmDocumentoArquivoAcoes';
import CrmPaginationBar from '@/components/crm-vendas/CrmPaginationBar';
import { useCrmContratosPage } from '@/hooks/crm-vendas/useCrmContratosPage';

export default function CrmVendasContratosPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';

  const {
    contratos,
    contratosFiltrados,
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
    modalType,
    selected,
    submitting,
    alterandoStatus,
    menuAberto,
    setMenuAberto,
    enviandoId,
    contratoWhatsappHabilitado,
    handleEnviarCliente,
    handleDownloadPdf,
    handleDownloadDocx,
    openModal,
    closeModal,
    handleMarcarComoAssinado,
    handleCancelarContrato,
    handleDelete,
    confirmAction,
    confirmando,
    closeConfirm,
    executeConfirm,
    irParaNovoContrato,
    irParaEditarContrato,
  } = useCrmContratosPage(slug);

  if (loading && contratos.length === 0) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-48 animate-pulse" />
        <SkeletonTable rows={5} columns={5} />
      </div>
    );
  }

  return (
    <>
      <CrmDocumentoListPageShell
        titulo="Criar Contrato"
        subtitulo="Gere contratos a partir das oportunidades fechadas como ganhas"
        slug={slug}
        error={error}
        filtroStatus={filtroStatus}
        onFiltroChange={setFiltroStatus}
        filtroOpcoes={filtroOpcoes}
        headerActions={
          <>
            <Link
              href={`/loja/${slug}/crm-vendas/contrato-templates`}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 rounded text-sm font-medium transition-colors shadow-sm"
            >
              <FileSignature size={18} />
              <span>Gerenciar Templates</span>
            </Link>
            <button
              type="button"
              onClick={irParaNovoContrato}
              className="flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded text-sm font-medium transition-colors shadow-sm"
            >
              <Plus size={18} />
              <span>Novo Contrato</span>
            </button>
          </>
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[500px]">
            <thead>
              <tr className="border-b border-gray-200 dark:border-[#0d1f3c] bg-gray-50 dark:bg-[#0d1f3c]/50">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Número</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Título</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Oportunidade</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Status</th>
                <th className="text-center py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase w-28">
                  <span className="block">Assinatura</span>
                  <span className="block text-[9px] font-normal normal-case text-gray-500 dark:text-gray-400">Cliente / vendedor</span>
                </th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Ações</th>
              </tr>
            </thead>
            <tbody>
              {contratos.length === 0 ? (
                <tr>
                  <CrmDocumentoEmptyState
                    icon={FileSignature}
                    titulo="Nenhum contrato cadastrado"
                    subtitulo="Crie contratos a partir de oportunidades fechadas como ganhas"
                    slug={slug}
                  />
                </tr>
              ) : (
                contratosFiltrados.map((c) => (
                  <tr key={c.id} className="border-b border-gray-100 dark:border-[#0d1f3c] hover:bg-gray-50 dark:hover:bg-[#0d1f3c]/30">
                    <td className="py-3 px-4 font-mono text-sm text-gray-600 dark:text-gray-400">#{c.numero || '---'}</td>
                    <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">{c.titulo || `Contrato #${c.id}`}</td>
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{c.oportunidade_titulo}</td>
                    <td className="py-3 px-4">
                      <CrmDocumentoStatusBadge
                        statusAssinatura={c.status_assinatura}
                        status={c.status}
                        labelsComercial={STATUS_LABEL}
                        labelsAssinatura={STATUS_ASSINATURA_LABEL}
                        variante="contrato"
                      />
                    </td>
                    <td className="py-3 px-4">
                      {c.status === 'cancelado' ? (
                        <span className="text-gray-300 dark:text-gray-600 text-center block">—</span>
                      ) : (
                        <CrmEnviarAssinaturaColuna
                          statusAssinatura={c.status_assinatura}
                          whatsappHabilitado={contratoWhatsappHabilitado}
                          enviando={enviandoId === c.id}
                          onEnviar={(canal) => handleEnviarCliente(c, canal)}
                        />
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex justify-end gap-1 flex-wrap items-center">
                        {c.status === 'cancelado' ? (
                          <CrmDocumentoMaisAcoesMenu
                            itemId={c.id}
                            aberto={menuAberto === c.id}
                            onToggle={() => setMenuAberto(menuAberto === c.id ? null : c.id)}
                            onClose={() => setMenuAberto(null)}
                            menuClassName="w-64"
                          >
                            <CrmDocumentoArquivoAcoes
                              somentePdf
                              motivoCancelamento={c.motivo_cancelamento}
                              onDownloadPdf={() => {
                                handleDownloadPdf(c.id, c.titulo);
                                setMenuAberto(null);
                              }}
                            />
                          </CrmDocumentoMaisAcoesMenu>
                        ) : (
                          <>
                            <CrmDocumentoMaisAcoesMenu
                              itemId={c.id}
                              aberto={menuAberto === c.id}
                              onToggle={() => setMenuAberto(menuAberto === c.id ? null : c.id)}
                              onClose={() => setMenuAberto(null)}
                            >
                              <CrmDocumentoArquivoAcoes
                                onDownloadPdf={() => {
                                  handleDownloadPdf(c.id, c.titulo);
                                  setMenuAberto(null);
                                }}
                                onDownloadDocx={() => {
                                  handleDownloadDocx(c.id, c.titulo);
                                  setMenuAberto(null);
                                }}
                              />
                            </CrmDocumentoMaisAcoesMenu>
                            {c.status_assinatura !== 'concluido' && (
                              <button
                                type="button"
                                onClick={() => handleMarcarComoAssinado(c.id)}
                                disabled={alterandoStatus !== null}
                                className="p-1.5 rounded bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 hover:bg-purple-200 dark:hover:bg-purple-900/50 disabled:opacity-50"
                                title="Marcar como assinado manualmente"
                              >
                                <FileSignature size={16} />
                              </button>
                            )}
                            <button type="button" onClick={() => openModal('view', c)} className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600" title="Visualizar"><Eye size={16} /></button>
                            <button type="button" onClick={() => irParaEditarContrato(c.id)} className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600" title="Editar"><Edit2 size={16} /></button>
                            <button
                              type="button"
                              onClick={() => openModal('cancelar', c)}
                              disabled={alterandoStatus !== null}
                              className="p-1.5 rounded bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 hover:bg-orange-200 dark:hover:bg-orange-900/50 disabled:opacity-50"
                              title="Cancelar contrato"
                            >
                              <Ban size={16} />
                            </button>
                            <button type="button" onClick={() => openModal('delete', c)} className="p-1.5 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600" title="Excluir"><Trash2 size={16} /></button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <CrmPaginationBar
          page={page}
          totalPages={totalPages}
          totalCount={totalCount}
          pageSize={pageSize}
          loading={loading}
          itemLabel="contratos"
          onPageChange={setPage}
        />
      </CrmDocumentoListPageShell>

      <div className="px-4 py-3 bg-gray-50 dark:bg-[#0d1f3c]/30 rounded-lg border border-gray-200 dark:border-[#0d1f3c]">
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
          Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, com registro de data, hora e endereço IP.
        </p>
      </div>

      {modalType === 'view' && selected && (
        <CrmDocumentoDetalhesModal
          aberto
          onClose={closeModal}
          titulo={selected.titulo}
          numero={selected.numero || undefined}
          oportunidadeTitulo={selected.oportunidade_titulo}
          leadNome={selected.lead_nome}
          statusExibicao={STATUS_LABEL[selected.status] || selected.status}
          valorTotal={selected.valor_total}
          descontoTipo={selected.desconto_tipo}
          descontoValor={selected.desconto_valor}
          valorComDesconto={selected.valor_com_desconto}
          conteudo={selected.conteudo}
        />
      )}

      {modalType === 'delete' && selected && (
        <CrmConfirmDeleteModal
          tituloItem={selected.titulo || selected.numero || 'este contrato'}
          enviando={submitting}
          onClose={closeModal}
          onConfirm={handleDelete}
        />
      )}

      {modalType === 'cancelar' && selected && (
        <CrmCancelarModal
          titulo={selected.titulo || selected.numero || 'este contrato'}
          tipo="contrato"
          onConfirm={handleCancelarContrato}
          onClose={closeModal}
        />
      )}

      {confirmAction && (
        <CrmConfirmActionModal
          open
          title="Marcar como assinado"
          message={`Marcar "${confirmAction.titulo}" como assinado manualmente?\n\nUse quando o cliente assinar de outra forma (manual, gov.br, etc).`}
          confirmLabel="Marcar assinado"
          loading={confirmando}
          onClose={closeConfirm}
          onConfirm={executeConfirm}
        />
      )}
    </>
  );
}
