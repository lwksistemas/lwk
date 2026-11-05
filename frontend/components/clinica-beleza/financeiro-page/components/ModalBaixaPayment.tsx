"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";
import { CLINICA_FORMA_PAGAMENTO_A_VISTA, CLINICA_FORMA_PAGAMENTO_LABEL } from "@/lib/clinica-beleza-constants";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import {
  novaLinhaEntrada,
  parseMoneyInput,
  round2,
  somaEntradas,
  valoresQuaseIguais,
  type EntradaPagamentoLinha,
} from "@/components/clinica-beleza/consultas/modal-receber-consulta-utils";
import { ReceberFormasPagamento } from "@/components/clinica-beleza/consultas/receber/ReceberFormasPagamento";
import type { FinanceiroPayment } from "../types";
import { validarBaixaFormas } from "./modal-baixa-payment-utils";

const FORMAS_BAIXA = CLINICA_FORMA_PAGAMENTO_A_VISTA.map(
  (codigo) => [codigo, CLINICA_FORMA_PAGAMENTO_LABEL[codigo]] as const,
);

interface Parcela {
  id: number;
  valor: string | number;
  payment_method: string;
  payment_method_label?: string;
  payment_date: string;
  status?: string;
  observacoes?: string;
  created_at: string;
}

interface ParcelasData {
  valor_total: number;
  valor_pago: number;
  saldo_devedor: number;
  desconto?: number;
  status: string;
  parcelas: Parcela[];
}

interface ModalBaixaPaymentProps {
  payment: FinanceiroPayment | null;
  onClose: () => void;
  onSuccess: () => void;
}

const fieldClass = "w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600";

export function ModalBaixaPayment({ payment, onClose, onSuccess }: ModalBaixaPaymentProps) {
  const [parcelasData, setParcelasData] = useState<ParcelasData | null>(null);
  const [loadingParcelas, setLoadingParcelas] = useState(false);
  const [desconto, setDesconto] = useState("");
  const [entradas, setEntradas] = useState<EntradaPagamentoLinha[]>([novaLinhaEntrada("CASH")]);
  const [quitar, setQuitar] = useState(true);
  const [paymentDate, setPaymentDate] = useState(new Date().toISOString().slice(0, 10));
  const [observacoes, setObservacoes] = useState("");
  const [saving, setSaving] = useState(false);
  const [removendoId, setRemovendoId] = useState<number | null>(null);
  const [error, setError] = useState("");

  const carregarParcelas = useCallback(async (id: number) => {
    setLoadingParcelas(true);
    try {
      const data = await ClinicaBelezaAPI.financeiro.payments.parcelas.list(id) as ParcelasData;
      setParcelasData(data);
    } catch {
      setParcelasData(null);
    } finally {
      setLoadingParcelas(false);
    }
  }, []);

  useEffect(() => {
    if (!payment) return;
    setDesconto("");
    setEntradas([novaLinhaEntrada("CASH")]);
    setQuitar(true);
    setPaymentDate(new Date().toISOString().slice(0, 10));
    setObservacoes("");
    setRemovendoId(null);
    setError("");
    setParcelasData(null);
    void carregarParcelas(payment.id);
  }, [payment, carregarParcelas]);

  const valorTotal = parcelasData?.valor_total ?? Number(payment?.valor_total_efetivo || payment?.valor_total || 0);
  const saldoDevedor = parcelasData?.saldo_devedor ?? Number(payment?.saldo_devedor ?? valorTotal);
  const valorPago = parcelasData?.valor_pago ?? 0;
  const parcelas = (parcelasData?.parcelas ?? []).filter((p) => p.status !== "CANCELLED");
  const valorDesconto = parseMoneyInput(desconto);
  const totalLiquido = round2(Math.max(0, saldoDevedor - valorDesconto));
  const descontoIntegral = totalLiquido <= 0.009 && valorDesconto > 0.009;
  const distribuido = useMemo(() => somaEntradas(entradas), [entradas]);
  const somaOk = descontoIntegral || (valoresQuaseIguais(distribuido, totalLiquido) && totalLiquido > 0);

  useEffect(() => {
    if (saldoDevedor <= 0) return;
    if (entradas.length !== 1) return;
    const atual = parseMoneyInput(entradas[0]?.valor);
    if (!valoresQuaseIguais(atual, totalLiquido)) {
      setEntradas((prev) =>
        prev.length === 1 ? [{ ...prev[0], valor: totalLiquido > 0 ? String(totalLiquido) : "" }] : prev,
      );
    }
    // A linha única acompanha o total. Com duas formas, o valor digitado permanece.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [totalLiquido, saldoDevedor]);

  useEffect(() => {
    if (saldoDevedor <= 0) return;
    if (descontoIntegral) {
      setQuitar(true);
      return;
    }
    setQuitar(valoresQuaseIguais(distribuido, totalLiquido) && totalLiquido > 0);
  }, [descontoIntegral, distribuido, totalLiquido, saldoDevedor]);

  if (!payment) return null;

  const updateEntrada = (id: string, patch: Partial<EntradaPagamentoLinha>) => {
    setEntradas((prev) => prev.map((linha) => (linha.id === id ? { ...linha, ...patch } : linha)));
  };

  const addEntrada = () => {
    const resto = Math.max(0, round2(totalLiquido - distribuido));
    setEntradas((prev) => [...prev, novaLinhaEntrada("PIX", resto > 0 ? resto : "")]);
  };

  const removeEntrada = (id: string) => {
    setEntradas((prev) => (prev.length <= 1 ? prev : prev.filter((linha) => linha.id !== id)));
  };

  const mensagemErro = (err: unknown) => {
    if (err && typeof err === "object" && "error" in err) return String((err as { error: unknown }).error);
    return "Erro ao registrar pagamento. Tente novamente.";
  };

  const handleConfirm = async () => {
    const validacao = validarBaixaFormas({
      saldoDevedor,
      desconto: valorDesconto,
      entradas: descontoIntegral ? [] : entradas,
      quitar,
    });
    if (validacao) {
      setError(validacao);
      return;
    }
    const linhas = descontoIntegral ? [] : entradas.filter((linha) => parseMoneyInput(linha.valor) > 0.009);
    const quita = descontoIntegral || valoresQuaseIguais(somaEntradas(linhas), totalLiquido);
    setSaving(true);
    setError("");
    let gravadas = 0;
    try {
      if (linhas.length === 0) {
        await ClinicaBelezaAPI.financeiro.payments.parcelas.add(payment.id, {
          valor: 0,
          payment_method: "CASH",
          payment_date: paymentDate,
          observacoes,
          desconto: valorDesconto,
        });
        gravadas = 1;
      }
      for (let i = 0; i < linhas.length; i += 1) {
        const linha = linhas[i];
        const notaCartao = linha.payment_method === "CREDIT_CARD" && Number(linha.parcelas) > 1
          ? `Cartão ${linha.parcelas}x`
          : "";
        const nota = [observacoes.trim(), notaCartao].filter(Boolean).join(" · ");
        await ClinicaBelezaAPI.financeiro.payments.parcelas.add(payment.id, {
          valor: round2(parseMoneyInput(linha.valor)),
          payment_method: linha.payment_method,
          payment_date: paymentDate,
          observacoes: nota,
          desconto: i === 0 && valorDesconto > 0 ? valorDesconto : undefined,
        });
        gravadas += 1;
      }
      onSuccess();
      if (quita) {
        onClose();
        return;
      }
      await carregarParcelas(payment.id);
      setDesconto("");
      setObservacoes("");
      setEntradas([novaLinhaEntrada("CASH")]);
    } catch (err) {
      if (gravadas > 0) {
        onSuccess();
        await carregarParcelas(payment.id);
        setDesconto("");
        setEntradas([novaLinhaEntrada("CASH")]);
      }
      setError(mensagemErro(err));
    } finally {
      setSaving(false);
    }
  };

  const handleRemoverParcela = async (parcela: Parcela) => {
    const valorTexto = formatCurrency(Number(parcela.valor));
    const quando = new Date(parcela.payment_date + "T12:00:00").toLocaleDateString("pt-BR");
    const confirmar = window.confirm(
      `Remover ${valorTexto} de ${quando} do histórico? O saldo será recalculado.`,
    );
    if (!confirmar) return;
    setRemovendoId(parcela.id);
    setError("");
    try {
      await ClinicaBelezaAPI.financeiro.payments.parcelas.remove(payment.id, parcela.id);
      onSuccess();
      await carregarParcelas(payment.id);
      setEntradas([novaLinhaEntrada("CASH")]);
    } catch (err) {
      setError(mensagemErro(err) || "Não foi possível remover este lançamento.");
    } finally {
      setRemovendoId(null);
    }
  };

  const aberto = saldoDevedor > 0.009;

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b dark:border-neutral-700">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Receber pagamento</h2>
          <button type="button" onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg" aria-label="Fechar">
            <X size={18} />
          </button>
        </div>
        <div className="p-5 space-y-4">
          {loadingParcelas && !parcelasData && (
            <p className="text-sm text-gray-500">Carregando...</p>
          )}
          {!aberto ? (
            <p className="text-sm font-medium text-green-700 dark:text-green-400">Este atendimento já está quitado.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2 text-sm">
                <p className="text-gray-500 dark:text-gray-400 text-xs uppercase font-semibold">Dados do atendimento</p>
                <p><strong>Paciente:</strong> {payment.paciente_nome || "—"}</p>
                {payment.procedimento_nome && (
                  <p><strong>Procedimento:</strong> {payment.procedimento_nome}</p>
                )}
                <p className="font-semibold text-gray-800 dark:text-gray-200 pt-1 border-t dark:border-neutral-600">
                  Total: {formatCurrency(valorTotal)}
                </p>
                {valorPago > 0.009 && (
                  <p className="text-orange-600 dark:text-orange-400 font-medium">
                    Já pago: {formatCurrency(valorPago)} · Saldo: {formatCurrency(saldoDevedor)}
                  </p>
                )}
                <div className="pt-3">
                  <label className="block text-sm font-medium mb-1" htmlFor="baixa-desconto">Desconto (R$)</label>
                  <input
                    id="baixa-desconto"
                    type="number"
                    step="0.01"
                    min="0"
                    value={desconto}
                    onChange={(e) => setDesconto(e.target.value)}
                    className={fieldClass}
                    placeholder="0,00"
                  />
                </div>
                <p className="text-base font-bold text-[#8B4557] dark:text-rose-300 pt-1">
                  Total a receber: {formatCurrency(totalLiquido)}
                </p>
              </div>
              {descontoIntegral ? (
                <p className="text-sm text-gray-600 dark:text-gray-300 rounded-lg border border-gray-200 dark:border-neutral-600 p-3">
                  Desconto integral. Nada a receber — confirme para quitar o atendimento.
                </p>
              ) : (
                <ReceberFormasPagamento
                  entradas={entradas}
                  distribuido={distribuido}
                  totalLiquido={totalLiquido}
                  somaOk={somaOk}
                  formas={FORMAS_BAIXA}
                  onAdd={addEntrada}
                  onRemove={removeEntrada}
                  onUpdate={updateEntrada}
                />
              )}
            </div>
          )}

          {aberto && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1" htmlFor="baixa-data">Data do pagamento</label>
                <input id="baixa-data" type="date" value={paymentDate} onChange={(e) => setPaymentDate(e.target.value)} className={fieldClass} />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1" htmlFor="baixa-obs">
                  Observações <span className="text-gray-400 font-normal">(opcional)</span>
                </label>
                <input
                  id="baixa-obs"
                  type="text"
                  value={observacoes}
                  onChange={(e) => setObservacoes(e.target.value)}
                  placeholder="Ex: família/funcionário, 1ª parcela..."
                  className={fieldClass}
                />
              </div>
            </div>
          )}

          {parcelas.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">Histórico de pagamentos</p>
              <div className="space-y-1 max-h-40 overflow-y-auto">
                {parcelas.map((p) => (
                  <div key={p.id} className="flex justify-between items-center text-sm bg-gray-50 dark:bg-neutral-700/50 rounded-lg px-3 py-2 gap-2">
                    <div className="min-w-0">
                      <span className="font-medium">{formatCurrency(Number(p.valor))}</span>
                      <span className="text-gray-500 dark:text-gray-400 ml-2 text-xs">
                        {p.payment_method_label || CLINICA_FORMA_PAGAMENTO_LABEL[p.payment_method] || p.payment_method}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(p.payment_date + "T12:00:00").toLocaleDateString("pt-BR")}
                      </span>
                      <button
                        type="button"
                        onClick={() => void handleRemoverParcela(p)}
                        disabled={removendoId !== null}
                        className="text-xs font-medium text-red-700 dark:text-red-300 hover:underline disabled:opacity-50"
                      >
                        {removendoId === p.id ? "Removendo..." : "Remover"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {error && (
            <div className="p-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
              {error}
            </div>
          )}

          {aberto && (
            <label className="flex items-center gap-2 text-sm pt-1">
              <input
                type="checkbox"
                checked={quitar || descontoIntegral}
                disabled={descontoIntegral}
                onChange={(e) => setQuitar(e.target.checked)}
              />
              Quitar pagamento completo
            </label>
          )}

          <div className="flex gap-2 pt-2 border-t dark:border-neutral-700">
            <button type="button" onClick={onClose} className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600">
              {aberto ? "Cancelar" : "Fechar"}
            </button>
            {aberto && (
              <button
                type="button"
                onClick={() => void handleConfirm()}
                disabled={saving}
                className="flex-1 py-2 rounded-lg text-white disabled:opacity-50"
                style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
              >
                {saving ? "Registrando..." : "Confirmar"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
