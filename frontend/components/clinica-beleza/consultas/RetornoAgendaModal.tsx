"use client";

import { Loader2, RefreshCw, X } from "lucide-react";
import { RetornoConsultaSection } from "./retorno-agenda/RetornoConsultaSection";
import { RetornoProcedimentoSection } from "./retorno-agenda/RetornoProcedimentoSection";
import { useRetornoAgenda } from "./retorno-agenda/useRetornoAgenda";

interface RetornoAgendaModalProps {
  open: boolean;
  onClose: () => void;
}

export function RetornoAgendaModal({ open, onClose }: RetornoAgendaModalProps) {
  const {
    config,
    regras,
    loading,
    salvando,
    erro,
    novaRegraProc,
    novaRegraDias,
    proceduresDisponiveis,
    setNovaRegraProc,
    setNovaRegraDias,
    loadAll,
    salvarConfig,
    atualizarDiasConsultaLocal,
    salvarDiasConsulta,
    adicionarRegra,
    excluirRegra,
  } = useRetornoAgenda(open);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 p-0 sm:p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-t-xl sm:rounded-xl shadow-xl w-full max-w-lg sm:max-w-4xl sm:w-[calc(100vw-2rem)] max-h-[95vh] sm:max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-neutral-700 shrink-0">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Retorno gratuito</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Isenta a taxa de consulta (local de atendimento) dentro do prazo configurado
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={salvando}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800 text-gray-500"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-5">
          {erro && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
              {erro}
            </div>
          )}

          {loading ? (
            <div className="text-center py-10 text-gray-500">
              <Loader2 size={24} className="animate-spin mx-auto mb-2" />
              Carregando...
            </div>
          ) : config ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
              <RetornoConsultaSection
                config={config}
                salvando={salvando}
                onToggleAtivo={(ativo) => void salvarConfig({ retorno_consulta_ativo: ativo })}
                onChangeDias={atualizarDiasConsultaLocal}
                onBlurDias={salvarDiasConsulta}
              />
              <RetornoProcedimentoSection
                config={config}
                regras={regras}
                proceduresDisponiveis={proceduresDisponiveis}
                salvando={salvando}
                novaRegraProc={novaRegraProc}
                novaRegraDias={novaRegraDias}
                onToggleAtivo={(ativo) => void salvarConfig({ retorno_procedimento_ativo: ativo })}
                onNovaRegraProcChange={setNovaRegraProc}
                onNovaRegraDiasChange={setNovaRegraDias}
                onAdicionarRegra={() => void adicionarRegra()}
                onExcluirRegra={(id) => void excluirRegra(id)}
              />
            </div>
          ) : null}
        </div>

        <div className="px-6 py-4 border-t border-gray-200 dark:border-neutral-700 flex justify-between shrink-0">
          <button
            type="button"
            onClick={() => void loadAll()}
            disabled={loading || salvando}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800"
          >
            <RefreshCw size={14} />
            Atualizar
          </button>
          <button
            type="button"
            onClick={onClose}
            disabled={salvando}
            className="px-3 py-1.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}
