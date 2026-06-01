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

import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { apenasDigitos } from "@/lib/format-br";
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
const MODULO_PRESCRICAO = "plataforma.prescricao";
const READY_FLAG = "__memedPrescricaoPronta";
const TIMEOUT_MS = 30000;

/** Indica se o módulo de prescrição da Memed já terminou de inicializar. */
function moduloPronto(): boolean {
  return typeof window !== "undefined" && (window as any)[READY_FLAG] === true;
}

/**
 * Registra (uma única vez) o listener de `core:moduleInit` e marca um flag global
 * quando o módulo de prescrição fica pronto.
 *
 * Por que global e idempotente: o evento `core:moduleInit` dispara só uma vez por
 * carregamento do script. Se registrarmos um novo listener a cada clique, o evento
 * já terá disparado e nunca mais chega — causando timeout. Marcar o flag e fazer
 * polling sobre ele evita essa corrida.
 */
function registrarListenerPrescricao(): void {
  if (typeof window === "undefined") return;
  const sinapse = (window as any).MdSinapsePrescricao;
  if (!sinapse?.event?.add || (window as any).__memedListenerRegistrado) return;
  (window as any).__memedListenerRegistrado = true;
  sinapse.event.add("core:moduleInit", (module: any) => {
    if (module?.name === MODULO_PRESCRICAO) {
      (window as any)[READY_FLAG] = true;
    }
  });
}

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
          // Script já presente: garante o token mais recente do prescritor e o listener.
          existing.setAttribute("data-token", token);
          registrarListenerPrescricao();
          resolve();
          return;
        }
        const script = document.createElement("script");
        script.id = SCRIPT_ID;
        script.type = "text/javascript";
        script.src = scriptUrl;
        script.setAttribute("data-token", token);
        script.async = true;
        script.onload = () => {
          registrarListenerPrescricao();
          resolve();
        };
        script.onerror = () => reject(new Error("Falha ao carregar o script da Memed."));
        document.body.appendChild(script);
      });
    }, []);

    const aguardarModulo = useCallback(() => {
      return new Promise<void>((resolve, reject) => {
        registrarListenerPrescricao();
        const inicio = Date.now();
        const verificar = () => {
          if (moduloPronto()) {
            resolve();
            return;
          }
          if (Date.now() - inicio > TIMEOUT_MS) {
            reject(new Error(
              "Tempo esgotado ao iniciar a Memed. Verifique a conexão e tente novamente.",
            ));
            return;
          }
          // O listener pode ainda não estar registrado se o script demorar a executar.
          registrarListenerPrescricao();
          setTimeout(verificar, 250);
        };
        verificar();
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

    // Pré-carrega a Memed ao abrir a consulta, para o primeiro clique ser instantâneo.
    useEffect(() => {
      garantirPronto().catch((e) => {
        logger.warn("Memed: pré-carregamento falhou (tentará novamente ao clicar):", e);
      });
    }, [garantirPronto]);

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
      const cpf = apenasDigitos(detalhe?.cpf);
      if (cpf) paciente.cpf = cpf;
      const telefone = apenasDigitos(detalhe?.telefone);
      if (telefone) paciente.telefone = telefone;
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
