"use client";

import type { LucideIcon } from "lucide-react";
import { useClinicaBelezaTheme } from "@/components/clinica-beleza/ClinicaBelezaThemeContext";
import { cbPrimaryAlpha } from "@/lib/clinica-beleza-theme-utils";

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
      className={`rounded-xl border border-[#E9D5E3] dark:border-neutral-700 bg-white dark:bg-neutral-900 overflow-hidden shadow-sm ${className}`}
    >
      <header
        className="flex items-center gap-2 px-3 py-1.5 border-b border-[#F3E8EE] dark:border-neutral-800 shrink-0"
        style={{
          backgroundImage: `linear-gradient(90deg, ${theme.primaryLight} 0%, ${cbPrimaryAlpha(8)} 100%)`,
        }}
      >
        <span
          className="flex h-5.5 w-5.5 h-[22px] w-[22px] items-center justify-center rounded-md bg-white/80 dark:bg-neutral-900/40"
          style={{ color: theme.primary }}
        >
          <Icon className="h-3.5 w-3.5" />
        </span>
        <h2 className="text-[15px] font-semibold text-gray-900 dark:text-gray-100">{title}</h2>
      </header>
      <div className="p-2 space-y-1.5">{children}</div>
    </section>
  );
}
