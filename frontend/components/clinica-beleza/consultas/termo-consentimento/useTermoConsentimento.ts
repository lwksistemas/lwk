import { useCallback, useEffect, useRef, useState } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { useToast } from "@/components/ui/Toast";
import type { TermoConsentimentoCanal, TermoProcedimento } from "./termo-consentimento-types";
import {
  extrairErroTermo,
  labelCanalTermo,
  snapshotTermoStatus,
} from "./termo-consentimento-types";

export function useTermoConsentimento({
  consultaId,
  exigeTermo,
  onUpdated,
  aberto,
}: {
  consultaId: number;
  exigeTermo?: boolean;
  onUpdated?: () => void;
  aberto: boolean;
}) {
  const toast = useToast();
  const [loading, setLoading] = useState(false);
  const [termos, setTermos] = useState<TermoProcedimento[]>([]);
  const termosRef = useRef<TermoProcedimento[]>([]);

  const carregar = useCallback(async () => {
    if (!exigeTermo) return;
    try {
      const res = await ClinicaBelezaAPI.consultas.termoConsentimento.get(consultaId);
      const novos = res.termos_procedimentos || [];
      const anterior = termosRef.current;
      const mudou = anterior.length > 0 && snapshotTermoStatus(novos) !== snapshotTermoStatus(anterior);
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

  const pendentesEnvio = termos.filter((t) => t.status === "rascunho");
  const pendentesAssinatura = termos.filter(
    (t) => t.status === "aguardando_paciente" || t.status === "aguardando_profissional",
  );
  const badgeCount = pendentesAssinatura.length || pendentesEnvio.length;

  const enviar = async (procedureId?: number, canal: TermoConsentimentoCanal = "email") => {
    const canalLabel = labelCanalTermo(canal);
    const msg = procedureId
      ? `Enviar termo deste procedimento por ${canalLabel} para o paciente assinar?`
      : `Enviar ${pendentesEnvio.length} termo(s) por ${canalLabel}? O paciente deve ler e assinar cada procedimento separadamente.`;
    if (!confirm(msg)) return;
    setLoading(true);
    try {
      const res = await ClinicaBelezaAPI.consultas.termoConsentimento.enviar(consultaId, procedureId, canal);
      toast.success(res.message || `${canalLabel} enviado.`);
      await carregar();
      onUpdated?.();
    } catch (e: unknown) {
      toast.error(extrairErroTermo(e));
    } finally {
      setLoading(false);
    }
  };

  const reenviar = async (procedureId: number, nome: string, canal: TermoConsentimentoCanal = "email") => {
    setLoading(true);
    try {
      const res = await ClinicaBelezaAPI.consultas.termoConsentimento.reenviar(consultaId, procedureId, canal);
      toast.success(res.message || `Link reenviado — ${nome}.`);
      await carregar();
      onUpdated?.();
    } catch (e: unknown) {
      toast.error(extrairErroTermo(e, "Erro ao reenviar."));
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
      toast.error(extrairErroTermo(e, "Erro ao baixar PDF."));
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    termos,
    pendentesEnvio,
    badgeCount,
    enviar,
    reenviar,
    baixarPdf,
  };
}
