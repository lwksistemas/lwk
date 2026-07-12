"use client";

import { useState } from "react";
import { Printer } from "lucide-react";
import { useToast } from "@/components/ui/Toast";

export function ConsultaPrintButton({
  onPrint,
  label = "Imprimir",
  className = "",
}: {
  onPrint: () => void | Promise<unknown>;
  label?: string;
  className?: string;
}) {
  const toast = useToast();
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    if (loading) return;
    setLoading(true);
    try {
      await onPrint();
    } catch (e) {
      let msg = "Não foi possível imprimir.";
      if (e instanceof Error) {
        msg = e.message;
      } else if (e && typeof e === "object") {
        const api = e as { error?: string; detail?: string };
        if (api.error) msg = api.error;
        else if (typeof api.detail === "string") msg = api.detail;
      }
      toast.error(msg);
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
