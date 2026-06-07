"use client";

import { useCallback, useEffect, useState } from "react";
import { FileSignature, Download, RefreshCw } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";

type TermoProcedimento = {
  id: number;
  procedure_id: number;
  procedure_nome: string;
  status: string;
  status_display: string;
  tem_conteudo: boolean;
};

export function ConsultaTermoConsentimentoButton({
  consultaId,
  exigeTermo,
  onUpdated,
}: {
  consultaId: number;
  exigeTermo?: boolean;
  statusAssinatura?: string;
  onUpdated?: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const [termos, setTermos] = useState<TermoProcedimento[]>([]);

  const carregar = useCallback(async () => {
    if (!exigeTermo) return;
    try {
      const res = await ClinicaBelezaAPI.consultas.termoConsentimento.get(consultaId);
      setTermos(res.termos_procedimentos || []);
    } catch {
      setTermos([]);
    }
  }, [consultaId, exigeTermo]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  if (!exigeTermo) return null;

  const pendentesEnvio = termos.filter((t) => t.status === "rascunho");

  const enviar = async (procedureId?: number) => {
    const msg = procedureId
      ? "Enviar termo deste procedimento por e-mail para o paciente assinar?"
      : `Enviar ${pendentesEnvio.length} termo(s) por e-mail? O paciente deve ler e assinar cada procedimento separadamente.`;
    if (!confirm(msg)) return;
    setLoading(true);
    try {
      const res = await ClinicaBelezaAPI.consultas.termoConsentimento.enviar(consultaId, procedureId);
      alert(res.message || "E-mail enviado.");
      await carregar();
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

  const reenviar = async (procedureId: number, nome: string) => {
    setLoading(true);
    try {
      const res = await ClinicaBelezaAPI.consultas.termoConsentimento.reenviar(consultaId, procedureId);
      alert(res.message || `Link reenviado — ${nome}.`);
      await carregar();
      onUpdated?.();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Erro ao reenviar.");
    } finally {
      setLoading(false);
    }
  };

  const baixarPdf = async (procedureId: number, nome: string) => {
    setLoading(true);
    try {
      const blob = await ClinicaBelezaAPI.consultas.termoConsentimento.downloadPdf(consultaId, procedureId);
      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download = `termo_${nome.replace(/\s+/g, "_")}_${consultaId}.pdf`;
      link.click();
      window.URL.revokeObjectURL(link.href);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Erro ao baixar PDF.");
    } finally {
      setLoading(false);
    }
  };

  if (!termos.length) {
    return (
      <span className="text-xs text-gray-500 dark:text-gray-400">Carregando termos…</span>
    );
  }

  return (
    <div className="flex flex-col gap-2 w-full max-w-xl">
      <p className="text-xs text-gray-600 dark:text-gray-400">
        Cada procedimento exige leitura e assinatura separadas.
      </p>
      {termos.map((t) => (
        <div
          key={t.procedure_id}
          className="flex flex-wrap items-center gap-2 rounded-lg border border-purple-100 dark:border-purple-900/40 bg-purple-50/50 dark:bg-purple-900/10 px-2.5 py-2"
        >
          <span className="text-sm font-medium text-gray-800 dark:text-gray-200 min-w-0 flex-1">
            {t.procedure_nome}
          </span>
          <span
            className="text-xs px-2 py-0.5 rounded-full bg-white dark:bg-neutral-800 text-purple-800 dark:text-purple-200"
            title="Status da assinatura"
          >
            {t.status_display}
          </span>
          {t.status === "rascunho" && (
            <button
              type="button"
              onClick={() => enviar(t.procedure_id)}
              disabled={loading}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-white text-xs font-medium disabled:opacity-50"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              <FileSignature size={14} />
              Enviar
            </button>
          )}
          {(t.status === "aguardando_paciente" || t.status === "aguardando_profissional") && (
            <button
              type="button"
              onClick={() => reenviar(t.procedure_id, t.procedure_nome)}
              disabled={loading}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium border border-gray-300 dark:border-neutral-600"
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              Reenviar
            </button>
          )}
          <button
            type="button"
            onClick={() => baixarPdf(t.procedure_id, t.procedure_nome)}
            disabled={loading}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium border border-gray-300 dark:border-neutral-600"
          >
            <Download size={14} />
            PDF
          </button>
        </div>
      ))}
      {pendentesEnvio.length > 1 && (
        <button
          type="button"
          onClick={() => enviar()}
          disabled={loading}
          className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-white text-sm font-medium disabled:opacity-50 self-start"
          style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
        >
          <FileSignature size={16} />
          {loading ? "Enviando…" : `Enviar todos (${pendentesEnvio.length})`}
        </button>
      )}
    </div>
  );
}
