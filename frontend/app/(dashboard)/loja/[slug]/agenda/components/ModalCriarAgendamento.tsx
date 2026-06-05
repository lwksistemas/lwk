"use client";

import { useEffect, useMemo, useState } from "react";
import { X, Trash2 } from "lucide-react";
import { ClinicaBelezaAPI, clinicaBelezaFetch, type ConvenioItem } from "@/lib/clinica-beleza-api";
import { buildPrecosMap, CONVENIO_PARTICULAR_LABEL, precoProcedimento } from "@/lib/convenio-precos";
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

function gName(o: { name?: string; nome?: string }): string {
  return o.name || o.nome || "";
}
function gDuration(o: { duration?: number; duracao_minutos?: number }): number {
  return o.duration ?? o.duracao_minutos ?? 30;
}
function gPrice(o: { price?: string; preco?: string }): number {
  return Number(o.price || o.preco) || 0;
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
  const [convenioId, setConvenioId] = useState("");
  const [convenios, setConvenios] = useState<ConvenioItem[]>([]);
  const [precosMap, setPrecosMap] = useState<Record<number, number>>({});
  const [selectedProcedures, setSelectedProcedures] = useState<number[]>([]);
  const [time, setTime] = useState("09:00");
  const [notes, setNotes] = useState("");
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState("");
  const [horariosProfissional, setHorariosProfissional] = useState<HorarioTrabalho[]>([]);

  useEffect(() => {
    if (!open) return;
    setPatientId("");
    setProfessionalId(defaultProfessionalId);
    setConvenioId("");
    setPrecosMap({});
    setSelectedProcedures([]);
    setTime(selectedDate ? formatTimeFromDate(selectedDate) : "09:00");
    setNotes("");
    setCreateError("");
    ClinicaBelezaAPI.convenios.list()
      .then((rows) => setConvenios(Array.isArray(rows) ? rows : []))
      .catch(() => setConvenios([]));
  }, [open, selectedDate, defaultProfessionalId]);

  useEffect(() => {
    if (!patientId) return;
    const paciente = patients.find((p) => p.id === parseInt(patientId, 10));
    setConvenioId(paciente?.convenio ? String(paciente.convenio) : "");
  }, [patientId, patients]);

  useEffect(() => {
    if (!convenioId) {
      setPrecosMap({});
      return;
    }
    ClinicaBelezaAPI.convenios.precos(Number(convenioId))
      .then((rows) => setPrecosMap(buildPrecosMap(rows)))
      .catch(() => setPrecosMap({}));
  }, [convenioId]);

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

  // Procedimentos disponíveis (exclui os já selecionados)
  const procedimentosDisponiveis = useMemo(
    () => procedures.filter((p) => !selectedProcedures.includes(p.id)),
    [procedures, selectedProcedures],
  );

  const adicionarProcedimento = (id: number) => {
    if (id && !selectedProcedures.includes(id)) {
      setSelectedProcedures((prev) => [...prev, id]);
    }
  };

  const removerProcedimento = (id: number) => {
    setSelectedProcedures((prev) => prev.filter((p) => p !== id));
  };

  // Duração e valor total
  const resumo = useMemo(() => {
    let duracao = 0;
    let valor = 0;
    for (const id of selectedProcedures) {
      const proc = procedures.find((p) => p.id === id);
      if (proc) {
        duracao += gDuration(proc);
        valor += precoProcedimento(id, gPrice(proc), convenioId ? Number(convenioId) : "", precosMap);
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
      payload.convenio = parseInt(convenioId, 10);
    }

    // Múltiplos procedimentos: envia procedures_ids
    if (selectedProcedures.length === 1) {
      payload.procedure = selectedProcedures[0];
    } else {
      payload.procedures_ids = selectedProcedures;
      payload.procedure = selectedProcedures[0]; // principal para retrocompatibilidade
    }

    try {
      if (!navigator.onLine) {
        await adicionarNaFilaSync({ tipo: "agendamento", payload });
        notificarFilaAtualizada();
        const patient = patients.find((p) => p.id === parseInt(patientId, 10));
        const professional = professionals.find((p) => p.id === parseInt(professionalId, 10));
        const procNames = selectedProcedures
          .map((id) => gName(procedures.find((p) => p.id === id) || {}))
          .filter(Boolean)
          .join(", ");
        const titulo = [gName(patient || {}), procNames].filter(Boolean).join(" • ") || "Agendamento (offline)";
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
              patient_name: gName(patient || {}),
              patient_phone: "",
              professional_name: gName(professional || {}),
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
    setPrecosMap({});
    setSelectedProcedures([]);
    setTime("09:00");
    setNotes("");
    setCreateError("");
    setCreateLoading(false);
    onClose();
  };

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

          {/* Data e Horário */}
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
                className="w-full px-3 py-2 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700"
              />
            </div>
          </div>

          {/* Paciente */}
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Paciente *</label>
            <select
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              className="w-full px-3 py-2 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700"
              required
            >
              <option value="">Selecione o paciente</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>{gName(p)}</option>
              ))}
            </select>
          </div>

          {/* Profissional */}
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Profissional *</label>
            <select
              value={professionalId}
              onChange={(e) => setProfessionalId(e.target.value)}
              className="w-full px-3 py-2 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700"
              required
            >
              <option value="">Selecione o profissional</option>
              {professionals.map((p) => (
                <option key={p.id} value={p.id}>{gName(p)}</option>
              ))}
            </select>
          </div>

          {/* Convênio */}
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Convênio</label>
            <select
              value={convenioId}
              onChange={(e) => setConvenioId(e.target.value)}
              className="w-full px-3 py-2 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700"
            >
              <option value="">{CONVENIO_PARTICULAR_LABEL}</option>
              {convenios.map((c) => (
                <option key={c.id} value={c.id}>{c.nome}</option>
              ))}
            </select>
          </div>

          {/* Procedimentos (múltiplos) */}
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              Procedimentos * <span className="font-normal text-gray-400">(pode adicionar vários)</span>
            </label>
            <select
              className="w-full px-3 py-2 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700"
              value=""
              onChange={(e) => {
                const id = Number(e.target.value);
                if (id) adicionarProcedimento(id);
              }}
            >
              <option value="">Adicionar procedimento...</option>
              {procedimentosDisponiveis.map((p) => (
                <option key={p.id} value={p.id}>{gName(p)} ({gDuration(p)} min)</option>
              ))}
            </select>

            {selectedProcedures.length > 0 && (
              <div className="mt-2 space-y-1.5">
                {selectedProcedures.map((id) => {
                  const proc = procedures.find((p) => p.id === id);
                  if (!proc) return null;
                  const valorProc = precoProcedimento(
                    id,
                    gPrice(proc),
                    convenioId ? Number(convenioId) : "",
                    precosMap,
                  );
                  return (
                    <div key={id} className="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-neutral-700/50 rounded-lg">
                      <div className="text-sm">
                        <span className="font-medium text-gray-800 dark:text-gray-200">{gName(proc)}</span>
                        <span className="text-gray-500 dark:text-gray-400 ml-2 text-xs">
                          {gDuration(proc)}min
                          {valorProc > 0 ? ` · R$ ${valorProc.toFixed(2)}` : ""}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => removerProcedimento(id)}
                        className="p-1 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  );
                })}
                <div className="flex items-center justify-between px-3 py-1.5 text-xs text-gray-600 dark:text-gray-400 border-t dark:border-neutral-600 pt-2">
                  <span>Duração total: <strong>{resumo.duracao} min</strong></span>
                  {resumo.valor > 0 && <span>Valor: <strong>R$ {resumo.valor.toFixed(2)}</strong></span>}
                </div>
              </div>
            )}
          </div>

          {/* Observações */}
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Observações</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 resize-none"
              placeholder="Opcional"
            />
          </div>
        </form>
        <div className="flex gap-3 px-5 py-4 border-t dark:border-neutral-700 shrink-0">
          <button
            type="button"
            onClick={resetAndClose}
            className="flex-1 py-2.5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleSubmit as any}
            disabled={createLoading}
            className="flex-1 py-2.5 rounded-lg bg-purple-600 text-white text-sm font-medium hover:bg-purple-700 disabled:opacity-50"
          >
            {createLoading ? "Agendando..." : "Agendar"}
          </button>
        </div>
      </div>
    </div>
  );
}
