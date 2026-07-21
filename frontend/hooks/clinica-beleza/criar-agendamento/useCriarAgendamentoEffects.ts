import { useEffect, useRef, useState, type Dispatch, type SetStateAction } from "react";
import {
  formatDateInputValue,
  formatTimeFromDate,
  resolveDefaultLocalId,
  resolveDefaultNomeAgendaId,
} from "@/components/clinica-beleza/criar-agendamento/criar-agendamento-utils";
import { ClinicaBelezaAPI, clinicaBelezaFetch, type RetornoVerificacaoResult } from "@/lib/clinica-beleza-api";
import { type HorarioTrabalho } from "@/lib/clinica-beleza-work-hours";
import type { UseCriarAgendamentoOptions } from "./criar-agendamento-types";

type FormSlice = {
  resetForm: () => void;
  setConvenioId: (v: number | "") => void;
  setProfessionalId: (v: number | "") => void;
  patientId: number | "";
  selectedProcedures: number[];
};

export function useCriarAgendamentoEffects(
  options: Pick<
    UseCriarAgendamentoOptions,
    "open" | "selectedDate" | "defaultProfessionalId" | "nomesAgenda" | "locaisAtendimento"
  >,
  form: FormSlice,
  localState: {
    setDateInput: (v: string) => void;
    setTime: (v: string) => void;
    setNotes: (v: string) => void;
    setNomeAgendaId: Dispatch<SetStateAction<number | "">>;
    setLocalAtendimentoId: Dispatch<SetStateAction<number | "">>;
    setCreateError: (v: string) => void;
    setRetornoInfo: (v: RetornoVerificacaoResult | null) => void;
    setRetornoProcedureId: (v: number | "") => void;
    setShowAdvanced: (v: boolean) => void;
    retornoProcedureId: number | "";
    professionalId: number | "";
    dateInput: string;
    setHorariosProfissional: (h: HorarioTrabalho[]) => void;
    setVerificandoRetorno: (v: boolean) => void;
  },
) {
  const { open, selectedDate, defaultProfessionalId, nomesAgenda, locaisAtendimento } = options;
  const { resetForm, setConvenioId, setProfessionalId, patientId, selectedProcedures } = form;
  const {
    setDateInput,
    setTime,
    setNotes,
    setNomeAgendaId,
    setLocalAtendimentoId,
    setCreateError,
    setRetornoInfo,
    setRetornoProcedureId,
    setShowAdvanced,
    retornoProcedureId,
    professionalId,
    dateInput,
    setHorariosProfissional,
    setVerificandoRetorno,
  } = localState;

  const [mounted, setMounted] = useState(false);
  /** Evita resetar data/hora enquanto o usuário edita (deps como nomesAgenda mudam a cada refetch). */
  const initializedOpenRef = useRef(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  useEffect(() => {
    if (!open) {
      initializedOpenRef.current = false;
      return;
    }
    if (initializedOpenRef.current) return;
    initializedOpenRef.current = true;

    resetForm();
    setConvenioId("");
    setProfessionalId(defaultProfessionalId ? Number(defaultProfessionalId) : "");
    setNomeAgendaId(resolveDefaultNomeAgendaId(nomesAgenda));
    setLocalAtendimentoId(resolveDefaultLocalId(locaisAtendimento));
    const base = selectedDate ?? new Date();
    setDateInput(formatDateInputValue(base));
    setTime(formatTimeFromDate(base));
    setNotes("");
    setCreateError("");
    setRetornoInfo(null);
    setRetornoProcedureId("");
    setShowAdvanced(false);
  }, [
    open,
    selectedDate,
    defaultProfessionalId,
    resetForm,
    setConvenioId,
    setProfessionalId,
    nomesAgenda,
    locaisAtendimento,
    setDateInput,
    setTime,
    setNotes,
    setNomeAgendaId,
    setLocalAtendimentoId,
    setCreateError,
    setRetornoInfo,
    setRetornoProcedureId,
    setShowAdvanced,
  ]);

  useEffect(() => {
    if (!open || nomesAgenda.length === 0) return;
    setNomeAgendaId((current) => current || resolveDefaultNomeAgendaId(nomesAgenda));
  }, [open, nomesAgenda, setNomeAgendaId]);

  useEffect(() => {
    if (!open || locaisAtendimento.length === 0) return;
    setLocalAtendimentoId((current) => current || resolveDefaultLocalId(locaisAtendimento));
  }, [open, locaisAtendimento, setLocalAtendimentoId]);

  useEffect(() => {
    if (!open || !patientId || !dateInput) {
      if (!dateInput && open && patientId) return; // aguardar dateInput ser preenchido
      setRetornoInfo(null);
      return;
    }
    let cancelled = false;
    const timer = setTimeout(async () => {
      setVerificandoRetorno(true);
      try {
        const procedureIds = [...selectedProcedures];
        if (retornoProcedureId && !procedureIds.includes(Number(retornoProcedureId))) {
          procedureIds.push(Number(retornoProcedureId));
        }
        const result = await ClinicaBelezaAPI.retorno.verificar({
          patient_id: Number(patientId),
          procedure_ids: procedureIds.length ? procedureIds : undefined,
          retorno_procedure_id: retornoProcedureId ? Number(retornoProcedureId) : undefined,
          reference_date: dateInput || undefined,
        });
        if (!cancelled) setRetornoInfo(result);
      } catch {
        if (!cancelled) setRetornoInfo(null);
      } finally {
        if (!cancelled) setVerificandoRetorno(false);
      }
    }, 350);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [
    open,
    patientId,
    selectedProcedures,
    retornoProcedureId,
    dateInput,
    setRetornoInfo,
    setVerificandoRetorno,
  ]);

  useEffect(() => {
    if (!open || !professionalId) {
      setHorariosProfissional([]);
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const res = await clinicaBelezaFetch(`/professionals/${professionalId}/horarios-trabalho/`);
        if (!res.ok || cancelled) return;
        const data = await res.json();
        setHorariosProfissional(Array.isArray(data) ? data : []);
      } catch {
        if (!cancelled) setHorariosProfissional([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open, professionalId, setHorariosProfissional]);

  return { mounted };
}
