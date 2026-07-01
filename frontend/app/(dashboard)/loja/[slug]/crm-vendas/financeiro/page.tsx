'use client';

import { RefreshCw, Plus, FileText, Download, FolderOpen } from 'lucide-react';
import { useCrmFinanceiroPage } from '@/hooks/crm-vendas/useCrmFinanceiroPage';
import {
  CrmFinanceiroGruposTable,
  CrmFinanceiroLancamentosTable,
  CrmFinanceiroResumoCards,
} from '@/components/crm-vendas/financeiro/CrmFinanceiroTables';
import { CrmGrupoModal, CrmLancamentoModal } from '@/components/crm-vendas/financeiro/CrmFinanceiroModals';
import { formatCurrency } from '@/lib/financeiro-helpers';

function ColunaFinanceiro({
  titulo,
  subtitulo,
  corHeader,
  totalPendente,
  totalPago,
  onNovo,
  children,
}: {
  titulo: string;
  subtitulo: string;
  corHeader: string;
  totalPendente: number;
  totalPago: number;
  onNovo: () => void;
  children: React.ReactNode;
}) {
  return (
    <section className="flex flex-col min-h-0 h-full rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-sm overflow-hidden">
      <header className={`flex flex-wrap items-center justify-between gap-2 px-4 py-3 border-b ${corHeader}`}>
        <div>
          <h2 className="text-base font-bold text-gray-900 dark:text-white">{titulo}</h2>
          <p className="text-xs text-gray-600 dark:text-gray-400">
            {subtitulo} · Pago {formatCurrency(totalPago)} · Pendente {formatCurrency(totalPendente)}
          </p>
        </div>
        <button
          type="button"
          onClick={onNovo}
          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded bg-white/90 dark:bg-gray-800 border border-gray-200 dark:border-gray-600 hover:bg-white dark:hover:bg-gray-700 shadow-sm"
        >
          <Plus size={14} />
          Novo
        </button>
      </header>
      <div className="flex-1 min-h-0 overflow-y-auto p-2 sm:p-3">{children}</div>
    </section>
  );
}

export default function CrmFinanceiroPage() {
  const f = useCrmFinanceiroPage();
  const showVendedorCol = f.isAdmin && !f.vendedorFiltro;

  return (
    <div className="w-full flex flex-col flex-1 min-h-0 gap-4 -m-2 sm:-m-4 lg:-m-6 p-2 sm:p-4 lg:p-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 shrink-0">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">Financeiro do vendedor</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Despesas e receitas lado a lado — visão completa da tela
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
                <option key={v.id} value={v.id}>{v.nome}</option>
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
              <input type="date" value={f.dataInicioRel} onChange={(e) => f.setDataInicioRel(e.target.value)} className="rounded border px-2 py-1.5 text-sm dark:bg-gray-800" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Até</label>
              <input type="date" value={f.dataFimRel} onChange={(e) => f.setDataFimRel(e.target.value)} className="rounded border px-2 py-1.5 text-sm dark:bg-gray-800" />
            </div>
          </>
        )}
        <button
          type="button"
          onClick={f.gerarRelatorioPdf}
          disabled={f.gerandoPdf}
          className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded bg-gray-800 text-white hover:bg-gray-900 disabled:opacity-50 dark:bg-gray-700 ml-auto"
        >
          <FileText size={16} />
          {f.gerandoPdf ? 'Gerando...' : 'PDF'}
        </button>
      </div>

      <div className="shrink-0">
        <CrmFinanceiroResumoCards resumo={f.resumo} loading={f.loading} />
      </div>

      {f.showGrupos && f.isAdmin && (
        <div className="shrink-0 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900 dark:text-white">Grupos de receitas e despesas</h3>
            <button
              type="button"
              onClick={() => {
                f.setEditingGrupo(null);
                f.setShowGrupoModal(true);
              }}
              className="inline-flex items-center gap-1 px-3 py-1.5 text-xs rounded bg-[#0176d3] text-white"
            >
              <Plus size={14} />
              Novo grupo
            </button>
          </div>
          <CrmFinanceiroGruposTable
            grupos={f.grupos}
            isAdmin={f.isAdmin}
            onEdit={(g) => {
              f.setEditingGrupo(g);
              f.setShowGrupoModal(true);
            }}
            onRemove={f.removerGrupo}
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 min-h-[min(70vh,720px)]">
        <ColunaFinanceiro
          titulo="Despesas"
          subtitulo="Saídas do vendedor"
          corHeader="bg-red-50 dark:bg-red-950/30 border-red-100 dark:border-red-900/40"
          totalPago={f.resumo?.despesas_pagas ?? 0}
          totalPendente={f.resumo?.despesas_pendentes ?? 0}
          onNovo={() => f.abrirNovo('despesa')}
        >
          <CrmFinanceiroLancamentosTable
            itens={f.lancamentosDespesa}
            tipo="despesa"
            compact
            showVendedor={showVendedorCol}
            onEdit={f.editar}
            onPagar={f.marcarPago}
            onRemove={f.removerLancamento}
          />
        </ColunaFinanceiro>

        <ColunaFinanceiro
          titulo="Receitas"
          subtitulo="Entradas e comissões"
          corHeader="bg-green-50 dark:bg-green-950/30 border-green-100 dark:border-green-900/40"
          totalPago={f.resumo?.receitas_pagas ?? 0}
          totalPendente={f.resumo?.receitas_pendentes ?? 0}
          onNovo={() => f.abrirNovo('receita')}
        >
          <CrmFinanceiroLancamentosTable
            itens={f.lancamentosReceita}
            tipo="receita"
            compact
            showVendedor={showVendedorCol}
            onEdit={f.editar}
            onPagar={f.marcarPago}
            onRemove={f.removerLancamento}
          />
        </ColunaFinanceiro>
      </div>

      <CrmLancamentoModal
        open={f.showModal}
        tipo={f.modalTipo}
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
