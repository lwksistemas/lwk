"use client";

import { useEffect, useState } from "react";
import { X, Printer, Mail, MessageCircle } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { CLINICA_FORMA_PAGAMENTO_LABEL } from "@/lib/clinica-beleza-constants";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { formatApiErrorBody } from "@/lib/api-errors";
import { formatCurrency } from "@/lib/financeiro-helpers";
import {
  saldoReceberConsulta,
  valorPagamentoConsulta,
} from "@/hooks/clinica-beleza/consulta-detail-actions/consulta-detail-actions-utils";
import { consultaProcedimentosNomes, type Consulta } from "./consultas-types";

interface ModalReceberConsultaProps {
  open: boolean;
  consulta: Consulta;
  onClose: () => void;
  onSuccess: (consulta: Consulta) => void;
}

export function ModalReceberConsulta({
  open,
  consulta,
  onClose,
  onSuccess,
}: ModalReceberConsultaProps) {
  const saldo = saldoReceberConsulta(consulta);
  const total = valorPagamentoConsulta(consulta);
  const valorConsulta = Number(consulta.valor_consulta ?? 0);
  const valorProcedimentos = Number(consulta.valor_procedimentos ?? 0);
  const [paymentMethod, setPaymentMethod] = useState("CASH");
  const [markAsPaid, setMarkAsPaid] = useState(true);
  const [amount, setAmount] = useState(String(saldo || total || ""));
  const [desconto, setDesconto] = useState("");
  const [parcelas, setParcelas] = useState("1");
  const [valorParcela, setValorParcela] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [confirmado, setConfirmado] = useState(false);
  const [consultaAtualizada, setConsultaAtualizada] = useState<Consulta | null>(null);

  // Reset apenas quando o modal abre (open muda de false para true)
  // NÃO resetar quando consulta muda (senão destrói a tela de recibo após onSuccess)
  const [prevOpen, setPrevOpen] = useState(false);
  useEffect(() => {
    if (open && !prevOpen) {
      // Modal acabou de abrir — resetar tudo
      const novoSaldo = saldoReceberConsulta(consulta);
      const novoTotal = valorPagamentoConsulta(consulta);
      setAmount(String(novoSaldo || novoTotal || ""));
      setDesconto("");
      setParcelas("1");
      setValorParcela("");
      setMarkAsPaid(true);
      setPaymentMethod("CASH");
      setError("");
      setConsultaAtualizada(null);
      // Se já está PAGO, abrir direto na tela de recibo (reimprimir/reenviar)
      if (consulta.payment_status === "PAID") {
        setConfirmado(true);
        setConsultaAtualizada(consulta);
      } else {
        setConfirmado(false);
      }
    }
    setPrevOpen(open);
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!open) return null;

  const valorBase = Number(amount) || 0;
  const valorDesconto = Number(desconto) || 0;
  const valorFinal = Math.max(0, valorBase - valorDesconto);
  const saldoAtual = saldoReceberConsulta(consulta);
  const numParcelas = Number(parcelas) || 1;

  const handleConfirm = async () => {
    if (valorFinal <= 0) {
      setError("Informe um valor maior que zero.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await ClinicaBelezaAPI.consultas.receber(consulta.id, {
        payment_method: paymentMethod,
        mark_as_paid: markAsPaid && valorFinal >= saldoAtual,
        amount: String(valorFinal),
        parcelas: paymentMethod === "CREDIT_CARD" ? numParcelas : 1,
        valor_parcela: paymentMethod === "CREDIT_CARD" && valorParcela ? valorParcela : undefined,
      });
      const atualizada = (data as { consulta?: Consulta }).consulta;
      if (!atualizada) throw new Error("Resposta inválida ao registrar recebimento.");
      setConsultaAtualizada(atualizada);
      setConfirmado(true);
      onSuccess(atualizada);
    } catch (e: unknown) {
      setError(formatApiErrorBody(e) || "Erro ao registrar recebimento.");
    } finally {
      setLoading(false);
    }
  };

  const handleEstornar = async () => {
    if (!confirm("Tem certeza que deseja estornar o pagamento? O valor voltará para pendente.")) return;
    setLoading(true);
    setError("");
    try {
      if (!consulta.payment_id) {
        setError("Pagamento não encontrado.");
        return;
      }
      await ClinicaBelezaAPI.put(`/payments/${consulta.payment_id}/`, {
        status: "PENDING",
        amount: "0",
      });
      // Recarregar consulta
      const res = await ClinicaBelezaAPI.get(`/consultas/${consulta.id}/`);
      const atualizada = res as Consulta;
      if (atualizada) {
        onSuccess(atualizada);
        onClose();
      }
    } catch (e: unknown) {
      setError(formatApiErrorBody(e) || "Erro ao estornar pagamento.");
    } finally {
      setLoading(false);
    }
  };

  const handleImprimir = () => {
    const w = window.open("", "_blank", "width=400,height=600");
    if (!w) return;
    const c = consultaAtualizada || consulta;
    const html = gerarHtmlRecibo(c, valorFinal, paymentMethod, numParcelas, valorParcela);
    w.document.write(html);
    w.document.close();
    w.print();
  };

  const handleEnviarEmail = () => {
    const c = consultaAtualizada || consulta;
    if (c.payment_id) {
      ClinicaBelezaAPI.payments.enviarRecibo(c.payment_id, "email").catch(() => {});
    }
  };

  const handleEnviarWhatsApp = () => {
    const c = consultaAtualizada || consulta;
    if (c.payment_id) {
      ClinicaBelezaAPI.payments.enviarRecibo(c.payment_id, "whatsapp").catch(() => {});
    }
  };

  // Tela pós-confirmação: opções de recibo
  if (confirmado) {
    return (
      <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4">
        <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-2xl">
          <div className="flex items-center justify-between p-4 border-b dark:border-neutral-700">
            <h2 className="text-lg font-bold text-green-700 dark:text-green-400">
              ✓ Pagamento registrado
            </h2>
            <button type="button" onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg">
              <X size={18} />
            </button>
          </div>
          <div className="p-6 space-y-4">
            <div className="text-sm space-y-1 bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
              <p><strong>Paciente:</strong> {consulta.patient_name}</p>
              <p><strong>Procedimento:</strong> {consultaProcedimentosNomes(consulta)}</p>
              <p><strong>Valor recebido:</strong> {formatCurrency(valorFinal)}</p>
              <p><strong>Forma:</strong> {CLINICA_FORMA_PAGAMENTO_LABEL[paymentMethod as keyof typeof CLINICA_FORMA_PAGAMENTO_LABEL] || paymentMethod}</p>
              {paymentMethod === "CREDIT_CARD" && numParcelas > 1 && (
                <p><strong>Parcelas:</strong> {numParcelas}x de R$ {valorParcela || (valorFinal / numParcelas).toFixed(2)}</p>
              )}
            </div>

            <p className="text-sm text-gray-600 dark:text-gray-400">
              Envie o recibo de pagamento para o cliente:
            </p>

            <div className="grid grid-cols-3 gap-3">
              <button type="button" onClick={handleImprimir}
                className="flex flex-col items-center gap-2 p-4 rounded-xl border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors">
                <Printer size={24} className="text-gray-700 dark:text-gray-300" />
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">Imprimir</span>
              </button>
              <button type="button" onClick={handleEnviarEmail}
                className="flex flex-col items-center gap-2 p-4 rounded-xl border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors">
                <Mail size={24} className="text-gray-700 dark:text-gray-300" />
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">Email</span>
              </button>
              <button type="button" onClick={handleEnviarWhatsApp}
                className="flex flex-col items-center gap-2 p-4 rounded-xl border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors">
                <MessageCircle size={24} className="text-gray-700 dark:text-gray-300" />
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">WhatsApp</span>
              </button>
            </div>

            <div className="flex justify-end pt-2">
              <button type="button" onClick={onClose}
                className="px-4 py-2 rounded-lg text-white"
                style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}>
                Fechar
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Formulário principal — layout paisagem (largo)
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b dark:border-neutral-700">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Receber pagamento</h2>
          <button type="button" onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg">
            <X size={18} />
          </button>
        </div>
        <div className="p-5 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Coluna esquerda: info do paciente */}
            <div className="space-y-2 text-sm">
              <p className="text-gray-500 dark:text-gray-400 text-xs uppercase font-semibold">Dados do atendimento</p>
              <p><strong>Paciente:</strong> {consulta.patient_name}</p>
              <p><strong>Procedimento:</strong> {consultaProcedimentosNomes(consulta)}</p>
              <p><strong>Valor da consulta:</strong> {formatCurrency(valorConsulta)}</p>
              <p><strong>Valor procedimento:</strong> {formatCurrency(valorProcedimentos)}</p>
              <p className="font-semibold text-gray-800 dark:text-gray-200 pt-1 border-t dark:border-neutral-600">
                Total: {formatCurrency(total)}
              </p>
              {Number(consulta.valor_pago ?? 0) > 0 && (
                <p className="text-orange-600 dark:text-orange-400 font-medium">
                  Saldo em aberto: {formatCurrency(saldoAtual)}
                </p>
              )}
            </div>

            {/* Coluna direita: campos de pagamento */}
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-1">Valor a receber (R$)</label>
                <input type="number" step="0.01" min="0" value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Desconto (R$)</label>
                <input type="number" step="0.01" min="0" value={desconto}
                  onChange={(e) => setDesconto(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                  placeholder="0,00" />
              </div>
              {valorDesconto > 0 && (
                <p className="text-sm font-semibold text-green-700 dark:text-green-400">
                  Valor final: {formatCurrency(valorFinal)}
                </p>
              )}
              <div>
                <label className="block text-sm font-medium mb-1">Forma de pagamento</label>
                <select value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600">
                  {Object.entries(CLINICA_FORMA_PAGAMENTO_LABEL).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>

              {paymentMethod === "CREDIT_CARD" && (
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-sm font-medium mb-1">Parcelas</label>
                    <select value={parcelas} onChange={(e) => setParcelas(e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600">
                      {Array.from({ length: 12 }, (_, i) => i + 1).map((n) => (
                        <option key={n} value={String(n)}>{n}x</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Valor parcela (R$)</label>
                    <input type="number" step="0.01" min="0"
                      value={valorParcela}
                      onChange={(e) => setValorParcela(e.target.value)}
                      placeholder={(valorFinal / numParcelas).toFixed(2)}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600" />
                    <p className="text-xs text-gray-500 mt-0.5">Com taxa do cartão</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {error && (
            <div className="p-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
              {error}
            </div>
          )}

          <label className="flex items-center gap-2 text-sm pt-1">
            <input type="checkbox" checked={markAsPaid}
              onChange={(e) => setMarkAsPaid(e.target.checked)} />
            Quitar pagamento completo
          </label>

          {/* Estornar pagamento — só em consulta NÃO finalizada com valor já pago */}
          {Number(consulta.valor_pago ?? 0) > 0 && consulta.status !== "COMPLETED" && (
            <button type="button" onClick={handleEstornar} disabled={loading}
              className="w-full py-2 text-sm rounded-lg border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20">
              Estornar pagamento (corrigir lançamento)
            </button>
          )}

          <div className="flex gap-2 pt-2 border-t dark:border-neutral-700">
            <button type="button" onClick={onClose}
              className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600">
              Cancelar
            </button>
            <button type="button" onClick={handleConfirm} disabled={loading}
              className="flex-1 py-2 rounded-lg text-white disabled:opacity-50"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}>
              {loading ? "Registrando..." : "Confirmar"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}


function gerarHtmlRecibo(
  consulta: Consulta,
  valor: number,
  metodo: string,
  parcelas: number,
  valorParcela: string,
): string {
  const metodoLabel = CLINICA_FORMA_PAGAMENTO_LABEL[metodo as keyof typeof CLINICA_FORMA_PAGAMENTO_LABEL] || metodo;
  const dataHora = new Date().toLocaleString("pt-BR");
  const parcelasInfo = metodo === "CREDIT_CARD" && parcelas > 1
    ? `<p><strong>Parcelas:</strong> ${parcelas}x de R$ ${valorParcela || (valor / parcelas).toFixed(2)}</p>`
    : "";

  return `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>Recibo de Pagamento</title>
<style>
  body { font-family: Arial, sans-serif; max-width: 350px; margin: 0 auto; padding: 20px; font-size: 13px; }
  h1 { text-align: center; font-size: 16px; border-bottom: 2px solid #333; padding-bottom: 8px; }
  .info { margin: 12px 0; }
  .info p { margin: 4px 0; }
  .total { font-size: 16px; font-weight: bold; border-top: 1px dashed #999; padding-top: 10px; margin-top: 12px; }
  .footer { text-align: center; margin-top: 20px; font-size: 11px; color: #666; border-top: 1px dashed #999; padding-top: 10px; }
  @media print { body { margin: 0; } }
</style>
</head><body>
<h1>RECIBO DE PAGAMENTO</h1>
<div class="info">
  <p><strong>Data:</strong> ${dataHora}</p>
  <p><strong>Paciente:</strong> ${consulta.patient_name}</p>
  <p><strong>Procedimento:</strong> ${consultaProcedimentosNomes(consulta)}</p>
</div>
<div class="info">
  <p><strong>Forma de pagamento:</strong> ${metodoLabel}</p>
  ${parcelasInfo}
</div>
<p class="total">Valor recebido: R$ ${valor.toFixed(2)}</p>
<div class="footer">
  <p>Documento gerado automaticamente pelo sistema.</p>
</div>
</body></html>`;
}
