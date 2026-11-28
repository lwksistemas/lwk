"use client";

import { createPortal } from "react-dom";
import { CalendarDays, Info, Loader2, X } from "lucide-react";
import { useClinicaBelezaTheme } from "@/components/clinica-beleza/ClinicaBelezaThemeContext";
import { CriarAgendamentoAgendaSection } from "@/components/clinica-beleza/criar-agendamento/CriarAgendamentoAgendaSection";
import { CriarAgendamentoClienteSection } from "@/components/clinica-beleza/criar-agendamento/CriarAgendamentoClienteSection";
import { CriarAgendamentoDireitaSection } from "@/components/clinica-beleza/criar-agendamento/CriarAgendamentoDireitaSection";
import {
  type CriarAgendamentoProfessional,
  type ModalCriarAgendamentoMode,
} from "@/components/clinica-beleza/criar-agendamento/criar-agendamento-utils";
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
import { useCriarAgendamento } from "@/hooks/clinica-beleza/useCriarAgendamento";
import type { ConsultaFormProcedure } from "@/hooks/clinica-beleza/useNovaConsultaForm";
import type { LocalAtendimentoItem, NomeAgendaItem } from "@/lib/clinica-beleza-api";
import { cbPrimaryGradient, cbPrimaryTitle } from "@/lib/clinica-beleza-theme-utils";

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
  /** Hex override; default = cor primária do tema da loja. */
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
  accentColor,
}: ModalCriarAgendamentoProps) {
  const theme = useClinicaBelezaTheme();
  const accent = accentColor || theme.primary;

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
      className="fixed inset-0 z-[110] flex items-end sm:items-center justify-center p-0 sm:p-2 md:p-3 bg-black/40 dark:bg-black/60"
      style={theme.cssVars}
      onClick={(e) => {
        if (e.target === e.currentTarget) form.resetAndClose();
      }}
    >
      <div
        className="flex flex-col w-[min(96vw,1020px)] max-h-[min(100dvh,720px)] sm:max-h-[min(90vh,720px)] h-fit bg-white dark:bg-neutral-900 sm:rounded-2xl shadow-2xl overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-criar-agendamento-title"
      >
        <header
          className="flex flex-wrap items-center gap-2 px-3.5 sm:px-4 py-2 border-b border-[#E9D5E3] dark:border-neutral-700 shrink-0"
          style={{
            backgroundImage: `linear-gradient(90deg, ${theme.primaryLight} 0%, #ffffff 72%)`,
          }}
        >
          <div
            className="flex w-9 h-9 rounded-lg items-center justify-center shrink-0 border border-white/70 shadow-sm"
            style={{ backgroundColor: theme.primaryLight }}
          >
            <CalendarDays className="w-4.5 h-4.5 w-[18px] h-[18px]" style={{ color: accent }} />
          </div>
          <div className="flex-1 min-w-0">
            <h1
              id="modal-criar-agendamento-title"
              className="text-[15px] sm:text-base font-bold truncate leading-tight"
              style={{ color: cbPrimaryTitle() }}
            >
              {form.modalTitle}
            </h1>
            <p className="text-[11px] truncate hidden sm:block leading-snug text-slate-500 dark:text-gray-400">
              {form.modalSubtitle}
            </p>
          </div>
          <button
            type="button"
            onClick={form.resetAndClose}
            className="p-1 rounded-lg hover:bg-black/5 dark:hover:bg-white/10 shrink-0"
            aria-label="Fechar"
          >
            <X className="w-5 h-5" style={{ color: accent }} />
          </button>
        </header>

        <form className="flex flex-col min-h-0 overflow-hidden" onSubmit={form.handleSubmit}>
          <div className="min-h-0 overflow-y-auto overscroll-contain p-2 sm:p-2.5 bg-[#FAF8FA] dark:bg-gray-950">
            {form.createError ? (
              <div className="mb-2 p-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
                {form.createError}
              </div>
            ) : null}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-2 lg:gap-2.5 items-start">
              <div className="space-y-2 min-w-0">
                <CriarAgendamentoClienteSection
                  {...form}
                  onSearchPatients={onSearchPatients}
                />
                <CriarAgendamentoAgendaSection {...form} />
              </div>
              <div className="min-w-0">
                <CriarAgendamentoDireitaSection {...form} />
              </div>
            </div>
          </div>

          <footer className="shrink-0 border-t border-[#E9D5E3] dark:border-neutral-700 bg-white dark:bg-neutral-900 px-3 sm:px-4 py-2">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 w-full">
              <div
                className="order-2 sm:order-1 flex-1 flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs text-gray-700 dark:text-gray-200 min-w-0"
                style={{ backgroundColor: theme.primaryLight }}
              >
                <Info className="h-3.5 w-3.5 shrink-0" style={{ color: accent }} />
                <span className="truncate">Confira os dados antes de agendar.</span>
              </div>
              <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-2 w-full sm:w-auto order-1 sm:order-2">
                <button
                  type="button"
                  onClick={form.resetAndClose}
                  className="sm:min-w-[100px] py-1.5 px-3.5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium text-gray-800 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-neutral-800 inline-flex items-center justify-center gap-1.5"
                >
                  <X size={14} />
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={!form.canSubmit}
                  aria-busy={form.createLoading}
                  className="sm:min-w-[120px] flex items-center justify-center gap-2 py-1.5 px-3.5 rounded-lg text-white text-sm font-semibold disabled:opacity-60 shadow-sm"
                  style={{ backgroundImage: cbPrimaryGradient(135) }}
                >
                  {form.createLoading ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <CalendarDays size={16} />
                  )}
                  {form.submitLabel}
                </button>
              </div>
            </div>
          </footer>
        </form>
      </div>
    </div>
  );

  return createPortal(modal, document.body);
}
