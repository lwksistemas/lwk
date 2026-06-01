"use client";

/**
 * Integração Memed — prescrição digital (Receituário e Exames).
 *
 * Fluxo:
 * 1. Busca o token do prescritor no backend (api-key/secret-key ficam no servidor).
 * 2. Injeta o script da Memed com data-token=<token>.
 * 3. Aguarda o módulo `plataforma.prescricao` iniciar e define o paciente.
 * 4. Abre o editor da Memed (medicamentos e exames ficam no mesmo editor).
 *
 * Carrega sob demanda (no primeiro clique) para não pesar a página.
 */

import { forwardRef, useCallback, useImperativeHandle, useRef } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { logger } from "@/lib/logger";

/* eslint-disable @typescript-eslint/no-explicit-any */
declare global {
  interface Window {
    MdHub?: any;
    MdSinapsePrescricao?: any;
  }
}

export interface MemedPrescricaoHandle {
  /** Garante a Memed carregada, define o paciente e abre o editor de prescrição. */
  abrir: () => Promise<void>;
}

interface MemedPrescricaoProps {
  professionalId?: number | null;
  patientId: number;
  patientName: string;
}

const SCRIPT_ID = "memed-sinapse-prescricao";

/** Converte data ISO (YYYY-MM-DD) para o formato dd/mm/aaaa esperado pela Memed. */
function toBrDate(value?: string | null): string {
  if (!value) return "";
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  if (!match) return "";
  const [, y, m, d] = match;
  return `${d}/${m}/${y}`;
}

const MemedPrescricao = forwardRef<MemedPrescricaoHandle, MemedPrescricaoProps>(
  ({ professionalId, patientId, patientName }, ref) => {
    const initPromiseRef = useRef<Promise<void> | null>(null);
    const readyRef = useRef(false);

    const carregarScript = useCallback((scriptUrl: string, token: string) => {
      return new Promise<void>((resolve, reject) => {
        const existing = document.getElementById(SCRIPT_ID) as HTMLScriptElement | null;
        if (existing) {
          // Script já presente: garante o token mais recente do prescritor.
          existing.setAttribute("data-token", token);
          resolve();
          return;
        }
        const script = document.createElement("script");
        script.id = SCRIPT_ID;
        script.type = "text/javascript";
        script.src = scriptUrl;
        script.setAttribute("data-token", token);
        script.async = true;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error("Falha ao carregar o script da Memed."));
        document.body.appendChild(script);
      });
    }, []);

    const aguardarModulo = useCallback(() => {
      return new Promise<void>((resolve, reject) => {
        if (!window.MdSinapsePrescricao) {
          reject(new Error("Memed não inicializada (MdSinapsePrescricao indisponível)."));
          return;
        }
        const timeout = setTimeout(
          () => reject(new Error("Tempo esgotado ao iniciar a Memed.")),
          30000,
        );
        window.MdSinapsePrescricao.event.add("core:moduleInit", (module: any) => {
          if (module?.name === "plataforma.prescricao") {
            clearTimeout(timeout);
            resolve();
          }
        });
      });
    }, []);

    const garantirPronto = useCallback(() => {
      if (readyRef.current) return Promise.resolve();
      if (initPromiseRef.current) return initPromiseRef.current;

      const promise = (async () => {
        const cfg = await ClinicaBelezaAPI.memed.token({
          professional: professionalId ?? undefined,
        });
        if (!cfg?.token || !cfg?.script_url) {
          throw new Error("Configuração da Memed incompleta.");
        }
        await carregarScript(cfg.script_url, cfg.token);
        await aguardarModulo();
        readyRef.current = true;
      })();

      initPromiseRef.current = promise;
      promise.catch(() => {
        // Permite nova tentativa após falha.
        initPromiseRef.current = null;
      });
      return promise;
    }, [professionalId, carregarScript, aguardarModulo]);

    const definirPaciente = useCallback(async () => {
      let detalhe: Record<string, any> = {};
      try {
        detalhe = await ClinicaBelezaAPI.get(`/patients/${patientId}/`);
      } catch (e) {
        logger.warn("Memed: não foi possível carregar detalhes do paciente:", e);
      }
      // A Memed não permite editar manualmente os campos enviados via MdHub.
      // Por isso enviamos apenas os campos preenchidos — o prescritor completa o resto.
      const paciente: Record<string, unknown> = {
        idExterno: String(patientId),
        nome: detalhe?.nome || patientName,
      };
      if (detalhe?.cpf) paciente.cpf = detalhe.cpf;
      if (detalhe?.telefone) paciente.telefone = detalhe.telefone;
      if (detalhe?.email) paciente.email = detalhe.email;
      if (detalhe?.endereco) paciente.endereco = detalhe.endereco;
      if (detalhe?.cidade) paciente.cidade = detalhe.cidade;
      const dataNascimento = toBrDate(detalhe?.data_nascimento);
      if (dataNascimento) paciente.data_nascimento = dataNascimento;

      await window.MdHub.command.send("plataforma.prescricao", "setPaciente", paciente);
    }, [patientId, patientName]);

    const abrir = useCallback(async () => {
      await garantirPronto();
      if (!window.MdHub) {
        throw new Error("Memed não disponível.");
      }
      await definirPaciente();
      // Método canônico do quickstart da Memed para exibir o módulo de prescrição.
      window.MdHub.module.show("plataforma.prescricao");
    }, [garantirPronto, definirPaciente]);

    useImperativeHandle(ref, () => ({ abrir }), [abrir]);

    return null;
  },
);

MemedPrescricao.displayName = "MemedPrescricao";

export default MemedPrescricao;
