"use client";

import { useState } from "react";
import { Eye } from "lucide-react";
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
  onAction: (modo: ConsultaPdfModo, janela?: Window | null) => void | Promise<unknown>;
  labelVisualizar?: string;
  className?: string;
};

export function ConsultaPrintButton({
  onAction,
  labelVisualizar = "Visualizar",
  className = "",
}: Props) {
  const toast = useToast();
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (loading) return;
    setLoading(true);
    // Abre a aba já no clique (dentro do gesto do usuário) para o navegador não
    // bloquear o pop-up quando o PDF precisa ser buscado/gerado na API (await).
    const janela = abrirJanelaPdf();
    try {
      await onAction("visualizar", janela);
    } catch (e) {
      fecharJanelaPdf(janela);
      toast.error(mensagemErro(e, "Não foi possível visualizar."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        void run();
      }}
      disabled={loading}
      title="Visualizar PDF — imprima pelo visualizador"
      className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700 disabled:opacity-50 transition-colors ${className}`}
    >
      <Eye size={13} />
      {loading ? "Abrindo..." : labelVisualizar}
    </button>
  );
}
