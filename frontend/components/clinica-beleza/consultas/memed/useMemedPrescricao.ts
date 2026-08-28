import { useCallback, useEffect, useRef } from "react";
import { ClinicaBelezaAPI, clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { logger } from "@/lib/logger";
import { mensagemPrescritorMemedPendente } from "@/components/clinica-beleza/memed-page/memed-page-utils";
import { parsePrescricaoMemed } from "@/lib/memed-prescricao-parser";
import { withTimeout } from "@/lib/memed-sdk";
import { MEMED_TOKEN_TIMEOUT_MS } from "./memed-constants";
import type { DadosClinicaMemed } from "./memed-paciente";
import { enviarPacienteMemed, enviarWorkplaceMemed } from "./memed-paciente";
import {
  abrirModuloPrescricaoMemed,
  aguardarIframeMemedNoHost,
  carregarScriptMemed,
  fecharModuloPrescricaoMemed,
  setPrescricaoImpressaHandler,
} from "./memed-script-loader";

function esperarProximoFrame(): Promise<void> {
  return new Promise((resolve) => {
    requestAnimationFrame(() => resolve());
  });
}

export function useMemedPrescricao({
  consultaId,
  professionalId,
  patientId,
  patientName,
  onPrescricaoRegistrada,
}: {
  consultaId: number;
  professionalId?: number | null;
  patientId: number;
  patientName: string;
  onPrescricaoRegistrada?: () => void;
}) {
  const initPromiseRef = useRef<Promise<void> | null>(null);
  const readyRef = useRef(false);
  const clinicaRef = useRef<DadosClinicaMemed | null>(null);

  const garantirPronto = useCallback(() => {
    if (readyRef.current) return Promise.resolve();
    if (initPromiseRef.current) return initPromiseRef.current;

    const promise = (async () => {
      const path =
        professionalId != null ? `/memed/token/?professional=${professionalId}` : "/memed/token/";
      const res = await withTimeout(
        clinicaBelezaFetch(path, { signal: AbortSignal.timeout(MEMED_TOKEN_TIMEOUT_MS) }),
        MEMED_TOKEN_TIMEOUT_MS,
        "Memed: tempo esgotado ao obter o token do prescritor",
      );
      const cfg = await res.json();
      if (!res.ok) {
        throw new Error(
          (typeof cfg?.error === "string" && cfg.error) ||
            "Não foi possível obter o token do prescritor na Memed.",
        );
      }
      if (!cfg?.token || !cfg?.script_url) {
        throw new Error("Configuração da Memed incompleta (token ou script ausente).");
      }
      clinicaRef.current = cfg.clinica ?? null;
      const pendente = mensagemPrescritorMemedPendente(cfg.prescritor);
      if (pendente) throw new Error(pendente);
      await carregarScriptMemed(cfg.script_url, cfg.token);
      readyRef.current = true;
    })();

    initPromiseRef.current = promise;
    promise.catch(() => {
      initPromiseRef.current = null;
    });
    return promise;
  }, [professionalId]);

  useEffect(() => {
    setPrescricaoImpressaHandler((data: unknown) => {
      const { prescricaoId, itens, resumo, pdfUrl } = parsePrescricaoMemed(data);
      if (!prescricaoId && !itens.length) {
        logger.warn("Memed: evento prescricaoImpressa sem dados utilizáveis.", data);
        return;
      }
      const payload = {
        prescricao_id: prescricaoId,
        resumo,
        itens,
        pdf_url: pdfUrl,
        professional: professionalId ?? null,
      };
      const salvar = () =>
        ClinicaBelezaAPI.memed.salvarPrescricao(consultaId, payload).then(() => {
          onPrescricaoRegistrada?.();
        });

      void salvar().catch((e) => logger.warn("Memed: falha ao registrar prescrição no histórico:", e));
      if (!pdfUrl && prescricaoId) {
        window.setTimeout(() => {
          void salvar().catch(() => {});
        }, 4000);
      }
    });
    return () => setPrescricaoImpressaHandler(null);
  }, [consultaId, professionalId, onPrescricaoRegistrada]);

  const abrir = useCallback(async () => {
    await esperarProximoFrame();
    await garantirPronto();
    abrirModuloPrescricaoMemed();
    await aguardarIframeMemedNoHost();
    void enviarPacienteMemed(patientId, patientName).catch((e) => {
      logger.warn("Memed: não foi possível definir o paciente:", e);
    });
    void enviarWorkplaceMemed(clinicaRef.current).catch((e) => {
      logger.warn("Memed: não foi possível definir o local de atendimento:", e);
    });
  }, [garantirPronto, patientId, patientName]);

  const fechar = useCallback(() => {
    try {
      fecharModuloPrescricaoMemed();
    } catch (e) {
      logger.warn("Memed: falha ao fechar o módulo de prescrição:", e);
    }
  }, []);

  return { abrir, fechar };
}
