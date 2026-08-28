import { useCallback, useEffect, useRef } from "react";
import { ClinicaBelezaAPI, clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { logger } from "@/lib/logger";
import { parsePrescricaoMemed } from "@/lib/memed-prescricao-parser";
import { MEMED_PRELOAD_SCRIPT_URL } from "./memed-constants";
import type { DadosClinicaMemed } from "./memed-paciente";
import { enviarPacienteMemed, enviarWorkplaceMemed } from "./memed-paciente";
import {
  abrirModuloPrescricaoMemed,
  aguardarModuloMemed,
  aguardarWidgetMemedOperacional,
  carregarScriptMemed,
  enviarComandoPrescricaoMemed,
  fecharModuloPrescricaoMemed,
  logoutMemedSdk,
  preloadMemedScript,
  setPrescricaoImpressaHandler,
} from "./memed-script-loader";

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
      preloadMemedScript(MEMED_PRELOAD_SCRIPT_URL);
      const path =
        professionalId != null ? `/memed/token/?professional=${professionalId}` : "/memed/token/";
      const res = await clinicaBelezaFetch(path);
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
      await carregarScriptMemed(cfg.script_url, cfg.token);
      await aguardarModuloMemed();
      readyRef.current = true;
    })();

    initPromiseRef.current = promise;
    promise.catch(() => {
      initPromiseRef.current = null;
    });
    return promise;
  }, [professionalId]);

  useEffect(() => {
    preloadMemedScript(MEMED_PRELOAD_SCRIPT_URL);
  }, []);

  useEffect(() => () => logoutMemedSdk(), []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") fecharModuloPrescricaoMemed();
    };
    window.addEventListener("keydown", onKeyDown, true);
    return () => window.removeEventListener("keydown", onKeyDown, true);
  }, []);

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
    await garantirPronto();
    if (!window.MdHub) throw new Error("Memed não disponível.");
    try {
      await aguardarWidgetMemedOperacional();
    } catch (e) {
      fecharModuloPrescricaoMemed();
      throw e;
    }
    try {
      await enviarPacienteMemed(patientId, patientName);
    } catch (e) {
      logger.warn("Memed: não foi possível definir o paciente:", e);
    }
    try {
      await enviarWorkplaceMemed(clinicaRef.current);
    } catch (e) {
      logger.warn("Memed: não foi possível definir o local de atendimento:", e);
    }
    abrirModuloPrescricaoMemed();
    try {
      await enviarComandoPrescricaoMemed("newPrescription");
    } catch (e) {
      logger.warn("Memed: newPrescription indisponível:", e);
    }
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
