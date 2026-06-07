"use client";

import { useState } from "react";
import { FileSignature, Download, RefreshCw } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";

const STATUS_LABEL: Record<string, string> = {
  rascunho: "Não enviado",
  aguardando_paciente: "Aguardando paciente",
  aguardando_profissional: "Aguardando profissional",
  concluido: "Assinado",
};

export function ConsultaTermoConsentimentoButton({
  consultaId,
  exigeTermo,
  statusAssinatura,
  onUpdated,
}: {
  consultaId: number;
  exigeTermo?: boolean;
  statusAssinatura?: string;
  onUpdated?: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const status = statusAssinatura || "rascunho";

  if (!exigeTermo) return null;

  const enviar = async () => {
    if (!confirm("Enviar termo de consentimento por e-mail para o paciente assinar primeiro?")) return;
    setLoading(true);
    try {
      const res = await ClinicaBelezaAPI.consultas.termoConsentimento.enviar(consultaId);
      alert(res.message || "E-mail enviado.");
      onUpdated?.();
    } catch (e: unknown) {
      const msg =
        e && typeof e === "object" && "detail" in e
          ? String((e as { detail: string }).detail)
          : e instanceof Error
            ? e.message
            : "Erro ao enviar.";
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  const reenviar = async () => {
    setLoading(true);
    try {
      const res = await ClinicaBelezaAPI.consultas.termoConsentimento.reenviar(consultaId);
      alert(res.message || "Link reenviado.");
      onUpdated?.();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Erro ao reenviar.");
    } finally {
      setLoading(false);
    }
  };

  const baixarPdf = async () => {
    setLoading(true);
    try {
      const blob = await ClinicaBelezaAPI.consultas.termoConsentimento.downloadPdf(consultaId);
      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download = `termo_consentimento_${consultaId}.pdf`;
      link.click();
      window.URL.revokeObjectURL(link.href);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Erro ao baixar PDF.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span
        className="text-xs px-2 py-1 rounded-full bg-purple-50 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200"
        title="Termo de consentimento esclarecido"
      >
        Termo: {STATUS_LABEL[status] || status}
      </span>
      {status === "rascunho" && (
        <button
          type="button"
          onClick={enviar}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white text-sm font-medium disabled:opacity-50"
          style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
        >
          <FileSignature size={16} />
          {loading ? "Enviando…" : "Assinatura digital"}
        </button>
      )}
      {(status === "aguardando_paciente" || status === "aguardando_profissional") && (
        <button
          type="button"
          onClick={reenviar}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border border-gray-300 dark:border-neutral-600"
        >
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          Reenviar link
        </button>
      )}
      <button
        type="button"
        onClick={baixarPdf}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border border-gray-300 dark:border-neutral-600"
      >
        <Download size={16} />
        PDF
      </button>
    </div>
  );
}
