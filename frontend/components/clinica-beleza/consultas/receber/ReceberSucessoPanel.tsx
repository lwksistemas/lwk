"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, PenLine, X } from "lucide-react";
import { CLINICA_FORMA_PAGAMENTO_LABEL } from "@/lib/clinica-beleza-constants";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { formatApiErrorBody } from "@/lib/api-errors";
import { useToast } from "@/components/ui/Toast";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { valorPagamentoConsulta } from "@/hooks/clinica-beleza/consulta-detail-actions/consulta-detail-actions-utils";
import { consultaProcedimentoLabel, type Consulta } from "../consultas-types";
import {
  formatEntradasResumo,
  type EntradaPagamentoLinha,
} from "../modal-receber-consulta-utils";
import { ReceberReciboActions } from "./ReceberReciboActions";

function EnviarReciboAssinaturaAcao({ paymentId }: { paymentId: number }) {
  const toast = useToast();
  const [enviando, setEnviando] = useState<"email" | "whatsapp" | null>(null);
  const [assinado, setAssinado] = useState(false);

  // Consulta o status ao montar: se já assinado, oculta os botões de envio para assinatura.
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
          O cliente já recebeu o PDF assinado por e-mail e WhatsApp.
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
        Envie o recibo para o cliente assinar. Após assinar, ele recebe o PDF assinado por e-mail e WhatsApp.
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

interface ReceberSucessoPanelProps {
  consultaExibida: Consulta;
  consultaStatus: string;
  precisaComplementar: boolean;
  ehAPrazo?: boolean;
  saldoAposRecebimento: number;
  reciboSnapshot: {
    desconto: number;
    totalLiquido: number;
    entradas: EntradaPagamentoLinha[];
  } | null;
  error: string;
  loading: boolean;
  onClose: () => void;
  onComplementar: () => void;
  onEstornar: () => void;
  onImprimir: () => void;
  onEmail: () => void;
  onWhatsApp: () => void;
}

export function ReceberSucessoPanel({
  consultaExibida,
  consultaStatus,
  precisaComplementar,
  ehAPrazo = false,
  saldoAposRecebimento,
  reciboSnapshot,
  error,
  loading,
  onClose,
  onComplementar,
  onEstornar,
  onImprimir,
  onEmail,
  onWhatsApp,
}: ReceberSucessoPanelProps) {
  const snap = reciboSnapshot;
  const resumoFormas = snap
    ? formatEntradasResumo(snap.entradas, CLINICA_FORMA_PAGAMENTO_LABEL as Record<string, string>)
    : "";
  const valorTotalConsulta = valorPagamentoConsulta(consultaExibida);
  const consultaJaFinalizada = consultaStatus === "COMPLETED";
  // Complementar direto só antes de finalizar; depois, o saldo é recebido no Financeiro.
  const podeComplementarAqui = precisaComplementar && !consultaJaFinalizada;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-2xl">
        <div className="flex items-center justify-between p-4 border-b dark:border-neutral-700">
          <h2
            className={`text-lg font-bold ${
              precisaComplementar
                ? "text-orange-700 dark:text-orange-400"
                : ehAPrazo
                  ? "text-slate-700 dark:text-slate-300"
                  : "text-green-700 dark:text-green-400"
            }`}
          >
            {precisaComplementar
              ? "✓ Pagamento parcial registrado"
              : ehAPrazo
                ? "✓ Pagamento a prazo registrado"
                : "✓ Pagamento registrado"}
          </h2>
          <button type="button" onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg">
            <X size={18} />
          </button>
        </div>
        <div className="p-6 space-y-4">
          <div
            className={`text-sm space-y-1 rounded-lg p-4 ${
              precisaComplementar
                ? "bg-orange-50 dark:bg-orange-900/20"
                : ehAPrazo
                  ? "bg-slate-50 dark:bg-slate-800/40"
                  : "bg-green-50 dark:bg-green-900/20"
            }`}
          >
            <p>
              <strong>Paciente:</strong> {consultaExibida.patient_name}
            </p>
            {consultaProcedimentoLabel(consultaExibida) && (
              <p>
                <strong>Procedimento:</strong> {consultaProcedimentoLabel(consultaExibida)}
              </p>
            )}
            {valorTotalConsulta > 0 && (
              <p>
                <strong>Valor:</strong> {formatCurrency(valorTotalConsulta)}
              </p>
            )}
            {snap && snap.desconto > 0 && (
              <p>
                <strong>Desconto:</strong> {formatCurrency(snap.desconto)}
              </p>
            )}
            {Boolean(consultaExibida.retorno_gratuito) && snap && snap.desconto <= 0 && (
              <p>
                <strong>Desconto retorno:</strong> {formatCurrency(valorTotalConsulta)}
              </p>
            )}
            <p>
              <strong>Valor recebido nesta operação:</strong>{" "}
              {formatCurrency(snap?.totalLiquido ?? Number(consultaExibida.valor_pago ?? 0))}
            </p>
            {ehAPrazo && (
              <p className="font-semibold text-slate-800 dark:text-slate-200 pt-1">
                A prazo: {formatCurrency(Number(consultaExibida.valor_restante ?? 0))}
                {consultaExibida.payment_data_vencimento
                  ? ` — vencimento ${consultaExibida.payment_data_vencimento.split("-").reverse().join("/")}`
                  : ""}
              </p>
            )}
            {resumoFormas && (
              <p>
                <strong>Formas nesta operação:</strong> {resumoFormas}
              </p>
            )}
            {Number(consultaExibida.valor_pago ?? 0) > 0 && (
              <p>
                <strong>Total já pago:</strong> {formatCurrency(Number(consultaExibida.valor_pago))}
              </p>
            )}
            <p className="text-xs text-gray-500 dark:text-gray-400 pt-1">
              O recibo impresso/WhatsApp/e-mail lista todas as formas e o total já pago.
            </p>              {precisaComplementar && (
              <p className="font-semibold text-orange-800 dark:text-orange-300 pt-1">
                Saldo em aberto: {formatCurrency(saldoAposRecebimento)}
                {consultaJaFinalizada
                  ? " — receba o saldo na página Financeiro."
                  : " — inclua outras formas para complementar."}
              </p>
            )}
          </div>

          {podeComplementarAqui && (
            <button
              type="button"
              onClick={onComplementar}
              className="w-full py-2.5 rounded-lg text-white text-sm font-medium"
              style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
            >
              Complementar saldo (várias formas)
            </button>
          )}

          {consultaJaFinalizada ? (
            <>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Envie o recibo de pagamento para o cliente:
              </p>
              <ReceberReciboActions
                onImprimir={onImprimir}
                onEmail={onEmail}
                onWhatsApp={onWhatsApp}
              />
              {ehAPrazo && consultaExibida.payment_id ? (
                <EnviarReciboAssinaturaAcao paymentId={consultaExibida.payment_id} />
              ) : null}
            </>
          ) : (
            <p className="text-sm text-gray-600 dark:text-gray-400 rounded-lg border border-gray-200 dark:border-neutral-600 p-3">
              Pagamento registrado. O comprovante fica disponível para impressão/envio
              após <strong>finalizar a consulta</strong>.
            </p>
          )}

          {error && (
            <div className="p-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
              {error}
            </div>
          )}

          <div className="flex justify-between items-center pt-2 gap-2">
            {consultaStatus !== "COMPLETED" && (
              <button
                type="button"
                onClick={onEstornar}
                disabled={loading}
                className="px-4 py-2 rounded-lg border border-red-300 text-red-600 hover:bg-red-50 text-sm disabled:opacity-50"
              >
                {loading ? "Corrigindo..." : "Corrigir pagamento"}
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-white ml-auto"
              style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
            >
              Fechar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
