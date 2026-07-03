'use client';

import { useState } from 'react';
import { Plus } from 'lucide-react';
import { useCrmFinanceiroPage } from '@/hooks/crm-vendas/useCrmFinanceiroPage';
import type { TipoFinanceiro } from '@/lib/crm-financeiro-types';
import {
  CrmFinanceiroGruposTable,
  CrmFinanceiroLancamentosTable,
  CrmFinanceiroResumoCards,
  CrmFinanceiroResumoPorGrupo,
} from '@/components/crm-vendas/financeiro/CrmFinanceiroTables';
import { CrmFinanceiroToolbar } from '@/components/crm-vendas/financeiro/CrmFinanceiroToolbar';
import { CrmFinanceiroPageModals } from '@/components/crm-vendas/financeiro/CrmFinanceiroPageModals';
import { formatCurrency } from '@/lib/financeiro-helpers';
import { prepararLancamentosParaTabela } from '@/lib/crm-financeiro-display';

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
  const lancamentosBrutos = tipoAtivo === 'despesa' ? f.lancamentosDespesa : f.lancamentosReceita;
  const lancamentos =
    tipoAtivo === 'receita' ? prepararLancamentosParaTabela(lancamentosBrutos) : lancamentosBrutos;
  const gruposTipo = f.grupos.filter((g) => g.tipo === tipoAtivo && g.is_active);
  const gruposModal = f.grupos.filter((g) => g.tipo === f.modalTipo && g.is_active);
  const totalPago = f.resumo ? cfg.totalPago(f.resumo) : 0;
  const totalPendente = f.resumo ? cfg.totalPendente(f.resumo) : 0;

  const selecionarTipo = (tipo: TipoFinanceiro) => {
    setTipoAtivo(tipo);
    f.setGrupoFiltroRelatorio('');
  };

  return (
    <div className="w-full flex flex-col flex-1 min-h-0 gap-4 -m-2 sm:-m-4 lg:-m-6 p-2 sm:p-4 lg:p-6">
      <CrmFinanceiroToolbar f={f} tipoAtivo={tipoAtivo} gruposTipo={gruposTipo} />

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
          itens={lancamentosBrutos}
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

      <CrmFinanceiroPageModals f={f} tipoAtivo={tipoAtivo} gruposModal={gruposModal} />
    </div>
  );
}
