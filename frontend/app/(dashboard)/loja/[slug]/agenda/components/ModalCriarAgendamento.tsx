"use client";

import { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";
import { ConvenioSelect } from "@/components/clinica-beleza/ConvenioSelect";
import { ProcedureMultiSelect } from "@/components/clinica-beleza/ProcedureMultiSelect";
import { useConvenioPrecos } from "@/hooks/clinica-beleza/useConvenioPrecos";
import { useConveniosList } from "@/hooks/clinica-beleza/useConveniosList";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { entityName, procedureDuration, procedurePrice } from "@/lib/clinica-beleza-entities";
import { precoProcedimento } from "@/lib/convenio-precos";
import { adicionarNaFilaSync } from "@/lib/offline-db";
import { notificarFilaAtualizada } from "@/hooks/useSyncPending";
import {
  type HorarioTrabalho,
  workHoursRejectionMessage,
} from "@/lib/clinica-beleza-work-hours";

interface Professional {
  id: number;
  name?: string;
  nome?: string;
  specialty?: string;
  especialidade?: string;
}

interface Patient {
  id: number;
  name?: string;
  nome?: string;
  convenio?: number | null;
}

interface Procedure {
  id: number;
  name?: string;
  nome?: string;
  duration?: number;
  duracao_minutos?: number;
  price?: string;
  preco?: string;
}

function formatTimeFromDate(date: Date): string {
  return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

interface ModalCriarAgendamentoProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  selectedDate: Date | null;
  defaultProfessionalId?: string;
  professionals: Professional[];
  patients: Patient[];
  procedures: Procedure[];
  onOfflineEventCreated?: (event: any) => void;
}

export function ModalCriarAgendamento({
  open,
  onClose,
  onSuccess,
  selectedDate,
  defaultProfessionalId = "",
  professionals,
  patients,
  procedures,
  onOfflineEventCreated,
}: ModalCriarAgendamentoProps) {
  const [patientId, setPatientId] = useState("");
  const [professionalId, setProfessionalId] = useState("");
  const [convenioId, setConvenioId] = useState<number | "">("");
  const [selectedProcedures, setSelectedProcedures] = useState<number[]>([]);
  const [time, setTime] = useState("09:00");
  const [notes, setNotes] = useState("");
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState("");
  const [horariosProfissional, setHorariosProfissional] = useState<HorarioTrabalho[]>([]);

  const convenios = useConveniosList(open);
  const precosMap = useConvenioPrecos(convenioId);

  useEffect(() => {
    if (!open) return;
    setPatientId("");
    setProfessionalId(defaultProfessionalId);
    setConvenioId("");
    setSelectedProcedures([]);
    setTime(selectedDate ? formatTimeFromDate(selectedDate) : "09:00");
    setNotes("");
    setCreateError("");
  }, [open, selectedDate, defaultProfessionalId]);

  useEffect(() => {
    if (!patientId) return;
    const paciente = patients.find((p) => p.id === parseInt(patientId, 10));
    setConvenioId(paciente?.convenio ?? "");
  }, [patientId, patients]);

  useEffect(() => {
    if (!open || !professionalId) {
      setHorariosProfissional([]);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const res = await clinicaBelezaFetch(`/professionals/${professionalId}/horarios-trabalho/`);
        if (!res.ok || cancelled) return;
        const data = await res.json();
        setHorariosProfissional(Array.isArray(data) ? data : []);
      } catch {
        if (!cancelled) setHorariosProfissional([]);
      }
    })();
    return () => { cancelled = true; };
  }, [open, professionalId]);

  const adicionarProcedimento = (id: number) => {
    if (id && !selectedProcedures.includes(id)) {
      setSelectedProcedures((prev) => [...prev, id]);
    }
  };

  const removerProcedimento = (id: number) => {
    setSelectedProcedures((prev) => prev.filter((p) => p !== id));
  };

  const resumo = useMemo(() => {
    let duracao = 0;
    let valor = 0;
    for (const id of selectedProcedures) {
      const proc = procedures.find((p) => p.id === id);
      if (proc) {
        duracao += procedureDuration(proc);
        const particular = Number(procedurePrice(proc)) || 0;
        valor += precoProcedimento(id, particular, convenioId, precosMap);
      }
    }
    return { duracao, valor };
  }, [selectedProcedures, procedures, convenioId, precosMap]);

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!patientId || !professionalId || selectedProcedures.length === 0) {
      setCreateError("Selecione paciente, profissional e pelo menos um procedimento.");
      return;
    }
    if (!selectedDate) {
      setCreateError("Data não definida.");
      return;
    }
    const [h, m] = time.split(":").map(Number);
    const date = new Date(selectedDate);
    date.setHours(h, m, 0, 0);

    const horarioMsg = workHoursRejectionMessage(date, resumo.duracao, horariosProfissional);
    if (horarioMsg) {
      setCreateError(horarioMsg);
      return;
    }

    setCreateLoading(true);
    setCreateError("");

    const payload: Record<string, unknown> = {
      date: date.toISOString(),
      status: "SCHEDULED",
      patient: parseInt(patientId, 10),
      professional: parseInt(professionalId, 10),
      notes: notes.trim() || null,
    };
    if (convenioId) {
      payload.convenio = Number(convenioId);
    }

    if (selectedProcedures.length === 1) {
      payload.procedure = selectedProcedures[0];
    } else {
      payload.procedures_ids = selectedProcedures;
      payload.procedure = selectedProcedures[0];
    }

    try {
      if (!navigator.onLine) {
        await adicionarNaFilaSync({ tipo: "agendamento", payload });
        notificarFilaAtualizada();
        const patient = patients.find((p) => p.id === parseInt(patientId, 10));
        const professional = professionals.find((p) => p.id === parseInt(professionalId, 10));
        const procNames = selectedProcedures
          .map((id) => entityName(procedures.find((p) => p.id === id) || {}))
          .filter(Boolean)
          .join(", ");
        const titulo = [entityName(patient || {}), procNames].filter(Boolean).join(" • ") || "Agendamento (offline)";
        const tempId = `offline-${Date.now()}`;
        const endDate = new Date(date);
        endDate.setMinutes(endDate.getMinutes() + resumo.duracao);

        if (onOfflineEventCreated) {
          onOfflineEventCreated({
            id: tempId,
            title: titulo,
            start: date.toISOString(),
            end: endDate.toISOString(),
            backgroundColor: "#a855f7",
            borderColor: "#9333ea",
            textColor: "#fff",
            extendedProps: {
              dbId: tempId,
              status: "SCHEDULED",
              patient_name: entityName(patient || {}),
              patient_phone: "",
              professional_name: entityName(professional || {}),
              procedure_name: procNames,
              procedure_duration: resumo.duracao,
              procedure_price: resumo.valor,
              notes: notes.trim() || "",
            },
          });
        }
        resetAndClose();
        return;
      }
      const res = await clinicaBelezaFetch("/agenda/create/", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || "Erro ao criar agendamento");
      }
      resetAndClose();
      onSuccess();
    } catch (err: unknown) {
      setCreateError(err instanceof Error ? err.message : "Erro ao criar agendamento");
    } finally {
      setCreateLoading(false);
    }
  };

  const resetAndClose = () => {
    setPatientId("");
    setProfessionalId("");
    setConvenioId("");
    setSelectedProcedures([]);
    setTime("09:00");
    setNotes("");
    setCreateError("");
    setCreateLoading(false);
    onClose();
  };

  const selectClass = "w-full px-3 py-2 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700";

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-md w-full max-h-[85vh] flex flex-col">
        <div className="flex justify-between items-center px-5 py-4 border-b dark:border-neutral-700 shrink-0">
          <h2 className="text-lg font-bold text-gray-800 dark:text-gray-100">Novo Agendamento</h2>
          <button
            onClick={resetAndClose}
            className="p-1.5 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg"
          >
            <X size={20} />
          </button>
        </div>
        <form className="flex-1 overflow-y-auto px-5 py-4 space-y-3" onSubmit={handleSubmit}>
          {createError && (
            <div className="p-2 rounded bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm">{createError}</div>
          )}

          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Data</label>
              <p className="text-sm text-gray-800 dark:text-gray-200 font-medium py-2">
                {selectedDate ? selectedDate.toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit", month: "short" }) : "—"}
              </p>
            </div>
            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Horário</label>
              <input
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                className={selectClass}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Paciente *</label>
            <select
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              className={selectClass}
              required
            >
              <option value="">Selecione o paciente</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>{entityName(p)}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Profissional *</label>
            <select
              value={professionalId}
              onChange={(e) => setProfessionalId(e.target.value)}
              className={selectClass}
              required
            >
              <option value="">Selecione o profissional</option>
              {professionals.map((p) => (
                <option key={p.id} value={p.id}>{entityName(p)}</option>
              ))}
            </select>
          </div>

          <ConvenioSelect
            convenios={convenios}
            value={convenioId}
            onChange={setConvenioId}
            hint=""
            className={selectClass}
          />

          <ProcedureMultiSelect
            procedures={procedures}
            selectedIds={selectedProcedures}
            onAdd={adicionarProcedimento}
            onRemove={removerProcedimento}
            convenioId={convenioId}
            precosMap={precosMap}
          />

          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Observações</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              className={`${selectClass} resize-none`}
              placeholder="Opcional"
            />
          </div>
          <div className="flex gap-3 pt-4 border-t dark:border-neutral-700 shrink-0">
            <button
              type="button"
              onClick={resetAndClose}
              className="flex-1 py-2.5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={createLoading}
              className="flex-1 py-2.5 rounded-lg bg-purple-600 text-white text-sm font-medium hover:bg-purple-700 disabled:opacity-50"
            >
              {createLoading ? "Agendando..." : "Agendar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
