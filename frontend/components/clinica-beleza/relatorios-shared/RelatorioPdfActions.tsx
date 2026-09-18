"use client";

import { useState } from "react";
import { Eye, Printer } from "lucide-react";
import { useToast } from "@/components/ui/Toast";
import { abrirJanelaPdf, fecharJanelaPdf, type ConsultaPdfModo } from "@/lib/consulta-print";

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
  disabled?: boolean;
  onPdf: (modo: ConsultaPdfModo, janela: Window | null) => Promise<void>;
};

const btnBase =
  "inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 text-xs sm:text-sm font-medium rounded-lg disabled:opacity-50";

export function RelatorioPdfActions({ disabled, onPdf }: Props) {
  const toast = useToast();
  const [loading, setLoading] = useState<ConsultaPdfModo | null>(null);

  const run = async (modo: ConsultaPdfModo) => {
    if (disabled || loading) return;
    setLoading(modo);
    const janela = abrirJanelaPdf();
    try {
      await onPdf(modo, janela);
    } catch (e) {
      fecharJanelaPdf(janela);
      toast.error(mensagemErro(e, "Não foi possível gerar o PDF."));
    } finally {
      setLoading(null);
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={() => void run("visualizar")}
        disabled={disabled || Boolean(loading)}
        title="Visualizar PDF"
        className={`${btnBase} text-white`}
        style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
      >
        <Eye size={16} />
        <span className="hidden sm:inline">{loading === "visualizar" ? "Abrindo…" : "PDF"}</span>
      </button>
      <button
        type="button"
        onClick={() => void run("imprimir")}
        disabled={disabled || Boolean(loading)}
        title="Imprimir PDF"
        className={`${btnBase} border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100`}
      >
        <Printer size={16} />
        <span className="hidden sm:inline">{loading === "imprimir" ? "Abrindo…" : "Imprimir"}</span>
      </button>
    </>
  );
}
