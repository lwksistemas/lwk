"use client";

import { useState } from "react";
import { Eye, Printer } from "lucide-react";
import { useToast } from "@/components/ui/Toast";
import type { ConsultaPdfModo } from "@/lib/consulta-print";

function mensagemErro(e: unknown, fallback: string): string {
  if (e instanceof Error) return e.message;
  if (e && typeof e === "object") {
    const api = e as { error?: string; detail?: string };
    if (api.error) return api.error;
    if (typeof api.detail === "string") return api.detail;
  }
  return fallback;
}

type Props = {
  /** Preferido: Visualizar + Imprimir com o mesmo handler. */
  onAction?: (modo: ConsultaPdfModo) => void | Promise<unknown>;
  /** Compat: só Imprimir (sem botão Visualizar). */
  onPrint?: () => void | Promise<unknown>;
  labelVisualizar?: string;
  labelImprimir?: string;
  className?: string;
};

export function ConsultaPrintButton({
  onAction,
  onPrint,
  labelVisualizar = "Visualizar",
  labelImprimir = "Imprimir",
  className = "",
}: Props) {
  const toast = useToast();
  const [loading, setLoading] = useState<ConsultaPdfModo | "print-only" | null>(null);

  const run = async (modo: ConsultaPdfModo | "print-only") => {
    if (loading) return;
    setLoading(modo);
    try {
      if (modo === "print-only") {
        await onPrint?.();
      } else if (onAction) {
        await onAction(modo);
      } else if (onPrint && modo === "imprimir") {
        await onPrint();
      }
    } catch (e) {
      toast.error(
        mensagemErro(
          e,
          modo === "visualizar" ? "Não foi possível visualizar." : "Não foi possível imprimir.",
        ),
      );
    } finally {
      setLoading(null);
    }
  };

  const btnClass =
    "inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700 disabled:opacity-50 transition-colors";

  if (onAction) {
    return (
      <div className={`inline-flex items-center gap-1.5 ${className}`}>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            void run("visualizar");
          }}
          disabled={!!loading}
          title="Visualizar PDF"
          className={btnClass}
        >
          <Eye size={13} />
          {loading === "visualizar" ? "Abrindo..." : labelVisualizar}
        </button>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            void run("imprimir");
          }}
          disabled={!!loading}
          title="Imprimir"
          className={btnClass}
        >
          <Printer size={13} />
          {loading === "imprimir" ? "Gerando..." : labelImprimir}
        </button>
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        void run("print-only");
      }}
      disabled={!!loading}
      title="Imprimir"
      className={`${btnClass} ${className}`}
    >
      <Printer size={13} />
      {loading ? "Gerando..." : labelImprimir}
    </button>
  );
}
