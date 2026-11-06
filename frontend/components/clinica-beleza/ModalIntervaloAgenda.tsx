"use client";

/**
 * Intervalo da grade da agenda por profissional.
 * GET/PUT /clinica-beleza/professionals/<id>/
 */

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { formatApiError } from "@/lib/api-errors";
import { INTERVALOS_AGENDA_MIN, INTERVALO_AGENDA_PADRAO } from "@/lib/intervalo-agenda";

interface ModalIntervaloAgendaProps {
  professionalId: number;
  professionalName: string;
  onClose: () => void;
  onSaved?: () => void;
}

export function ModalIntervaloAgenda({
  professionalId,
  professionalName,
  onClose,
  onSaved,
}: ModalIntervaloAgendaProps) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [intervalo, setIntervalo] = useState(String(INTERVALO_AGENDA_PADRAO));

  useEffect(() => {
    const fetchProfessional = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await ClinicaBelezaAPI.professionals.get(professionalId);
        const minutos = data?.intervalo_agenda_minutos;
        const n = Number(minutos);
        setIntervalo(
          (INTERVALOS_AGENDA_MIN as readonly number[]).includes(n)
            ? String(n)
            : String(INTERVALO_AGENDA_PADRAO),
        );
      } catch {
        setError("Não foi possível carregar o intervalo da agenda.");
      } finally {
        setLoading(false);
      }
    };
    fetchProfessional();
  }, [professionalId]);

  const handleSave = async () => {
    const parsed = parseInt(intervalo, 10);
    if (!(INTERVALOS_AGENDA_MIN as readonly number[]).includes(parsed)) {
      setError("Escolha um intervalo da lista.");
      return;
    }

    setSaving(true);
    setError("");
    try {
      await ClinicaBelezaAPI.professionals.update(professionalId, {
        intervalo_agenda_minutos: parsed,
      });
      onSaved?.();
      onClose();
    } catch (e) {
      setError(formatApiError(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-md flex flex-col border dark:border-neutral-700">
        <div className="flex justify-between items-center p-4 border-b dark:border-neutral-700 shrink-0">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
            Intervalo da agenda — {professionalName}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-4">
          {error && (
            <div className="mb-4 p-2 rounded bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm">
              {error}
            </div>
          )}
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                Passo dos horários deste profissional na agenda. O padrão é 15 minutos.
              </p>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                Intervalo (min)
              </label>
              <select
                value={intervalo}
                onChange={(e) => setIntervalo(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500/40"
              >
                {INTERVALOS_AGENDA_MIN.map((min) => (
                  <option key={min} value={min}>
                    {min} minutos
                  </option>
                ))}
              </select>
            </>
          )}
        </div>

        <div className="flex gap-2 p-4 border-t dark:border-neutral-700 shrink-0">
          <button
            onClick={onClose}
            className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 text-gray-700 dark:text-gray-300"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            disabled={saving || loading}
            className="flex-1 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50"
          >
            {saving ? "Salvando..." : "Salvar"}
          </button>
        </div>
      </div>
    </div>
  );
}
