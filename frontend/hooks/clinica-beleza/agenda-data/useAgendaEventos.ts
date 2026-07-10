import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import type {
  BloqueioHorario,
  ClinicaPatient,
  ClinicaProcedure,
  ClinicaProfessional,
  HorarioTrabalhoRow,
} from "@/lib/clinica-beleza-entities";
import {
  CLINICA_AGENDA_STATUS_COLORS,
  type AgendaStatusColorMap,
} from "@/lib/clinica-beleza-constants";
import {
  buscarAgendamentosOffline,
  buscarProfissionaisOffline,
  obterFilaSync,
} from "@/lib/offline-db";
import { logger } from "@/lib/logger";
import {
  agendaEventsEqual,
  buildEventosOnline,
  buildPendingSyncEvents,
  formatarAgendaEvento,
  intervalosAgendaProfissional,
  temExpedienteProfissional,
} from "./agenda-event-mappers";

export function useAgendaEventos({
  isOnline,
  selectedProfessional,
  eventsData,
  bloqueios,
  horariosTrabalho,
  professionals,
  patients,
  procedures,
  statusColors = CLINICA_AGENDA_STATUS_COLORS,
}: {
  isOnline: boolean;
  selectedProfessional: string;
  eventsData: unknown;
  bloqueios: BloqueioHorario[];
  horariosTrabalho: HorarioTrabalhoRow[];
  professionals: ClinicaProfessional[];
  patients: ClinicaPatient[];
  procedures: ClinicaProcedure[];
  statusColors?: AgendaStatusColorMap;
}) {
  const horariosTrabalhoRef = useRef<HorarioTrabalhoRow[]>(horariosTrabalho);
  horariosTrabalhoRef.current = horariosTrabalho;
  const statusColorsRef = useRef<AgendaStatusColorMap>(statusColors);
  statusColorsRef.current = statusColors;

  const [offlineEventos, setOfflineEventos] = useState<AgendaEventData[]>([]);
  const [offlineLoading, setOfflineLoading] = useState(false);
  const [pendingEvents, setPendingEvents] = useState<AgendaEventData[]>([]);
  const [eventos, setEventos] = useState<AgendaEventData[]>([]);

  const loadOffline = useCallback(async () => {
    setOfflineLoading(true);
    try {
      const horariosOffline = horariosTrabalhoRef.current;
      const colors = statusColorsRef.current;
      const [agendaRaw, profs] = await Promise.all([
        buscarAgendamentosOffline(),
        buscarProfissionaisOffline(),
      ]);
      const profsList = profs as ClinicaProfessional[];
      const intervalos =
        selectedProfessional && horariosOffline.length > 0
          ? intervalosAgendaProfissional(selectedProfessional, horariosOffline, profsList)
          : [];
      const temExpediente = temExpedienteProfissional(selectedProfessional, horariosOffline);
      if (Array.isArray(agendaRaw) && agendaRaw.length > 0) {
        let list = agendaRaw as Record<string, unknown>[];
        if (selectedProfessional) {
          list = list.filter((e) => String(e.professional) === selectedProfessional);
        }
        setOfflineEventos([
          ...list.map((e) => formatarAgendaEvento(e, temExpediente, colors)),
          ...intervalos,
        ]);
      } else {
        setOfflineEventos(intervalos);
      }
    } catch (error) {
      logger.warn("Erro ao carregar dados offline:", error);
    } finally {
      setOfflineLoading(false);
    }
  }, [selectedProfessional]);

  useEffect(() => {
    if (isOnline) return;
    void loadOffline();
  }, [isOnline, loadOffline, statusColors]);

  useEffect(() => {
    if (!isOnline) return;
    void obterFilaSync().then((fila) => {
      const temExpediente = temExpedienteProfissional(selectedProfessional, horariosTrabalho);
      setPendingEvents(
        buildPendingSyncEvents({
          fila,
          patients,
          procedures,
          professionals,
          temExpediente,
          statusColors,
        }),
      );
    });
  }, [
    isOnline,
    patients,
    procedures,
    professionals,
    selectedProfessional,
    horariosTrabalho,
    statusColors,
  ]);

  const eventosOnline = useMemo(
    () =>
      buildEventosOnline({
        rawEvents: Array.isArray(eventsData) ? (eventsData as Record<string, unknown>[]) : [],
        bloqueios,
        horariosTrabalho,
        professionals,
        selectedProfessional,
        pendingEvents,
        statusColors,
      }),
    [
      bloqueios,
      eventsData,
      horariosTrabalho,
      pendingEvents,
      professionals,
      selectedProfessional,
      statusColors,
    ],
  );

  useEffect(() => {
    const next = isOnline ? eventosOnline : offlineEventos;
    setEventos((prev) => (agendaEventsEqual(prev, next) ? prev : next));
  }, [eventosOnline, offlineEventos, isOnline]);

  return { eventos, setEventos, offlineLoading, loadOffline };
}
