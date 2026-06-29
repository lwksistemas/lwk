"use client";

import { createPortal } from "react-dom";
import { ArrowLeft, CalendarDays, Loader2, Save } from "lucide-react";
import { ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { CriarAgendamentoAdvancedSection } from "@/components/clinica-beleza/criar-agendamento/CriarAgendamentoAdvancedSection";
import { CriarAgendamentoAgendaSection } from "@/components/clinica-beleza/criar-agendamento/CriarAgendamentoAgendaSection";
import { CriarAgendamentoClienteSection } from "@/components/clinica-beleza/criar-agendamento/CriarAgendamentoClienteSection";
import {
  type CriarAgendamentoProfessional,
  type ModalCriarAgendamentoMode,
} from "@/components/clinica-beleza/criar-agendamento/criar-agendamento-utils";
import type { PatientQuickOption } from "@/components/clinica-beleza/PatientQuickRegisterField";
import { useCriarAgendamento } from "@/hooks/clinica-beleza/useCriarAgendamento";
import type { ConsultaFormProcedure } from "@/hooks/clinica-beleza/useNovaConsultaForm";
import type { LocalAtendimentoItem, NomeAgendaItem } from "@/lib/clinica-beleza-api";

export type { ModalCriarAgendamentoMode };

interface ModalCriarAgendamentoProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  selectedDate: Date | null;
  mode?: ModalCriarAgendamentoMode;
  defaultProfessionalId?: string;
  professionals: CriarAgendamentoProfessional[];
  patients: PatientQuickOption[];
  procedures: ConsultaFormProcedure[];
  nomesAgenda: NomeAgendaItem[];
  locaisAtendimento: LocalAtendimentoItem[];
  onPatientsChange: (patients: PatientQuickOption[]) => void;
  onSearchPatients?: (query: string) => Promise<PatientQuickOption[]>;
  onConsultaCreated?: (consultaId: number) => void;
  onOfflineEventCreated?: (event: unknown) => void;
  accentColor?: string;
}

export function ModalCriarAgendamento({
  open,
  onClose,
  onSuccess,
  selectedDate,
  mode = "agenda",
  defaultProfessionalId = "",
  professionals,
  patients,
  procedures,
  nomesAgenda,
  locaisAtendimento,
  onPatientsChange,
  onSearchPatients,
  onConsultaCreated,
  onOfflineEventCreated,
  accentColor = CLINICA_BELEZA_PRIMARY,
}: ModalCriarAgendamentoProps) {
  const form = useCriarAgendamento({
    open,
    mode,
    selectedDate,
    defaultProfessionalId,
    professionals,
    patients,
    procedures,
    nomesAgenda,
    locaisAtendimento,
    onClose,
    onSuccess,
    onPatientsChange,
    onConsultaCreated,
    onOfflineEventCreated,
  });

  if (!open || !form.mounted) return null;

  const modal = (
    <div
      className="fixed inset-0 z-[110] flex items-end sm:items-center justify-center p-0 sm:p-4 md:p-6 bg-black/40 dark:bg-black/60"
      onClick={(e) => {
        if (e.target === e.currentTarget) form.resetAndClose();
      }}
    >
      <div
        className="flex flex-col w-full sm:max-w-2xl md:max-w-3xl lg:max-w-4xl max-h-[100dvh] sm:max-h-[92vh] bg-white dark:bg-neutral-900 sm:rounded-xl shadow-2xl overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-criar-agendamento-title"
      >
        <header className="flex flex-wrap items-center gap-2 sm:gap-3 px-4 sm:px-5 py-3 border-b border-gray-200 dark:border-neutral-700 shrink-0 bg-white dark:bg-neutral-900">
          <button
            type="button"
            onClick={form.resetAndClose}
            className="p-1.5 sm:p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 shrink-0"
            aria-label="Voltar"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </button>
          <div
            className="hidden sm:flex w-9 h-9 rounded-lg items-center justify-center shrink-0"
            style={{ backgroundColor: `${accentColor}18` }}
          >
            <CalendarDays className="w-4 h-4" style={{ color: accentColor }} />
          </div>
          <div className="flex-1 min-w-0">
            <h1
              id="modal-criar-agendamento-title"
              className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate leading-tight"
            >
              {form.modalTitle}
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate hidden sm:block leading-snug">
              {form.modalSubtitle}
            </p>
          </div>
        </header>

        <form className="flex flex-col flex-1 min-h-0" onSubmit={form.handleSubmit}>
          <div className="flex-1 min-h-0 overflow-y-auto p-4 sm:p-5 bg-[#f7f2f4] dark:bg-gray-950">
            {form.createError && (
              <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
                {form.createError}
              </div>
            )}

            <ClinicaBelezaPanel className="p-4 sm:p-5 md:p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5 md:gap-6 lg:gap-8 w-full">
                <CriarAgendamentoClienteSection
                  {...form}
                  onSearchPatients={onSearchPatients}
                />
                <CriarAgendamentoAgendaSection {...form} />
              </div>
              <CriarAgendamentoAdvancedSection {...form} />
            </ClinicaBelezaPanel>
          </div>

          <footer className="shrink-0 border-t border-gray-200 dark:border-neutral-700 bg-white/80 dark:bg-neutral-800/80 px-4 sm:px-5 py-3 sm:py-4">
            <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-2 sm:gap-3 w-full">
              <button
                type="button"
                onClick={form.resetAndClose}
                className="sm:min-w-[120px] py-2.5 px-5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-neutral-800"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={form.createLoading}
                className="sm:min-w-[180px] flex items-center justify-center gap-2 py-2.5 px-5 rounded-lg text-white text-sm font-medium disabled:opacity-60"
                style={{ backgroundColor: accentColor }}
              >
                {form.createLoading ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
                {form.submitLabel}
              </button>
            </div>
          </footer>
        </form>
      </div>
    </div>
  );

  return createPortal(modal, document.body);
}
