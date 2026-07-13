import { useEffect } from "react";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import type {
  ClinicaPatient,
  ClinicaProcedure,
  ClinicaProfessional,
} from "@/lib/clinica-beleza-entities";
import {
  salvarPacientesOffline,
  salvarProfissionaisOffline,
  salvarProcedimentosOffline,
  salvarAgendamentosOffline,
} from "@/lib/offline-db";

export function useAgendaOfflineCache(
  isOnline: boolean,
  professionals: ClinicaProfessional[],
  patients: ClinicaPatient[],
  procedures: ClinicaProcedure[],
  eventsData: AgendaEventData[] | undefined,
) {
  useEffect(() => {
    if (!isOnline || !professionals.length) return;
    void salvarProfissionaisOffline(professionals);
  }, [isOnline, professionals]);

  useEffect(() => {
    if (!isOnline || !patients.length) return;
    void salvarPacientesOffline(patients);
  }, [isOnline, patients]);

  useEffect(() => {
    if (!isOnline || !procedures.length) return;
    void salvarProcedimentosOffline(procedures);
  }, [isOnline, procedures]);

  useEffect(() => {
    if (!isOnline || !eventsData) return;
    void salvarAgendamentosOffline(eventsData);
  }, [isOnline, eventsData]);
}
