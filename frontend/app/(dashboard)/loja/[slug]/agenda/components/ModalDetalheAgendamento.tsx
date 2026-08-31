"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { X, MessageCircle } from "lucide-react";
import {
  getAgendaStatusColor,
  getAgendaStatusLabelModal,
  getAgendaStatusOpcoesModal,
  normalizeAgendaStatus,
} from "@/lib/clinica-beleza-constants";
import { useAgendaStatusColors } from "@/components/clinica-beleza/ClinicaBelezaThemeContext";
import { buildConsultaDetailHref } from "@/components/clinica-beleza/consultas-page/consultas-page-utils";
import { ProcedureMultiSelect } from "@/components/clinica-beleza/ProcedureMultiSelect";
import {
  groupProceduresByCategoria,
  labelTipoAgendamento,
  stripCategoriaPrefixFromNome,
  type ProcedureCategoriaGroup,
} from "@/lib/clinica-beleza-categories";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import { entityName } from "@/lib/clinica-beleza-entities";
import type { ConsultaFormProcedure } from "@/hooks/clinica-beleza/useNovaConsultaForm";

function toDatetimeLocalValue(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function idsProcedimentosIniciais(
  event: AgendaEventData,
  procedures: ConsultaFormProcedure[],
): number[] {
  const list = event.extendedProps.procedures_list;
  if (Array.isArray(list) && list.length) {
    return list.map((p) => Number(p.id)).filter((id) => Number.isFinite(id));
  }
  const nome = event.extendedProps.procedure_name || "";
  if (!nome || /^consulta(\s|$|—|-)/i.test(nome.trim())) return [];
  const found = procedures.find((p) => entityName(p) === nome);
  return found ? [found.id] : [];
}

function procedimentosAgrupadosDoEvento(
  event: AgendaEventData,
  procedures: ConsultaFormProcedure[],
): ProcedureCategoriaGroup<ConsultaFormProcedure>[] {
  const list = event.extendedProps.procedures_list;
  const itens: ConsultaFormProcedure[] = [];
  if (Array.isArray(list) && list.length) {
    for (const p of list) {
      const found = procedures.find((c) => c.id === p.id);
      itens.push({
        id: p.id,
        nome: p.nome || found?.nome,
        categoria: p.categoria || found?.categoria || found?.category,
      });
    }
  } else {
    for (const id of idsProcedimentosIniciais(event, procedures)) {
      const found = procedures.find((p) => p.id === id);
      if (found) itens.push(found);
    }
  }
  return groupProceduresByCategoria(itens);
}

const STATUS_EDICAO_BLOQUEADA = new Set(["IN_PROGRESS", "COMPLETED", "CANCELLED"]);
const STATUS_JA_CONFIRMADO = new Set(["CLIENT_CONFIRMED", "PHONE_CONFIRMED"]);

interface ModalDetalheAgendamentoProps {
  open: boolean;
  onClose: () => void;
  event: AgendaEventData;
  professionals: { id: number; nome?: string; name?: string }[];
  procedures: ConsultaFormProcedure[];
  onUpdateStatus: (status: string) => Promise<void>;
  onSalvarDetalhe: (payload: {
    date?: string;
    professional?: number;
    procedures_ids?: number[];
  }) => Promise<void>;
  onDelete: () => Promise<void>;
  onReenviarWhatsApp: () => Promise<void>;
  updatingStatus: boolean;
  salvandoDetalhe: boolean;
  reenviandoMensagem: boolean;
}

export function ModalDetalheAgendamento({
  open,
  onClose,
  event,
  professionals,
  procedures,
  onUpdateStatus,
  onSalvarDetalhe,
  onDelete,
  onReenviarWhatsApp,
  updatingStatus,
  salvandoDetalhe,
  reenviandoMensagem,
}: ModalDetalheAgendamentoProps) {
  const params = useParams();
  const slug = params.slug as string;
  const statusColors = useAgendaStatusColors();
  const [professionalId, setProfessionalId] = useState("");
  const [procedureIds, setProcedureIds] = useState<number[]>([]);
  const [dateLocal, setDateLocal] = useState("");

  useEffect(() => {
    if (!open || !event) return;
    setProfessionalId(
      event.extendedProps.professional != null ? String(event.extendedProps.professional) : "",
    );
    setProcedureIds(idsProcedimentosIniciais(event, procedures));
    setDateLocal(toDatetimeLocalValue(event.start));
  }, [open, event, procedures]);

  const status = event?.extendedProps.status || "SCHEDULED";
  const statusSomenteLeitura = status === "IN_PROGRESS" || status === "COMPLETED";
  const podeEditarCampos = !STATUS_EDICAO_BLOQUEADA.has(status);
  const statusLabel = getAgendaStatusLabelModal(status);
  const opcoesStatus = getAgendaStatusOpcoesModal(status);
  const coresStatus = getAgendaStatusColor(status, statusColors);

  const mudou = useMemo(() => {
    if (!event) return false;
    const profAtual = event.extendedProps.professional != null
      ? String(event.extendedProps.professional)
      : "";
    const idsAtual = idsProcedimentosIniciais(event, procedures);
    const dateAtual = toDatetimeLocalValue(event.start);
    const procsIguais =
      idsAtual.length === procedureIds.length &&
      idsAtual.every((id, i) => id === procedureIds[i]);
    return profAtual !== professionalId || !procsIguais || dateAtual !== dateLocal;
  }, [event, procedures, professionalId, procedureIds, dateLocal]);

  if (!open || !event) return null;

  const salvar = async () => {
    if (!mudou || !podeEditarCampos) return;
    if (!professionalId) return;
    if (STATUS_JA_CONFIRMADO.has(status)) {
      const ok = window.confirm(
        "O cliente já confirmou este horário. Ao salvar, a confirmação anterior deixa de valer e um novo link será enviado no WhatsApp.",
      );
      if (!ok) return;
    }
    const payload: { date?: string; professional?: number; procedures_ids?: number[] } = {};
    const profAtual = event.extendedProps.professional != null
      ? String(event.extendedProps.professional)
      : "";
    if (professionalId !== profAtual) payload.professional = Number(professionalId);
    const idsAtual = idsProcedimentosIniciais(event, procedures);
    const procsIguais =
      idsAtual.length === procedureIds.length &&
      idsAtual.every((id, i) => id === procedureIds[i]);
    if (!procsIguais) payload.procedures_ids = procedureIds;
    if (dateLocal !== toDatetimeLocalValue(event.start) && dateLocal) {
      payload.date = new Date(dateLocal).toISOString();
    }
    if (!payload.date && payload.professional == null && !payload.procedures_ids) return;
    await onSalvarDetalhe(payload);
  };

  const tipoAgendamento = labelTipoAgendamento(procedureIds.length);
  const gruposSomenteLeitura = procedimentosAgrupadosDoEvento(event, procedures);

  const duracaoPreco = (
    <p className="text-sm text-gray-600 dark:text-gray-400">
      {(event.extendedProps.duracao_minutos ?? event.extendedProps.procedure_duration)} min
      {" "}- R$ {event.extendedProps.procedure_price}
    </p>
  );

  const blocoStatusAjuda = statusSomenteLeitura ? (
    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1.5 space-y-2">
      <p>
        {status === "COMPLETED"
          ? "Consulta finalizada em Consultas — exibido em verde escuro na agenda."
          : status === "IN_PROGRESS"
            ? "Em atendimento: o horário da agenda foi atualizado para o início real. Finalize a consulta em Consultas quando terminar (não pela agenda)."
            : "Início e conclusão do atendimento são feitos em Consultas."}
      </p>
      {status === "IN_PROGRESS" && event.extendedProps.consulta_id != null && (
        <Link
          href={buildConsultaDetailHref(slug, event.extendedProps.consulta_id)}
          className="inline-flex text-sm font-medium text-violet-700 dark:text-violet-300 hover:underline"
          onClick={onClose}
        >
          Abrir consulta em atendimento →
        </Link>
      )}
    </div>
  ) : status === "SCHEDULED" || status === "PENDING" ? (
    <p className="text-xs text-amber-700 dark:text-amber-400 mt-1.5">
      Aguardando resposta do cliente no WhatsApp ou pelo link. A agenda atualiza sozinha em alguns segundos.
    </p>
  ) : status === "CLIENT_CONFIRMED" ? (
    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1.5">
      Confirmado pelo WhatsApp ou link. Não abre consulta — registre &quot;Cliente presente&quot; quando chegar.
    </p>
  ) : status === "PHONE_CONFIRMED" ? (
    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1.5">
      Confirmado por ligação (recepção). Quando o cliente chegar, altere para &quot;Cliente presente&quot;.
    </p>
  ) : status === "CONFIRMED" ? (
    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1.5 space-y-2">
      <p>
        Consulta criada com status <strong className="text-amber-700 dark:text-amber-400">RECEBER</strong>.
        O pagamento é feito em Consultas (botão Receber), antes ou durante o atendimento — sem bloquear o início.
      </p>
      {event.extendedProps.consulta_id != null && (
        <Link
          href={buildConsultaDetailHref(slug, event.extendedProps.consulta_id)}
          className="inline-flex text-sm font-medium text-amber-700 dark:text-amber-300 hover:underline"
          onClick={onClose}
        >
          Abrir consulta em Consultas →
        </Link>
      )}
    </div>
  ) : status === "CANCELLED" ? (
    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1.5">
      Cancelado pelo cliente (WhatsApp) ou pela recepção.
    </p>
  ) : null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-3 sm:p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl w-full max-w-4xl p-5 sm:p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-start mb-4">
          <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Detalhes do Agendamento</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 md:gap-6">
          <div className="space-y-3">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Cliente</p>
              <p className="font-semibold text-gray-900 dark:text-gray-100">{event.extendedProps.patient_name}</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">{event.extendedProps.patient_phone}</p>
            </div>

            <div>
              <div className="flex items-center justify-between gap-2 mb-1">
                <p className="text-sm text-gray-500 dark:text-gray-400">Atendimento</p>
                <span
                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                    procedureIds.length === 0
                      ? "bg-sky-50 text-sky-800 dark:bg-sky-900/30 dark:text-sky-200"
                      : "text-white"
                  }`}
                  style={
                    procedureIds.length > 0
                      ? { backgroundColor: "var(--cb-primary, #8B3D52)" }
                      : undefined
                  }
                >
                  {tipoAgendamento}
                </span>
              </div>
              {podeEditarCampos ? (
                <ProcedureMultiSelect
                  procedures={procedures}
                  selectedIds={procedureIds}
                  onAdd={(id) =>
                    setProcedureIds((prev) => (prev.includes(id) ? prev : [...prev, id]))
                  }
                  onRemove={(id) => setProcedureIds((prev) => prev.filter((x) => x !== id))}
                  optional
                  showSummary
                  hint="(opcional — escolha a categoria e depois o procedimento)"
                />
              ) : gruposSomenteLeitura.length === 0 ? (
                <p className="font-semibold text-gray-900 dark:text-gray-100">Somente consulta</p>
              ) : (
                <div className="space-y-2.5 border border-gray-200 dark:border-neutral-600 rounded-lg p-3">
                  {gruposSomenteLeitura.map((grupo) => (
                    <div key={grupo.slug}>
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                        {grupo.label}
                      </p>
                      <ul className="mt-1 space-y-0.5">
                        {grupo.items.map((p) => (
                          <li
                            key={p.id}
                            className="text-sm font-medium text-gray-900 dark:text-gray-100"
                          >
                            {stripCategoriaPrefixFromNome(entityName(p), grupo.slug)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              )}
              {!podeEditarCampos ? <div className="mt-1">{duracaoPreco}</div> : null}
            </div>

            {event.extendedProps.notes ? (
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Observações</p>
                <p className="text-sm text-gray-800 dark:text-gray-200">{event.extendedProps.notes}</p>
              </div>
            ) : null}
          </div>

          <div className="space-y-3">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Profissional</p>
              {podeEditarCampos ? (
                <select
                  value={professionalId}
                  onChange={(e) => setProfessionalId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm"
                >
                  <option value="">Selecione</option>
                  {professionals.map((prof) => (
                    <option key={prof.id} value={prof.id}>
                      {entityName(prof)}
                    </option>
                  ))}
                </select>
              ) : (
                <p className="font-semibold text-gray-900 dark:text-gray-100">{event.extendedProps.professional_name}</p>
              )}
            </div>

            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Data e Hora</p>
              {podeEditarCampos ? (
                <input
                  type="datetime-local"
                  value={dateLocal}
                  onChange={(e) => setDateLocal(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm"
                />
              ) : (
                <p className="font-semibold text-gray-900 dark:text-gray-100">
                  {new Date(event.start).toLocaleString("pt-BR")}
                </p>
              )}
            </div>

            {podeEditarCampos && (status === "SCHEDULED" || status === "PENDING") ? (
              <p className="text-xs text-amber-700 dark:text-amber-400">
                Ao mudar profissional, procedimento ou horário, o link de confirmação anterior deixa de valer.
                O cliente recebe um novo link no WhatsApp.
              </p>
            ) : null}
            {podeEditarCampos && STATUS_JA_CONFIRMADO.has(status) ? (
              <p className="text-xs text-amber-700 dark:text-amber-400">
                Já confirmado. Se você alterar estes dados, a confirmação volta para “aguardando” e um novo
                link é enviado — o anterior avisa que o agendamento mudou.
              </p>
            ) : null}

            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                Status {updatingStatus && <span className="text-xs">(salvando…)</span>}
              </p>
              {statusSomenteLeitura ? (
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-50 dark:bg-neutral-900/60 border border-gray-200 dark:border-neutral-600">
                  <span
                    className="shrink-0 w-3 h-3 rounded-full"
                    style={{
                      backgroundColor: coresStatus.bg,
                      border: `2px solid ${coresStatus.border}`,
                    }}
                    aria-hidden
                  />
                  <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
                    {statusLabel}
                  </span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span
                    className="shrink-0 w-3 h-3 rounded-full border-2 border-gray-900/10"
                    style={{
                      backgroundColor: coresStatus.bg,
                      borderColor: coresStatus.border,
                    }}
                    aria-hidden
                  />
                  <select
                    value={normalizeAgendaStatus(status)}
                    onChange={async (e) => {
                      await onUpdateStatus(e.target.value);
                    }}
                    disabled={updatingStatus}
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm disabled:opacity-70"
                  >
                    {opcoesStatus.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              {blocoStatusAjuda}
            </div>
          </div>
        </div>

        <div className="mt-5 flex flex-col sm:flex-row gap-2">
          {podeEditarCampos ? (
            <button
              type="button"
              onClick={salvar}
              disabled={!mudou || salvandoDetalhe || !professionalId}
              className="sm:flex-1 px-4 py-2 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
            >
              {salvandoDetalhe ? "Salvando…" : "Salvar alterações"}
            </button>
          ) : null}
          <button
            type="button"
            onClick={onReenviarWhatsApp}
            disabled={reenviandoMensagem || !event.extendedProps.patient_phone}
            className="sm:flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Reenviar solicitação de confirmação por WhatsApp"
          >
            <MessageCircle size={18} />
            {reenviandoMensagem ? "Enviando…" : "Reenviar WhatsApp"}
          </button>
          <button
            onClick={onDelete}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Deletar
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 dark:bg-neutral-600 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-neutral-500 transition-colors"
          >
            Fechar
          </button>
        </div>
        {!event.extendedProps.patient_phone ? (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">Cliente sem telefone; não é possível reenviar.</p>
        ) : null}
      </div>
    </div>
  );
}
