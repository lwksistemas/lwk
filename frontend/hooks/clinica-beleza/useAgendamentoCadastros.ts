"use client";

import { useCallback, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
import type { ConsultaFormProcedure } from "@/hooks/clinica-beleza/useNovaConsultaForm";
import {
  clinicaBelezaQueryKeys,
  fetchClinicaLocaisAtendimento,
  fetchClinicaNomesAgenda,
  fetchClinicaProcedures,
  fetchClinicaProfessionals,
  searchClinicaPatients,
} from "@/lib/clinica-beleza-cadastros-api";
import type { LocalAtendimentoItem, NomeAgendaItem } from "@/lib/clinica-beleza-api";

interface Professional {
  id: number;
  name?: string;
  nome?: string;
}

export function useAgendamentoCadastros(enabled = true) {
  const queryClient = useQueryClient();
  const [localPatients, setLocalPatients] = useState<PatientQuickOption[]>([]);

  const professionalsQuery = useQuery({
    queryKey: clinicaBelezaQueryKeys.professionals(),
    queryFn: fetchClinicaProfessionals,
    enabled,
  });

  const proceduresQuery = useQuery({
    queryKey: clinicaBelezaQueryKeys.procedures(),
    queryFn: () => fetchClinicaProcedures(),
    enabled,
  });

  const nomesAgendaQuery = useQuery({
    queryKey: clinicaBelezaQueryKeys.nomesAgenda(),
    queryFn: fetchClinicaNomesAgenda,
    enabled,
  });

  const locaisQuery = useQuery({
    queryKey: clinicaBelezaQueryKeys.locaisAtendimento(),
    queryFn: fetchClinicaLocaisAtendimento,
    enabled,
  });

  const searchPatients = useCallback(
    async (query: string) => {
      const q = query.trim();
      if (q.length < 1) return [];
      return queryClient.fetchQuery({
        queryKey: clinicaBelezaQueryKeys.patientSearch(q),
        queryFn: () => searchClinicaPatients(q),
        staleTime: 30_000,
      });
    },
    [queryClient],
  );

  const reload = useCallback(async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: clinicaBelezaQueryKeys.professionals() }),
      queryClient.invalidateQueries({ queryKey: clinicaBelezaQueryKeys.procedures() }),
      queryClient.invalidateQueries({ queryKey: clinicaBelezaQueryKeys.nomesAgenda() }),
      queryClient.invalidateQueries({ queryKey: clinicaBelezaQueryKeys.locaisAtendimento() }),
    ]);
  }, [queryClient]);

  const setPatients = useCallback(
    (updater: PatientQuickOption[] | ((prev: PatientQuickOption[]) => PatientQuickOption[])) => {
      setLocalPatients((prev) => (typeof updater === "function" ? updater(prev) : updater));
    },
    [],
  );

  return {
    loading:
      professionalsQuery.isLoading ||
      proceduresQuery.isLoading ||
      nomesAgendaQuery.isLoading ||
      locaisQuery.isLoading,
    patients: localPatients,
    professionals: (professionalsQuery.data ?? []) as Professional[],
    procedures: (proceduresQuery.data ?? []) as ConsultaFormProcedure[],
    nomesAgenda: (nomesAgendaQuery.data ?? []) as NomeAgendaItem[],
    locaisAtendimento: (locaisQuery.data ?? []) as LocalAtendimentoItem[],
    setPatients,
    searchPatients,
    reload,
  };
}
