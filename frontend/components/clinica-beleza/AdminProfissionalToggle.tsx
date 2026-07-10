'use client';

import { useCallback, useEffect, useState } from 'react';
import { ClinicaBelezaAPI } from '@/lib/clinica-beleza-api';

interface AdminProfissionalToggleProps {
  onToggled?: () => void;
}

export function AdminProfissionalToggle({ onToggled }: AdminProfissionalToggleProps) {
  const [visible, setVisible] = useState(false);
  const [enabled, setEnabled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await ClinicaBelezaAPI.professionals.adminStatus();
        if (!cancelled) {
          setVisible(true);
          setEnabled(!!data.is_enabled);
        }
      } catch {
        if (!cancelled) setVisible(false);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleToggle = useCallback(async () => {
    const next = !enabled;
    setSaving(true);
    setError('');
    try {
      await ClinicaBelezaAPI.professionals.toggleAdmin(next);
      setEnabled(next);
      onToggled?.();
    } catch (e: unknown) {
      const msg =
        (e as { detail?: string })?.detail ||
        (e as { error?: string })?.error ||
        'Não foi possível alterar. Tente novamente.';
      setError(typeof msg === 'string' ? msg : 'Erro ao alterar.');
    } finally {
      setSaving(false);
    }
  }, [enabled, onToggled]);

  if (loading || !visible) return null;

  return (
    <div
      className="mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-3"
    >
      <div>
        <p className="text-sm font-medium text-gray-900 dark:text-white">Habilitar como profissional</p>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Apareça na agenda e receba agendamentos como profissional da clínica.
        </p>
        {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
      </div>
      <label className="inline-flex items-center gap-2 cursor-pointer shrink-0">
        <span className="text-sm text-gray-600 dark:text-gray-300">{enabled ? 'Ativo' : 'Inativo'}</span>
        <input
          type="checkbox"
          checked={enabled}
          disabled={saving}
          onChange={handleToggle}
          className="h-5 w-5 rounded border-gray-300"
          style={{ accentColor: 'var(--cb-primary, #8B3D52)' }}
        />
      </label>
    </div>
  );
}
