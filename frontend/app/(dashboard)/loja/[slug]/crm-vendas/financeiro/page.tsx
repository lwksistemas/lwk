'use client';

import { useState } from 'react';
import { RefreshCw, Plus, FileText, Download, FolderOpen } from 'lucide-react';
import { useCrmFinanceiroPage } from '@/hooks/crm-vendas/useCrmFinanceiroPage';
import type { TipoFinanceiro } from '@/hooks/crm-vendas/useCrmFinanceiroPage';
import {
  CrmFinanceiroGruposTable,
  CrmFinanceiroLancamentosTable,
  CrmFinanceiroResumoCards,
  CrmFinanceiroResumoPorGrupo,
} from '@/components/crm-vendas/financeiro/CrmFinanceiroTables';
import { CrmGrupoModal, CrmLancamentoModal } from '@/components/crm-vendas/financeiro/CrmFinanceiroModals';
import { formatCurrency } from '@/lib/financeiro-helpers';

const TIPO_CONFIG: Record<
  TipoFinanceiro,
  {
    titulo: string;
    subtitulo: string;
    corHeader: string;
    corTabAtiva: string;
    totalPago: (r: NonNullable<ReturnType<typeof useCrmFinanceiroPage>['resumo']>) => number;
    totalPendente: (r: NonNullable<ReturnType<typeof useCrmFinanceiroPage>['resumo']>) => number;
  }
> = {
  despesa: {
    titulo: 'Despesas',
    subtitulo: 'Saídas do vendedor',
    corHeader: 'bg-red-50 dark:bg-red-950/30 border-red-100 dark:border-red-900/40',
    corTabAtiva: 'bg-red-600 text-white border-red-600',
    totalPago: (r) => r.despesas_pagas,
    totalPendente: (r) => r.despesas_pendentes,
  },
  receita: {
    titulo: 'Receitas',
    subtitulo: 'Entradas e comissões',
    corHeader: 'bg-green-50 dark:bg-green-950/30 border-green-100 dark:border-green-900/40',
    corTabAtiva: 'bg-green-600 text-white border-green-600',
    totalPago: (r) => r.receitas_pagas,
    totalPendente: (r) => r.receitas_pendentes,
  },
};

export default function CrmFinanceiroPage() {
  const f = useCrmFinanceiroPage();
  const [tipoAtivo, setTipoAtivo] = useState<TipoFinanceiro>('despesa');
  const showVendedorCol = f.isAdmin && !f.vendedorFiltro;

  const cfg = TIPO_CONFIG[tipoAtivo];
  const lancamentos = tipoAtivo === 'despesa' ? f.lancamentosDespesa : f.lancamentosReceita;
  const gruposTipo = f.grupos.filter((g) => g.tipo === tipoAtivo && g.is_active);
  const totalPago = f.resumo ? cfg.totalPago(f.resumo) : 0;
  const totalPendente = f.resumo ? cfg.totalPendente(f.resumo) : 0;

  const selecionarTipo = (tipo: TipoFinanceiro) => {
    setTipoAtivo(tipo);
    f.setGrupoFiltroRelatorio('');
  };

  return (
    <div className="w-full flex flex-col flex-1 min-h-0 gap-4 -m-2 sm:-m-4 lg:-m-6 p-2 sm:p-4 lg:p-6">
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
        <div>
          <label className="block text-xs text-gray-500 mb-1">Grupo (relatório)</label>
          <select
            value={f.grupoFiltroRelatorio}
            onChange={(e) => f.setGrupoFiltroRelatorio(e.target.value)}
            className="rounded border px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700 min-w-[160px]"
          >
            <option value="">Todos os grupos</option>
            {gruposTipo.map((g) => (
              <option key={g.id} value={g.id}>{g.nome}</option>
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

      <div className="flex gap-2 shrink-0">
        {(['despesa', 'receita'] as const).map((tipo) => {
          const tab = TIPO_CONFIG[tipo];
          const ativo = tipoAtivo === tipo;
          return (
            <button
              key={tipo}
              type="button"
              onClick={() => selecionarTipo(tipo)}
              className={`px-5 py-2.5 text-sm font-semibold rounded-lg border transition-colors ${
                ativo
                  ? tab.corTabAtiva
                  : 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
              }`}
            >
              {tab.titulo}
            </button>
          );
        })}
      </div>

      <section className="shrink-0 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <h3 className="font-semibold text-gray-900 dark:text-white">
            Relatório por grupo — {cfg.titulo.toLowerCase()}
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Totais no período selecionado · clique em PDF para baixar por grupo
          </p>
        </div>
        <CrmFinanceiroResumoPorGrupo
          itens={lancamentos}
          tipo={tipoAtivo}
          gerandoPdf={f.gerandoPdf}
          onGerarPdfGrupo={(grupoId) => f.gerarRelatorioPdf(grupoId)}
        />
      </section>

      <section className="flex flex-col flex-1 min-h-[min(70vh,720px)] rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-sm overflow-hidden">
        <header className={`flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-b ${cfg.corHeader}`}>
          <div>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">{cfg.titulo}</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {cfg.subtitulo} · Pago {formatCurrency(totalPago)} · Pendente {formatCurrency(totalPendente)}
            </p>
          </div>
          <button
            type="button"
            onClick={() => f.abrirNovo(tipoAtivo)}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-[#0176d3] text-white hover:bg-[#0159a8] shadow-sm"
          >
            <Plus size={16} />
            Novo
          </button>
        </header>
        <div className="flex-1 min-h-0 overflow-y-auto p-3 sm:p-4">
          <CrmFinanceiroLancamentosTable
            itens={lancamentos}
            tipo={tipoAtivo}
            showVendedor={showVendedorCol}
            onEdit={f.editar}
            onPagar={f.marcarPago}
            onRemove={f.removerLancamento}
          />
        </div>
      </section>

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
        tipoInicial={tipoAtivo}
        saving={f.saving}
        onClose={() => f.setShowGrupoModal(false)}
        onSave={f.salvarGrupo}
      />
    </div>
  );
}
