"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { ArrowLeft, CalendarDays, ChevronDown, ChevronUp, Loader2, Save } from "lucide-react";
import { ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
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

function resolveDefaultNomeAgendaId(items: NomeAgendaItem[]): number | "" {
  if (items.length === 0) return "";
  const padrao = items.find((n) => n.is_padrao);
  return padrao?.id ?? items[0].id;
}

function resolveDefaultLocalId(items: LocalAtendimentoItem[]): number | "" {
  if (items.length === 0) return "";
  const padrao = items.find((l) => l.is_padrao);
  return padrao?.id ?? items[0].id;
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
  accentColor?: string;
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
      {children}
    </label>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-neutral-800 pb-2">
      {children}
    </p>
  );
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
  accentColor = CLINICA_BELEZA_PRIMARY,
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
  const [mounted, setMounted] = useState(false);

  const nomeAgendaUnico = nomesAgenda.length === 1 ? nomesAgenda[0] : null;
  const localUnico = locaisAtendimento.length === 1 ? locaisAtendimento[0] : null;

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
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    resetForm();
    setConvenioId("");
    setProfessionalId(defaultProfessionalId ? Number(defaultProfessionalId) : "");
    setNomeAgendaId(resolveDefaultNomeAgendaId(nomesAgenda));
    setLocalAtendimentoId(resolveDefaultLocalId(locaisAtendimento));
    const base = selectedDate ?? new Date();
    setDateInput(formatDateInputValue(base));
    setTime(formatTimeFromDate(base));
    setNotes("");
    setCreateError("");
    setRetornoInfo(null);
    setRetornoProcedureId("");
    setShowAdvanced(false);
  }, [open, selectedDate, defaultProfessionalId, resetForm, setConvenioId, setProfessionalId, nomesAgenda, locaisAtendimento]);

  useEffect(() => {
    if (!open || nomesAgenda.length === 0) return;
    setNomeAgendaId((current) => current || resolveDefaultNomeAgendaId(nomesAgenda));
  }, [open, nomesAgenda]);

  useEffect(() => {
    if (!open || locaisAtendimento.length === 0) return;
    setLocalAtendimentoId((current) => current || resolveDefaultLocalId(locaisAtendimento));
  }, [open, locaisAtendimento]);

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationError = validateBase();
    if (validationError) {
      setCreateError(validationError.replace("cliente", "paciente"));
      return;
    }
    const agendaId = nomeAgendaId || resolveDefaultNomeAgendaId(nomesAgenda);
    if (!agendaId) {
      setCreateError("Selecione o nome da agenda.");
      return;
    }
    const localId = localAtendimentoId || resolveDefaultLocalId(locaisAtendimento);
    const date = buildAppointmentDate();
    if (!date) {
      setCreateError("Data não definida.");
      return;
    }

    const localSel = localId
      ? locaisAtendimento.find((l) => l.id === localId)
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
      nome_agenda: Number(agendaId),
      notes: notes.trim() || null,
      date: date.toISOString(),
    };
    if (professionalId) basePayload.professional = Number(professionalId);
    if (localId) basePayload.local_atendimento = Number(localId);
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
        if (!navigator.onLine) {
          await adicionarNaFilaSync({ tipo: "consulta", payload: basePayload });
          notificarFilaAtualizada();
          resetAndClose();
          onSuccess();
          return;
        }
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
        const nomeAgenda = nomesAgenda.find((a) => a.id === agendaId)?.nome;
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
      const apiMsg =
        err && typeof err === 'object' && 'error' in err && typeof (err as { error?: unknown }).error === 'string'
          ? (err as { error: string }).error
          : null;
      setCreateError(
        apiMsg
          || (err instanceof Error ? err.message : null)
          || (isConsulta ? 'Erro ao abrir consulta' : 'Erro ao criar agendamento'),
      );
    } finally {
      setCreateLoading(false);
    }
  };

  const inputClass =
    "w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-0";

  const localSel = localAtendimentoId
    ? locaisAtendimento.find((l) => l.id === localAtendimentoId)
    : undefined;
  const taxaConsultaBase = localSel ? Number(localSel.valor_consulta) || 0 : 0;
  const taxaConsulta = retornoInfo?.elegivel ? 0 : taxaConsultaBase;
  const totalEstimado = taxaConsulta + resumo.valor;
  const regrasRetornoProc = retornoInfo?.regras_procedimento ?? [];
  const retornoProcAtivo = retornoInfo?.config?.retorno_procedimento_ativo ?? false;

  const campoNomeAgenda = nomeAgendaUnico ? (
    <div>
      <FieldLabel>Nome da agenda *</FieldLabel>
      <div className="px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-gray-50/80 dark:bg-neutral-900/50 text-gray-900 dark:text-gray-100">
        {nomeAgendaUnico.nome}
      </div>
    </div>
  ) : (
    <div>
      <FieldLabel>Nome da agenda *</FieldLabel>
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
  );

  const campoLocalAtendimento = localUnico ? (
    <div>
      <FieldLabel>Local de atendimento</FieldLabel>
      <div className="px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-gray-50/80 dark:bg-neutral-900/50 text-gray-900 dark:text-gray-100">
        {localUnico.nome}
      </div>
    </div>
  ) : (
    <div>
      <FieldLabel>Local de atendimento</FieldLabel>
      <select
        value={localAtendimentoId}
        onChange={(e) => setLocalAtendimentoId(e.target.value ? Number(e.target.value) : "")}
        className={inputClass}
      >
        <option value="">Selecione o local (opcional)</option>
        {locaisAtendimento.map((l) => (
          <option key={l.id} value={l.id}>{l.nome}</option>
        ))}
      </select>
      {locaisAtendimento.length === 0 && (
        <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
          Cadastre locais em Consultas → ícone de engrenagem.
        </p>
      )}
    </div>
  );

  if (!open || !mounted) return null;

  const modalTitle = isConsulta ? "Nova consulta" : "Novo agendamento";
  const modalSubtitle = isConsulta
    ? "Abrir consulta na clínica"
    : "Agendar atendimento na clínica";
  const submitLabel = isConsulta
    ? (createLoading ? "Abrindo..." : "Abrir consulta")
    : (createLoading ? "Agendando..." : "Agendar");

  const modal = (
    <div
      className="fixed inset-0 z-[110] flex items-end sm:items-center justify-center p-0 sm:p-4 md:p-6 bg-black/40 dark:bg-black/60"
      onClick={(e) => {
        if (e.target === e.currentTarget) resetAndClose();
      }}
    >
      <div
        className="flex flex-col w-full sm:max-w-2xl md:max-w-3xl lg:max-w-4xl max-h-[100dvh] sm:max-h-[92vh] bg-white dark:bg-neutral-900 sm:rounded-xl shadow-2xl overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-criar-agendamento-title"
      >
      <header className="flex flex-wrap items-center gap-2 sm:gap-3 px-4 sm:px-5 py-3 border-b border-gray-200 dark:border-neutral-700 shrink-0 bg-white dark:bg-neutral-900">
        <button
          type="button"
          onClick={resetAndClose}
          className="p-1.5 sm:p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 shrink-0"
          aria-label="Voltar"
        >
          <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-300" />
        </button>
        <div
          className="hidden sm:flex w-9 h-9 rounded-lg items-center justify-center shrink-0"
          style={{ backgroundColor: `${accentColor}18` }}
        >
          <CalendarDays className="w-4 h-4" style={{ color: accentColor }} />
        </div>
        <div className="flex-1 min-w-0">
          <h1
            id="modal-criar-agendamento-title"
            className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate leading-tight"
          >
            {modalTitle}
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 truncate hidden sm:block leading-snug">
            {modalSubtitle}
          </p>
        </div>
      </header>

      <form className="flex flex-col flex-1 min-h-0" onSubmit={handleSubmit}>
        <div className="flex-1 min-h-0 overflow-y-auto p-4 sm:p-5 bg-[#f7f2f4] dark:bg-gray-950">
          {createError && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
              {createError}
            </div>
          )}

          <ClinicaBelezaPanel className="p-4 sm:p-5 md:p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 md:gap-6 lg:gap-8 w-full">
              <div className="space-y-4">
                <SectionTitle>Cliente</SectionTitle>
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

                <ProcedureMultiSelect
                  procedures={procedures}
                  selectedIds={selectedProcedures}
                  onAdd={adicionarProcedimento}
                  onRemove={removerProcedimento}
                  convenioId={convenioId}
                  precosMap={precosMap}
                  optional
                />
              </div>

              <div className="space-y-4">
                <SectionTitle>Agendamento</SectionTitle>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <FieldLabel>Data *</FieldLabel>
                    <input
                      type="date"
                      value={dateInput}
                      onChange={(e) => setDateInput(e.target.value)}
                      className={inputClass}
                      required
                    />
                  </div>
                  <div>
                    <FieldLabel>Horário *</FieldLabel>
                    <input
                      type="time"
                      value={time}
                      onChange={(e) => setTime(e.target.value)}
                      className={inputClass}
                      required
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <FieldLabel>Profissional</FieldLabel>
                    <select
                      value={professionalId}
                      onChange={(e) => setProfessionalId(e.target.value ? Number(e.target.value) : "")}
                      className={inputClass}
                    >
                      <option value="">Selecione o profissional (opcional)</option>
                      {professionals.map((p) => (
                        <option key={p.id} value={p.id}>{entityName(p)}</option>
                      ))}
                    </select>
                  </div>
                  <div>{campoNomeAgenda}</div>
                  <div>
                    <ConvenioSelect convenios={convenios} value={convenioId} onChange={setConvenioId} hint="" className={inputClass} />
                  </div>
                  <div>{campoLocalAtendimento}</div>
                </div>

                {retornoInfo?.elegivel && patientId && (
                  <div className="p-2.5 rounded-lg text-sm bg-emerald-50 dark:bg-emerald-900/20 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                    <span className="font-medium">Retorno gratuito</span>
                    <span className="block text-xs mt-0.5">{retornoInfo.mensagem}</span>
                  </div>
                )}

                {localAtendimentoId && (
                  <div className="p-3 rounded-lg bg-gray-50 dark:bg-neutral-900/50 text-sm space-y-1 border border-gray-100 dark:border-neutral-700">
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
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-gray-100 dark:border-neutral-800 space-y-3">
              <button
                type="button"
                onClick={() => setShowAdvanced((v) => !v)}
                className="w-full flex items-center justify-between gap-2 text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                <span>Mais opções (retorno, observações…)</span>
                {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>

              {showAdvanced && (
                <div className="space-y-4 pt-2">
                  {retornoProcAtivo && regrasRetornoProc.length > 0 && patientId && (
                    <div>
                      <FieldLabel>Retorno do procedimento</FieldLabel>
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

                  <div>
                    <FieldLabel>Observações</FieldLabel>
                    <textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      rows={3}
                      className={`${inputClass} resize-y min-h-[72px]`}
                      placeholder="Opcional"
                    />
                  </div>
                </div>
              )}
            </div>
          </ClinicaBelezaPanel>
        </div>

        <footer className="shrink-0 border-t border-gray-200 dark:border-neutral-700 bg-white/80 dark:bg-neutral-800/80 px-4 sm:px-5 py-3 sm:py-4">
          <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-2 sm:gap-3 w-full">
            <button
              type="button"
              onClick={resetAndClose}
              className="sm:min-w-[120px] py-2.5 px-5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-neutral-800"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={createLoading}
              className="sm:min-w-[180px] flex items-center justify-center gap-2 py-2.5 px-5 rounded-lg text-white text-sm font-medium disabled:opacity-60"
              style={{ backgroundColor: accentColor }}
            >
              {createLoading ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
              {submitLabel}
            </button>
          </div>
        </footer>
      </form>
      </div>
    </div>
  );

  return createPortal(modal, document.body);
}
