"use client";

import { useEffect, useState } from "react";
import { ClinicaBelezaAPI, type LocalAtendimentoItem } from "@/lib/clinica-beleza-api";
import type { ConsultaFormPatient, ConsultaFormProcedure } from "@/hooks/clinica-beleza/useNovaConsultaForm";
import { logger } from "@/lib/logger";

interface ProfessionalOption {
  id: number;
  nome?: string;
  name?: string;
}

export function useConsultaCadastros() {
  const [patients, setPatients] = useState<ConsultaFormPatient[]>([]);
  const [professionals, setProfessionals] = useState<ProfessionalOption[]>([]);
  const [procedures, setProcedures] = useState<ConsultaFormProcedure[]>([]);
  const [locais, setLocais] = useState<LocalAtendimentoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const [pac, prof, proc, locaisRes] = await Promise.all([
          ClinicaBelezaAPI.get<ConsultaFormPatient[]>("/patients/"),
          ClinicaBelezaAPI.professionals.list(),
          ClinicaBelezaAPI.get<ConsultaFormProcedure[]>("/procedures/"),
          ClinicaBelezaAPI.locaisAtendimento.list(),
        ]);
        const ativos = <T,>(arr: unknown) => (Array.isArray(arr) ? (arr as T[]) : []);
        setPatients(ativos<ConsultaFormPatient>(pac));
        setProfessionals(ativos<ProfessionalOption>(prof));
        setProcedures(ativos<ConsultaFormProcedure>(proc));
        setLocais(Array.isArray(locaisRes) ? locaisRes : []);
      } catch (e) {
        logger.warn("Erro ao carregar dados para nova consulta:", e);
        setError("Não foi possível carregar os cadastros. Tente novamente.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return { patients, professionals, procedures, locais, loading, error };
}
