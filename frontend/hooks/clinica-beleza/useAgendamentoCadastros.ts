"use client";

import { useCallback, useEffect, useState } from "react";
import type { PatientQuickOption } from "@/components/clinica-beleza/PatientQuickRegisterField";
import type { ConsultaFormProcedure } from "@/hooks/clinica-beleza/useNovaConsultaForm";
import {
  clinicaBelezaFetch,
  type LocalAtendimentoItem,
  type NomeAgendaItem,
} from "@/lib/clinica-beleza-api";

interface Professional {
  id: number;
  name?: string;
  nome?: string;
}

export function useAgendamentoCadastros(enabled = true) {
  const [loading, setLoading] = useState(false);
  const [patients, setPatients] = useState<PatientQuickOption[]>([]);
  const [professionals, setProfessionals] = useState<Professional[]>([]);
  const [procedures, setProcedures] = useState<ConsultaFormProcedure[]>([]);
  const [nomesAgenda, setNomesAgenda] = useState<NomeAgendaItem[]>([]);
  const [locaisAtendimento, setLocaisAtendimento] = useState<LocalAtendimentoItem[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [resProf, resPat, resProc, resAgendas, resLocais] = await Promise.all([
        clinicaBelezaFetch("/professionals/"),
        clinicaBelezaFetch("/patients/"),
        clinicaBelezaFetch("/procedures/"),
        clinicaBelezaFetch("/nomes-agenda/"),
        clinicaBelezaFetch("/locais-atendimento/"),
      ]);
      setProfessionals(resProf.ok ? await resProf.json() : []);
      setPatients(resPat.ok ? await resPat.json() : []);
      setProcedures(resProc.ok ? await resProc.json() : []);
      const agendas = resAgendas.ok ? await resAgendas.json() : [];
      const locais = resLocais.ok ? await resLocais.json() : [];
      setNomesAgenda(Array.isArray(agendas) ? agendas : []);
      setLocaisAtendimento(Array.isArray(locais) ? locais : []);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (enabled) load();
  }, [enabled, load]);

  return {
    loading,
    patients,
    professionals,
    procedures,
    nomesAgenda,
    locaisAtendimento,
    setPatients,
    reload: load,
  };
}
