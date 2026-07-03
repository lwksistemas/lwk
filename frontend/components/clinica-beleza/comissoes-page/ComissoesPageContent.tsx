"use client";

import { Download, Printer, Search } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { formatRelatorioCurrency } from "@/components/clinica-beleza/relatorios-shared/relatorios-shared-utils";
import { ComissoesBlocoProfissional } from "./ComissoesBlocoProfissional";
import { useComissoesPage } from "./useComissoesPage";

export function ComissoesPageContent() {
  const {
    slug,
    dataInicio,
    setDataInicio,
    dataFim,
    setDataFim,
    professionalId,
    setProfessionalId,
    professionals,
    profissionalNome,
    data,
    loading,
    error,
    logoUrl,
    clinicaNome,
    temTimbrado,
    pdfLoading,
    buscar,
    exportarCSV,
    exportarPDF,
  } = useComissoesPage();

  const formatCurrency = formatRelatorioCurrency;

  const exportActions = (
    <>
      <button
        type="button"
        onClick={exportarCSV}
        disabled={!data?.profissionais.length}
        className="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 text-xs sm:text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 disabled:opacity-50"
      >
        <Download size={16} />
        <span className="hidden sm:inline">CSV</span>
      </button>
      <button
        type="button"
        onClick={() => void exportarPDF()}
        disabled={!data?.profissionais.length || pdfLoading}
        className="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 text-xs sm:text-sm font-medium rounded-lg text-white disabled:opacity-50"
        style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
        title={
          !logoUrl && temTimbrado
            ? "PDF com papel timbrado (Configurações → Memed). Para imprimir, use o visualizador do PDF."
            : "Baixar relatório em PDF. Para imprimir, use o visualizador do PDF."
        }
      >
        <Printer size={16} />
        <span className="hidden sm:inline">{pdfLoading ? "Gerando…" : "PDF"}</span>
        <span className="sm:hidden">{pdfLoading ? "…" : "PDF"}</span>
      </button>
    </>
  );

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Comissões dos Profissionais"
        subtitle="Consultas, procedimentos e total em sequência"
        backHref={`/loja/${slug}/relatorios`}
        extraActions={exportActions}
      />
      <ClinicaBelezaPageContent className="print-area">
        <div className="hidden print:block mb-6 text-center">
          {logoUrl ? (
            <div className="flex justify-center mb-4">
              <img src={logoUrl} alt={clinicaNome} className="max-h-20 object-contain" />
            </div>
          ) : clinicaNome ? (
            <p className="text-lg font-bold text-gray-800 mb-2">{clinicaNome}</p>
          ) : null}
          <h1 className="text-2xl font-bold" style={{ color: CLINICA_BELEZA_PRIMARY }}>
            Relatório de Comissões
          </h1>
          {profissionalNome && (
            <p className="text-base font-semibold text-gray-800 mt-2">Profissional: {profissionalNome}</p>
          )}
          <p className="text-sm text-gray-600 mt-1">
            Período: {dataInicio} a {dataFim}
          </p>
        </div>

        <ClinicaBelezaPanel className="p-4 mb-6 no-print">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Data Início</label>
              <input
                type="date"
                value={dataInicio}
                onChange={(e) => setDataInicio(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Data Fim</label>
              <input
                type="date"
                value={dataFim}
                onChange={(e) => setDataFim(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Profissional</label>
              <select
                value={professionalId}
                onChange={(e) => setProfessionalId(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Todos</option>
                {professionals.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nome}
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={() => void buscar()}
              disabled={loading}
              className="w-full inline-flex items-center justify-center gap-1.5 px-4 py-2 min-h-[40px] text-sm font-medium rounded-lg text-white"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              <Search size={16} /> Buscar
            </button>
          </div>
        </ClinicaBelezaPanel>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 text-sm">
            {error}
          </div>
        )}

        {loading && (
          <div className="flex justify-center py-12">
            <div className="w-10 h-10 border-4 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {!loading && data && (
          <div className="space-y-6">
            {data.profissionais.length === 0 ? (
              <p className="text-center py-12 text-gray-500">Nenhum dado no período.</p>
            ) : (
              <>
                {data.profissionais.map((p) => (
                  <ComissoesBlocoProfissional key={p.professional_id} p={p} />
                ))}

                {data.profissionais.length > 1 && (
                  <div
                    className="rounded-xl border-2 border-gray-300 dark:border-gray-600 p-4"
                    style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}08` }}
                  >
                    <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                      Totais do período
                    </p>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-xs text-gray-500 uppercase">Valor consulta</p>
                        <p className="text-lg font-bold tabular-nums">{formatCurrency(data.totais.valor_consulta)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 uppercase">Comissão consulta</p>
                        <p className="text-lg font-bold tabular-nums">{formatCurrency(data.totais.comissao_consulta)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 uppercase">Valor procedimentos</p>
                        <p className="text-lg font-bold tabular-nums">{formatCurrency(data.totais.valor_procedimento)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 uppercase">Comissão procedimentos</p>
                        <p className="text-lg font-bold tabular-nums">{formatCurrency(data.totais.comissao_procedimento)}</p>
                      </div>
                    </div>
                    <div className="mt-4 pt-4 border-t border-gray-300 dark:border-gray-600 flex flex-wrap justify-end items-end gap-x-10 gap-y-2">
                      <div className="text-right">
                        <p className="text-xs text-gray-500 uppercase">Comissão total</p>
                        <p className="text-xl font-bold tabular-nums" style={{ color: CLINICA_BELEZA_PRIMARY }}>
                          {formatCurrency(data.totais.comissao_total)}
                        </p>
                      </div>
                      <div className="text-right pl-6 border-l-2 border-gray-400 dark:border-gray-500">
                        <p className="text-xs text-gray-500 uppercase">Valor total</p>
                        <p className="text-2xl font-bold tabular-nums text-gray-900 dark:text-white">
                          {formatCurrency(data.totais.valor_total)}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </ClinicaBelezaPageContent>
    </>
  );
}
