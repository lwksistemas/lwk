'use client';

import Link from 'next/link';
import { DollarSign, LayoutDashboard, LayoutGrid, List, Plus, Printer } from 'lucide-react';
import PipelineBoard from '@/components/crm-vendas/PipelineBoard';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import ModalCriarOportunidade from './components/ModalCriarOportunidade';
import ModalEditarOportunidade from './components/ModalEditarOportunidade';
import { useCrmPipelinePage } from '@/hooks/crm-vendas/useCrmPipelinePage';
import { CRM_PERIODO_PIPELINE } from '@/lib/crm-periodos';

export default function CrmVendasPipelinePage() {
  const { etapasAtivas } = useCRMConfig();
  const {
    slug,
    oportunidades,
    loading,
    error,
    oportunidadeEditar,
    setOportunidadeEditar,
    modalCriar,
    setModalCriar,
    initialLeadId,
    viewPipeline,
    setViewPipeline,
    filtroEtapaPipeline,
    setFiltroEtapaPipeline,
    filtroVendedor,
    setFiltroVendedor,
    vendedores,
    periodoPipeline,
    selecionarPeriodoPipeline,
    dataInicio,
    setDataInicio,
    dataFim,
    setDataFim,
    limparPeriodoPipeline,
    imprimindo,
    oportunidadesBase,
    oportunidadesFiltradas,
    handleAbrirCriar,
    handleCardClick,
    handleExportarPDF,
    handleModalSuccess,
    handleEtapaChange,
  } = useCrmPipelinePage();

  return (
    <div className="space-y-8">
      {error && (
        <div className="rounded-xl bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">
          {error}
        </div>
      )}
      <div className="flex flex-wrap items-center justify-between gap-4 print:hidden">
        <h1 className="text-3xl font-semibold text-gray-800 dark:text-white flex items-center gap-2">
          <DollarSign className="w-8 h-8" />
          Pipeline de vendas
        </h1>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handleAbrirCriar}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 transition text-sm font-medium"
          >
            <Plus size={18} />
            Nova oportunidade
          </button>
          <Link
            href={`/loja/${slug}/crm-vendas/leads`}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 transition text-sm font-medium"
          >
            Ver Leads
          </Link>
          <Link
            href={`/loja/${slug}/crm-vendas`}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 transition text-sm font-medium"
          >
            <LayoutDashboard size={18} />
            Ver Dashboard
          </Link>
        </div>
      </div>
      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-200 dark:border-slate-700 shadow-sm p-6 hover:shadow-md hover:border-blue-100 dark:hover:border-slate-600 transition-all space-y-4 print:shadow-none print:border-gray-300">
        <div className="flex flex-col gap-3 print:hidden">
          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
            <div className="inline-flex rounded-lg border border-gray-200 dark:border-gray-600 p-0.5 bg-gray-50 dark:bg-gray-800/80">
              <button
                type="button"
                onClick={() => setViewPipeline('board')}
                className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition ${
                  viewPipeline === 'board'
                    ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                <LayoutGrid size={16} aria-hidden />
                Quadro
              </button>
              <button
                type="button"
                onClick={() => setViewPipeline('list')}
                className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition ${
                  viewPipeline === 'list'
                    ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                <List size={16} aria-hidden />
                Lista
              </button>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <label htmlFor="filtro-etapa-pipeline" className="text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap">
                Etapa:
              </label>
              <select
                id="filtro-etapa-pipeline"
                value={filtroEtapaPipeline}
                onChange={(e) => setFiltroEtapaPipeline(e.target.value)}
                className="min-w-[12rem] px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
              >
                <option value="">Todos ({oportunidadesBase.length})</option>
                {etapasAtivas().map((et) => {
                  const count = oportunidadesBase.filter((o) => o.etapa === et.key).length;
                  return (
                    <option key={et.key} value={et.key}>
                      {et.label} — {count} {count === 1 ? 'oportunidade' : 'oportunidades'}
                    </option>
                  );
                })}
              </select>
              {vendedores.length > 0 && (
                <>
                  <label htmlFor="filtro-vendedor-pipeline" className="text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap ml-2">
                    Vendedor:
                  </label>
                  <select
                    id="filtro-vendedor-pipeline"
                    value={filtroVendedor}
                    onChange={(e) => setFiltroVendedor(e.target.value)}
                    className="min-w-[12rem] px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                  >
                    <option value="">Todos</option>
                    {vendedores.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.nome}
                      </option>
                    ))}
                  </select>
                </>
              )}
            </div>
          </div>

          <div className="flex flex-wrap items-end gap-3">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300 pb-2 shrink-0">
              Período:
            </span>
            <div className="flex flex-col gap-0.5 min-w-0">
              <label htmlFor="periodo-pipeline" className="text-xs text-gray-500 dark:text-gray-400">
                Preset
              </label>
              <select
                id="periodo-pipeline"
                value={periodoPipeline}
                onChange={(e) => selecionarPeriodoPipeline(e.target.value)}
                className="min-w-[11rem] px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
              >
                {CRM_PERIODO_PIPELINE.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-0.5 min-w-0">
              <label htmlFor="data-inicio" className="text-xs text-gray-500 dark:text-gray-400">
                Data início
              </label>
              <input
                id="data-inicio"
                type="date"
                value={dataInicio}
                onChange={(e) => setDataInicio(e.target.value)}
                className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
              />
            </div>
            <span className="text-sm text-gray-500 dark:text-gray-400 pb-2 shrink-0">até</span>
            <div className="flex flex-col gap-0.5 min-w-0">
              <label htmlFor="data-fim" className="text-xs text-gray-500 dark:text-gray-400">
                Data fim
              </label>
              <input
                id="data-fim"
                type="date"
                value={dataFim}
                onChange={(e) => setDataFim(e.target.value)}
                className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
              />
            </div>
            {periodoPipeline !== 'mes_atual' && (
              <button
                type="button"
                onClick={limparPeriodoPipeline}
                className="text-sm text-red-600 dark:text-red-400 hover:underline pb-2"
              >
                Restaurar mês atual
              </button>
            )}
            <button
              type="button"
              onClick={handleExportarPDF}
              disabled={imprimindo}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition text-sm font-medium ml-auto"
            >
              <Printer className="w-4 h-4" aria-hidden />
              {imprimindo ? 'Preparando...' : 'Imprimir / PDF'}
            </button>
          </div>
        </div>
        <div className="hidden print:block mb-4 pb-3 border-b border-gray-200 text-gray-900">
          <p className="text-lg font-semibold">Pipeline de vendas</p>
          {filtroVendedor && (
            <p className="text-sm text-gray-600 mt-1">
              Vendedor: {vendedores.find((v) => String(v.id) === filtroVendedor)?.nome || filtroVendedor}
            </p>
          )}
          {(dataInicio || dataFim) && (
            <p className="text-sm text-gray-600 mt-1">
              Período: {dataInicio ? new Date(dataInicio + 'T12:00:00').toLocaleDateString('pt-BR') : '—'} até{' '}
              {dataFim ? new Date(dataFim + 'T12:00:00').toLocaleDateString('pt-BR') : '—'}
            </p>
          )}
        </div>
        <PipelineBoard
          oportunidades={oportunidadesFiltradas}
          loading={loading && oportunidades.length === 0}
          etapas={etapasAtivas()}
          onCardClick={handleCardClick}
          onEtapaChange={handleEtapaChange}
          viewMode={viewPipeline}
          filtroEtapa={filtroEtapaPipeline}
        />
      </div>

      <ModalCriarOportunidade
        open={modalCriar}
        onClose={() => setModalCriar(false)}
        onSuccess={handleModalSuccess}
        slug={slug}
        etapas={etapasAtivas()}
        initialLeadId={initialLeadId}
      />

      {oportunidadeEditar && (
        <ModalEditarOportunidade
          oportunidade={oportunidadeEditar}
          onClose={() => setOportunidadeEditar(null)}
          onSuccess={handleModalSuccess}
          slug={slug}
          etapas={etapasAtivas()}
        />
      )}
    </div>
  );
}
