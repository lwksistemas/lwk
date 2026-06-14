"use client";

/**
 * Modal para definir tempo padrão de consulta por profissional.
 */

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";

interface ModalTempoConsultaProfissionalProps {
  professionalId: number;
  professionalName: string;
  onClose: () => void;
  onSaved?: (professional: { id: number; tempo_consulta_minutos?: number | null }) => void;
}

export function ModalTempoConsultaProfissional({
  professionalId,
  professionalName,
  onClose,
  onSaved,
}: ModalTempoConsultaProfissionalProps) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [tempo, setTempo] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const data = await ClinicaBelezaAPI.professionals.get(professionalId);
        if (cancelled) return;
        const t = data?.tempo_consulta_minutos;
        setTempo(t != null && t > 0 ? String(t) : "");
      } catch {
        if (!cancelled) setError("Não foi possível carregar o profissional.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [professionalId]);

  const handleSave = async () => {
    setError("");
    const raw = tempo.trim();
    const parsed = raw === "" ? null : Number(raw);
    if (parsed != null && (Number.isNaN(parsed) || parsed < 5 || parsed > 480)) {
      setError("Informe um tempo entre 5 e 480 minutos, ou deixe vazio para usar o padrão do local.");
      return;
    }

    setSaving(true);
    try {
      const saved = await ClinicaBelezaAPI.professionals.update(professionalId, {
        tempo_consulta_minutos: parsed,
      }) as { id?: number; tempo_consulta_minutos?: number | null };
      const savedTempo = saved?.tempo_consulta_minutos ?? null;
      if (parsed != null && savedTempo !== parsed) {
        setError(
          'O servidor não confirmou o tempo salvo. Aguarde o deploy do backend no beta e tente novamente.',
        );
        return;
      }
      if (saved?.id) {
        onSaved?.({ id: saved.id, tempo_consulta_minutos: savedTempo });
      } else {
        onSaved?.({ id: professionalId, tempo_consulta_minutos: savedTempo });
      }
      onClose();
    } catch (err: unknown) {
      let msg = "Erro ao salvar.";
      if (err instanceof Error) {
        msg = err.message;
      } else if (err && typeof err === "object") {
        const apiErr = err as { error?: string; detail?: string };
        msg = apiErr.error || apiErr.detail || msg;
      }
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-xl bg-white dark:bg-neutral-900 shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 dark:border-neutral-700 px-5 py-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Tempo da consulta</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">{professionalName}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-gray-500 hover:bg-gray-100 dark:hover:bg-neutral-800"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>

        <div className="px-5 py-4 space-y-4">
          {loading ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">Carregando...</p>
          ) : (
            <>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Duração padrão das consultas deste profissional na agenda.
                Se os procedimentos da consulta somarem <strong>mais tempo</strong>, prevalece a soma dos procedimentos.
              </p>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Tempo (minutos)
                </label>
                <input
                  type="number"
                  min={5}
                  max={480}
                  step={5}
                  value={tempo}
                  onChange={(e) => setTempo(e.target.value)}
                  placeholder="Ex.: 40 (vazio = padrão do local)"
                  className="w-full rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 px-3 py-2 text-gray-900 dark:text-white"
                />
              </div>
            </>
          )}
          {error && (
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          )}
        </div>

        <div className="flex justify-end gap-2 border-t border-gray-200 dark:border-neutral-700 px-5 py-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-neutral-800"
            disabled={saving}
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={loading || saving}
            className="rounded-lg bg-pink-600 px-4 py-2 text-sm font-medium text-white hover:bg-pink-700 disabled:opacity-50"
          >
            {saving ? "Salvando..." : "Salvar"}
          </button>
        </div>
      </div>
    </div>
  );
}
