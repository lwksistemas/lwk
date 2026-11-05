"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, PenLine } from "lucide-react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { formatApiErrorBody } from "@/lib/api-errors";
import { useToast } from "@/components/ui/Toast";

export function EnviarReciboAssinaturaAcao({ paymentId }: { paymentId: number }) {
  const toast = useToast();
  const [enviando, setEnviando] = useState<"email" | "whatsapp" | null>(null);
  const [assinado, setAssinado] = useState(false);

  useEffect(() => {
    let ativo = true;
    ClinicaBelezaAPI.payments
      .assinaturaReciboStatus(paymentId)
      .then((r) => {
        if (ativo) setAssinado(r?.status_assinatura === "concluido");
      })
      .catch(() => {
        /* silencioso: mantém os botões disponíveis */
      });
    return () => {
      ativo = false;
    };
  }, [paymentId]);

  const enviar = async (canal: "email" | "whatsapp") => {
    setEnviando(canal);
    try {
      await ClinicaBelezaAPI.payments.enviarReciboParaAssinatura(paymentId, canal);
      toast.success(
        canal === "email"
          ? "Recibo enviado para assinatura por e-mail."
          : "Recibo enviado para assinatura por WhatsApp.",
      );
    } catch (e: unknown) {
      toast.error(formatApiErrorBody(e) || "Erro ao enviar recibo para assinatura.");
    } finally {
      setEnviando(null);
    }
  };

  if (assinado) {
    return (
      <div className="rounded-lg border border-green-200 dark:border-green-800 bg-green-50/70 dark:bg-green-950/30 p-3">
        <p className="text-sm font-medium text-green-800 dark:text-green-300 flex items-center gap-1.5">
          <CheckCircle2 size={15} /> Recibo assinado digitalmente pelo cliente
        </p>
        <p className="text-xs text-green-700/80 dark:text-green-300/80 mt-0.5">
          O cliente já recebeu a foto do recibo assinado por e-mail e WhatsApp.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-purple-200 dark:border-purple-800 bg-purple-50/70 dark:bg-purple-950/30 p-3">
      <p className="text-sm font-medium text-purple-900 dark:text-purple-200 flex items-center gap-1.5">
        <PenLine size={15} /> Assinatura digital do recibo
      </p>
      <p className="text-xs text-purple-800/80 dark:text-purple-300/80 mt-0.5 mb-2">
        Envie o recibo para o cliente assinar. Após assinar, ele recebe só a foto do recibo por e-mail e WhatsApp.
      </p>
      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => void enviar("email")}
          disabled={enviando !== null}
          className="py-2 rounded-lg text-sm font-medium bg-white dark:bg-neutral-800 border border-purple-300 dark:border-purple-700 text-purple-700 dark:text-purple-300 hover:bg-purple-100 dark:hover:bg-purple-900/40 disabled:opacity-50"
        >
          {enviando === "email" ? "Enviando…" : "Assinar por e-mail"}
        </button>
        <button
          type="button"
          onClick={() => void enviar("whatsapp")}
          disabled={enviando !== null}
          className="py-2 rounded-lg text-sm font-medium bg-white dark:bg-neutral-800 border border-purple-300 dark:border-purple-700 text-purple-700 dark:text-purple-300 hover:bg-purple-100 dark:hover:bg-purple-900/40 disabled:opacity-50"
        >
          {enviando === "whatsapp" ? "Enviando…" : "Assinar por WhatsApp"}
        </button>
      </div>
    </div>
  );
}
