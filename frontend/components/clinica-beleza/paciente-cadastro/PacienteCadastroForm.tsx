"use client";

import { ArrowLeft, Loader2, Save } from "lucide-react";
import { ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { PacienteDadosPessoaisSection } from "./PacienteDadosPessoaisSection";
import { PacienteEnderecoSection } from "./PacienteEnderecoSection";
import type { PacienteCadastroFormProps } from "./paciente-cadastro-types";

export type { PacienteFormState, PacienteCadastroFormProps } from "./paciente-cadastro-types";
export { PACIENTE_EMPTY_FORM } from "./paciente-cadastro-types";

export function PacienteCadastroForm({
  editing,
  form,
  setForm,
  error,
  saving,
  convenios,
  buscarCepLoading,
  onCepChange,
  onBuscarCep,
  onSave,
  onCancel,
  accentColor = 'var(--cb-primary, #8B3D52)',
  lojaSlug,
  showHeader = true,
}: PacienteCadastroFormProps) {
  const onChange = (patch: Partial<typeof form>) => setForm((f) => ({ ...f, ...patch }));

  return (
    <div className="flex flex-col flex-1 min-h-0 w-full">
      {showHeader && (
        <div className="flex items-center justify-between gap-3 px-4 md:px-8 py-3 border-b border-gray-200 dark:border-neutral-800 shrink-0">
          <button
            type="button"
            onClick={onCancel}
            className="inline-flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
          >
            <ArrowLeft size={16} />
            Voltar à lista
          </button>
          <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">
            {editing ? "Editar cliente" : "Novo cliente"}
          </span>
          <div className="w-[100px]" aria-hidden />
        </div>
      )}

      <div className="flex-1 min-h-0 overflow-y-auto p-4 md:p-6 lg:p-8 bg-[var(--cb-page-bg,#f7f2f4)] dark:bg-gray-950">
        {error && (
          <div className="mb-5 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
            {error}
          </div>
        )}

        <ClinicaBelezaPanel className="p-5 md:p-6 lg:p-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10 xl:gap-14 w-full max-w-none">
            <PacienteDadosPessoaisSection
              form={form}
              convenios={convenios}
              saving={saving}
              accentColor={accentColor}
              lojaSlug={lojaSlug}
              onChange={onChange}
            />
            <PacienteEnderecoSection
              form={form}
              buscarCepLoading={buscarCepLoading}
              accentColor={accentColor}
              onChange={onChange}
              onCepChange={onCepChange}
              onBuscarCep={onBuscarCep}
            />
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
            {saving ? "Salvando..." : editing ? "Salvar alterações" : "Cadastrar cliente"}
          </button>
        </div>
      </div>
    </div>
  );
}
