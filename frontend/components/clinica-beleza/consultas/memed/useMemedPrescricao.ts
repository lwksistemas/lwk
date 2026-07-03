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
  carregarScriptMemed,
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
    let tentativas = 0;
    const maxTentativas = 2;
    const tentarPrecarregar = () => {
      garantirPronto().catch((e) => {
        tentativas++;
        logger.warn(`Memed: pré-carregamento falhou (tentativa ${tentativas}/${maxTentativas}):`, e);
        if (tentativas < maxTentativas) setTimeout(tentarPrecarregar, 3000);
      });
    };
    tentarPrecarregar();
  }, [garantirPronto]);

  useEffect(() => () => logoutMemedSdk(), []);

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
    await enviarPacienteMemed(patientId, patientName);
    try {
      await enviarWorkplaceMemed(clinicaRef.current);
    } catch (e) {
      logger.warn("Memed: não foi possível definir o local de atendimento:", e);
    }
    abrirModuloPrescricaoMemed();
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
