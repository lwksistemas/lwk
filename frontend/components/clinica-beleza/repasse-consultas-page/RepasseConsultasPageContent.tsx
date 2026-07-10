"use client";

import Link from "next/link";
import { ArrowLeft, Download, Search } from "lucide-react";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { formatRelatorioCurrency } from "@/components/clinica-beleza/relatorios-shared/relatorios-shared-utils";
import { RepasseCardAtendimento } from "./RepasseCardAtendimento";
import { useRepasseConsultasPage } from "./useRepasseConsultasPage";

export function RepasseConsultasPageContent() {
  const {
    slug,
    dataInicio,
    setDataInicio,
    dataFim,
    setDataFim,
    professionalId,
    setProfessionalId,
    professionals,
    data,
    loading,
    error,
    pdfLoading,
    buscar,
    exportarPDF,
  } = useRepasseConsultasPage();

  return (
    <ClinicaBelezaPageContent>
      <Link
        href={`/loja/${slug}/relatorios`}
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-4 no-print"
      >
        <ArrowLeft size={16} /> Voltar aos relatórios
      </Link>

      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Repasse por Consulta</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Cada atendimento com consulta e procedimentos — para o profissional apresentar à clínica.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void exportarPDF()}
          disabled={pdfLoading || !data?.profissionais.length}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-white text-sm font-medium disabled:opacity-50 shrink-0"
          style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
        >
          <Download size={16} />
          {pdfLoading ? "Gerando PDF…" : "PDF"}
        </button>
      </div>

      <ClinicaBelezaPanel className="p-4 md:p-5 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">De</label>
            <input
              type="date"
              value={dataInicio}
              onChange={(e) => setDataInicio(e.target.value)}
              className="w-full px-3 py-2 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Até</label>
            <input
              type="date"
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
              className="w-full px-3 py-2 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Profissional</label>
            <select
              value={professionalId}
              onChange={(e) => setProfessionalId(e.target.value)}
              className="w-full px-3 py-2 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
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
            type="button"
            onClick={() => void buscar()}
            disabled={loading}
            className="self-end w-full inline-flex items-center justify-center gap-1.5 px-4 py-2 min-h-[40px] text-sm font-medium rounded-lg text-white"
            style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
          >
            <Search size={16} /> Buscar
          </button>
        </div>
      </ClinicaBelezaPanel>

      {error && <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg mb-6 text-sm">{error}</div>}

      {loading && (
        <div className="flex justify-center py-12">
          <div className="w-10 h-10 border-4 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {!loading && data && (
        <div className="space-y-8">
          {data.profissionais.length === 0 ? (
            <p className="text-center py-12 text-gray-500">Nenhum atendimento pago no período.</p>
          ) : (
            data.profissionais.map((p) => (
              <section key={p.professional_id}>
                <h2 className="text-lg font-bold mb-4" style={{ color: 'var(--cb-primary, #8B3D52)' }}>
                  {p.nome}
                  <span className="text-sm font-normal text-gray-500 ml-2">
                    {p.total_atendimentos} atendimento(s) · Comissão {formatRelatorioCurrency(p.comissao_total)}
                  </span>
                </h2>
                <div className="grid grid-cols-1 2xl:grid-cols-2 gap-4">
                  {p.atendimentos.map((at) => (
                    <RepasseCardAtendimento key={at.appointment_id} at={at} />
                  ))}
                </div>
              </section>
            ))
          )}

          {data.profissionais.length > 1 && (
            <div
              className="rounded-xl border-2 border-gray-300 dark:border-gray-600 p-4"
              style={{ backgroundColor: 'color-mix(in srgb, var(--cb-primary, #8B3D52) 3%, transparent)' }}
            >
              <p className="text-sm font-semibold mb-2">Totais do período</p>
              <p className="text-lg font-bold tabular-nums">
                {data.totais.total_atendimentos} atendimentos · Comissão{" "}
                {formatRelatorioCurrency(data.totais.comissao_total)}
              </p>
            </div>
          )}
        </div>
      )}
    </ClinicaBelezaPageContent>
  );
}
