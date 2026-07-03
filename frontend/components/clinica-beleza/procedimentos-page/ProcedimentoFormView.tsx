"use client";

import { Loader2, Save, Stethoscope } from "lucide-react";
import { entityName } from "@/lib/clinica-beleza-entities";
import type { ConvenioItem } from "@/lib/clinica-beleza-api";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { ProcedimentoDadosFields } from "./ProcedimentoDadosFields";
import { ProcedimentoPrecosFields, ProcedimentoTermoFields } from "./ProcedimentoTermoPrecosFields";
import type { Procedure, ProcedimentoFormState } from "./procedimentos-page-types";

interface ProcedimentoFormViewProps {
  editing: Procedure | null;
  form: ProcedimentoFormState;
  convenios: ConvenioItem[];
  precosConvenio: Record<number, string>;
  error: string;
  saving: boolean;
  accentColor: string;
  onFormChange: (patch: Partial<ProcedimentoFormState>) => void;
  onPrecoChange: (convenioId: number, value: string) => void;
  onCancel: () => void;
  onSave: () => void;
}

export function ProcedimentoFormView({
  editing,
  form,
  convenios,
  precosConvenio,
  error,
  saving,
  accentColor,
  onFormChange,
  onPrecoChange,
  onCancel,
  onSave,
}: ProcedimentoFormViewProps) {
  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={editing ? "Editar procedimento" : "Novo procedimento"}
        subtitle={editing ? entityName(editing) : "Cadastro de procedimento da clínica"}
        onBack={onCancel}
        icon={Stethoscope}
      />
      <ClinicaBelezaPageContent className="flex flex-col flex-1 min-h-0 !p-0 !bg-[#f7f2f4] dark:!bg-gray-950">
        <div className="flex flex-col flex-1 min-h-0 w-full">
          <div className="flex-1 min-h-0 overflow-y-auto p-4 md:p-6 lg:p-8 bg-[#f7f2f4] dark:bg-gray-950">
            {error && (
              <div className="mb-5 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
                {error}
              </div>
            )}

            <ClinicaBelezaPanel className="p-5 md:p-6 lg:p-8">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10 xl:gap-14 w-full max-w-none">
                <ProcedimentoDadosFields form={form} onChange={onFormChange} />
                <div className="space-y-6">
                  <ProcedimentoTermoFields form={form} accentColor={accentColor} onChange={onFormChange} />
                  <ProcedimentoPrecosFields
                    convenios={convenios}
                    precosConvenio={precosConvenio}
                    onPrecoChange={onPrecoChange}
                  />
                </div>
              </div>
            </ClinicaBelezaPanel>
          </div>

          <div className="shrink-0 border-t border-gray-200 dark:border-neutral-700 bg-white/80 dark:bg-neutral-800/80 px-4 md:px-6 lg:px-8 py-4">
            <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-3 w-full">
              <button
                type="button"
                onClick={onCancel}
                className="sm:min-w-[120px] py-2.5 px-5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-neutral-800"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={onSave}
                disabled={saving}
                className="sm:min-w-[180px] flex items-center justify-center gap-2 py-2.5 px-5 rounded-lg text-white text-sm font-medium disabled:opacity-60"
                style={{ backgroundColor: accentColor }}
              >
                {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
                {saving ? "Salvando..." : editing ? "Salvar alterações" : "Cadastrar procedimento"}
              </button>
            </div>
          </div>
        </div>
      </ClinicaBelezaPageContent>
    </>
  );
}
