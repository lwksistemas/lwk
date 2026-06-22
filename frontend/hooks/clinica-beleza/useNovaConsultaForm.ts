"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useConvenioPrecos } from "@/hooks/clinica-beleza/useConvenioPrecos";
import { useConveniosList } from "@/hooks/clinica-beleza/useConveniosList";
import { procedureDuration, procedurePrice } from "@/lib/clinica-beleza-entities";
import { precoProcedimento } from "@/lib/convenio-precos";

export interface ConsultaFormPatient {
  id: number;
  nome?: string;
  name?: string;
  convenio?: number | null;
}

export interface ConsultaFormProcedure {
  id: number;
  nome?: string;
  name?: string;
  duracao_minutos?: number;
  duration?: number;
  preco?: number | string;
  price?: string;
}

interface Options {
  patients: ConsultaFormPatient[];
  procedures: ConsultaFormProcedure[];
  enabled?: boolean;
  /** Nova consulta avulsa permite orçamento/representante sem procedimento. */
  requireProcedure?: boolean;
}

export function useNovaConsultaForm({
  patients,
  procedures,
  enabled = true,
  requireProcedure = true,
}: Options) {
  const [patientId, setPatientId] = useState<number | "">("");
  const [professionalId, setProfessionalId] = useState<number | "">("");
  const [convenioId, setConvenioId] = useState<number | "">("");
  const [selectedProcedures, setSelectedProcedures] = useState<number[]>([]);

  const convenios = useConveniosList(enabled);
  const precosMap = useConvenioPrecos(convenioId);

  useEffect(() => {
    if (!patientId) return;
    const paciente = patients.find((p) => p.id === patientId);
    setConvenioId(paciente?.convenio ?? "");
  }, [patientId, patients]);

  const adicionarProcedimento = useCallback((id: number) => {
    setSelectedProcedures((prev) => (id && !prev.includes(id) ? [...prev, id] : prev));
  }, []);

  const removerProcedimento = useCallback((id: number) => {
    setSelectedProcedures((prev) => prev.filter((p) => p !== id));
  }, []);

  const resumo = useMemo(() => {
    let duracao = 0;
    let valor = 0;
    for (const id of selectedProcedures) {
      const proc = procedures.find((p) => p.id === id);
      if (!proc) continue;
      duracao += procedureDuration(proc);
      const particular = Number(procedurePrice(proc)) || 0;
      valor += precoProcedimento(id, particular, convenioId, precosMap);
    }
    return { duracao, valor };
  }, [selectedProcedures, procedures, convenioId, precosMap]);

  const resetForm = useCallback(() => {
    setPatientId("");
    setProfessionalId("");
    setConvenioId("");
    setSelectedProcedures([]);
  }, []);

  const validateBase = useCallback((): string | null => {
    if (!patientId) {
      return "Selecione o paciente.";
    }
    if (requireProcedure && selectedProcedures.length === 0) {
      return "Selecione pelo menos um procedimento.";
    }
    return null;
  }, [patientId, selectedProcedures, requireProcedure]);

  return {
    patientId,
    setPatientId,
    professionalId,
    setProfessionalId,
    convenioId,
    setConvenioId,
    selectedProcedures,
    setSelectedProcedures,
    convenios,
    precosMap,
    adicionarProcedimento,
    removerProcedimento,
    resumo,
    resetForm,
    validateBase,
  };
}
