"use client";

import { Search } from "lucide-react";

export function LocalizarClienteButton({
  onClick,
  title = "Localizar cliente",
}: {
  onClick: () => void;
  title?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-200 rounded-lg border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-800 transition-colors shrink-0"
      title={title}
    >
      <Search className="w-4 h-4 shrink-0" style={{ color: "var(--cb-primary, #8B3D52)" }} />
      <span className="hidden sm:inline">Localizar cliente</span>
      <span className="sm:hidden">Localizar</span>
    </button>
  );
}
