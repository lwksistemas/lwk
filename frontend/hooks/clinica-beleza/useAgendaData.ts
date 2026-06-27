"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { entityName } from "@/lib/clinica-beleza-entities";
import type {
  BloqueioHorario,
  ClinicaPatient,
  ClinicaProcedure,
  ClinicaProfessional,
  HorarioTrabalhoRow,
} from "@/lib/clinica-beleza-entities";
import {
  CLINICA_AGENDA_BLOQUEIO_COLORS,
  CLINICA_AGENDA_STATUS_COLORS,
} from "@/lib/clinica-beleza-constants";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import type { LocalAtendimentoItem, NomeAgendaItem } from "@/lib/clinica-beleza-api";
import {
  clinicaBelezaQueryKeys,
  fetchClinicaAgendaBloqueios,
  fetchClinicaAgendaEvents,
  fetchClinicaAgendaPatients,
  fetchClinicaHorariosTrabalho,
  fetchClinicaLocaisAtendimento,
  fetchClinicaNomesAgenda,
  fetchClinicaProcedures,
  fetchClinicaSchedulingProfessionals,
} from "@/lib/clinica-beleza-cadastros-api";
import { intervalosEventsFromHorarios } from "@/lib/clinica-beleza-work-hours";
import {
  salvarPacientesOffline,
  buscarPacientesOffline,
  salvarProfissionaisOffline,
  buscarProfissionaisOffline,
  salvarProcedimentosOffline,
  buscarProcedimentosOffline,
  salvarAgendamentosOffline,
  buscarAgendamentosOffline,
  obterFilaSync,
} from "@/lib/offline-db";
import { logger } from "@/lib/logger";

function formatarEvento(
  e: Record<string, unknown>,
  comRestricaoExpediente: boolean,
): AgendaEventData {
  const status = String(e.status ?? "");
  const cores = CLINICA_AGENDA_STATUS_COLORS[status] || { bg: "#a855f7", border: "#9333ea" };
  const titulo =
    [e.patient_name, e.procedure_name].filter(Boolean).join(" • ") ||
    String(e.title ?? "") ||
    "Agendamento";
  return {
    id: String(e.id),
    title: titulo,
    start: String(e.start),
    end: String(e.end),
    backgroundColor: cores.bg,
    borderColor: cores.border,
    textColor: "#fff",
    ...(comRestricaoExpediente ? { constraint: "businessHours" as const } : {}),
    extendedProps: {
      dbId: e.id as string | number,
      status,
      patient_name: String(e.patient_name ?? ""),
      patient_phone: String(e.patient_phone ?? ""),
      professional_name: String(e.professional_name ?? ""),
      procedure_name: String(e.procedure_name ?? ""),
      procedure_duration: e.procedure_duration as number | undefined,
      duracao_minutos: e.duracao_minutos as number | undefined,
      procedure_price: e.procedure_price as string | undefined,
      notes: String(e.notes ?? ""),
      version: e.version as number | undefined,
      updated_at: e.updated_at as string | undefined,
    },
  };
}

function agendaEventsEqual(a: AgendaEventData[], b: AgendaEventData[]): boolean {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    const x = a[i];
    const y = b[i];
    if (
      x.id !== y.id ||
      x.start !== y.start ||
      x.end !== y.end ||
      x.title !== y.title ||
      x.backgroundColor !== y.backgroundColor
    ) {
      return false;
    }
    if (x.extendedProps?.status !== y.extendedProps?.status) return false;
  }
  return true;
}

function bloqueiosToEvents(bloqueiosList: BloqueioHorario[]): AgendaEventData[] {
  return bloqueiosList.map((b) => {
    const rawS = b.data_inicio ?? "";
    const rawE = b.data_fim ?? "";
    const hasT =
      typeof rawS === "string" &&
      rawS.includes("T") &&
      typeof rawE === "string" &&
      rawE.includes("T");
    const startStr = hasT ? rawS : (rawS.slice(0, 10) ? `${rawS.slice(0, 10)}T00:00:00` : "");
    const endStr = hasT ? rawE : (rawS.slice(0, 10) ? `${rawS.slice(0, 10)}T23:59:59` : "");
    return {
      id: `bloqueio-${b.id}`,
      title: `🚫 ${b.motivo}`,
      start: startStr,
      end: endStr,
      allDay: false,
      backgroundColor: CLINICA_AGENDA_BLOQUEIO_COLORS.bg,
      borderColor: CLINICA_AGENDA_BLOQUEIO_COLORS.border,
      textColor: "#fff",
      editable: true,
      durationEditable: true,
      startEditable: true,
      classNames: ["fc-event-bloqueio"],
      extendedProps: {
        isBloqueio: true,
        bloqueioId: b.id,
        motivo: b.motivo,
        professional: b.professional,
        professional_name: b.professional_name || "Todos",
      },
    } as AgendaEventData;
  });
}

export function useAgendaData(selectedProfessional: string) {
  const queryClient = useQueryClient();
  const [isOnline, setIsOnline] = useState(
    () => typeof navigator === "undefined" || navigator.onLine,
  );
  const [offlineEventos, setOfflineEventos] = useState<AgendaEventData[]>([]);
  const [offlineLoading, setOfflineLoading] = useState(false);
  const horariosTrabalhoRef = useRef<HorarioTrabalhoRow[]>([]);

  useEffect(() => {
    const syncOnline = () => setIsOnline(navigator.onLine);
    window.addEventListener("online", syncOnline);
    window.addEventListener("offline", syncOnline);
    return () => {
      window.removeEventListener("online", syncOnline);
      window.removeEventListener("offline", syncOnline);
    };
  }, []);

  const professionalsQuery = useQuery({
    queryKey: clinicaBelezaQueryKeys.schedulingProfessionals(),
    queryFn: fetchClinicaSchedulingProfessionals,
    enabled: isOnline,
  });

  const patientsQuery = useQuery({
    queryKey: clinicaBelezaQueryKeys.agendaPatients(),
    queryFn: fetchClinicaAgendaPatients,
    enabled: isOnline,
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

  const horariosQuery = useQuery({
    queryKey: clinicaBelezaQueryKeys.horariosTrabalho(selectedProfessional),
    queryFn: () => fetchClinicaHorariosTrabalho(selectedProfessional),
    enabled: isOnline && Boolean(selectedProfessional),
  });

  const eventsQuery = useQuery({
    queryKey: clinicaBelezaQueryKeys.agendaEvents(selectedProfessional),
    queryFn: () => fetchClinicaAgendaEvents(selectedProfessional),
    enabled: isOnline,
  });

  const bloqueiosQuery = useQuery({
    queryKey: clinicaBelezaQueryKeys.agendaBloqueios(selectedProfessional),
    queryFn: () => fetchClinicaAgendaBloqueios(selectedProfessional),
    enabled: isOnline,
  });

  const professionals = (professionalsQuery.data ?? []) as ClinicaProfessional[];
  const patients = (patientsQuery.data ?? []) as ClinicaPatient[];
  const procedures = (proceduresQuery.data ?? []) as ClinicaProcedure[];
  const nomesAgenda = (nomesAgendaQuery.data ?? []) as NomeAgendaItem[];
  const locaisAtendimento = (locaisQuery.data ?? []) as LocalAtendimentoItem[];
  const horariosTrabalho = (horariosQuery.data ?? []) as HorarioTrabalhoRow[];
  const bloqueios = (bloqueiosQuery.data ?? []) as BloqueioHorario[];

  horariosTrabalhoRef.current = horariosTrabalho;

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
    if (!isOnline || !eventsQuery.data) return;
    void salvarAgendamentosOffline(eventsQuery.data);
  }, [isOnline, eventsQuery.data]);

  const loadOffline = useCallback(async () => {
    setOfflineLoading(true);
    try {
      const horariosOffline = horariosTrabalhoRef.current;
      const [agendaRaw, profs, pacs, procs] = await Promise.all([
        buscarAgendamentosOffline(),
        buscarProfissionaisOffline(),
        buscarPacientesOffline(),
        buscarProcedimentosOffline(),
      ]);
      const profName =
        entityName(
          (profs as ClinicaProfessional[]).find((p) => p.id === Number(selectedProfessional)) || {},
        ) || "Profissional";
      const intervalos =
        selectedProfessional && horariosOffline.length > 0
          ? intervalosEventsFromHorarios(selectedProfessional, horariosOffline, profName)
          : [];
      const temExpediente = Boolean(
        selectedProfessional && horariosOffline.some((h) => h.ativo),
      );
      if (Array.isArray(agendaRaw) && agendaRaw.length > 0) {
        let list = agendaRaw as Record<string, unknown>[];
        if (selectedProfessional) {
          list = list.filter((e) => String(e.professional) === selectedProfessional);
        }
        setOfflineEventos([...list.map((e) => formatarEvento(e, temExpediente)), ...intervalos]);
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
  }, [isOnline, loadOffline]);

  const [pendingEvents, setPendingEvents] = useState<AgendaEventData[]>([]);

  useEffect(() => {
    if (!isOnline) return;
    void obterFilaSync().then((fila) => {
      const pacs = patients;
      const procs = procedures;
      const profs = professionals;
      const temExpedienteCarregado = Boolean(
        selectedProfessional && horariosTrabalho.some((h) => h.ativo),
      );
      const events = fila
        .filter((f) => f.tipo === "agendamento")
        .map((item) => {
          const p = item.payload as Record<string, unknown>;
          const date = p.date ? new Date(String(p.date)) : new Date();
          const patient = pacs.find((x) => x.id === p.patient);
          const procedure = procs.find((x) => x.id === p.procedure);
          const professional = profs.find((x) => x.id === p.professional);
          const duration = procedure?.duration ?? 30;
          const endDate = new Date(date);
          endDate.setMinutes(endDate.getMinutes() + duration);
          return {
            id: `offline-${item.id}`,
            title:
              [entityName(patient || {}), entityName(procedure || {})].filter(Boolean).join(" • ") ||
              "Agendamento (pendente sync)",
            start: date.toISOString(),
            end: endDate.toISOString(),
            backgroundColor: "#a855f7",
            borderColor: "#9333ea",
            textColor: "#fff",
            ...(temExpedienteCarregado ? { constraint: "businessHours" as const } : {}),
            extendedProps: {
              dbId: `offline-${item.id}`,
              status: String(p.status || "SCHEDULED"),
              patient_name: entityName(patient || {}),
              patient_phone: "",
              professional_name: professional?.name ?? "",
              procedure_name: entityName(procedure || {}),
              procedure_duration: duration,
              procedure_price: String(procedure?.price ?? ""),
              notes: String(p.notes ?? ""),
            },
          } as AgendaEventData;
        });
      setPendingEvents(events);
    });
  }, [isOnline, patients, procedures, professionals, selectedProfessional, horariosTrabalho]);

  const eventosOnline = useMemo(() => {
    const temExpedienteCarregado = Boolean(
      selectedProfessional && horariosTrabalho.some((h) => h.ativo),
    );
    const rawEvents = Array.isArray(eventsQuery.data) ? eventsQuery.data : [];
    const eventosFormatados = rawEvents.map((ev: Record<string, unknown>) =>
      formatarEvento(ev, temExpedienteCarregado),
    );
    const bloqueiosAsEvents = bloqueiosToEvents(bloqueios);
    const profName =
      entityName(professionals.find((p) => p.id === Number(selectedProfessional)) || {}) ||
      "Profissional";
    const intervalos =
      selectedProfessional && horariosTrabalho.length > 0
        ? intervalosEventsFromHorarios(selectedProfessional, horariosTrabalho, profName)
        : [];
    return [...eventosFormatados, ...bloqueiosAsEvents, ...intervalos, ...pendingEvents];
  }, [
    bloqueios,
    eventsQuery.data,
    horariosTrabalho,
    pendingEvents,
    professionals,
    selectedProfessional,
  ]);

  const [eventos, setEventos] = useState<AgendaEventData[]>([]);

  useEffect(() => {
    const next = isOnline ? eventosOnline : offlineEventos;
    setEventos((prev) => (agendaEventsEqual(prev, next) ? prev : next));
  }, [eventosOnline, offlineEventos, isOnline]);

  const loading = isOnline
    ? professionalsQuery.isLoading ||
      patientsQuery.isLoading ||
      proceduresQuery.isLoading ||
      eventsQuery.isLoading
    : offlineLoading;

  const carregarDados = useCallback(async () => {
    if (!isOnline) {
      await loadOffline();
      return;
    }
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: clinicaBelezaQueryKeys.schedulingProfessionals() }),
      queryClient.invalidateQueries({ queryKey: clinicaBelezaQueryKeys.agendaPatients() }),
      queryClient.invalidateQueries({ queryKey: clinicaBelezaQueryKeys.procedures() }),
      queryClient.invalidateQueries({ queryKey: clinicaBelezaQueryKeys.nomesAgenda() }),
      queryClient.invalidateQueries({ queryKey: clinicaBelezaQueryKeys.locaisAtendimento() }),
      queryClient.invalidateQueries({
        queryKey: clinicaBelezaQueryKeys.horariosTrabalho(selectedProfessional),
      }),
      queryClient.invalidateQueries({
        queryKey: clinicaBelezaQueryKeys.agendaEvents(selectedProfessional),
      }),
      queryClient.invalidateQueries({
        queryKey: clinicaBelezaQueryKeys.agendaBloqueios(selectedProfessional),
      }),
    ]);
  }, [isOnline, loadOffline, queryClient, selectedProfessional]);

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
