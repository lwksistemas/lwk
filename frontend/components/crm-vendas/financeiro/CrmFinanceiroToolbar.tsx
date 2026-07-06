'use client';

import { RefreshCw, Download, FolderOpen, FileText } from 'lucide-react';
import { CRM_PERIODO_FINANCEIRO } from '@/lib/crm-periodos';
import type { useCrmFinanceiroPage } from '@/hooks/crm-vendas/useCrmFinanceiroPage';
import type { TipoFinanceiro } from '@/lib/crm-financeiro-types';

type FinanceiroPage = ReturnType<typeof useCrmFinanceiroPage>;

interface Props {
  f: FinanceiroPage;
  tipoAtivo: TipoFinanceiro;
  gruposTipo: FinanceiroPage['grupos'];
}

export function CrmFinanceiroToolbar({ f, tipoAtivo, gruposTipo }: Props) {
  return (
    <>
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 shrink-0">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">Financeiro do vendedor</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Escolha despesas ou receitas — lista em tela cheia
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {f.isAdmin && (
            <>
              <button
                type="button"
                onClick={() => f.setShowGrupos((v) => !v)}
                className={`inline-flex items-center gap-2 px-3 py-2 text-sm rounded border ${
                  f.showGrupos
                    ? 'bg-[#0176d3] text-white border-[#0176d3]'
                    : 'border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800'
                }`}
              >
                <FolderOpen size={16} />
                Grupos
              </button>
              <button
                type="button"
                onClick={f.sincronizarComissoes}
                disabled={f.sincronizando}
                className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded border border-[#0176d3] text-[#0176d3] hover:bg-blue-50 dark:hover:bg-blue-950/30 disabled:opacity-50"
              >
                <Download size={16} className={f.sincronizando ? 'animate-pulse' : ''} />
                {f.sincronizando ? 'Sync...' : 'Sync comissões'}
              </button>
            </>
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

      <p className="text-xs text-gray-500 dark:text-gray-400 shrink-0 px-1">
        Receitas pagas entram no período pela data do pagamento (caixa). Pendentes, pela data de vencimento
        (competência). Comissões costumam ser recebidas no mês seguinte ao fechamento da venda.
      </p>

      <div className="flex flex-wrap items-end gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50/80 dark:bg-gray-900/40 shrink-0">
        {f.isAdmin && (
          <div>
            <label className="block text-xs text-gray-500 mb-1">Vendedor</label>
            <select
              value={f.vendedorFiltro}
              onChange={(e) => f.setVendedorFiltro(e.target.value)}
              className="rounded border px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700 min-w-[180px]"
            >
              <option value="">Todos</option>
              {f.vendedores.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.nome}
                </option>
              ))}
            </select>
          </div>
        )}
        <div>
          <label className="block text-xs text-gray-500 mb-1">Período</label>
          <select
            value={f.periodoRelatorio}
            onChange={(e) => f.setPeriodoRelatorio(e.target.value)}
            className="rounded border px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
          >
            {CRM_PERIODO_FINANCEIRO.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
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
        <div>
          <label className="block text-xs text-gray-500 mb-1">Grupo</label>
          <select
            value={f.grupoFiltroRelatorio}
            onChange={(e) => f.setGrupoFiltroRelatorio(e.target.value)}
            className="rounded border px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700 min-w-[160px]"
          >
            <option value="">Todos os grupos</option>
            {gruposTipo.map((g) => (
              <option key={g.id} value={g.id}>
                {g.nome}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          onClick={() => f.gerarRelatorioPdf()}
          disabled={f.gerandoPdf}
          className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded bg-gray-800 text-white hover:bg-gray-900 disabled:opacity-50 dark:bg-gray-700 ml-auto"
        >
          <FileText size={16} />
          {f.gerandoPdf ? 'Gerando...' : f.grupoFiltroRelatorio ? 'PDF do grupo' : 'PDF geral'}
        </button>
      </div>
    </>
  );
}
