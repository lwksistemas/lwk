"use client";

import { useAgendaStatusColors } from "@/components/clinica-beleza/ClinicaBelezaThemeContext";
import { useAgendaEventos } from "./useAgendaEventos";
import { useAgendaOnlineStatus } from "./useAgendaOnlineStatus";
import { useAgendaOfflineCache } from "./useAgendaOfflineCache";
import {
  useAgendaCadastroQueries,
  useAgendaCalendarQueries,
  useAgendaRefresh,
} from "./useAgendaQueries";

export function useAgendaData(selectedProfessional: string) {
  const isOnline = useAgendaOnlineStatus();
  const statusColors = useAgendaStatusColors();

  const {
    professionalsQuery,
    proceduresQuery,
    professionals,
    patients,
    procedures,
    nomesAgenda,
    locaisAtendimento,
  } = useAgendaCadastroQueries(isOnline);

  const { eventsQuery, horariosTrabalho, bloqueios } = useAgendaCalendarQueries(
    isOnline,
    selectedProfessional,
  );

  useAgendaOfflineCache(isOnline, professionals, patients, procedures, eventsQuery.data);

  const { eventos, setEventos, offlineLoading, loadOffline } = useAgendaEventos({
    isOnline,
    selectedProfessional,
    eventsData: eventsQuery.data,
    bloqueios,
    horariosTrabalho,
    professionals,
    patients,
    procedures,
    statusColors,
  });

  const { carregarDados, setPatients } = useAgendaRefresh(
    isOnline,
    selectedProfessional,
    loadOffline,
  );

  const loading = isOnline
    ? professionalsQuery.isLoading ||
      proceduresQuery.isLoading ||
      eventsQuery.isLoading
    : offlineLoading;

  return {
    eventos,
    setEventos,
    loading,
    professionals,
    horariosTrabalho,
    patients,
    setPatients,
    procedures,
    nomesAgenda,
    locaisAtendimento,
    bloqueios,
    carregarDados,
  };
}
