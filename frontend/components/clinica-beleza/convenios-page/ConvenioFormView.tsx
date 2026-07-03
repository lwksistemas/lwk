"use client";

import { ArrowLeft, Save } from "lucide-react";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { toUpperCase } from "@/lib/format-br";

interface ConvenioFormViewProps {
  basePath: string;
  novoNome: string;
  erro: string;
  salvando: boolean;
  onNomeChange: (value: string) => void;
  onVoltar: () => void;
  onSalvar: () => void;
}

export function ConvenioFormView({
  basePath,
  novoNome,
  erro,
  salvando,
  onNomeChange,
  onVoltar,
  onSalvar,
}: ConvenioFormViewProps) {
  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Novo convênio"
        subtitle="Informe o nome; o código será gerado automaticamente"
        backHref={basePath}
      />
      <ClinicaBelezaPageContent className="flex flex-col flex-1 !p-0">
        <div className="px-4 md:px-6 lg:px-8 pt-2 pb-3 border-b border-gray-200 dark:border-neutral-800 bg-white/80 dark:bg-neutral-900/80">
          <button
            type="button"
            onClick={onVoltar}
            className="inline-flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
          >
            <ArrowLeft size={16} />
            Voltar à lista
          </button>
        </div>
        <div className="flex-1 p-4 md:p-6 lg:p-8 w-full">
          <ClinicaBelezaPanel className="p-5 md:p-8 max-w-lg">
            {erro && (
              <div className="mb-5 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
                {erro}
              </div>
            )}
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Nome do convênio *
            </label>
            <input
              type="text"
              value={novoNome}
              onChange={(e) => onNomeChange(toUpperCase(e.target.value))}
              placeholder="Ex.: Unimed, Particular, Santa Casa..."
              autoFocus
              className="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-700 mb-6"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-6">
              Os valores praticados por convênio são definidos na página de Procedimentos.
            </p>
            <div className="flex flex-col-reverse sm:flex-row gap-3 pt-4 border-t border-gray-100 dark:border-neutral-700">
              <button
                type="button"
                onClick={onVoltar}
                className="flex-1 sm:flex-none py-2.5 px-6 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={onSalvar}
                disabled={salvando || !novoNome.trim()}
                className="flex-1 sm:flex-none flex items-center justify-center gap-2 py-2.5 px-6 rounded-lg text-white text-sm font-medium disabled:opacity-50"
                style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
              >
                <Save size={16} />
                {salvando ? "Criando..." : "Criar convênio"}
              </button>
            </div>
          </ClinicaBelezaPanel>
        </div>
      </ClinicaBelezaPageContent>
    </>
  );
}
