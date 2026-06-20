"use client";

import { useEffect, useState } from "react";
import { ChevronDown, ChevronUp, X } from "lucide-react";
import { ConvenioSelect } from "@/components/clinica-beleza/ConvenioSelect";
import { ProcedureMultiSelect } from "@/components/clinica-beleza/ProcedureMultiSelect";
import {
  PatientQuickRegisterField,
  type PatientQuickOption,
} from "@/components/clinica-beleza/PatientQuickRegisterField";
import { useNovaConsultaForm, type ConsultaFormProcedure } from "@/hooks/clinica-beleza/useNovaConsultaForm";
import { formatApiErrorBody } from "@/lib/api-errors";
import { ClinicaBelezaAPI, clinicaBelezaFetch, type RetornoVerificacaoResult } from "@/lib/clinica-beleza-api";
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
  const [retornoInfo, setRetornoInfo] = useState<RetornoVerificacaoResult | null>(null);
  const [retornoProcedureId, setRetornoProcedureId] = useState<number | "">("");
  const [verificandoRetorno, setVerificandoRetorno] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const nomeAgendaUnico = nomesAgenda.length === 1 ? nomesAgenda[0] : null;

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
    setRetornoInfo(null);
    setRetornoProcedureId("");
    setShowAdvanced(false);
  }, [open, selectedDate, defaultProfessionalId, resetForm, setConvenioId, setProfessionalId]);

  useEffect(() => {
    if (!open || !nomeAgendaUnico) return;
    setNomeAgendaId(nomeAgendaUnico.id);
  }, [open, nomeAgendaUnico]);

  useEffect(() => {
    if (!open || !patientId) {
      setRetornoInfo(null);
      return;
    }
    let cancelled = false;
    const timer = setTimeout(async () => {
      setVerificandoRetorno(true);
      try {
        const procedureIds = [...selectedProcedures];
        if (retornoProcedureId && !procedureIds.includes(Number(retornoProcedureId))) {
          procedureIds.push(Number(retornoProcedureId));
        }
        const result = await ClinicaBelezaAPI.retorno.verificar({
          patient_id: Number(patientId),
          procedure_ids: procedureIds.length ? procedureIds : undefined,
          retorno_procedure_id: retornoProcedureId ? Number(retornoProcedureId) : undefined,
        });
        if (!cancelled) setRetornoInfo(result);
      } catch {
        if (!cancelled) setRetornoInfo(null);
      } finally {
        if (!cancelled) setVerificandoRetorno(false);
      }
    }, 350);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [open, patientId, selectedProcedures, retornoProcedureId]);

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
    if (retornoProcedureId) {
      basePayload.retorno_procedure = Number(retornoProcedureId);
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

  const localSel = localAtendimentoId
    ? locaisAtendimento.find((l) => l.id === localAtendimentoId)
    : undefined;
  const taxaConsultaBase = localSel ? Number(localSel.valor_consulta) || 0 : 0;
  const taxaConsulta = retornoInfo?.elegivel ? 0 : taxaConsultaBase;
  const totalEstimado = taxaConsulta + resumo.valor;
  const regrasRetornoProc = retornoInfo?.regras_procedimento ?? [];
  const retornoProcAtivo = retornoInfo?.config?.retorno_procedimento_ativo ?? false;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4">
      <div
        className="bg-white dark:bg-neutral-800 rounded-t-xl sm:rounded-2xl shadow-2xl border border-gray-200 dark:border-neutral-700 w-full max-w-lg sm:max-w-xl max-h-[92dvh] sm:max-h-[88vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center px-4 py-3 border-b dark:border-neutral-700 shrink-0">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-gray-800 dark:text-gray-100">
              {isConsulta ? "Nova consulta" : "Novo Agendamento"}
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Preencha paciente, data e profissional para agendar.
            </p>
          </div>
          <button onClick={resetAndClose} className="p-1.5 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg shrink-0" aria-label="Fechar">
            <X size={20} />
          </button>
        </div>

        <form className="flex flex-col flex-1 min-h-0" onSubmit={handleSubmit}>
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
            {createError && (
              <div className="p-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm">
                {createError}
              </div>
            )}

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

            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Profissional *</label>
              <select
                value={professionalId}
                onChange={(e) => setProfessionalId(e.target.value ? Number(e.target.value) : "")}
                className={inputClass}
                required
              >
                <option value="">Selecione o profissional</option>
                {professionals.map((p) => (
                  <option key={p.id} value={p.id}>{entityName(p)}</option>
                ))}
              </select>
            </div>

            {nomeAgendaUnico ? (
              <div className="rounded-lg border border-purple-100 dark:border-purple-900/40 bg-purple-50/60 dark:bg-purple-950/20 px-3 py-2 text-sm text-purple-900 dark:text-purple-200">
                <span className="text-xs text-purple-700 dark:text-purple-300 block mb-0.5">Agenda</span>
                {nomeAgendaUnico.nome}
              </div>
            ) : (
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
            )}

            {retornoInfo?.elegivel && patientId && (
              <div className="p-2.5 rounded-lg text-sm bg-emerald-50 dark:bg-emerald-900/20 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                <span className="font-medium">Retorno gratuito</span>
                <span className="block text-xs mt-0.5">{retornoInfo.mensagem}</span>
              </div>
            )}

            <button
              type="button"
              onClick={() => setShowAdvanced((v) => !v)}
              className="w-full flex items-center justify-between gap-2 px-3 py-2.5 rounded-lg border border-dashed border-gray-300 dark:border-neutral-600 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700/50"
            >
              <span>Mais opções (local, convênio, procedimentos…)</span>
              {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>

            {showAdvanced && (
              <div className="space-y-3 pt-1 border-t border-gray-100 dark:border-neutral-700">
                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Local de atendimento
                  </label>
                  <select
                    value={localAtendimentoId}
                    onChange={(e) => setLocalAtendimentoId(e.target.value ? Number(e.target.value) : "")}
                    className={inputClass}
                  >
                    <option value="">Opcional</option>
                    {locaisAtendimento.map((l) => (
                      <option key={l.id} value={l.id}>{l.nome}</option>
                    ))}
                  </select>
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

                {retornoProcAtivo && regrasRetornoProc.length > 0 && patientId && (
                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Retorno do procedimento
                    </label>
                    <select
                      value={retornoProcedureId}
                      onChange={(e) => setRetornoProcedureId(e.target.value ? Number(e.target.value) : "")}
                      className={inputClass}
                    >
                      <option value="">Não é retorno de procedimento</option>
                      {regrasRetornoProc.map((r) => (
                        <option key={r.id} value={r.procedure}>
                          {r.procedure_name} — prazo {r.dias_retorno} dias
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {verificandoRetorno && patientId && !retornoInfo?.elegivel && (
                  <p className="text-xs text-gray-500 dark:text-gray-400">Verificando retorno...</p>
                )}

                {localAtendimentoId && (
                  <div className="p-3 rounded-lg bg-gray-50 dark:bg-neutral-800/80 text-sm space-y-1">
                    <div className="flex justify-between text-gray-600 dark:text-gray-400">
                      <span>Taxa de consulta</span>
                      <span>
                        {retornoInfo?.elegivel ? (
                          <>
                            <span className="line-through opacity-60 mr-1">
                              {taxaConsultaBase.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}
                            </span>
                            <span className="text-emerald-600 dark:text-emerald-400 font-medium">R$ 0,00</span>
                          </>
                        ) : (
                          taxaConsultaBase.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
                        )}
                      </span>
                    </div>
                    {resumo.valor > 0 && (
                      <div className="flex justify-between text-gray-600 dark:text-gray-400">
                        <span>Procedimentos</span>
                        <span>{resumo.valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</span>
                      </div>
                    )}
                    <div className="flex justify-between font-medium text-gray-900 dark:text-gray-100 pt-1 border-t border-gray-200 dark:border-neutral-700">
                      <span>Total estimado</span>
                      <span>{totalEstimado.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</span>
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Observações</label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={2}
                    className={`${inputClass} resize-none min-h-[64px]`}
                    placeholder="Opcional"
                  />
                </div>
              </div>
            )}
          </div>

          <div className="flex gap-3 px-4 py-3 border-t dark:border-neutral-700 shrink-0 bg-white dark:bg-neutral-800">
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
