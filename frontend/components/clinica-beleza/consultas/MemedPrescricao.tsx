"use client";

/**
 * Integração Memed — prescrição digital (Receituário e Exames).
 * Abre num modal do LWK (data-container) para a overlay fullscreen da Memed
 * V4 não travar a consulta.
 */

import { forwardRef, useCallback, useEffect, useImperativeHandle, useState } from "react";
import { flushSync } from "react-dom";
import { X } from "lucide-react";
import { MEMED_CONTAINER_ID } from "./memed/memed-constants";
import { useMemedPrescricao } from "./memed/useMemedPrescricao";
import { moverIframeMemedParaHost } from "@/lib/memed-sdk";

export interface MemedPrescricaoHandle {
  abrir: () => Promise<void>;
  fechar: () => void;
}

interface MemedPrescricaoProps {
  consultaId: number;
  professionalId?: number | null;
  patientId: number;
  patientName: string;
  onPrescricaoRegistrada?: () => void;
}

const MemedPrescricao = forwardRef<MemedPrescricaoHandle, MemedPrescricaoProps>(
  ({ consultaId, professionalId, patientId, patientName, onPrescricaoRegistrada }, ref) => {
    const [aberto, setAberto] = useState(false);
    const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
    const [erro, setErro] = useState<string | null>(null);
    const { abrir: abrirSdk, fechar: fecharSdk } = useMemedPrescricao({
      consultaId,
      professionalId,
      patientId,
      patientName,
      onPrescricaoRegistrada,
    });

    const fechar = useCallback(() => {
      fecharSdk();
      setAberto(false);
      setErro(null);
    }, [fecharSdk]);

    const abrir = useCallback(async () => {
      flushSync(() => {
        setAberto(true);
        setStatus("loading");
        setErro(null);
      });
      try {
        await abrirSdk();
        setStatus("ready");
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Erro ao abrir a prescrição da Memed.";
        setStatus("error");
        setErro(msg);
        throw e;
      }
    }, [abrirSdk]);

    useImperativeHandle(ref, () => ({ abrir, fechar }), [abrir, fechar]);

    useEffect(() => {
      if (!aberto) return;
      const onKey = (event: KeyboardEvent) => {
        if (event.key === "Escape") fechar();
      };
      window.addEventListener("keydown", onKey, true);
      const interval = window.setInterval(() => {
        if (moverIframeMemedParaHost(document, MEMED_CONTAINER_ID) && status === "loading") {
          setStatus("ready");
        }
      }, 400);
      return () => {
        window.removeEventListener("keydown", onKey, true);
        window.clearInterval(interval);
      };
    }, [aberto, fechar, status]);

    return (
      <div
        className="fixed inset-0 flex flex-col bg-black/50 p-2 sm:p-4"
        style={{
          zIndex: aberto ? 2147483647 : -1,
          visibility: aberto ? "visible" : "hidden",
          pointerEvents: aberto ? "auto" : "none",
        }}
        role="dialog"
        aria-modal={aberto}
        aria-hidden={!aberto}
        aria-label="Prescrição Memed"
      >
        <div className="mx-auto flex h-full w-full max-w-6xl flex-col overflow-hidden rounded-xl bg-white shadow-2xl dark:bg-neutral-900">
          <div className="flex items-center justify-between gap-3 border-b border-gray-200 px-4 py-3 dark:border-neutral-700">
            <div>
              <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">Prescrição Memed</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">{patientName}</p>
            </div>
            <button
              type="button"
              onClick={fechar}
              className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-800 hover:bg-gray-50 dark:border-neutral-600 dark:text-gray-100 dark:hover:bg-neutral-800"
            >
              <X size={16} />
              Fechar
            </button>
          </div>
          {status === "loading" && aberto && (
            <p className="px-4 py-2 text-sm text-gray-500">Carregando o editor da Memed…</p>
          )}
          {status === "error" && erro && (
            <p className="px-4 py-2 text-sm text-red-700 dark:text-red-400">{erro}</p>
          )}
          <div
            id={MEMED_CONTAINER_ID}
            className="w-full flex-1 bg-white"
            style={{ minHeight: 700, height: "calc(100vh - 9rem)" }}
          />
        </div>
      </div>
    );
  },
);

MemedPrescricao.displayName = "MemedPrescricao";

export default MemedPrescricao;
