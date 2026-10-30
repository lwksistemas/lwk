'use client';

import {
  CRM_PROPOSTA_STATUS_LABEL as STATUS_LABEL,
  CRM_STATUS_ASSINATURA_LABEL as STATUS_ASSINATURA_LABEL,
} from '@/lib/crm-constants';
import { formatDate } from '@/lib/financeiro-helpers';
import { Eye, Edit2, Trash2, ClipboardList, FileSignature, Ban, ShoppingCart, Mail, MessageCircle } from 'lucide-react';
import CrmEnviarAssinaturaColuna from '@/components/crm-vendas/CrmEnviarAssinaturaColuna';
import CrmDocumentoStatusBadge from '@/components/crm-vendas/CrmDocumentoStatusBadge';
import { CrmDocumentoEmptyState } from '@/components/crm-vendas/documentos/CrmDocumentoListPageShell';
import CrmDocumentoMaisAcoesMenu from '@/components/crm-vendas/documentos/CrmDocumentoMaisAcoesMenu';
import CrmDocumentoArquivoAcoes from '@/components/crm-vendas/documentos/CrmDocumentoArquivoAcoes';
import {
  propostaOcultaColunaAssinatura,
  rotuloOportunidadePropostaLista,
  rotuloPrestadorPropostaLista,
  rotuloTituloPropostaLista,
} from '@/lib/crm-propostas-helpers';
import type { CrmProposta } from '@/hooks/crm-vendas/useCrmPropostasPage';
import {
  COLUNAS_PROPOSTAS_DISPONIVEIS,
  DEFAULT_COLUNAS_PROPOSTAS,
  colunasDocumentoNaLista,
  colunasVisiveisFromConfig,
  type CrmColunaDef,
} from '@/lib/crm-colunas-config';

export type PropostasTableProps = {
  slug: string;
  propostas: CrmProposta[];
  colunas?: CrmColunaDef[];
  exibirColunaAssinatura: boolean;
  propostaWhatsappHabilitada: boolean;
  enviandoId: number | null;
  alterandoStatus: number | null;
  menuAberto: number | null;
  setMenuAberto: (id: number | null) => void;
  onEnviarCliente: (proposta: CrmProposta, canal: 'email' | 'whatsapp') => void;
  onDownloadPdf: (id: number, titulo: string) => void;
  onDownloadDocx: (id: number, titulo: string) => void;
  onView: (proposta: CrmProposta) => void;
  onEditar: (id: number) => void;
  onMarcarComoAssinado: (propostaId: number) => void;
  onConfirmarPedido: (propostaId: number) => void;
  onCancelar: (proposta: CrmProposta) => void;
  onExcluir: (proposta: CrmProposta) => void;
};

export function PropostasTable({
  slug,
  propostas,
  colunas,
  exibirColunaAssinatura,
  propostaWhatsappHabilitada,
  enviandoId,
  alterandoStatus,
  menuAberto,
  setMenuAberto,
  onEnviarCliente,
  onDownloadPdf,
  onDownloadDocx,
  onView,
  onEditar,
  onMarcarComoAssinado,
  onConfirmarPedido,
  onCancelar,
  onExcluir,
}: PropostasTableProps) {
  const colunasTabela = colunasDocumentoNaLista(
    colunas?.length
      ? colunas
      : colunasVisiveisFromConfig(null, COLUNAS_PROPOSTAS_DISPONIVEIS, DEFAULT_COLUNAS_PROPOSTAS),
    exibirColunaAssinatura,
  );

  const renderCelula = (p: CrmProposta, key: string) => {
    if (key === 'numero') {
      return <span className="font-mono text-sm text-gray-600 dark:text-gray-400">#{p.numero || '---'}</span>;
    }
    if (key === 'titulo') return rotuloTituloPropostaLista(p);
    if (key === 'oportunidade') return rotuloOportunidadePropostaLista(p);
    if (key === 'prestador') return rotuloPrestadorPropostaLista(p);
    if (key === 'status') {
      return (
        <CrmDocumentoStatusBadge
          statusAssinatura={p.status_assinatura}
          status={p.status}
          labelsComercial={STATUS_LABEL}
          labelsAssinatura={STATUS_ASSINATURA_LABEL}
          variante="proposta"
        />
      );
    }
    if (key === 'assinatura') {
      if (propostaOcultaColunaAssinatura(p)) {
        return <span className="text-gray-300 dark:text-gray-600 text-center block">—</span>;
      }
      return (
        <CrmEnviarAssinaturaColuna
          statusAssinatura={p.status_assinatura}
          whatsappHabilitado={propostaWhatsappHabilitada}
          enviando={enviandoId === p.id}
          onEnviar={(canal) => onEnviarCliente(p, canal)}
        />
      );
    }
    if (key === 'emissao') return formatDate(p.created_at);
    return null;
  };

  return (
    <div className="overflow-x-auto max-w-full">
      <table className="w-full min-w-[500px]">
        <thead>
          <tr className="border-b border-gray-200 dark:border-[#0d1f3c] bg-gray-50 dark:bg-[#0d1f3c]/50">
            {colunasTabela.map((col) => (
              <th
                key={col.key}
                className={`py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase ${
                  col.key === 'assinatura' ? 'text-center w-28' : 'text-left'
                } ${col.key === 'emissao' ? 'whitespace-nowrap' : ''}`}
              >
                {col.key === 'assinatura' ? (
                  <>
                    <span className="block">Assinatura</span>
                    <span className="block text-[9px] font-normal normal-case text-gray-500 dark:text-gray-400">
                      Cliente / vendedor
                    </span>
                  </>
                ) : (
                  col.label
                )}
              </th>
            ))}
            <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">
              Ações
            </th>
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
              <tr
                key={p.id}
                className="border-b border-gray-100 dark:border-[#0d1f3c] hover:bg-gray-50 dark:hover:bg-[#0d1f3c]/30"
              >
                {colunasTabela.map((col) => {
                  const texto = col.key === 'titulo'
                    ? rotuloTituloPropostaLista(p)
                    : col.key === 'oportunidade'
                      ? rotuloOportunidadePropostaLista(p)
                      : col.key === 'prestador'
                        ? rotuloPrestadorPropostaLista(p)
                        : undefined;
                  return (
                    <td
                      key={col.key}
                      title={texto}
                      className={`py-3 px-4 ${
                        col.key === 'titulo' ? 'font-medium text-gray-900 dark:text-white max-w-[220px] truncate' : ''
                      } ${
                        col.key === 'oportunidade' || col.key === 'prestador'
                          ? 'text-gray-700 dark:text-gray-300 max-w-[220px] truncate'
                          : ''
                      } ${col.key === 'emissao' ? 'text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap' : ''}`}
                    >
                      {renderCelula(p, col.key)}
                    </td>
                  );
                })}
                <td className="py-3 px-4">
                  <div className="flex justify-end items-center gap-1">
                    <button
                      type="button"
                      onClick={() => onView(p)}
                      className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300"
                      title="Visualizar"
                    >
                      <Eye size={16} />
                    </button>
                    {p.status !== 'cancelada' && (
                      <button
                        type="button"
                        onClick={() => onEditar(p.id)}
                        className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300"
                        title="Editar"
                      >
                        <Edit2 size={16} />
                      </button>
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
                          onDownloadPdf(p.id, p.titulo);
                          setMenuAberto(null);
                        }}
                        onDownloadDocx={() => {
                          onDownloadDocx(p.id, p.titulo);
                          setMenuAberto(null);
                        }}
                      />
                      {p.status !== 'cancelada' && (
                        <>
                          <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
                          {p.status_assinatura === 'aguardando_vendedor' && (
                            <>
                              <button
                                type="button"
                                onClick={() => {
                                  onEnviarCliente(p, 'whatsapp');
                                  setMenuAberto(null);
                                }}
                                disabled={enviandoId !== null}
                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
                              >
                                <MessageCircle size={15} className="text-green-600" /> Reenviar ao vendedor (WhatsApp)
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  onEnviarCliente(p, 'email');
                                  setMenuAberto(null);
                                }}
                                disabled={enviandoId !== null}
                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
                              >
                                <Mail size={15} className="text-blue-600" /> Reenviar ao vendedor (e-mail)
                              </button>
                            </>
                          )}
                          {p.status_assinatura !== 'concluido' && (
                            <button
                              type="button"
                              onClick={() => {
                                onMarcarComoAssinado(p.id);
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
                                onConfirmarPedido(p.id);
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
                              onCancelar(p);
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
                              onExcluir(p);
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
  );
}
