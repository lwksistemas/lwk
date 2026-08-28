import { useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  BloqueioHorario,
  ClinicaPatient,
  ClinicaProcedure,
  ClinicaProfessional,
  HorarioTrabalhoRow,
} from "@/lib/clinica-beleza-entities";
import type { LocalAtendimentoItem, NomeAgendaItem } from "@/lib/clinica-beleza-api";
import {
  clinicaBelezaQueryKeys,
  fetchClinicaAgendaBloqueios,
  fetchClinicaAgendaEvents,
  fetchClinicaHorariosTrabalho,
  fetchClinicaLocaisAtendimento,
  fetchClinicaNomesAgenda,
  fetchClinicaProcedures,
  fetchClinicaSchedulingProfessionals,
} from "@/lib/clinica-beleza-cadastros-api";

export function useAgendaCadastroQueries(isOnline: boolean) {
  const queryClient = useQueryClient();

  const professionalsQuery = useQuery({
    queryKey: clinicaBelezaQueryKeys.schedulingProfessionals(),
    queryFn: fetchClinicaSchedulingProfessionals,
    enabled: isOnline,
  });

  // Cache local de pacientes da sessão (criados no modal); autocomplete usa search sob demanda.
  const patientsQuery = useQuery({
    queryKey: clinicaBelezaQueryKeys.agendaPatients(),
    queryFn: async (): Promise<ClinicaPatient[]> =>
      queryClient.getQueryData<ClinicaPatient[]>(clinicaBelezaQueryKeys.agendaPatients()) ?? [],
    enabled: false,
    initialData: [],
    staleTime: Infinity,
  });

  const proceduresQuery = useQuery({
    queryKey: clinicaBelezaQueryKeys.procedures(),
    queryFn: () => fetchClinicaProcedures(),
    enabled: isOnline,
  });

  const nomesAgendaQuery = useQuery({
    queryKey: clinicaBelezaQueryKeys.nomesAgenda(),
    queryFn: fetchClinicaNomesAgenda,
    enabled: isOnline,
  });

  const locaisQuery = useQuery({
    queryKey: clinicaBelezaQueryKeys.locaisAtendimento(),
    queryFn: fetchClinicaLocaisAtendimento,
    enabled: isOnline,
  });

  const professionals = (professionalsQuery.data ?? []) as ClinicaProfessional[];
  const patients = (patientsQuery.data ?? []) as ClinicaPatient[];
  const procedures = (proceduresQuery.data ?? []) as ClinicaProcedure[];
  const nomesAgenda = (nomesAgendaQuery.data ?? []) as NomeAgendaItem[];
  const locaisAtendimento = (locaisQuery.data ?? []) as LocalAtendimentoItem[];

  return {
    professionalsQuery,
    patientsQuery,
    proceduresQuery,
    professionals,
    patients,
    procedures,
    nomesAgenda,
    locaisAtendimento,
  };
}

export function useAgendaCalendarQueries(isOnline: boolean, selectedProfessional: string) {
  const horariosQuery = useQuery({
    queryKey: clinicaBelezaQueryKeys.horariosTrabalho(selectedProfessional),
    queryFn: () => fetchClinicaHorariosTrabalho(selectedProfessional),
    enabled: isOnline && Boolean(selectedProfessional),
  });

  const eventsQuery = useQuery({
    queryKey: clinicaBelezaQueryKeys.agendaEvents(selectedProfessional),
    queryFn: () => fetchClinicaAgendaEvents(selectedProfessional),
    enabled: isOnline,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });

  const bloqueiosQuery = useQuery({
    queryKey: clinicaBelezaQueryKeys.agendaBloqueios(selectedProfessional),
    queryFn: () => fetchClinicaAgendaBloqueios(selectedProfessional),
    enabled: isOnline,
  });

  const horariosTrabalho = (horariosQuery.data ?? []) as HorarioTrabalhoRow[];
  const bloqueios = (bloqueiosQuery.data ?? []) as BloqueioHorario[];

  return { horariosQuery, eventsQuery, bloqueiosQuery, horariosTrabalho, bloqueios };
}

export function useAgendaRefresh(
  isOnline: boolean,
  selectedProfessional: string,
  loadOffline: () => Promise<void>,
) {
  const queryClient = useQueryClient();

  const carregarDados = useCallback(async () => {
    if (!isOnline) {
      await loadOffline();
      return;
    }
    // Usar refetchQueries em vez de invalidateQueries para a query de eventos.
    // invalidateQueries marca como stale permanentemente, causando refetches
    // indesejados que cancelam o drag-and-drop do FullCalendar.
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: clinicaBelezaQueryKeys.schedulingProfessionals() }),
      queryClient.invalidateQueries({ queryKey: clinicaBelezaQueryKeys.procedures() }),
      queryClient.invalidateQueries({ queryKey: clinicaBelezaQueryKeys.nomesAgenda() }),
      queryClient.invalidateQueries({ queryKey: clinicaBelezaQueryKeys.locaisAtendimento() }),
      queryClient.invalidateQueries({
        queryKey: clinicaBelezaQueryKeys.horariosTrabalho(selectedProfessional),
      }),
      queryClient.refetchQueries({
        queryKey: clinicaBelezaQueryKeys.agendaEvents(selectedProfessional),
      }),
      queryClient.refetchQueries({
        queryKey: clinicaBelezaQueryKeys.agendaBloqueios(selectedProfessional),
      }),
    ]);
  }, [isOnline, loadOffline, queryClient, selectedProfessional]);

  const recarregarEventos = useCallback(async () => {
    if (!isOnline) return;
    await queryClient.refetchQueries({
      queryKey: clinicaBelezaQueryKeys.agendaEvents(selectedProfessional),
    });
  }, [isOnline, queryClient, selectedProfessional]);

  const setPatients = useCallback(
    (updater: ClinicaPatient[] | ((prev: ClinicaPatient[]) => ClinicaPatient[])) => {
      queryClient.setQueryData<ClinicaPatient[]>(
        clinicaBelezaQueryKeys.agendaPatients(),
        (prev) => {
          const base = prev ?? [];
          return typeof updater === "function" ? updater(base) : updater;
        },
      );
    },
    [queryClient],
  );

  return { carregarDados, recarregarEventos, setPatients };
}

export function prefetchClinicaAgenda(queryClient: ReturnType<typeof useQueryClient>) {
  return Promise.all([
    queryClient.prefetchQuery({
      queryKey: clinicaBelezaQueryKeys.schedulingProfessionals(),
      queryFn: fetchClinicaSchedulingProfessionals,
    }),
    queryClient.prefetchQuery({
      queryKey: clinicaBelezaQueryKeys.agendaEvents(""),
      queryFn: () => fetchClinicaAgendaEvents(""),
      staleTime: Infinity,
    }),
  ]);
}
