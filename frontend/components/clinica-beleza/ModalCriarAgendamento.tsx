"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { ConvenioSelect } from "@/components/clinica-beleza/ConvenioSelect";
import { ProcedureMultiSelect } from "@/components/clinica-beleza/ProcedureMultiSelect";
import {
  PatientQuickRegisterField,
  type PatientQuickOption,
} from "@/components/clinica-beleza/PatientQuickRegisterField";
import { useNovaConsultaForm, type ConsultaFormProcedure } from "@/hooks/clinica-beleza/useNovaConsultaForm";
import { formatApiErrorBody } from "@/lib/api-errors";
import { ClinicaBelezaAPI, clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import type { LocalAtendimentoItem, NomeAgendaItem } from "@/lib/clinica-beleza-api";
import { entityName } from "@/lib/clinica-beleza-entities";
import { adicionarNaFilaSync } from "@/lib/offline-db";
import { notificarFilaAtualizada } from "@/hooks/useSyncPending";
import {
  type HorarioTrabalho,
  workHoursRejectionMessage,
} from "@/lib/clinica-beleza-work-hours";
import { calcularDuracaoAgendamento } from "@/lib/clinica-beleza-duracao";

interface Professional {
  id: number;
  name?: string;
  nome?: string;
  specialty?: string;
  especialidade?: string;
  tempo_consulta_minutos?: number | null;
}

export type ModalCriarAgendamentoMode = "agenda" | "consulta";

function formatTimeFromDate(date: Date): string {
  return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function formatDateInputValue(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

interface ModalCriarAgendamentoProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  selectedDate: Date | null;
  mode?: ModalCriarAgendamentoMode;
  defaultProfessionalId?: string;
  professionals: Professional[];
  patients: PatientQuickOption[];
  procedures: ConsultaFormProcedure[];
  nomesAgenda: NomeAgendaItem[];
  locaisAtendimento: LocalAtendimentoItem[];
  onPatientsChange: (patients: PatientQuickOption[]) => void;
  onSearchPatients?: (query: string) => Promise<PatientQuickOption[]>;
  onConsultaCreated?: (consultaId: number) => void;
  onOfflineEventCreated?: (event: unknown) => void;
}

export function ModalCriarAgendamento({
  open,
  onClose,
  onSuccess,
  selectedDate,
  mode = "agenda",
  defaultProfessionalId = "",
  professionals,
  patients,
  procedures,
  nomesAgenda,
  locaisAtendimento,
  onPatientsChange,
  onSearchPatients,
  onConsultaCreated,
  onOfflineEventCreated,
}: ModalCriarAgendamentoProps) {
  const isConsulta = mode === "consulta";
  const [time, setTime] = useState("09:00");
  const [dateInput, setDateInput] = useState("");
  const [notes, setNotes] = useState("");
  const [nomeAgendaId, setNomeAgendaId] = useState<number | "">("");
  const [localAtendimentoId, setLocalAtendimentoId] = useState<number | "">("");
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState("");
  const [horariosProfissional, setHorariosProfissional] = useState<HorarioTrabalho[]>([]);

  const {
    patientId,
    setPatientId,
    professionalId,
    setProfessionalId,
    convenioId,
    setConvenioId,
    selectedProcedures,
    convenios,
    precosMap,
    adicionarProcedimento,
    removerProcedimento,
    resumo,
    resetForm,
    validateBase,
  } = useNovaConsultaForm({ patients, procedures, enabled: open, requireProcedure: false });

  useEffect(() => {
    if (!open) return;
    resetForm();
    setConvenioId("");
    setProfessionalId(defaultProfessionalId ? Number(defaultProfessionalId) : "");
    setNomeAgendaId("");
    setLocalAtendimentoId("");
    const base = selectedDate ?? new Date();
    setDateInput(formatDateInputValue(base));
    setTime(formatTimeFromDate(base));
    setNotes("");
    setCreateError("");
  }, [open, selectedDate, defaultProfessionalId, resetForm, setConvenioId, setProfessionalId]);

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

  if (!open) return null;

  const handleCreatePatient = async (data: { nome: string; telefone: string; cpf: string }) => {
    const body: Record<string, string> = { nome: data.nome };
    if (data.telefone) body.telefone = data.telefone.replace(/\D/g, "");
    if (data.cpf) body.cpf = data.cpf.replace(/\D/g, "");
    const res = await clinicaBelezaFetch("/patients/", {
      method: "POST",
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(formatApiErrorBody(err) || "Erro ao cadastrar paciente");
    }
    return res.json();
  };

  const buildAppointmentDate = (): Date | null => {
    const dateSource = dateInput
      ? new Date(`${dateInput}T12:00:00`)
      : selectedDate;
    if (!dateSource) return null;
    const [h, m] = time.split(":").map(Number);
    const date = new Date(dateSource);
    date.setHours(h, m, 0, 0);
    return date;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationError = validateBase();
    if (validationError) {
      setCreateError(validationError.replace("cliente", "paciente"));
      return;
    }
    if (!nomeAgendaId) {
      setCreateError("Selecione o nome da agenda.");
      return;
    }
    const date = buildAppointmentDate();
    if (!date) {
      setCreateError("Data não definida.");
      return;
    }

    const localSel = localAtendimentoId
      ? locaisAtendimento.find((l) => l.id === localAtendimentoId)
      : undefined;
    const profSel = professionalId
      ? professionals.find((p) => p.id === professionalId)
      : undefined;
    const duracaoChecagem = calcularDuracaoAgendamento(
      resumo.duracao,
      profSel,
      localSel,
    );

    const horarioMsg = workHoursRejectionMessage(date, duracaoChecagem, horariosProfissional);
    if (horarioMsg) {
      setCreateError(horarioMsg);
      return;
    }

    setCreateLoading(true);
    setCreateError("");

    const basePayload: Record<string, unknown> = {
      patient: Number(patientId),
      professional: Number(professionalId),
      nome_agenda: Number(nomeAgendaId),
      notes: notes.trim() || null,
      date: date.toISOString(),
    };
    if (localAtendimentoId) basePayload.local_atendimento = Number(localAtendimentoId);
    if (convenioId) basePayload.convenio = Number(convenioId);
    if (selectedProcedures.length === 1) {
      basePayload.procedure = selectedProcedures[0];
    } else if (selectedProcedures.length > 1) {
      basePayload.procedures_ids = selectedProcedures;
      basePayload.procedure = selectedProcedures[0];
    }

    try {
      if (isConsulta) {
        const consulta = await ClinicaBelezaAPI.consultas.criar(basePayload);
        resetAndClose();
        onSuccess();
        if (consulta?.id != null) onConsultaCreated?.(Number(consulta.id));
        return;
      }

      const payload = { ...basePayload, status: "SCHEDULED" };

      if (!navigator.onLine) {
        await adicionarNaFilaSync({ tipo: "agendamento", payload });
        notificarFilaAtualizada();
        const patient = patients.find((p) => p.id === patientId);
        const professional = professionals.find((p) => p.id === professionalId);
        const procNames = selectedProcedures
          .map((id) => entityName(procedures.find((p) => p.id === id) || {}))
          .filter(Boolean)
          .join(", ");
        const nomeAgenda = nomesAgenda.find((a) => a.id === nomeAgendaId)?.nome;
        const titulo = [entityName(patient || {}), procNames || nomeAgenda || "Atendimento"]
          .filter(Boolean)
          .join(" • ") || "Agendamento (offline)";
        const tempId = `offline-${Date.now()}`;
        const endDate = new Date(date);
        endDate.setMinutes(endDate.getMinutes() + duracaoChecagem);

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
        throw new Error(formatApiErrorBody(data) || "Erro ao criar agendamento");
      }
      resetAndClose();
      onSuccess();
    } catch (err: unknown) {
      setCreateError(
        err instanceof Error
          ? err.message
          : isConsulta
            ? "Erro ao abrir consulta"
            : "Erro ao criar agendamento",
      );
    } finally {
      setCreateLoading(false);
    }
  };

  const resetAndClose = () => {
    resetForm();
    setTime("09:00");
    setDateInput("");
    setNotes("");
    setNomeAgendaId("");
    setLocalAtendimentoId("");
    setCreateError("");
    setCreateLoading(false);
    onClose();
  };

  const inputClass =
    "w-full px-3 py-2.5 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 min-h-[44px]";

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4 overflow-y-auto">
      <div
        className="bg-white dark:bg-neutral-800 rounded-t-xl sm:rounded-2xl shadow-2xl border border-gray-200 dark:border-neutral-700 w-full max-w-md sm:max-w-4xl sm:w-[calc(100vw-2rem)] max-h-[95vh] sm:max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center px-4 sm:px-6 py-4 border-b dark:border-neutral-700 shrink-0">
          <h2 className="text-lg font-bold text-gray-800 dark:text-gray-100">
            {isConsulta ? "Nova consulta" : "Novo Agendamento"}
          </h2>
          <button onClick={resetAndClose} className="p-1.5 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg" aria-label="Fechar">
            <X size={20} />
          </button>
        </div>

        <form className="flex-1 overflow-y-auto px-4 sm:px-6 py-4" onSubmit={handleSubmit}>
          {createError && (
            <div className="mb-4 p-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm">
              {createError}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Data *</label>
                  <input
                    type="date"
                    value={dateInput}
                    onChange={(e) => setDateInput(e.target.value)}
                    className={inputClass}
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Horário *</label>
                  <input type="time" value={time} onChange={(e) => setTime(e.target.value)} className={inputClass} required />
                </div>
              </div>

              <PatientQuickRegisterField
                patients={patients}
                patientId={patientId}
                onSelect={setPatientId}
                onClear={() => setPatientId("")}
                onPatientCreated={(p) => onPatientsChange([...patients, p])}
                onCreatePatient={handleCreatePatient}
                onSearchPatients={onSearchPatients}
                disabled={createLoading}
              />

              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Nome da agenda *</label>
                <select
                  value={nomeAgendaId}
                  onChange={(e) => setNomeAgendaId(e.target.value ? Number(e.target.value) : "")}
                  className={inputClass}
                  required
                >
                  <option value="">Selecione a agenda</option>
                  {nomesAgenda.map((a) => (
                    <option key={a.id} value={a.id}>{a.nome}</option>
                  ))}
                </select>
                {nomesAgenda.length === 0 && (
                  <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
                    Cadastre nomes de agenda em Consultas → ícone de calendário.
                  </p>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Local de atendimento
                </label>
                <select
                  value={localAtendimentoId}
                  onChange={(e) => setLocalAtendimentoId(e.target.value ? Number(e.target.value) : "")}
                  className={inputClass}
                >
                  <option value="">Selecione o local (opcional)</option>
                  {locaisAtendimento.map((l) => {
                    const valor = Number(l.valor_consulta).toLocaleString("pt-BR", {
                      style: "currency",
                      currency: "BRL",
                    });
                    const label = [l.nome, valor].filter(Boolean).join(" · ");
                    return (
                    <option key={l.id} value={l.id}>
                      {label}
                    </option>
                    );
                  })}
                </select>
                {locaisAtendimento.length === 0 && (
                  <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
                    Cadastre locais em Consultas → ícone de engrenagem.
                  </p>
                )}
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Profissional *</label>
                <select
                  value={professionalId}
                  onChange={(e) => setProfessionalId(e.target.value ? Number(e.target.value) : "")}
                  className={inputClass}
                  required
                >
                  <option value="">Selecione o profissional</option>
                  {professionals.map((p) => {
                    const tempo =
                      p.tempo_consulta_minutos != null && p.tempo_consulta_minutos > 0
                        ? `${p.tempo_consulta_minutos} min`
                        : null;
                    const label = [entityName(p), tempo].filter(Boolean).join(" · ");
                    return (
                      <option key={p.id} value={p.id}>{label}</option>
                    );
                  })}
                </select>
                {professionalId && horariosProfissional.length === 0 && (
                  <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
                    Profissional sem horário de trabalho cadastrado — o agendamento não será validado por expediente.
                  </p>
                )}
              </div>

              <ConvenioSelect convenios={convenios} value={convenioId} onChange={setConvenioId} hint="" className={inputClass} />

              <ProcedureMultiSelect
                procedures={procedures}
                selectedIds={selectedProcedures}
                onAdd={adicionarProcedimento}
                onRemove={removerProcedimento}
                convenioId={convenioId}
                precosMap={precosMap}
                optional
              />
              {selectedProcedures.length === 0 && (
                <p className="text-xs text-gray-500 dark:text-gray-400 -mt-2">
                  Opcional — use para orçamento ou atendimento de representante.
                </p>
              )}

              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Observações</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className={`${inputClass} resize-none min-h-[80px]`}
                  placeholder="Opcional"
                />
              </div>
            </div>
          </div>

          <div className="flex gap-3 pt-5 mt-2 border-t dark:border-neutral-700 shrink-0">
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
              {createLoading
                ? isConsulta
                  ? "Abrindo..."
                  : "Agendando..."
                : isConsulta
                  ? "Abrir consulta"
                  : "Agendar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
