"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { getClinicaBelezaBaseUrl, getClinicaBelezaHeaders } from "@/lib/clinica-beleza-api";
import { adicionarNaFilaSync } from "@/lib/offline-db";
import { notificarFilaAtualizada } from "@/hooks/useSyncPending";

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

function gName(o: { name?: string; nome?: string }): string {
  return o.name || o.nome || "";
}
function gDuration(o: { duration?: number; duracao_minutos?: number }): number {
  return o.duration ?? o.duracao_minutos ?? 30;
}

interface ModalCriarAgendamentoProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  selectedDate: Date | null;
  professionals: Professional[];
  patients: Patient[];
  procedures: Procedure[];
  /** Append a temporary offline event to the calendar */
  onOfflineEventCreated?: (event: any) => void;
}

export function ModalCriarAgendamento({
  open,
  onClose,
  onSuccess,
  selectedDate,
  professionals,
  patients,
  procedures,
  onOfflineEventCreated,
}: ModalCriarAgendamentoProps) {
  const [createForm, setCreateForm] = useState({
    patientId: "",
    professionalId: "",
    procedureId: "",
    time: selectedDate
      ? selectedDate.getHours().toString().padStart(2, "0") + ":" + selectedDate.getMinutes().toString().padStart(2, "0")
      : "09:00",
    notes: "",
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState("");

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.patientId || !createForm.professionalId || !createForm.procedureId) {
      setCreateError("Selecione paciente, profissional e procedimento.");
      return;
    }
    if (!selectedDate) {
      setCreateError("Data não definida.");
      return;
    }
    const [h, m] = createForm.time.split(":").map(Number);
    const date = new Date(selectedDate);
    date.setHours(h, m, 0, 0);
    setCreateLoading(true);
    setCreateError("");
    const payload = {
      date: date.toISOString(),
      status: "SCHEDULED",
      patient: parseInt(createForm.patientId, 10),
      professional: parseInt(createForm.professionalId, 10),
      procedure: parseInt(createForm.procedureId, 10),
      notes: createForm.notes.trim() || null,
    };
    try {
      if (!navigator.onLine) {
        await adicionarNaFilaSync({ tipo: "agendamento", payload });
        notificarFilaAtualizada();
        const patient = patients.find((p) => p.id === parseInt(createForm.patientId, 10));
        const professional = professionals.find((p) => p.id === parseInt(createForm.professionalId, 10));
        const procedure = procedures.find((p) => p.id === parseInt(createForm.procedureId, 10));
        const titulo = [gName(patient || {}), gName(procedure || {})].filter(Boolean).join(" • ") || "Agendamento (offline)";
        const tempId = `offline-${Date.now()}`;
        const endDate = new Date(date);
        endDate.setMinutes(endDate.getMinutes() + (procedure?.duration ?? 30));

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
              patient_name: gName(patient || {}),
              patient_phone: "",
              professional_name: professional?.name ?? "",
              procedure_name: gName(procedure || {}),
              procedure_duration: procedure?.duration ?? 30,
              procedure_price: procedure?.price ?? "",
              notes: createForm.notes.trim() || "",
            },
          });
        }
        resetAndClose();
        return;
      }
      const baseURL = getClinicaBelezaBaseUrl();
      const headers = getClinicaBelezaHeaders();
      const res = await fetch(`${baseURL}/agenda/create/`, {
        method: "POST",
        headers,
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
    setCreateForm({ patientId: "", professionalId: "", procedureId: "", time: "09:00", notes: "" });
    setCreateError("");
    setCreateLoading(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-4 border-b dark:border-neutral-700">
          <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Novo Agendamento</h2>
          <button
            onClick={resetAndClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>
        <form className="p-4 space-y-3" onSubmit={handleSubmit}>
          {createError && (
            <div className="p-2 rounded bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm">{createError}</div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data</label>
            <p className="text-gray-800 dark:text-gray-200 font-medium">
              {selectedDate ? selectedDate.toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit", month: "short" }) : "—"}
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Horário</label>
            <input
              type="time"
              value={createForm.time}
              onChange={(e) => setCreateForm((f) => ({ ...f, time: e.target.value }))}
              className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Paciente *</label>
            <select
              value={createForm.patientId}
              onChange={(e) => setCreateForm((f) => ({ ...f, patientId: e.target.value }))}
              className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
              required
            >
              <option value="">Selecione o paciente</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>{gName(p)}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Profissional *</label>
            <select
              value={createForm.professionalId}
              onChange={(e) => setCreateForm((f) => ({ ...f, professionalId: e.target.value }))}
              className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
              required
            >
              <option value="">Selecione o profissional</option>
              {professionals.map((p) => (
                <option key={p.id} value={p.id}>{gName(p)}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Procedimento *</label>
            <select
              value={createForm.procedureId}
              onChange={(e) => setCreateForm((f) => ({ ...f, procedureId: e.target.value }))}
              className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
              required
            >
              <option value="">Selecione o procedimento</option>
              {procedures.map((p) => (
                <option key={p.id} value={p.id}>{gName(p)} ({gDuration(p)} min)</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Observações</label>
            <textarea
              value={createForm.notes}
              onChange={(e) => setCreateForm((f) => ({ ...f, notes: e.target.value }))}
              rows={2}
              className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 resize-none"
              placeholder="Opcional"
            />
          </div>
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={resetAndClose}
              className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 text-gray-700 dark:text-gray-300"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={createLoading}
              className="flex-1 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50"
            >
              {createLoading ? "Agendando..." : "Agendar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
