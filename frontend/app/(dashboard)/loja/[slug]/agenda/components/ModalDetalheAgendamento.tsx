"use client";

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
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";

export type { AgendaEventData };

interface ModalDetalheAgendamentoProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  event: AgendaEventData;
  onUpdateStatus: (status: string) => Promise<void>;
  onDelete: () => Promise<void>;
  onReenviarWhatsApp: () => Promise<void>;
  updatingStatus: boolean;
  reenviandoMensagem: boolean;
}

export function ModalDetalheAgendamento({
  open,
  onClose,
  event,
  onUpdateStatus,
  onDelete,
  onReenviarWhatsApp,
  updatingStatus,
  reenviandoMensagem,
}: ModalDetalheAgendamentoProps) {
  const params = useParams();
  const slug = params.slug as string;
  const statusColors = useAgendaStatusColors();

  if (!open || !event) return null;

  const status = event.extendedProps.status || "SCHEDULED";
  const statusSomenteLeitura = status === "IN_PROGRESS" || status === "COMPLETED";
  const statusLabel = getAgendaStatusLabelModal(status);
  const opcoesStatus = getAgendaStatusOpcoesModal(status);
  const coresStatus = getAgendaStatusColor(status, statusColors);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-md w-full p-6">
        <div className="flex justify-between items-start mb-4">
          <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Detalhes do Agendamento</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Cliente</p>
            <p className="font-semibold text-gray-900 dark:text-gray-100">{event.extendedProps.patient_name}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">{event.extendedProps.patient_phone}</p>
          </div>

          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Procedimento</p>
            <p className="font-semibold text-gray-900 dark:text-gray-100">{event.extendedProps.procedure_name}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {(event.extendedProps.duracao_minutos ?? event.extendedProps.procedure_duration)} min
              {event.extendedProps.duracao_minutos != null &&
                event.extendedProps.duracao_minutos !== event.extendedProps.procedure_duration && (
                  <span className="text-amber-600 dark:text-amber-400"> (ajustado na agenda)</span>
                )}
              {" "}- R$ {event.extendedProps.procedure_price}
            </p>
          </div>

          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Profissional</p>
            <p className="font-semibold text-gray-900 dark:text-gray-100">{event.extendedProps.professional_name}</p>
          </div>

          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Data e Hora</p>
            <p className="font-semibold text-gray-900 dark:text-gray-100">
              {new Date(event.start).toLocaleString("pt-BR")}
            </p>
          </div>

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
            {statusSomenteLeitura ? (
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
            ) : null}
          </div>

          {event.extendedProps.notes && (
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Observações</p>
              <p className="text-sm text-gray-800 dark:text-gray-200">{event.extendedProps.notes}</p>
            </div>
          )}
        </div>

        <div className="mt-4 flex flex-col gap-2">
          <button
            type="button"
            onClick={onReenviarWhatsApp}
            disabled={reenviandoMensagem || !event.extendedProps.patient_phone}
            className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Reenviar solicitação de confirmação por WhatsApp"
          >
            <MessageCircle size={18} />
            {reenviandoMensagem ? "Enviando…" : "Reenviar confirmação WhatsApp"}
          </button>
          {!event.extendedProps.patient_phone && (
            <p className="text-xs text-gray-500 dark:text-gray-400">Cliente sem telefone; não é possível reenviar.</p>
          )}
        </div>
        <div className="mt-4 flex gap-3">
          <button
            onClick={onDelete}
            className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Deletar
          </button>
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-200 dark:bg-neutral-600 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-neutral-500 transition-colors"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}
