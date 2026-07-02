'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, Users, Plus, Trash2, Mail } from 'lucide-react';
import CrmPaginationBar from '@/components/crm-vendas/CrmPaginationBar';
import { useCrmFuncionariosPage } from '@/hooks/crm-vendas/useCrmFuncionariosPage';

export default function ConfiguracoesFuncionariosPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const configBase = `/loja/${slug}/crm-vendas/configuracoes`;

  const {
    vendedores,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    error,
    formErro,
    reenviando,
    excluindo,
    confirmarExcluir,
    setConfirmarExcluir,
    abrirNovo,
    abrirEditar,
    handleExcluir,
    handleReenviarSenha,
  } = useCrmFuncionariosPage(slug);

  return (
    <div className="space-y-6">
      <Link
        href={configBase}
        className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-[#0176d3] dark:hover:text-[#0d9dda]"
      >
        <ArrowLeft size={16} />
        Voltar às configurações
      </Link>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-[#e3f3ff] dark:bg-[#0176d3]/20 text-[#0176d3]">
            <Users size={24} />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">Cadastrar funcionários</h1>
            <p className="text-sm text-gray-600 dark:text-gray-400">Gerencie vendedores e equipe de vendas</p>
          </div>
        </div>
        <button
          type="button"
          onClick={abrirNovo}
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded-lg font-medium text-sm transition-colors"
        >
          <Plus size={18} />
          Novo vendedor
        </button>
      </div>

      {(error || formErro) && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 text-sm">
          {error || formErro}
        </div>
      )}

      <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : vendedores.length === 0 ? (
          <div className="p-8 text-center">
            <Users size={40} className="mx-auto text-gray-400 dark:text-gray-500 mb-3" />
            <p className="text-gray-600 dark:text-gray-400 mb-4">Nenhum funcionário cadastrado</p>
            <button
              type="button"
              onClick={abrirNovo}
              className="inline-flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded-lg font-medium text-sm"
            >
              <Plus size={18} />
              Cadastrar primeiro vendedor
            </button>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-[#0d1f3c]">
            {vendedores.map((v) => (
              <div
                key={v.id}
                className="flex items-center justify-between gap-4 p-4 hover:bg-gray-50 dark:hover:bg-[#0d1f3c]/50 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="font-medium text-gray-900 dark:text-white truncate">{v.nome}</p>
                    {v.is_admin && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                        Administrador
                      </span>
                    )}
                    {v.grupo_nome && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                        {v.grupo_nome}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                    {v.email || v.telefone || v.cargo || '—'}
                  </p>
                  {v.tem_acesso && v.email && (
                    <span className="inline-flex items-center gap-1 mt-1 text-xs text-emerald-600 dark:text-emerald-400">
                      <Mail size={12} />
                      Acesso ao sistema
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {v.email && (
                    <button
                      type="button"
                      onClick={() => handleReenviarSenha(v)}
                      disabled={reenviando === v.id}
                      className="px-3 py-1.5 text-sm font-medium text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 rounded transition-colors disabled:opacity-50"
                    >
                      {reenviando === v.id ? 'Enviando...' : 'Reenviar senha'}
                    </button>
                  )}
                  {!v.is_admin && (
                    <>
                      <button
                        type="button"
                        onClick={() => abrirEditar(v)}
                        className="px-3 py-1.5 text-sm font-medium text-[#0176d3] hover:bg-[#0159a8]/10 dark:hover:bg-[#0176d3]/20 rounded transition-colors"
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => setConfirmarExcluir(v)}
                        className="p-1.5 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                        title="Excluir"
                      >
                        <Trash2 size={18} />
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
            {vendedores.length === 1 && vendedores[0].id === 'admin' && (
              <div className="p-4 text-center text-sm text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-[#0d1f3c]/30">
                Nenhum vendedor ou gerente cadastrado. Use o botão &quot;Novo vendedor&quot; para adicionar.
              </div>
            )}
          </div>
        )}
        <CrmPaginationBar
          page={page}
          totalPages={totalPages}
          totalCount={totalCount}
          pageSize={pageSize}
          loading={loading}
          itemLabel="funcionários"
          onPageChange={setPage}
        />
      </div>

      {confirmarExcluir && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => !excluindo && setConfirmarExcluir(null)}
          />
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-[#16325c] rounded-xl shadow-xl w-full max-w-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Excluir vendedor</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Tem certeza que deseja excluir <strong>{confirmarExcluir.nome}</strong>? Esta ação não pode ser
                desfeita.
              </p>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setConfirmarExcluir(null)}
                  disabled={!!excluindo}
                  className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-[#0d1f3c] disabled:opacity-50"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={() => handleExcluir(confirmarExcluir)}
                  disabled={!!excluindo}
                  className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-medium disabled:opacity-50"
                >
                  {excluindo ? 'Excluindo...' : 'Excluir'}
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
