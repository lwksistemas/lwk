'use client';

import CrmPaginationBar from '@/components/crm-vendas/CrmPaginationBar';
import CrmConfirmDeleteModal from '@/components/crm-vendas/CrmConfirmDeleteModal';
import { Plus, Eye, Edit2, Trash2, Building2, Download } from 'lucide-react';
import SkeletonTable from '@/components/crm-vendas/SkeletonTable';
import { formatTelefone } from '@/lib/format-br';
import { formatDate } from '@/lib/financeiro-helpers';
import { useCrmCustomersPage, type CrmConta } from '@/hooks/crm-vendas/useCrmCustomersPage';

function renderCelulaConta(c: CrmConta, coluna: string) {
  switch (coluna) {
    case 'nome':
      return (
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-[#0176d3] to-[#0d9dda] flex items-center justify-center text-white font-semibold text-xs shrink-0">
            {c.nome.charAt(0).toUpperCase()}
          </div>
          <span className="font-medium text-gray-900 dark:text-white">{c.nome}</span>
        </div>
      );
    case 'tipo':
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
            c.tipo === 'prestadora'
              ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
              : c.tipo === 'ambos'
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
          }`}
        >
          {c.tipo === 'prestadora' ? 'Prestadora' : c.tipo === 'ambos' ? 'Cliente + Prestadora' : 'Cliente'}
        </span>
      );
    case 'segmento':
      return <span className="text-gray-700 dark:text-gray-300">{c.segmento || '–'}</span>;
    case 'email':
      return <span className="text-gray-700 dark:text-gray-300">{c.email || '–'}</span>;
    case 'telefone':
      return <span className="text-gray-700 dark:text-gray-300">{c.telefone ? formatTelefone(c.telefone) : '–'}</span>;
    case 'cidade':
      return <span className="text-gray-700 dark:text-gray-300">{c.cidade || '–'}</span>;
    case 'cnpj':
      return <span className="text-gray-700 dark:text-gray-300">{c.cnpj || '–'}</span>;
    case 'razao_social':
      return <span className="text-gray-700 dark:text-gray-300">{c.razao_social || '–'}</span>;
    case 'uf':
      return <span className="text-gray-700 dark:text-gray-300">{c.uf || '–'}</span>;
    case 'created_at':
      return <span className="text-gray-700 dark:text-gray-300">{formatDate(c.created_at)}</span>;
    default:
      return <span className="text-gray-700 dark:text-gray-300">–</span>;
  }
}

export default function CrmVendasCustomersPage() {
  const {
    contas,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    error,
    colunasVisiveis,
    contaParaExcluir,
    setContaParaExcluir,
    submitting,
    handleDelete,
    irParaNovaConta,
    irParaEditarConta,
    irParaVerConta,
    exportContasCsv,
  } = useCrmCustomersPage();

  if (loading && contas.length === 0) {
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
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Contas</h1>
        <div className="flex items-center gap-2">
          {contas.length > 0 && (
            <button
              type="button"
              onClick={() => exportContasCsv(contas)}
              className="flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded text-sm font-medium hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              <Download size={16} /> Exportar CSV
            </button>
          )}
          <button
            type="button"
            onClick={irParaNovaConta}
            className="flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded text-sm font-medium shadow-sm"
          >
            <Plus size={18} /> <span>Nova Conta</span>
          </button>
        </div>
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
              {contas.length === 0 ? (
                <tr>
                  <td colSpan={colunasVisiveis.length + 1} className="py-12 text-center text-gray-500 dark:text-gray-400">
                    <Building2 size={48} className="mx-auto mb-3 opacity-30" />
                    <p className="font-medium">Nenhuma conta cadastrada</p>
                    <p className="text-sm mt-1">Clique em &quot;Nova Conta&quot; para começar</p>
                  </td>
                </tr>
              ) : (
                contas.map((c) => (
                  <tr
                    key={c.id}
                    className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                  >
                    {colunasVisiveis.map((col) => (
                      <td key={col.key} className="py-3 px-4">
                        {renderCelulaConta(c, col.key)}
                      </td>
                    ))}
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          type="button"
                          onClick={() => irParaVerConta(c.id)}
                          className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300"
                          title="Visualizar"
                        >
                          <Eye size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => irParaEditarConta(c.id)}
                          className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300"
                          title="Editar"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => setContaParaExcluir(c)}
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
          itemLabel="contas"
          onPageChange={setPage}
        />
      </div>

      {contaParaExcluir && (
        <CrmConfirmDeleteModal
          tituloItem={contaParaExcluir.nome}
          enviando={submitting}
          onClose={() => setContaParaExcluir(null)}
          onConfirm={handleDelete}
        />
      )}
    </div>
  );
}
