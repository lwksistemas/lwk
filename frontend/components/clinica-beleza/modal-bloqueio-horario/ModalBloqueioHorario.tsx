"use client";

import { X } from "lucide-react";
import {
  MODOS_BLOQUEIO_INTERVALO,
  TIPOS_BLOQUEIO,
  profissionalBloqueioLabel,
  type BloqueioProfessional,
} from "./modal-bloqueio-horario-utils";
import { useModalBloqueioHorario } from "./useModalBloqueioHorario";

export interface ModalBloqueioHorarioProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  professionals: BloqueioProfessional[];
  dataInicioSugerida?: Date | null;
  defaultProfessionalId?: string;
}

const fieldClass =
  "w-full px-3 py-2.5 min-h-[44px] border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-[#8B4557] focus:border-transparent";

export function ModalBloqueioHorario({
  isOpen,
  onClose,
  onSuccess,
  professionals,
  dataInicioSugerida,
  defaultProfessionalId,
}: ModalBloqueioHorarioProps) {
  const state = useModalBloqueioHorario({
    isOpen,
    onClose,
    onSuccess,
    dataInicioSugerida,
    defaultProfessionalId,
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/50 backdrop-blur-sm">
      <div
        className="bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[92vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="shrink-0 border-b border-gray-200 dark:border-neutral-700 px-5 sm:px-6 py-3.5 flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Bloquear Horário</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg transition-colors"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 sm:p-6">
          {state.erro && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-400 text-sm">
              {state.erro}
            </div>
          )}

          <div className="mb-4">
            <span className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Intervalo
            </span>
            <div
              className="inline-flex w-full sm:w-auto rounded-lg border border-gray-300 dark:border-neutral-600 p-0.5 bg-gray-100 dark:bg-neutral-700/80"
              role="group"
              aria-label="Modo do intervalo"
            >
              {MODOS_BLOQUEIO_INTERVALO.map((m) => {
                const active = state.modo === m.value;
                return (
                  <button
                    key={m.value}
                    type="button"
                    onClick={() => state.setModo(m.value)}
                    className={`flex-1 sm:flex-none px-4 py-2 min-h-[40px] text-sm font-medium rounded-md transition-colors ${
                      active
                        ? "bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 shadow-sm"
                        : "text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
                    }`}
                  >
                    {m.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Layout paisagem: 2 colunas no desktop, 1 no mobile */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Tipo de bloqueio
              </label>
              <select
                value={state.tipoSelecionado}
                onChange={(e) => state.onTipoChange(e.target.value)}
                className={fieldClass}
              >
                {TIPOS_BLOQUEIO.map((t) => (
                  <option key={t.value || "outro"} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Profissional
              </label>
              <select
                value={state.professionalId}
                onChange={(e) => state.setProfessionalId(e.target.value)}
                className={fieldClass}
              >
                <option value="">Bloqueio geral (todos)</option>
                {professionals.map((p) => (
                  <option key={p.id} value={p.id}>
                    {profissionalBloqueioLabel(p)}
                  </option>
                ))}
              </select>
            </div>

            {state.tipoSelecionado === "" && (
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Motivo (outro)
                </label>
                <input
                  type="text"
                  value={state.motivoOutro}
                  onChange={(e) => state.setMotivoOutro(e.target.value)}
                  placeholder="Ex.: Reunião, treinamento..."
                  className={fieldClass}
                />
              </div>
            )}

            {state.modo === "dias" ? (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Data início *
                  </label>
                  <input
                    type="date"
                    value={state.dataInicioDia}
                    onChange={(e) => state.setDataInicioDia(e.target.value)}
                    className={fieldClass}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Data fim *
                  </label>
                  <input
                    type="date"
                    value={state.dataFimDia}
                    onChange={(e) => state.setDataFimDia(e.target.value)}
                    className={fieldClass}
                  />
                </div>
              </>
            ) : (
              <>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Data *
                  </label>
                  <input
                    type="date"
                    value={state.dataHorario}
                    onChange={(e) => state.setDataHorario(e.target.value)}
                    className={fieldClass}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Hora início *
                  </label>
                  <input
                    type="time"
                    value={state.horaInicio}
                    onChange={(e) => state.setHoraInicio(e.target.value)}
                    className={fieldClass}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Hora fim *
                  </label>
                  <input
                    type="time"
                    value={state.horaFim}
                    onChange={(e) => state.setHoraFim(e.target.value)}
                    className={fieldClass}
                  />
                </div>
              </>
            )}

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Observações
              </label>
              <textarea
                value={state.observacoes}
                onChange={(e) => state.setObservacoes(e.target.value)}
                placeholder="Opcional"
                rows={2}
                className={`${fieldClass} resize-none`}
              />
            </div>
          </div>

          <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">
            {state.modo === "dias"
              ? "Bloqueia o(s) dia(s) inteiro(s) no intervalo (ex.: férias de 17 a 25)."
              : "Bloqueia apenas o horário no dia escolhido (ex.: 13:00–17:00)."}{" "}
            O intervalo de almoço do profissional é configurado em Profissionais → Horários de trabalho.
          </p>
        </div>

        <div className="shrink-0 border-t border-gray-200 dark:border-neutral-700 bg-gray-50 dark:bg-neutral-700/50 px-5 sm:px-6 py-3.5 flex flex-row-reverse gap-3">
          <button
            type="button"
            onClick={() => void state.salvar()}
            disabled={state.loading}
            className="min-w-[140px] px-5 py-2.5 min-h-[44px] bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {state.loading ? "Salvando..." : "Bloquear"}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="min-w-[120px] px-5 py-2.5 min-h-[44px] bg-gray-200 dark:bg-neutral-600 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-neutral-500 transition-colors font-medium"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}
