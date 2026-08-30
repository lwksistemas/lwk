"use client";

/**
 * Integração Memed — prescrição digital (Receituário e Exames).
 * Só a barra Fechar é do React. O iframe fica no overlay da Memed
 * (memed-auto-generated): um host no JSX causa o erro #418 e tela branca.
 */

import { forwardRef, useCallback, useEffect, useImperativeHandle, useState } from "react";
import { createPortal, flushSync } from "react-dom";
import { X } from "lucide-react";
import { useMemedPrescricao } from "./memed/useMemedPrescricao";

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
    const [montado, setMontado] = useState(false);
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
      setMontado(true);
    }, []);

    useEffect(() => {
      if (!aberto) return;
      const onKey = (event: KeyboardEvent) => {
        if (event.key === "Escape") fechar();
      };
      window.addEventListener("keydown", onKey, true);
      // V4: o widget gerencia o próprio overlay/iframe — marcar como pronto após curto delay
      const timer = window.setTimeout(() => {
        if (status === "loading") setStatus("ready");
      }, 2000);
      return () => {
        window.removeEventListener("keydown", onKey, true);
        window.clearTimeout(timer);
      };
    }, [aberto, fechar, status]);

    const ui = (
      <div
        className="fixed inset-x-0 top-0 flex items-center justify-between gap-3 border-b border-gray-200 bg-white px-4 py-3 shadow-md dark:border-neutral-700 dark:bg-neutral-900"
        style={{
          zIndex: aberto ? 10000 : -1,
          visibility: aberto ? "visible" : "hidden",
          pointerEvents: aberto ? "auto" : "none",
        }}
        role="dialog"
        aria-modal={aberto}
        aria-hidden={!aberto}
        aria-label="Prescrição Memed"
      >
        <div>
          <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">Prescrição Memed</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">{patientName}</p>
          {status === "loading" && (
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">Carregando o editor da Memed…</p>
          )}
          {status === "error" && erro && (
            <p className="mt-0.5 text-xs text-red-700 dark:text-red-400">{erro}</p>
          )}
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
    );

    if (!montado) return null;
    return createPortal(ui, document.body);
  },
);

MemedPrescricao.displayName = "MemedPrescricao";

export default MemedPrescricao;
