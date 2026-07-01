'use client';

import dynamic from 'next/dynamic';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  CRM_PROPOSTA_STATUS_LABEL as STATUS_LABEL,
  CRM_STATUS_ASSINATURA_LABEL as STATUS_ASSINATURA_LABEL,
} from '@/lib/crm-constants';
import { formatDate } from '@/lib/financeiro-helpers';
import { Plus, Eye, Edit2, Trash2, ClipboardList, FileText, FileSignature, Ban, ShoppingCart } from 'lucide-react';
import SkeletonTable from '@/components/crm-vendas/SkeletonTable';
import CrmEnviarAssinaturaColuna from '@/components/crm-vendas/CrmEnviarAssinaturaColuna';
import CrmConfirmDeleteModal from '@/components/crm-vendas/CrmConfirmDeleteModal';
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
import {
  propostaOcultaColunaAssinatura,
  useCrmPropostasPage,
} from '@/hooks/crm-vendas/useCrmPropostasPage';

const ModalPropostaForm = dynamic(() => import('@/components/crm-vendas/modals/ModalPropostaForm'), { ssr: false });

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
    formData,
    setFormData,
    submitting,
    salvandoPadrao,
    templates,
    alterandoStatus,
    menuAberto,
    setMenuAberto,
    lojaInfo,
    leadInfo,
    vendedorNome,
    itensOportunidade,
    oportunidadeTituloInicial,
    openModal,
    closeModal,
    handleOportunidadeChange,
    handleSubmit,
    handleDelete,
    handleSalvarComoPadrao,
    handleMarcarComoAssinado,
    handleConfirmarPedido,
    handleCancelarProposta,
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
        <div className="overflow-x-auto">
          <table className="w-full min-w-[500px]">
            <thead>
              <tr className="border-b border-gray-200 dark:border-[#0d1f3c] bg-gray-50 dark:bg-[#0d1f3c]/50">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Número</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Título</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Oportunidade</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Status</th>
                {exibirColunaAssinatura && (
                  <th className="text-center py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase w-28">
                    <span className="block">Assinatura</span>
                    <span className="block text-[9px] font-normal normal-case text-gray-500 dark:text-gray-400">Cliente / vendedor</span>
                  </th>
                )}
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase whitespace-nowrap">Emissão</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Ações</th>
              </tr>
            </thead>
            <tbody>
              {propostas.length === 0 ? (
                <tr>
                  <CrmDocumentoEmptyState
                    icon={ClipboardList}
                    titulo="Nenhuma proposta cadastrada"
                    subtitulo='Clique em "Nova Proposta" ou vá ao Pipeline para criar'
                    slug={slug}
                  />
                </tr>
              ) : (
                propostas.map((p) => (
                  <tr key={p.id} className="border-b border-gray-100 dark:border-[#0d1f3c] hover:bg-gray-50 dark:hover:bg-[#0d1f3c]/30">
                    <td className="py-3 px-4 font-mono text-sm text-gray-600 dark:text-gray-400">#{p.numero || '---'}</td>
                    <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">{p.titulo}</td>
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{p.oportunidade_titulo}</td>
                    <td className="py-3 px-4">
                      <CrmDocumentoStatusBadge
                        statusAssinatura={p.status_assinatura}
                        status={p.status}
                        labelsComercial={STATUS_LABEL}
                        labelsAssinatura={STATUS_ASSINATURA_LABEL}
                        variante="proposta"
                      />
                    </td>
                    {exibirColunaAssinatura && (
                      <td className="py-3 px-4">
                        {propostaOcultaColunaAssinatura(p) ? (
                          <span className="text-gray-300 dark:text-gray-600 text-center block">—</span>
                        ) : (
                          <CrmEnviarAssinaturaColuna
                            statusAssinatura={p.status_assinatura}
                            whatsappHabilitado={propostaWhatsappHabilitada}
                            enviando={enviandoId === p.id}
                            onEnviar={(canal) => handleEnviarCliente(p, canal)}
                          />
                        )}
                      </td>
                    )}
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap">
                      {formatDate(p.created_at)}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex justify-end items-center gap-1">
                        <button type="button" onClick={() => openModal('view', p)} className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300" title="Visualizar"><Eye size={16} /></button>
                        {p.status !== 'cancelada' && (
                          <button type="button" onClick={() => openModal('edit', p)} className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300" title="Editar"><Edit2 size={16} /></button>
                        )}
                        <CrmDocumentoMaisAcoesMenu
                          itemId={p.id}
                          aberto={menuAberto === p.id}
                          onToggle={() => setMenuAberto(menuAberto === p.id ? null : p.id)}
                          onClose={() => setMenuAberto(null)}
                          placement="fixed"
                        >
                          <CrmDocumentoArquivoAcoes
                            somentePdf={p.status === 'cancelada'}
                            motivoCancelamento={p.status === 'cancelada' ? p.motivo_cancelamento : undefined}
                            onDownloadPdf={() => {
                              handleDownloadPdf(p.id, p.titulo);
                              setMenuAberto(null);
                            }}
                            onDownloadDocx={() => {
                              handleDownloadDocx(p.id, p.titulo);
                              setMenuAberto(null);
                            }}
                          />
                          {p.status !== 'cancelada' && (
                            <>
                              <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
                              {p.status_assinatura !== 'concluido' && (
                                <button
                                  type="button"
                                  onClick={() => {
                                    handleMarcarComoAssinado(p.id);
                                    setMenuAberto(null);
                                  }}
                                  disabled={alterandoStatus !== null}
                                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
                                >
                                  <FileSignature size={15} className="text-purple-500" /> Marcar como assinado
                                </button>
                              )}
                              {p.status === 'aceita' && p.status_assinatura !== 'concluido' && (
                                <button
                                  type="button"
                                  onClick={() => {
                                    handleConfirmarPedido(p.id);
                                    setMenuAberto(null);
                                  }}
                                  disabled={alterandoStatus !== null}
                                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-emerald-700 dark:text-emerald-300 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 disabled:opacity-50 font-medium"
                                >
                                  <ShoppingCart size={15} className="text-emerald-600" /> Confirmar como Pedido
                                </button>
                              )}
                              <button
                                type="button"
                                onClick={() => {
                                  openModal('cancelar', p);
                                  setMenuAberto(null);
                                }}
                                disabled={alterandoStatus !== null}
                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50"
                              >
                                <Ban size={15} className="text-red-500" /> Cancelar proposta
                              </button>
                              <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
                              <button
                                type="button"
                                onClick={() => {
                                  openModal('delete', p);
                                  setMenuAberto(null);
                                }}
                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                              >
                                <Trash2 size={15} /> Excluir proposta
                              </button>
                            </>
                          )}
                        </CrmDocumentoMaisAcoesMenu>
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
          itemLabel="propostas"
          onPageChange={setPage}
        />
      </CrmDocumentoListPageShell>

      <div className="px-4 py-3 bg-gray-50 dark:bg-[#0d1f3c]/30 rounded-lg border border-gray-200 dark:border-[#0d1f3c]">
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
          Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, com registro de data, hora e endereço IP.
        </p>
      </div>

      {modalType === 'edit' && (
        <ModalPropostaForm
          title="Editar Proposta"
          form={formData}
          formErro={null}
          enviando={submitting}
          lojaInfo={lojaInfo}
          leadInfo={leadInfo}
          itensOportunidade={itensOportunidade}
          statusOpcoes={Object.entries(STATUS_LABEL).map(([value, label]) => ({ value, label }))}
          onFormChange={setFormData}
          onOportunidadeChange={handleOportunidadeChange}
          onSubmit={handleSubmit}
          onClose={closeModal}
          isEdit
          oportunidadeTituloInicial={oportunidadeTituloInicial}
          onSalvarComoPadrao={handleSalvarComoPadrao}
          salvandoPadrao={salvandoPadrao}
          templates={templates}
          onSelecionarTemplate={(conteudo) => setFormData((f) => ({ ...f, conteudo }))}
          vendedorNome={vendedorNome}
        />
      )}

      {modalType === 'view' && selected && (
        <CrmDocumentoDetalhesModal
          aberto
          onClose={closeModal}
          titulo={selected.titulo}
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
          tituloItem={selected.titulo}
          enviando={submitting}
          onClose={closeModal}
          onConfirm={handleDelete}
        />
      )}

      {modalType === 'cancelar' && selected && (
        <CrmCancelarModal
          titulo={selected.titulo}
          tipo="proposta"
          onConfirm={handleCancelarProposta}
          onClose={closeModal}
        />
      )}
    </>
  );
}
