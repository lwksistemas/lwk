"use client";

import type { LucideIcon } from "lucide-react";
import { useClinicaBelezaTheme } from "@/components/clinica-beleza/ClinicaBelezaThemeContext";

export function AgendamentoSectionCard({
  icon: Icon,
  title,
  children,
  className = "",
}: {
  icon: LucideIcon;
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  const theme = useClinicaBelezaTheme();
  return (
    <section
      className={`rounded-xl border border-gray-200/80 dark:border-neutral-700 bg-white dark:bg-neutral-900 overflow-hidden shadow-sm ${className}`}
    >
      <header
        className="flex items-center gap-2.5 px-3.5 py-2.5 border-b border-gray-100 dark:border-neutral-800"
        style={{ backgroundColor: theme.primaryLight }}
      >
        <span
          className="flex h-7 w-7 items-center justify-center rounded-lg bg-white/70 dark:bg-neutral-900/40"
          style={{ color: theme.primary }}
        >
          <Icon className="h-3.5 w-3.5" />
        </span>
        <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">{title}</h2>
      </header>
      <div className="p-3.5 sm:p-4 space-y-3">{children}</div>
    </section>
  );
}
