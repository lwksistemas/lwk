"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { FileSignature, Download, RefreshCw, ChevronDown } from "lucide-react";
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

const STATUS_BADGE: Record<string, string> = {
  rascunho: "bg-gray-100 text-gray-600 dark:bg-neutral-700 dark:text-gray-300",
  aguardando_paciente: "bg-amber-50 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200",
  aguardando_profissional: "bg-blue-50 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200",
  concluido: "bg-green-50 text-green-800 dark:bg-green-900/30 dark:text-green-200",
};

export function ConsultaTermoConsentimentoButton({
  consultaId,
  exigeTermo,
  onUpdated,
}: {
  consultaId: number;
  exigeTermo?: boolean;
  onUpdated?: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const [termos, setTermos] = useState<TermoProcedimento[]>([]);
  const [aberto, setAberto] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const termosRef = useRef<TermoProcedimento[]>([]);

  const snapshotStatus = (lista: TermoProcedimento[]) =>
    lista.map((t) => `${t.procedure_id}:${t.status}`).join("|");

  const carregar = useCallback(async () => {
    if (!exigeTermo) return;
    try {
      const res = await ClinicaBelezaAPI.consultas.termoConsentimento.get(consultaId);
      const novos = res.termos_procedimentos || [];
      const anterior = termosRef.current;
      const mudou =
        anterior.length > 0 && snapshotStatus(novos) !== snapshotStatus(anterior);
      termosRef.current = novos;
      setTermos(novos);
      if (mudou) onUpdated?.();
    } catch {
      termosRef.current = [];
      setTermos([]);
    }
  }, [consultaId, exigeTermo, onUpdated]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const aguardandoAssinatura = termos.some(
    (t) => t.status === "aguardando_paciente" || t.status === "aguardando_profissional",
  );

  useEffect(() => {
    if (!exigeTermo || !aguardandoAssinatura) return;

    const atualizar = () => {
      if (document.visibilityState !== "hidden") void carregar();
    };

    const intervalo = window.setInterval(atualizar, aberto ? 3000 : 5000);
    const onVisivel = () => atualizar();
    document.addEventListener("visibilitychange", onVisivel);
    window.addEventListener("focus", onVisivel);

    return () => {
      clearInterval(intervalo);
      document.removeEventListener("visibilitychange", onVisivel);
      window.removeEventListener("focus", onVisivel);
    };
  }, [exigeTermo, aguardandoAssinatura, aberto, carregar]);

  useEffect(() => {
    if (aberto) void carregar();
  }, [aberto, carregar]);

  useEffect(() => {
    if (!aberto) return;
    const fechar = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setAberto(false);
      }
    };
    document.addEventListener("mousedown", fechar);
    return () => document.removeEventListener("mousedown", fechar);
  }, [aberto]);

  if (!exigeTermo) return null;

  const pendentesEnvio = termos.filter((t) => t.status === "rascunho");
  const pendentesAssinatura = termos.filter(
    (t) => t.status === "aguardando_paciente" || t.status === "aguardando_profissional",
  );
  const badgeCount = pendentesAssinatura.length || pendentesEnvio.length;

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
      const errMsg =
        e && typeof e === "object" && "detail" in e
          ? String((e as { detail: string }).detail)
          : e instanceof Error
            ? e.message
            : "Erro ao enviar.";
      alert(errMsg);
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

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setAberto((v) => !v)}
        className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
          aberto
            ? "text-white"
            : "bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-neutral-700"
        }`}
        style={aberto ? { backgroundColor: CLINICA_BELEZA_PRIMARY } : undefined}
        title="Termos de consentimento por procedimento"
      >
        <FileSignature size={16} />
        Termos
        {badgeCount > 0 && (
          <span
            className={`min-w-[1.25rem] h-5 px-1 rounded-full text-[10px] font-bold flex items-center justify-center ${
              aberto ? "bg-white/25 text-white" : "text-white"
            }`}
            style={aberto ? undefined : { backgroundColor: CLINICA_BELEZA_PRIMARY }}
          >
            {badgeCount}
          </span>
        )}
        <ChevronDown size={14} className={`transition-transform ${aberto ? "rotate-180" : ""}`} />
      </button>

      {aberto && (
        <div className="absolute left-0 top-full mt-2 z-50 w-[min(100vw-2rem,22rem)] rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 shadow-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 dark:border-neutral-800">
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">Termos de consentimento</p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Cada procedimento exige leitura e assinatura separadas.
            </p>
          </div>

          <div className="max-h-[min(50vh,16rem)] overflow-y-auto">
            {!termos.length ? (
              <p className="px-4 py-6 text-sm text-gray-500 text-center">Carregando…</p>
            ) : (
              <ul className="divide-y divide-gray-100 dark:divide-neutral-800">
                {termos.map((t) => (
                  <li key={t.procedure_id} className="px-4 py-3">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100 leading-tight">
                        {t.procedure_nome}
                      </span>
                      <span
                        className={`shrink-0 text-[10px] px-2 py-0.5 rounded-full font-medium ${
                          STATUS_BADGE[t.status] || STATUS_BADGE.rascunho
                        }`}
                      >
                        {t.status_display}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {t.status === "rascunho" && (
                        <button
                          type="button"
                          onClick={() => enviar(t.procedure_id)}
                          disabled={loading}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-white text-xs font-medium disabled:opacity-50"
                          style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                        >
                          <FileSignature size={12} />
                          Enviar
                        </button>
                      )}
                      {(t.status === "aguardando_paciente" || t.status === "aguardando_profissional") && (
                        <button
                          type="button"
                          onClick={() => reenviar(t.procedure_id, t.procedure_nome)}
                          disabled={loading}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-800 disabled:opacity-50"
                        >
                          <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
                          Reenviar
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => baixarPdf(t.procedure_id, t.procedure_nome)}
                        disabled={loading}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-800 disabled:opacity-50"
                      >
                        <Download size={12} />
                        PDF
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {pendentesEnvio.length > 1 && (
            <div className="px-4 py-3 border-t border-gray-100 dark:border-neutral-800 bg-gray-50/80 dark:bg-neutral-800/50">
              <button
                type="button"
                onClick={() => enviar()}
                disabled={loading}
                className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-white text-sm font-medium disabled:opacity-50"
                style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
              >
                <FileSignature size={14} />
                {loading ? "Enviando…" : `Enviar todos (${pendentesEnvio.length})`}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
