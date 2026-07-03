"use client";

import { ArrowLeft, Megaphone, Save } from "lucide-react";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { CampanhaFormFields } from "./CampanhaFormFields";
import type { Campanha, CampanhaFormState } from "./campanhas-page-types";

interface CampanhaFormViewProps {
  basePath: string;
  editing: Campanha | null;
  form: CampanhaFormState;
  error: string;
  saving: boolean;
  onFormChange: (patch: Partial<CampanhaFormState>) => void;
  onCancel: () => void;
  onSave: () => void;
}

export function CampanhaFormView({
  basePath,
  editing,
  form,
  error,
  saving,
  onFormChange,
  onCancel,
  onSave,
}: CampanhaFormViewProps) {
  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={editing ? "Editar campanha" : "Nova campanha"}
        subtitle={editing ? editing.titulo : "Crie promoções para enviar por WhatsApp"}
        backHref={basePath}
        icon={Megaphone}
      />
      <ClinicaBelezaPageContent>
        <ClinicaBelezaPanel className="p-6 md:p-8 max-w-2xl">
          {error && (
            <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg mb-4">
              {error}
            </p>
          )}
          <CampanhaFormFields form={form} onChange={onFormChange} />
          <div className="flex gap-3 mt-8 pt-6 border-t border-gray-200 dark:border-neutral-700">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium"
            >
              <ArrowLeft size={16} />
              Cancelar
            </button>
            <button
              type="button"
              onClick={onSave}
              disabled={saving}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-white text-sm font-medium disabled:opacity-50"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              <Save size={16} />
              {saving ? "Salvando..." : "Salvar"}
            </button>
          </div>
        </ClinicaBelezaPanel>
      </ClinicaBelezaPageContent>
    </>
  );
}
