'use client';

import CrmPaginationBar from '@/components/crm-vendas/CrmPaginationBar';
import { Plus, Eye, Edit2, Trash2, User } from 'lucide-react';
import SkeletonTable from '@/components/crm-vendas/SkeletonTable';
import { ContatoViewModal } from './components/ContatoViewModal';
import { ContatoDeleteModal } from './components/ContatoDeleteModal';
import { formatTelefone } from '@/lib/format-br';
import { formatDate } from '@/lib/financeiro-helpers';
import { useCrmContatosPage, type CrmContato } from '@/hooks/crm-vendas/useCrmContatosPage';

function renderCelulaContato(c: CrmContato, coluna: string) {
  switch (coluna) {
    case 'nome':
      return (
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#06a59a] to-[#0d9dda] flex items-center justify-center text-white font-semibold text-xs shrink-0">
            {c.nome.charAt(0).toUpperCase()}
          </div>
          <span className="font-medium text-gray-900 dark:text-white">{c.nome}</span>
        </div>
      );
    case 'conta':
      return <span className="text-gray-700 dark:text-gray-300">{c.conta_nome || '–'}</span>;
    case 'cargo':
      return <span className="text-gray-700 dark:text-gray-300">{c.cargo || '–'}</span>;
    case 'email':
      return <span className="text-gray-700 dark:text-gray-300">{c.email || '–'}</span>;
    case 'telefone':
      return <span className="text-gray-700 dark:text-gray-300">{c.telefone ? formatTelefone(c.telefone) : '–'}</span>;
    case 'created_at':
      return <span className="text-gray-700 dark:text-gray-300">{formatDate(c.created_at)}</span>;
    default:
      return <span className="text-gray-700 dark:text-gray-300">–</span>;
  }
}

export default function CrmVendasContatosPage() {
  const {
    contatos,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    error,
    colunasVisiveis,
    contaFiltro,
    contaFiltroNome,
    modalType,
    selectedContato,
    submitting,
    openModal,
    closeModal,
    irParaNovoContato,
    irParaEditarContato,
    limparFiltroConta,
    handleDelete,
  } = useCrmContatosPage();

  if (loading && contatos.length === 0) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-32 animate-pulse" />
          <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-32 animate-pulse" />
        </div>
        <SkeletonTable rows={5} columns={5} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Contatos</h1>
          {contaFiltro ? (
            <div className="flex items-center gap-2 mt-1">
              <p className="text-sm text-gray-600 dark:text-gray-400">Filtrando por conta:</p>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                {contaFiltroNome || `ID ${contaFiltro}`}
              </span>
              <button
                type="button"
                onClick={limparFiltroConta}
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                Limpar filtro
              </button>
            </div>
          ) : (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Pessoas vinculadas às contas</p>
          )}
        </div>
        <button
          type="button"
          onClick={irParaNovoContato}
          className="flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded text-sm font-medium transition-colors shadow-sm"
        >
          <Plus size={18} /> <span>Novo Contato</span>
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">
          {error}
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px]">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
                {colunasVisiveis.map((col) => (
                  <th
                    key={col.key}
                    className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider"
                  >
                    {col.label}
                  </th>
                ))}
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody>
              {contatos.length === 0 ? (
                <tr>
                  <td colSpan={colunasVisiveis.length + 1} className="py-12 text-center text-gray-500 dark:text-gray-400">
                    <User size={48} className="mx-auto mb-3 opacity-30" />
                    <p className="font-medium">Nenhum contato cadastrado</p>
                    <p className="text-sm mt-1">Clique em &quot;Novo Contato&quot; para começar</p>
                  </td>
                </tr>
              ) : (
                contatos.map((c) => (
                  <tr
                    key={c.id}
                    className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                  >
                    {colunasVisiveis.map((col) => (
                      <td key={col.key} className="py-3 px-4">
                        {renderCelulaContato(c, col.key)}
                      </td>
                    ))}
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          type="button"
                          onClick={() => openModal('view', c)}
                          className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300"
                          title="Visualizar"
                        >
                          <Eye size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => irParaEditarContato(c.id)}
                          className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300"
                          title="Editar"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => openModal('delete', c)}
                          className="p-1.5 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400"
                          title="Excluir"
                        >
                          <Trash2 size={16} />
                        </button>
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
          itemLabel="contatos"
          onPageChange={setPage}
        />
      </div>

      {modalType === 'view' && selectedContato && (
        <ContatoViewModal
          contato={selectedContato}
          onClose={closeModal}
          onEdit={() => {
            closeModal();
            irParaEditarContato(selectedContato.id);
          }}
        />
      )}
      {modalType === 'delete' && selectedContato && (
        <ContatoDeleteModal
          contato={selectedContato}
          submitting={submitting}
          onClose={closeModal}
          onConfirm={handleDelete}
        />
      )}
    </div>
  );
}
