"use client";

import { useState } from "react";
import { Printer } from "lucide-react";

export function ConsultaPrintButton({
  onPrint,
  label = "Imprimir",
  className = "",
}: {
  onPrint: () => void | Promise<void>;
  label?: string;
  className?: string;
}) {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    if (loading) return;
    setLoading(true);
    try {
      await onPrint();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Não foi possível imprimir.";
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={loading}
      title="Imprimir"
      className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700 disabled:opacity-50 transition-colors ${className}`}
    >
      <Printer size={13} />
      {loading ? "Gerando..." : label}
    </button>
  );
}
