"use client";

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { Loader2 } from "lucide-react";
import { useToast } from "@/components/ui/Toast";
import {
  agendamentoOnlineAdminApi,
  mensagemErroAgendamentoOnline,
  type AgendamentoOnlineConfig,
} from "@/lib/clinica-beleza-api/agendamento-online";

export function SectionCard({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-3xl border border-[#f0e4e6] bg-white p-4 dark:border-gray-700 dark:bg-gray-800 sm:p-5">
      <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">{title}</h2>
      {description ? <p className="mt-0.5 text-sm text-[#8a6e74] dark:text-gray-400">{description}</p> : null}
      <div className="mt-4 space-y-4">{children}</div>
    </section>
  );
}

export function ToggleRow({
  label,
  hint,
  checked,
  onChange,
  primary,
  disabled,
}: {
  label: string;
  hint?: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  primary: string;
  disabled?: boolean;
}) {
  return (
    <div className="flex items-start justify-between gap-3">
      <div className="min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{label}</p>
        {hint ? <p className="text-xs text-[#8a6e74] dark:text-gray-400">{hint}</p> : null}
      </div>
      <Switch checked={checked} onChange={onChange} primary={primary} disabled={disabled} label={label} />
    </div>
  );
}

export function Switch({
  checked,
  onChange,
  primary,
  disabled,
  label,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  primary: string;
  disabled?: boolean;
  label: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className="relative mt-0.5 inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors disabled:opacity-50"
      style={{ backgroundColor: checked ? primary : "#e5d8db" }}
    >
      <span
        className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
          checked ? "translate-x-[22px]" : "translate-x-0.5"
        }`}
      />
    </button>
  );
}

const inputCls =
  "w-full rounded-xl border border-[#e8d9dc] bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-[var(--ao-primary,#ec4899)] focus:ring-2 focus:ring-[color-mix(in_srgb,var(--ao-primary,#ec4899)_25%,transparent)] dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100";

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-[#6b5459] dark:text-gray-300">{label}</span>
      {children}
      {hint ? <span className="mt-1 block text-xs text-[#8a6e74] dark:text-gray-400">{hint}</span> : null}
    </label>
  );
}

export function TextInput({
  label,
  hint,
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  label: string;
  hint?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <Field label={label} hint={hint}>
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className={inputCls}
      />
    </Field>
  );
}

export function NumberInput({
  label,
  hint,
  value,
  onChange,
  min = 0,
}: {
  label: string;
  hint?: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
}) {
  return (
    <Field label={label} hint={hint}>
      <input
        type="number"
        min={min}
        value={Number.isFinite(value) ? value : 0}
        onChange={(e) => onChange(Math.max(min, Number(e.target.value) || 0))}
        className={inputCls}
      />
    </Field>
  );
}

export function TextArea({
  label,
  hint,
  value,
  onChange,
  rows = 3,
}: {
  label: string;
  hint?: string;
  value: string;
  onChange: (v: string) => void;
  rows?: number;
}) {
  return (
    <Field label={label} hint={hint}>
      <textarea rows={rows} value={value} onChange={(e) => onChange(e.target.value)} className={inputCls} />
    </Field>
  );
}

export function SelectInput({
  label,
  hint,
  value,
  onChange,
  options,
}: {
  label: string;
  hint?: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <Field label={label} hint={hint}>
      <select value={value} onChange={(e) => onChange(e.target.value)} className={inputCls}>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </Field>
  );
}

export function PrimaryButton({
  children,
  onClick,
  disabled,
  loading,
  primary,
  type = "button",
}: {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  primary: string;
  type?: "button" | "submit";
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className="inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      style={{ backgroundColor: primary }}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
      {children}
    </button>
  );
}

export function SecondaryButton({
  children,
  onClick,
  disabled,
  href,
  target,
}: {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  href?: string;
  target?: string;
}) {
  const cls =
    "inline-flex items-center justify-center gap-2 rounded-xl border border-[#e8d9dc] bg-white px-3 py-2 text-sm font-medium text-gray-800 transition hover:bg-[#fbf6f4] disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100";
  if (href) {
    return (
      <a href={href} target={target} rel={target === "_blank" ? "noopener noreferrer" : undefined} className={cls}>
        {children}
      </a>
    );
  }
  return (
    <button type="button" onClick={onClick} disabled={disabled} className={cls}>
      {children}
    </button>
  );
}

/**
 * Rascunho local de um subconjunto de campos da config. Salva só esses campos (PATCH).
 */
export function useConfigDraft<K extends keyof AgendamentoOnlineConfig>(
  cfg: AgendamentoOnlineConfig,
  campos: readonly K[],
  onSaved: (cfg: AgendamentoOnlineConfig) => void,
) {
  const toast = useToast();
  const pick = useCallback(
    (c: AgendamentoOnlineConfig) =>
      Object.fromEntries(campos.map((k) => [k, c[k]])) as Pick<AgendamentoOnlineConfig, K>,
    [campos],
  );
  const [draft, setDraft] = useState(() => pick(cfg));
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setDraft(pick(cfg));
  }, [cfg, pick]);

  const dirty = useMemo(() => campos.some((k) => draft[k] !== cfg[k]), [campos, draft, cfg]);

  const set = useCallback(<F extends K>(k: F, v: AgendamentoOnlineConfig[F]) => {
    setDraft((d) => ({ ...d, [k]: v }));
  }, []);

  const save = useCallback(async () => {
    setSaving(true);
    try {
      const updated = await agendamentoOnlineAdminApi.patchConfig(draft);
      onSaved(updated);
      toast.success("Configurações salvas.");
    } catch (err) {
      toast.error(mensagemErroAgendamentoOnline(err, "Não foi possível salvar."));
    } finally {
      setSaving(false);
    }
  }, [draft, onSaved, toast]);

  return { draft, set, save, saving, dirty };
}

export function SaveBar({
  dirty,
  saving,
  onSave,
  primary,
}: {
  dirty: boolean;
  saving: boolean;
  onSave: () => void;
  primary: string;
}) {
  return (
    <div className="flex items-center justify-end gap-3">
      {dirty ? <span className="text-xs text-[#8a6e74]">Alterações não salvas</span> : null}
      <PrimaryButton primary={primary} onClick={onSave} disabled={!dirty} loading={saving}>
        Salvar alterações
      </PrimaryButton>
    </div>
  );
}
