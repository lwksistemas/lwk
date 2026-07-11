"use client";

import { useEffect, useMemo, useState } from "react";
import { Plus, Trash2, X, Printer, Mail, MessageCircle } from "lucide-react";
import { useToast } from "@/components/ui/Toast";
import { CLINICA_FORMA_PAGAMENTO_LABEL } from "@/lib/clinica-beleza-constants";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { formatApiErrorBody } from "@/lib/api-errors";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { formatCep, formatCpfCnpj, formatTelefone } from "@/lib/format-br";
import {
  saldoReceberConsulta,
  valorPagamentoConsulta,
} from "@/hooks/clinica-beleza/consulta-detail-actions/consulta-detail-actions-utils";
import { consultaProcedimentosNomes, type Consulta } from "./consultas-types";
import {
  buildReceberPayload,
  calcularTotalLiquido,
  formatEntradasResumo,
  novaLinhaEntrada,
  parseMoneyInput,
  somaEntradas,
  validateReceberForm,
  valoresQuaseIguais,
  type EntradaPagamentoLinha,
} from "./modal-receber-consulta-utils";

function labelDocumentoLoja(cpfCnpj?: string): string {
  const d = (cpfCnpj || "").replace(/\D/g, "");
  if (d.length === 11) return "CPF";
  if (d.length === 14) return "CNPJ";
  return "CPF/CNPJ";
}

function linhaTelCep(telefone?: string, cep?: string): string {
  const partes: string[] = [];
  const tel = formatTelefone(telefone || "");
  const cepFmt = formatCep(cep || "");
  if (tel) partes.push(`Tel: ${tel}`);
  if (cepFmt) partes.push(`CEP ${cepFmt}`);
  return partes.join("  ·  ");
}

interface ModalReceberConsultaProps {
  open: boolean;
  consulta: Consulta;
  onClose: () => void;
  onSuccess: (consulta: Consulta) => void;
}

const fieldClass =
  "w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600";

export function ModalReceberConsulta({
  open,
  consulta,
  onClose,
  onSuccess,
}: ModalReceberConsultaProps) {
  const toast = useToast();
  const total = valorPagamentoConsulta(consulta);
  const valorConsulta = Number(consulta.valor_consulta ?? 0);
  const valorProcedimentos = Number(consulta.valor_procedimentos ?? 0);
  const saldoAtual = saldoReceberConsulta(consulta);
  const baseReceber = saldoAtual > 0 ? saldoAtual : total;

  const [desconto, setDesconto] = useState("");
  const [entradas, setEntradas] = useState<EntradaPagamentoLinha[]>([novaLinhaEntrada("CASH")]);
  const [markAsPaid, setMarkAsPaid] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [confirmado, setConfirmado] = useState(false);
  const [consultaAtualizada, setConsultaAtualizada] = useState<Consulta | null>(null);
  const [reciboSnapshot, setReciboSnapshot] = useState<{
    desconto: number;
    totalLiquido: number;
    entradas: EntradaPagamentoLinha[];
  } | null>(null);

  const [prevOpen, setPrevOpen] = useState(false);

  const reiniciarFormularioComplemento = (c: Consulta) => {
    const novoSaldo = saldoReceberConsulta(c);
    const novoTotal = valorPagamentoConsulta(c);
    const base = novoSaldo > 0 ? novoSaldo : novoTotal;
    setDesconto("");
    setEntradas([novaLinhaEntrada("CASH", base)]);
    setMarkAsPaid(true);
    setError("");
    setConsultaAtualizada(null);
    setReciboSnapshot(null);
    setConfirmado(false);
  };

  useEffect(() => {
    if (open && !prevOpen) {
      const novoSaldo = saldoReceberConsulta(consulta);
      const quitado = novoSaldo <= 0 && consulta.payment_status === "PAID";
      if (quitado) {
        setConfirmado(true);
        setConsultaAtualizada(consulta);
        setReciboSnapshot(null);
        setError("");
      } else {
        reiniciarFormularioComplemento(consulta);
      }
    }
    setPrevOpen(open);
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  // Se a consulta ganhou saldo (ex.: procedimento extra) com o modal ainda aberto no recibo.
  useEffect(() => {
    if (!open || !confirmado) return;
    const c = consultaAtualizada || consulta;
    if (saldoReceberConsulta(c) > 0) {
      // Mantém o recibo, mas o botão de complementar fica disponível (saldoAtualizado abaixo).
    }
  }, [open, confirmado, consulta, consultaAtualizada]);

  const consultaExibida = consultaAtualizada || consulta;
  const saldoProp = saldoReceberConsulta(consulta);
  const saldoAtualizada = consultaAtualizada ? saldoReceberConsulta(consultaAtualizada) : 0;
  const saldoAposRecebimento = Math.max(saldoProp, saldoAtualizada);
  const precisaComplementar = confirmado && saldoAposRecebimento > 0;
  const consultaParaComplemento =
    saldoProp >= saldoAtualizada ? consulta : consultaExibida;
  const valorDesconto = parseMoneyInput(desconto);
  const totalLiquido = calcularTotalLiquido(baseReceber, valorDesconto);
  const distribuido = useMemo(() => somaEntradas(entradas), [entradas]);

  // Ao mudar desconto/total líquido com 1 linha, sincroniza o valor da linha
  useEffect(() => {
    if (!open || confirmado) return;
    if (entradas.length !== 1) return;
    const atual = parseMoneyInput(entradas[0].valor);
    if (!valoresQuaseIguais(atual, totalLiquido)) {
      setEntradas((prev) =>
        prev.length === 1 ? [{ ...prev[0], valor: totalLiquido > 0 ? String(totalLiquido) : "" }] : prev,
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [totalLiquido, open, confirmado]);

  useEffect(() => {
    if (!open || confirmado) return;
    setMarkAsPaid(valoresQuaseIguais(distribuido, totalLiquido) && totalLiquido > 0);
  }, [distribuido, totalLiquido, open, confirmado]);

  if (!open) return null;

  const updateEntrada = (id: string, patch: Partial<EntradaPagamentoLinha>) => {
    setEntradas((prev) => prev.map((e) => (e.id === id ? { ...e, ...patch } : e)));
  };

  const addEntrada = () => {
    const resto = Math.max(0, Math.round((totalLiquido - distribuido) * 100) / 100);
    setEntradas((prev) => [...prev, novaLinhaEntrada("PIX", resto > 0 ? resto : "")]);
  };

  const removeEntrada = (id: string) => {
    setEntradas((prev) => (prev.length <= 1 ? prev : prev.filter((e) => e.id !== id)));
  };

  const handleConfirm = async () => {
    const validationError = validateReceberForm({
      totalLiquido,
      desconto: valorDesconto,
      base: baseReceber,
      entradas,
      markAsPaid,
    });
    if (validationError) {
      setError(validationError);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const payload = buildReceberPayload({
        desconto: valorDesconto,
        entradas,
        markAsPaid,
        totalLiquido,
      });
      const data = await ClinicaBelezaAPI.consultas.receber(consulta.id, payload);
      const atualizada = (data as { consulta?: Consulta }).consulta;
      if (!atualizada) throw new Error("Resposta inválida ao registrar recebimento.");
      setReciboSnapshot({
        desconto: valorDesconto,
        totalLiquido: distribuido,
        entradas: [...entradas],
      });
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
    if (!confirm("Corrigir o pagamento? O lançamento atual será limpo para você informar de novo. (Ainda não entrou no Financeiro.)")) return;
    setLoading(true);
    setError("");
    try {
      const res = await ClinicaBelezaAPI.consultas.estornarPagamento(consulta.id);
      const atualizada = (res?.consulta || res) as Consulta;
      setConfirmado(false);
      setConsultaAtualizada(null);
      setReciboSnapshot(null);
      onSuccess(atualizada);
      onClose();
    } catch (e: unknown) {
      setError(formatApiErrorBody(e) || "Erro ao corrigir pagamento.");
    } finally {
      setLoading(false);
    }
  };

  const handleImprimir = async () => {
    const c = consultaAtualizada || consulta;
    let lojaData: {
      nome?: string;
      cpf_cnpj?: string;
      endereco?: string;
      telefone?: string;
      email?: string;
      cep?: string;
    } = {};
    try {
      const info = await ClinicaBelezaAPI.loja.info();
      lojaData = info;
    } catch {
      /* usa defaults */
    }
    const snap = reciboSnapshot;
    const html = gerarHtmlRecibo({
      consulta: c,
      valorPago: snap?.totalLiquido ?? Number(c.valor_pago ?? 0),
      desconto: snap?.desconto ?? 0,
      entradas: snap?.entradas ?? [],
      lojaData,
    });
    const w = window.open("", "_blank", "width=320,height=700");
    if (!w) return;
    w.document.write(html);
    w.document.close();
  };

  const handleEnviarEmail = async () => {
    const c = consultaAtualizada || consulta;
    if (!c.payment_id) {
      toast.error("Pagamento não encontrado.");
      return;
    }
    try {
      await ClinicaBelezaAPI.payments.enviarRecibo(c.payment_id, "email");
      toast.success("Recibo enviado por email!");
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { error?: string } } };
      toast.error(ax?.response?.data?.error || formatApiErrorBody(e) || "Erro ao enviar email.");
    }
  };

  const handleEnviarWhatsApp = async () => {
    const c = consultaAtualizada || consulta;
    if (!c.payment_id) {
      toast.error("Pagamento não encontrado.");
      return;
    }
    try {
      await ClinicaBelezaAPI.payments.enviarRecibo(c.payment_id, "whatsapp");
      toast.success("Recibo enviado por WhatsApp!");
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { error?: string } } };
      toast.error(ax?.response?.data?.error || formatApiErrorBody(e) || "Erro ao enviar WhatsApp.");
    }
  };

  if (confirmado) {
    const snap = reciboSnapshot;
    const resumoFormas = snap
      ? formatEntradasResumo(snap.entradas, CLINICA_FORMA_PAGAMENTO_LABEL as Record<string, string>)
      : "";
    return (
      <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4">
        <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-2xl">
          <div className="flex items-center justify-between p-4 border-b dark:border-neutral-700">
            <h2
              className={`text-lg font-bold ${
                precisaComplementar
                  ? "text-orange-700 dark:text-orange-400"
                  : "text-green-700 dark:text-green-400"
              }`}
            >
              {precisaComplementar ? "✓ Pagamento parcial registrado" : "✓ Pagamento registrado"}
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
                  : "bg-green-50 dark:bg-green-900/20"
              }`}
            >
              <p>
                <strong>Paciente:</strong> {consultaExibida.patient_name}
              </p>
              <p>
                <strong>Procedimento:</strong> {consultaProcedimentosNomes(consultaExibida)}
              </p>
              {snap && snap.desconto > 0 && (
                <p>
                  <strong>Desconto:</strong> {formatCurrency(snap.desconto)}
                </p>
              )}
              <p>
                <strong>Valor recebido nesta operação:</strong>{" "}
                {formatCurrency(snap?.totalLiquido ?? Number(consultaExibida.valor_pago ?? 0))}
              </p>
              {resumoFormas && (
                <p>
                  <strong>Formas:</strong> {resumoFormas}
                </p>
              )}
              {Number(consultaExibida.valor_pago ?? 0) > 0 && (
                <p>
                  <strong>Total já pago:</strong> {formatCurrency(Number(consultaExibida.valor_pago))}
                </p>
              )}
              {precisaComplementar && (
                <p className="font-semibold text-orange-800 dark:text-orange-300 pt-1">
                  Saldo em aberto: {formatCurrency(saldoAposRecebimento)} — inclua outras formas para
                  complementar.
                </p>
              )}
            </div>

            {precisaComplementar && (
              <button
                type="button"
                onClick={() => reiniciarFormularioComplemento(consultaParaComplemento)}
                className="w-full py-2.5 rounded-lg text-white text-sm font-medium"
                style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
              >
                Complementar saldo (várias formas)
              </button>
            )}

            <p className="text-sm text-gray-600 dark:text-gray-400">
              Envie o recibo de pagamento para o cliente:
            </p>
            <div className="grid grid-cols-3 gap-3">
              <button
                type="button"
                onClick={handleImprimir}
                className="flex flex-col items-center gap-2 p-4 rounded-xl border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors"
              >
                <Printer size={24} className="text-gray-700 dark:text-gray-300" />
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">Imprimir</span>
              </button>
              <button
                type="button"
                onClick={handleEnviarEmail}
                className="flex flex-col items-center gap-2 p-4 rounded-xl border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors"
              >
                <Mail size={24} className="text-gray-700 dark:text-gray-300" />
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">Email</span>
              </button>
              <button
                type="button"
                onClick={handleEnviarWhatsApp}
                className="flex flex-col items-center gap-2 p-4 rounded-xl border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors"
              >
                <MessageCircle size={24} className="text-gray-700 dark:text-gray-300" />
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">WhatsApp</span>
              </button>
            </div>

            {error && (
              <div className="p-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
                {error}
              </div>
            )}

            <div className="flex justify-between items-center pt-2 gap-2">
              {consulta.status !== "COMPLETED" && (
                <button
                  type="button"
                  onClick={handleEstornar}
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

  const somaOk = valoresQuaseIguais(distribuido, totalLiquido) && totalLiquido > 0;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b dark:border-neutral-700">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Receber pagamento</h2>
          <button type="button" onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg">
            <X size={18} />
          </button>
        </div>
        <div className="p-5 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2 text-sm">
              <p className="text-gray-500 dark:text-gray-400 text-xs uppercase font-semibold">
                Dados do atendimento
              </p>
              <p>
                <strong>Paciente:</strong> {consulta.patient_name}
              </p>
              <p>
                <strong>Procedimento:</strong> {consultaProcedimentosNomes(consulta)}
              </p>
              <p>
                <strong>Valor da consulta:</strong> {formatCurrency(valorConsulta)}
              </p>
              <p>
                <strong>Valor procedimento:</strong> {formatCurrency(valorProcedimentos)}
              </p>
              <p className="font-semibold text-gray-800 dark:text-gray-200 pt-1 border-t dark:border-neutral-600">
                Total: {formatCurrency(total)}
              </p>
              {Number(consulta.valor_pago ?? 0) > 0 && (
                <p className="text-orange-600 dark:text-orange-400 font-medium">
                  Já pago: {formatCurrency(Number(consulta.valor_pago))} · Saldo:{" "}
                  {formatCurrency(saldoAtual)}
                </p>
              )}
              {Number(consulta.valor_pago ?? 0) > 0 && saldoAtual > 0 && (
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Complemente o saldo com uma ou mais formas (Dinheiro, PIX, Débito, Crédito…).
                </p>
              )}
              <div className="pt-3">
                <label className="block text-sm font-medium mb-1">Desconto (R$)</label>
                <input
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

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-gray-500 dark:text-gray-400 text-xs uppercase font-semibold">
                  Formas de pagamento
                </p>
                <button
                  type="button"
                  onClick={addEntrada}
                  className="inline-flex items-center gap-1 text-sm font-medium text-[#8B4557] hover:underline"
                >
                  <Plus size={16} /> Adicionar forma
                </button>
              </div>

              <div className="space-y-3">
                {entradas.map((linha, idx) => (
                  <div
                    key={linha.id}
                    className="rounded-lg border border-gray-200 dark:border-neutral-600 p-3 space-y-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs text-gray-500">Forma {idx + 1}</span>
                      {entradas.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeEntrada(linha.id)}
                          className="p-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                          aria-label="Remover forma"
                        >
                          <Trash2 size={16} />
                        </button>
                      )}
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      <div>
                        <label className="block text-xs font-medium mb-1">Forma</label>
                        <select
                          value={linha.payment_method}
                          onChange={(e) => updateEntrada(linha.id, { payment_method: e.target.value })}
                          className={fieldClass}
                        >
                          {Object.entries(CLINICA_FORMA_PAGAMENTO_LABEL).map(([value, label]) => (
                            <option key={value} value={value}>
                              {label}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-medium mb-1">Valor (R$)</label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          value={linha.valor}
                          onChange={(e) => updateEntrada(linha.id, { valor: e.target.value })}
                          className={fieldClass}
                        />
                      </div>
                    </div>
                    {linha.payment_method === "CREDIT_CARD" && (
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-xs font-medium mb-1">Parcelas</label>
                          <select
                            value={linha.parcelas || "1"}
                            onChange={(e) => updateEntrada(linha.id, { parcelas: e.target.value })}
                            className={fieldClass}
                          >
                            {Array.from({ length: 12 }, (_, i) => i + 1).map((n) => (
                              <option key={n} value={String(n)}>
                                {n}x
                              </option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-medium mb-1">Valor parcela (R$)</label>
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            value={linha.valorParcela || ""}
                            onChange={(e) => updateEntrada(linha.id, { valorParcela: e.target.value })}
                            placeholder={(
                              parseMoneyInput(linha.valor) / (Number(linha.parcelas) || 1)
                            ).toFixed(2)}
                            className={fieldClass}
                          />
                          <p className="text-xs text-gray-500 mt-0.5">Com taxa do cartão</p>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <p
                className={`text-sm font-medium ${
                  somaOk ? "text-green-700 dark:text-green-400" : "text-amber-700 dark:text-amber-400"
                }`}
              >
                Distribuído: {formatCurrency(distribuido)} / {formatCurrency(totalLiquido)}
                {somaOk ? " ✓" : ""}
              </p>
            </div>
          </div>

          {error && (
            <div className="p-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
              {error}
            </div>
          )}

          <label className="flex items-center gap-2 text-sm pt-1">
            <input
              type="checkbox"
              checked={markAsPaid}
              onChange={(e) => setMarkAsPaid(e.target.checked)}
            />
            Quitar pagamento completo
          </label>

          {Number(consulta.valor_pago ?? 0) > 0 && consulta.status !== "COMPLETED" && (
            <button
              type="button"
              onClick={handleEstornar}
              disabled={loading}
              className="w-full py-2 text-sm rounded-lg border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              Corrigir pagamento
            </button>
          )}

          <div className="flex gap-2 pt-2 border-t dark:border-neutral-700">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleConfirm}
              disabled={loading}
              className="flex-1 py-2 rounded-lg text-white disabled:opacity-50"
              style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
            >
              {loading ? "Registrando..." : "Confirmar"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function gerarHtmlRecibo(params: {
  consulta: Consulta;
  valorPago: number;
  desconto: number;
  entradas: EntradaPagamentoLinha[];
  lojaData: {
    nome?: string;
    cpf_cnpj?: string;
    endereco?: string;
    telefone?: string;
    email?: string;
    cep?: string;
  };
}): string {
  const { consulta, valorPago, desconto, entradas, lojaData } = params;
  const dataHora = new Date().toLocaleString("pt-BR", {
    timeZone: "America/Sao_Paulo",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
  const valorConsulta = Number(consulta.valor_consulta ?? 0);
  const valorProcs = Number(consulta.valor_procedimentos ?? 0);
  const totalGeral = valorConsulta + valorProcs;
  const telCep = linhaTelCep(lojaData.telefone, lojaData.cep);

  const formasHtml = entradas
    .filter((e) => parseMoneyInput(e.valor) > 0)
    .map((e) => {
      const label =
        CLINICA_FORMA_PAGAMENTO_LABEL[e.payment_method as keyof typeof CLINICA_FORMA_PAGAMENTO_LABEL] ||
        e.payment_method;
      const nParc = Number(e.parcelas) || 1;
      const parcInfo =
        e.payment_method === "CREDIT_CARD" && nParc > 1
          ? ` (${nParc}x R$ ${e.valorParcela || (parseMoneyInput(e.valor) / nParc).toFixed(2)})`
          : "";
      return `<tr><td>${label}${parcInfo}</td><td style="text-align:right">R$ ${parseMoneyInput(e.valor).toFixed(2)}</td></tr>`;
    })
    .join("");

  const procs = consulta.procedures_list ?? [];
  const procsHtml =
    procs.length > 0
      ? procs
          .map(
            (p) =>
              `<tr><td style="padding-left:8px">• ${p.nome}</td><td style="text-align:right">R$ ${Number(p.valor).toFixed(2)}</td></tr>`,
          )
          .join("")
      : `<tr><td style="padding-left:8px">• ${consulta.procedure_name || "Consulta"}</td><td style="text-align:right">R$ ${valorProcs.toFixed(2)}</td></tr>`;

  return `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>Recibo de Pagamento</title>
<style>
  @page { size: 80mm auto; margin: 4mm; }
  body { font-family: 'Courier New', monospace; width: 72mm; margin: 0 auto; padding: 8px; font-size: 11px; line-height: 1.4; }
  .header { text-align: center; border-bottom: 1px dashed #333; padding-bottom: 6px; margin-bottom: 8px; }
  .header h1 { font-size: 13px; margin: 0 0 2px; }
  .header p { margin: 1px 0; font-size: 10px; color: #444; }
  .section { margin: 6px 0; }
  .section-title { font-weight: bold; font-size: 10px; text-transform: uppercase; border-bottom: 1px dotted #aaa; margin-bottom: 4px; }
  table { width: 100%; border-collapse: collapse; font-size: 11px; }
  td { padding: 2px 0; vertical-align: top; }
  .divider { border-top: 1px dashed #333; margin: 8px 0; }
  .total { font-size: 14px; font-weight: bold; text-align: center; margin: 8px 0; }
  .footer { text-align: center; font-size: 9px; color: #666; margin-top: 10px; border-top: 1px dashed #333; padding-top: 6px; }
  @media print { body { margin: 0; width: 72mm; } }
</style>
</head><body>
<div class="header">
  <h1>${lojaData.nome || consulta.local_atendimento_name || "CLÍNICA"}</h1>
  ${lojaData.cpf_cnpj ? `<p>${labelDocumentoLoja(lojaData.cpf_cnpj)}: ${formatCpfCnpj(lojaData.cpf_cnpj)}</p>` : ""}
  ${lojaData.endereco ? `<p>${lojaData.endereco}</p>` : ""}
  ${telCep ? `<p>${telCep}</p>` : ""}
  ${lojaData.email ? `<p>${lojaData.email}</p>` : ""}
  <p style="margin-top:4px;font-weight:bold">RECIBO DE PAGAMENTO</p>
  <p>${dataHora}</p>
</div>

<div class="section">
  <div class="section-title">Cliente</div>
  <table>
    <tr><td>${consulta.patient_name}</td></tr>
  </table>
</div>

<div class="section">
  <div class="section-title">Profissional</div>
  <table>
    <tr><td>${consulta.professional_name || "—"}</td></tr>
  </table>
</div>

<div class="section">
  <div class="section-title">Serviços</div>
  <table>
    ${valorConsulta > 0 ? `<tr><td>Taxa de consulta</td><td style="text-align:right">R$ ${valorConsulta.toFixed(2)}</td></tr>` : ""}
    ${procsHtml}
  </table>
</div>

<div class="divider"></div>
<table>
  <tr><td><strong>Subtotal</strong></td><td style="text-align:right"><strong>R$ ${totalGeral.toFixed(2)}</strong></td></tr>
  ${desconto > 0 ? `<tr><td>Desconto</td><td style="text-align:right">- R$ ${desconto.toFixed(2)}</td></tr>` : ""}
  <tr><td><strong>Total</strong></td><td style="text-align:right"><strong>R$ ${(totalGeral - desconto).toFixed(2)}</strong></td></tr>
</table>

<div class="section">
  <div class="section-title">Pagamento</div>
  <table>
    ${formasHtml || `<tr><td>Pagamento</td><td style="text-align:right">R$ ${valorPago.toFixed(2)}</td></tr>`}
  </table>
</div>

<div class="total">VALOR PAGO: R$ ${valorPago.toFixed(2)}</div>

<div class="footer">
  <p>Obrigado pela preferência!</p>
  <p>Documento não fiscal — gerado pelo sistema.</p>
  <button onclick="window.print()" style="margin-top:8px;padding:6px 16px;font-size:12px;cursor:pointer;border:1px solid #333;border-radius:4px;background:#fff;">Imprimir</button>
</div>
</body></html>`;
}
