"use client";

import { X, MessageCircle } from "lucide-react";

/** Cores por status */
const CORES_STATUS: Record<string, { bg: string; border: string }> = {
  SCHEDULED: { bg: "#a855f7", border: "#9333ea" },
  CONFIRMED: { bg: "#22c55e", border: "#16a34a" },
  PENDING: { bg: "#f59e0b", border: "#d97706" },
  IN_PROGRESS: { bg: "#3b82f6", border: "#2563eb" },
  COMPLETED: { bg: "#0d9488", border: "#0f766e" },
  CANCELLED: { bg: "#dc2626", border: "#b91c1c" },
  NO_SHOW: { bg: "#b45309", border: "#92400e" },
};

export interface AgendaEventData {
  id: string;
  title: string;
  start: string;
  end: string;
  backgroundColor: string;
  borderColor: string;
  textColor: string;
  extendedProps: {
    dbId: number | string;
    status: string;
    patient_name: string;
    patient_phone: string;
    professional_name: string;
    procedure_name: string;
    procedure_duration: number;
    procedure_price: string;
    notes: string;
    version?: number;
    updated_at?: string;
  };
}

interface ModalDetalheAgendamentoProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  event: AgendaEventData;
  onUpdateStatus: (status: string) => Promise<void>;
  onDelete: () => Promise<void>;
  onReenviarWhatsApp: () => Promise<void>;
  onAbrirConsulta?: () => void;
  consultaDisponivel?: boolean;
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
  onAbrirConsulta,
  consultaDisponivel,
  updatingStatus,
  reenviandoMensagem,
}: ModalDetalheAgendamentoProps) {
  if (!open || !event) return null;

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
              {event.extendedProps.procedure_duration} min - R${" "}
              {event.extendedProps.procedure_price}
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
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Status {updatingStatus && <span className="text-xs">(salvando…)</span>}</p>
            <div className="flex items-center gap-2">
              <span
                className="shrink-0 w-3 h-3 rounded-full border-2 border-gray-900/10"
                style={{
                  backgroundColor: CORES_STATUS[event.extendedProps.status]?.bg ?? "#a855f7",
                  borderColor: CORES_STATUS[event.extendedProps.status]?.border ?? "#9333ea",
                }}
                aria-hidden
              />
              <select
                value={event.extendedProps.status}
                onChange={(e) => onUpdateStatus(e.target.value)}
                disabled={updatingStatus}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm disabled:opacity-70"
              >
                <option value="SCHEDULED">🟣 Agendado</option>
                <option value="CONFIRMED">🟢 Confirmado</option>
                <option value="PENDING">🟠 Pendente</option>
                <option value="IN_PROGRESS">🔵 Em Atendimento</option>
                <option value="COMPLETED">⚫ Concluído</option>
                <option value="CANCELLED">🔴 Cancelado</option>
                <option value="NO_SHOW">⬜ Faltou</option>
              </select>
            </div>
          </div>

          {event.extendedProps.notes && (
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Observações</p>
              <p className="text-sm text-gray-800 dark:text-gray-200">{event.extendedProps.notes}</p>
            </div>
          )}
        </div>

        <div className="mt-4 flex flex-col gap-2">
          {consultaDisponivel && onAbrirConsulta && (
            <button
              type="button"
              onClick={onAbrirConsulta}
              className="flex items-center justify-center gap-2 w-full px-4 py-2 text-white rounded-lg transition-colors"
              style={{ backgroundColor: "#8B3D52" }}
            >
              Abrir consulta
            </button>
          )}
          <button
            type="button"
            onClick={onReenviarWhatsApp}
            disabled={reenviandoMensagem || !event.extendedProps.patient_phone}
            className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Reenviar confirmação por WhatsApp ao cliente"
          >
            <MessageCircle size={18} />
            {reenviandoMensagem ? "Enviando…" : "Reenviar mensagem WhatsApp"}
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
            Salvar
          </button>
        </div>
      </div>
    </div>
  );
}
