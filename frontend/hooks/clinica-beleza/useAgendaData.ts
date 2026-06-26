"use client";

import { useCallback, useRef, useState } from "react";
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
import { clinicaBelezaFetch, parseClinicaBelezaListResponse } from "@/lib/clinica-beleza-api";
import type { LocalAtendimentoItem, NomeAgendaItem } from "@/lib/clinica-beleza-api";
import {
  intervalosEventsFromHorarios,
} from "@/lib/clinica-beleza-work-hours";
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

function horariosEqual(a: HorarioTrabalhoRow[], b: HorarioTrabalhoRow[]): boolean {
  if (a.length !== b.length) return false;
  return JSON.stringify(a) === JSON.stringify(b);
}

export function useAgendaData(selectedProfessional: string) {
  const [eventos, setEventos] = useState<AgendaEventData[]>([]);
  const [loading, setLoading] = useState(true);
  const [professionals, setProfessionals] = useState<ClinicaProfessional[]>([]);
  const [horariosTrabalho, setHorariosTrabalho] = useState<HorarioTrabalhoRow[]>([]);
  const [patients, setPatients] = useState<ClinicaPatient[]>([]);
  const [procedures, setProcedures] = useState<ClinicaProcedure[]>([]);
  const [nomesAgenda, setNomesAgenda] = useState<NomeAgendaItem[]>([]);
  const [locaisAtendimento, setLocaisAtendimento] = useState<LocalAtendimentoItem[]>([]);
  const [bloqueios, setBloqueios] = useState<BloqueioHorario[]>([]);
  const horariosTrabalhoRef = useRef<HorarioTrabalhoRow[]>([]);

  const carregarDados = useCallback(async () => {
    try {
      const online = typeof navigator !== "undefined" && navigator.onLine;
      if (online) {
        const agendaPath = selectedProfessional
          ? `/agenda/?professional=${selectedProfessional}`
          : "/agenda/";
        const bloqueiosPath = selectedProfessional
          ? `/bloqueios/?professional=${selectedProfessional}`
          : "/bloqueios/";
        const horariosReq = selectedProfessional
          ? clinicaBelezaFetch(`/professionals/${selectedProfessional}/horarios-trabalho/`)
          : Promise.resolve(null);
        const [resEv, resBl, resProf, resPat, resProc, resHor, resAgendas, resLocais] =
          await Promise.all([
            clinicaBelezaFetch(agendaPath),
            clinicaBelezaFetch(bloqueiosPath),
            clinicaBelezaFetch("/professionals/?page=1&page_size=200&scheduling=true"),
            clinicaBelezaFetch("/patients/?page=1&page_size=500"),
            clinicaBelezaFetch("/procedures/?page=1&page_size=200"),
            horariosReq,
            clinicaBelezaFetch("/nomes-agenda/"),
            clinicaBelezaFetch("/locais-atendimento/"),
          ]);

        const profs: ClinicaProfessional[] = resProf.ok
          ? parseClinicaBelezaListResponse<ClinicaProfessional>(await resProf.json())
          : [];
        const pacs: ClinicaPatient[] = resPat.ok
          ? parseClinicaBelezaListResponse<ClinicaPatient>(await resPat.json())
          : [];
        const procs: ClinicaProcedure[] = resProc.ok
          ? parseClinicaBelezaListResponse<ClinicaProcedure>(await resProc.json())
          : [];
        const agendas: NomeAgendaItem[] = resAgendas.ok ? await resAgendas.json() : [];
        const locais: LocalAtendimentoItem[] = resLocais.ok ? await resLocais.json() : [];
        setNomesAgenda(Array.isArray(agendas) ? agendas : []);
        setLocaisAtendimento(Array.isArray(locais) ? locais : []);

        let horariosAtivos: HorarioTrabalhoRow[] = [];
        if (resHor?.ok) {
          horariosAtivos = await resHor.json();
          if (!horariosEqual(horariosTrabalhoRef.current, horariosAtivos)) {
            horariosTrabalhoRef.current = horariosAtivos;
            setHorariosTrabalho(horariosAtivos);
          }
        } else if (horariosTrabalhoRef.current.length > 0) {
          horariosTrabalhoRef.current = [];
          setHorariosTrabalho([]);
        }

        if (profs.length) {
          setProfessionals(profs);
          await salvarProfissionaisOffline(profs);
        }
        if (pacs.length) {
          setPatients(pacs);
          await salvarPacientesOffline(pacs);
        }
        if (procs.length) {
          setProcedures(procs);
          await salvarProcedimentosOffline(procs);
        }

        const temExpedienteCarregado = Boolean(
          selectedProfessional && horariosAtivos.some((h) => h.ativo),
        );

        let eventosFormatados: AgendaEventData[] = [];
        if (resEv.ok) {
          const data = await resEv.json();
          await salvarAgendamentosOffline(data);
          eventosFormatados = data.map((ev: Record<string, unknown>) =>
            formatarEvento(ev, temExpedienteCarregado),
          );
        }

        let bloqueiosAsEvents: AgendaEventData[] = [];
        if (resBl.ok) {
          const bloqueiosList: BloqueioHorario[] = await resBl.json();
          setBloqueios(bloqueiosList);
          bloqueiosAsEvents = bloqueiosList.map((b) => {
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

        const profName =
          entityName(profs.find((p) => p.id === Number(selectedProfessional)) || {}) ||
          "Profissional";
        const intervalos =
          selectedProfessional && horariosAtivos.length > 0
            ? intervalosEventsFromHorarios(selectedProfessional, horariosAtivos, profName)
            : [];

        const fila = await obterFilaSync();
        const pendingEvents = fila
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

        const nextEventos = [
          ...eventosFormatados,
          ...bloqueiosAsEvents,
          ...intervalos,
          ...pendingEvents,
        ];
        setEventos((prev) => (agendaEventsEqual(prev, nextEventos) ? prev : nextEventos));
      } else {
        const horariosOffline = horariosTrabalhoRef.current;
        const [agendaRaw, profs, pacs, procs] = await Promise.all([
          buscarAgendamentosOffline(),
          buscarProfissionaisOffline(),
          buscarPacientesOffline(),
          buscarProcedimentosOffline(),
        ]);
        if (Array.isArray(profs)) setProfessionals(profs as ClinicaProfessional[]);
        if (Array.isArray(pacs)) setPatients(pacs as ClinicaPatient[]);
        if (Array.isArray(procs)) setProcedures(procs as ClinicaProcedure[]);
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
          const nextEventos = [
            ...list.map((e) => formatarEvento(e, temExpediente)),
            ...intervalos,
          ];
          setEventos((prev) => (agendaEventsEqual(prev, nextEventos) ? prev : nextEventos));
        } else {
          setEventos((prev) => (agendaEventsEqual(prev, intervalos) ? prev : intervalos));
        }
      }
      setLoading(false);
    } catch (error) {
      logger.warn("Erro ao carregar dados:", error);
      setLoading(false);
    }
  }, [selectedProfessional]);

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
