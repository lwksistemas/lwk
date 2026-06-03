"use client";

/**
 * Toggle para habilitar/desabilitar o administrador como profissional.
 * Visível apenas para o owner da loja (decisão do componente pai).
 *
 * - GET /professionals/admin-status/ → estado atual
 * - POST /professionals/toggle-admin/ → habilitar/desabilitar
 */

import { useCallback, useEffect, useState } from "react";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";

interface AdminProfissionalToggleProps {
  onToggled: () => void;
}

interface AdminStatus {
  is_enabled: boolean;
  professional_id: number | null;
}

export function AdminProfissionalToggle({ onToggled }: AdminProfissionalToggleProps) {
  const [enabled, setEnabled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [error, setError] = useState("");

  const fetchStatus = useCallback(async () => {
    try {
      const res = await clinicaBelezaFetch("/professionals/admin-status/");
      if (res.ok) {
        const data: AdminStatus = await res.json();
        setEnabled(data.is_enabled);
      }
    } catch {
      // Silently ignore on mount — component won't break
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleToggle = async () => {
    const newValue = !enabled;
    setEnabled(newValue);
    setToggling(true);
    setError("");

    try {
      const res = await clinicaBelezaFetch("/professionals/toggle-admin/", {
        method: "POST",
        body: JSON.stringify({ enable: newValue }),
      });

      if (!res.ok) {
        // Revert on error
        setEnabled(!newValue);
        const data = await res.json().catch(() => null);
        const msg = data?.detail || data?.error || "Erro ao atualizar status de profissional.";
        setError(typeof msg === "string" ? msg : JSON.stringify(msg));
        return;
      }

      // Success — notify parent to reload list
      onToggled();
    } catch {
      // Revert on network error
      setEnabled(!newValue);
      setError("Erro ao comunicar com servidor. Tente novamente.");
    } finally {
      setToggling(false);
    }
  };

  if (loading) {
    return null;
  }

  return (
    <div className="flex items-center gap-3 mb-4 p-3 rounded-lg bg-white/80 dark:bg-neutral-800/70 shadow-sm">
      <label className="relative inline-flex items-center cursor-pointer">
        <input
          type="checkbox"
          checked={enabled}
          onChange={handleToggle}
          disabled={toggling}
          className="sr-only peer"
        />
        <div
          className={`w-11 h-6 rounded-full peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-offset-2 transition-colors duration-200 ${
            enabled
              ? ""
              : "bg-gray-300 dark:bg-neutral-600"
          } ${toggling ? "opacity-60" : ""}`}
          style={enabled ? { backgroundColor: CLINICA_BELEZA_PRIMARY } : undefined}
        >
          <div
            className={`absolute top-[2px] left-[2px] w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 ${
              enabled ? "translate-x-5" : "translate-x-0"
            }`}
          />
        </div>
      </label>
      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
        Habilitar como profissional
      </span>
      {toggling && (
        <span className="text-xs text-gray-500 dark:text-gray-400">Salvando...</span>
      )}
      {error && (
        <span className="text-xs text-red-600 dark:text-red-400 ml-2">{error}</span>
      )}
    </div>
  );
}
