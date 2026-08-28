"use client";

/**
 * Integração Memed — prescrição digital (Receituário e Exames).
 * Barra Fechar do LWK por cima do overlay da Memed (sem mover o iframe).
 */

import { forwardRef, useCallback, useEffect, useImperativeHandle, useState } from "react";
import { flushSync } from "react-dom";
import { X } from "lucide-react";
import { MEMED_CONTAINER_ID } from "./memed/memed-constants";
import { useMemedPrescricao } from "./memed/useMemedPrescricao";
import { garantirEditorMemedVisivel } from "@/lib/memed-sdk";

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

    const editorAberto = aberto && status === "ready";
    const avisoAberto = aberto && status !== "ready";

    useEffect(() => {
      if (!aberto) return;
      const onKey = (event: KeyboardEvent) => {
        if (event.key === "Escape") fechar();
      };
      window.addEventListener("keydown", onKey, true);
      const interval = window.setInterval(() => {
        if (garantirEditorMemedVisivel(document, MEMED_CONTAINER_ID) && status === "loading") {
          setStatus("ready");
        }
      }, 400);
      return () => {
        window.removeEventListener("keydown", onKey, true);
        window.clearInterval(interval);
      };
    }, [aberto, fechar, status]);

    return (
      <>
        {avisoAberto && (
          <div
            className="fixed inset-0 z-[2147483647] flex items-center justify-center bg-black/50 p-4"
            role="dialog"
            aria-modal="true"
            aria-label="Prescrição Memed"
          >
            <div className="w-full max-w-lg rounded-xl bg-white p-5 shadow-2xl dark:bg-neutral-900">
              <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">Prescrição Memed</p>
              <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">{patientName}</p>
              {status === "loading" && (
                <p className="mt-3 text-sm text-gray-600 dark:text-gray-300">Carregando o editor da Memed…</p>
              )}
              {status === "error" && erro && (
                <p className="mt-3 text-sm text-red-700 dark:text-red-400">{erro}</p>
              )}
              <button
                type="button"
                onClick={fechar}
                className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-800 hover:bg-gray-50 dark:border-neutral-600 dark:text-gray-100 dark:hover:bg-neutral-800"
              >
                <X size={16} />
                Fechar
              </button>
            </div>
          </div>
        )}
        <div
          className="fixed inset-x-0 top-0 flex items-center justify-between gap-3 border-b border-gray-200 bg-white px-4 py-3 shadow-md dark:border-neutral-700 dark:bg-neutral-900"
          style={{
            zIndex: editorAberto ? 2147483647 : -1,
            visibility: editorAberto ? "visible" : "hidden",
            pointerEvents: editorAberto ? "auto" : "none",
          }}
          role="dialog"
          aria-modal={editorAberto}
          aria-hidden={!editorAberto}
          aria-label="Prescrição Memed"
        >
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
        <div
          id={MEMED_CONTAINER_ID}
          className="bg-white"
          style={{
            position: "fixed",
            top: editorAberto ? "4.25rem" : 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: editorAberto ? 2147483645 : -1,
            visibility: editorAberto ? "visible" : "hidden",
            pointerEvents: editorAberto ? "auto" : "none",
            minHeight: editorAberto ? 400 : 0,
          }}
        />
      </>
    );
  },
);

MemedPrescricao.displayName = "MemedPrescricao";

export default MemedPrescricao;
