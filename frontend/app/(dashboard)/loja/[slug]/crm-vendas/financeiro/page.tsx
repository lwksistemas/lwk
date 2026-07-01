'use client';

import { RefreshCw, Plus, FileText, Download } from 'lucide-react';
import { useCrmFinanceiroPage } from '@/hooks/crm-vendas/useCrmFinanceiroPage';
import {
  CrmFinanceiroGruposTable,
  CrmFinanceiroLancamentosTable,
  CrmFinanceiroResumoCards,
} from '@/components/crm-vendas/financeiro/CrmFinanceiroTables';
import { CrmGrupoModal, CrmLancamentoModal } from '@/components/crm-vendas/financeiro/CrmFinanceiroModals';

export default function CrmFinanceiroPage() {
  const f = useCrmFinanceiroPage();

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">Financeiro do vendedor</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Receitas, despesas e comissões por vendedor
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {f.isAdmin && (
            <button
              type="button"
              onClick={f.sincronizarComissoes}
              disabled={f.sincronizando}
              className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded border border-[#0176d3] text-[#0176d3] hover:bg-blue-50 dark:hover:bg-blue-950/30 disabled:opacity-50"
            >
              <Download size={16} className={f.sincronizando ? 'animate-pulse' : ''} />
              {f.sincronizando ? 'Sincronizando...' : 'Sync comissões'}
            </button>
          )}
          <button
            type="button"
            onClick={() => f.loadAll()}
            disabled={f.loading}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded bg-[#0176d3] text-white hover:bg-[#0159a8] disabled:opacity-50"
          >
            <RefreshCw size={16} className={f.loading ? 'animate-spin' : ''} />
            Atualizar
          </button>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap items-end gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50/80 dark:bg-gray-900/40">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Período do relatório PDF</label>
          <select
            value={f.periodoRelatorio}
            onChange={(e) => f.setPeriodoRelatorio(e.target.value)}
            className="rounded border px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
          >
            <option value="mes_atual">Mês atual</option>
            <option value="mes_passado">Mês passado</option>
            <option value="trimestre_atual">Trimestre atual</option>
            <option value="ano_atual">Ano atual</option>
            <option value="personalizado">Personalizado</option>
          </select>
        </div>
        {f.periodoRelatorio === 'personalizado' && (
          <>
            <div>
              <label className="block text-xs text-gray-500 mb-1">De</label>
              <input
                type="date"
                value={f.dataInicioRel}
                onChange={(e) => f.setDataInicioRel(e.target.value)}
                className="rounded border px-2 py-1.5 text-sm dark:bg-gray-800"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Até</label>
              <input
                type="date"
                value={f.dataFimRel}
                onChange={(e) => f.setDataFimRel(e.target.value)}
                className="rounded border px-2 py-1.5 text-sm dark:bg-gray-800"
              />
            </div>
          </>
        )}
        <button
          type="button"
          onClick={f.gerarRelatorioPdf}
          disabled={f.gerandoPdf}
          className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded bg-gray-800 text-white hover:bg-gray-900 disabled:opacity-50 dark:bg-gray-700"
        >
          <FileText size={16} />
          {f.gerandoPdf ? 'Gerando PDF...' : 'Relatório PDF'}
        </button>
      </div>

      {f.isAdmin && (
        <div className="mb-4">
          <label className="text-sm text-gray-600 dark:text-gray-400 mr-2">Vendedor:</label>
          <select
            value={f.vendedorFiltro}
            onChange={(e) => f.setVendedorFiltro(e.target.value)}
            className="rounded border px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
          >
            <option value="">Todos</option>
            {f.vendedores.map((v) => (
              <option key={v.id} value={v.id}>{v.nome}</option>
            ))}
          </select>
        </div>
      )}

      <CrmFinanceiroResumoCards resumo={f.resumo} loading={f.loading} />

      <div className="flex flex-wrap gap-2 mb-4 border-b border-gray-200 dark:border-gray-700 pb-2">
        {(['receita', 'despesa', 'grupos'] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => f.setTab(t)}
            className={`px-4 py-2 text-sm font-medium rounded-t transition-colors ${
              f.tab === t
                ? 'bg-[#0176d3] text-white'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
          >
            {t === 'receita' ? 'Receitas' : t === 'despesa' ? 'Despesas' : 'Grupos'}
          </button>
        ))}
        {f.tab !== 'grupos' && (
          <button
            type="button"
            onClick={() => f.abrirNovo(f.tab)}
            className="ml-auto inline-flex items-center gap-1 px-3 py-2 text-sm rounded bg-green-600 text-white hover:bg-green-700"
          >
            <Plus size={16} />
            Nova {f.tab === 'receita' ? 'receita' : 'despesa'}
          </button>
        )}
        {f.tab === 'grupos' && f.isAdmin && (
          <button
            type="button"
            onClick={() => {
              f.setEditingGrupo(null);
              f.setShowGrupoModal(true);
            }}
            className="ml-auto inline-flex items-center gap-1 px-3 py-2 text-sm rounded bg-[#0176d3] text-white"
          >
            <Plus size={16} />
            Novo grupo
          </button>
        )}
      </div>

      {f.tab === 'grupos' ? (
        <CrmFinanceiroGruposTable
          grupos={f.grupos}
          isAdmin={f.isAdmin}
          onEdit={(g) => {
            f.setEditingGrupo(g);
            f.setShowGrupoModal(true);
          }}
          onRemove={f.removerGrupo}
        />
      ) : (
        <CrmFinanceiroLancamentosTable
          itens={f.lancamentos}
          tipo={f.tab}
          onEdit={f.editar}
          onPagar={f.marcarPago}
          onRemove={f.removerLancamento}
        />
      )}

      <CrmLancamentoModal
        open={f.showModal}
        tipo={f.tab === 'grupos' ? 'receita' : f.tab}
        editing={f.editing}
        grupos={f.grupos}
        vendedores={f.vendedores}
        isAdmin={f.isAdmin}
        saving={f.saving}
        onClose={() => f.setShowModal(false)}
        onSave={f.salvarLancamento}
      />

      <CrmGrupoModal
        open={f.showGrupoModal}
        editing={f.editingGrupo}
        tipoInicial="receita"
        saving={f.saving}
        onClose={() => f.setShowGrupoModal(false)}
        onSave={f.salvarGrupo}
      />
    </div>
  );
}
