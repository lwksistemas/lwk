"use client";

import { ArrowLeft, Plus, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

export interface StandardPageHeaderProps {
  title: string;
  subtitle?: string;
  onBack?: () => void;
  showBack?: boolean;
  icon?: LucideIcon;
  newLabel?: string;
  onNew?: () => void;
  primaryColor?: string;
  extraActions?: ReactNode;
}

/** Cabeçalho de lista/formulário sem depender do shell da clínica. */
export function StandardPageHeader({
  title,
  subtitle,
  onBack,
  showBack = Boolean(onBack),
  icon: Icon,
  newLabel = "Novo",
  onNew,
  primaryColor = "#7a3044",
  extraActions,
}: StandardPageHeaderProps) {
  return (
    <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex min-w-0 items-start gap-2">
        {showBack && onBack ? (
          <button
            type="button"
            onClick={onBack}
            className="mt-0.5 inline-flex shrink-0 items-center justify-center rounded-lg p-1.5 text-gray-600 hover:bg-black/5"
            aria-label="Voltar"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
        ) : null}
        {Icon ? <Icon className="mt-1 h-5 w-5 shrink-0" style={{ color: primaryColor }} /> : null}
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold sm:text-3xl">{title}</h1>
          {subtitle ? <p className="mt-0.5 text-sm text-[#8a6e74]">{subtitle}</p> : null}
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {extraActions}
        {onNew ? (
          <button
            type="button"
            onClick={onNew}
            className="inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium text-white"
            style={{ backgroundColor: primaryColor }}
          >
            <Plus className="h-4 w-4" />
            {newLabel}
          </button>
        ) : null}
      </div>
    </div>
  );
}
