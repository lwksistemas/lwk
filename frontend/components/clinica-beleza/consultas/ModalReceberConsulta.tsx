"use client";

import { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";
import { useToast } from "@/components/ui/Toast";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { formatApiErrorBody } from "@/lib/api-errors";
import {
  saldoReceberConsulta,
  valorPagamentoConsulta,
} from "@/hooks/clinica-beleza/consulta-detail-actions/consulta-detail-actions-utils";
import { type Consulta } from "./consultas-types";
import {
  buildReceberPayload,
  calcularTotalLiquido,
  novaLinhaEntrada,
  parseMoneyInput,
  somaEntradas,
  validateReceberForm,
  valoresQuaseIguais,
  type EntradaPagamentoLinha,
} from "./modal-receber-consulta-utils";
import { gerarHtmlRecibo } from "./receber/gerar-html-recibo";
import { ReceberDadosAtendimento } from "./receber/ReceberDadosAtendimento";
import { ReceberFormasPagamento } from "./receber/ReceberFormasPagamento";
import { ReceberSucessoPanel } from "./receber/ReceberSucessoPanel";

interface ModalReceberConsultaProps {
  open: boolean;
  consulta: Consulta;
  onClose: () => void;
  onSuccess: (consulta: Partial<Consulta>) => void;
}

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
      const retornoGratuitoFinalizado = Boolean(consulta.retorno_gratuito) && consulta.status === "COMPLETED" && novoSaldo <= 0;
      const finalizadaSemPagamento = consulta.status === "COMPLETED" && novoSaldo <= 0 && !consulta.payment_status;
      if (quitado || retornoGratuitoFinalizado || finalizadaSemPagamento) {
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
      const atualizada = res.consulta;
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

    // Recibo do cliente: todas as formas já pagas + total acumulado (não só esta operação).
    let entradasRecibo = reciboSnapshot?.entradas ?? [];
    let valorPagoRecibo = reciboSnapshot?.totalLiquido ?? Number(c.valor_pago ?? 0);
    let descontoRecibo = reciboSnapshot?.desconto ?? 0;
    if (c.payment_id) {
      try {
        const parcelasRes = (await ClinicaBelezaAPI.financeiro.payments.parcelas.list(
          c.payment_id,
        )) as {
          parcelas?: Array<{ status?: string; valor?: number | string; payment_method?: string }>;
          valor_pago?: number;
        };
        const parcelas = Array.isArray(parcelasRes?.parcelas)
          ? parcelasRes.parcelas
          : Array.isArray(parcelasRes)
            ? (parcelasRes as Array<{ status?: string; valor?: number | string; payment_method?: string }>)
            : [];
        const pagas = parcelas.filter((p) => (p.status || "PAID") === "PAID");
        if (pagas.length > 0) {
          entradasRecibo = pagas.map((p) =>
            novaLinhaEntrada(p.payment_method || "CASH", Number(p.valor ?? 0)),
          );
          valorPagoRecibo =
            typeof parcelasRes?.valor_pago === "number"
              ? parcelasRes.valor_pago
              : pagas.reduce((s, p) => s + Number(p.valor ?? 0), 0);
        }
      } catch {
        /* mantém snapshot da operação */
      }
    }
    if (Number(c.valor_pago ?? 0) > valorPagoRecibo) {
      valorPagoRecibo = Number(c.valor_pago);
    }

    const html = gerarHtmlRecibo({
      consulta: c,
      valorPago: valorPagoRecibo,
      desconto: descontoRecibo,
      entradas: entradasRecibo,
      lojaData,
      saldoRestante: saldoReceberConsulta(c),
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
    return (
      <ReceberSucessoPanel
        consultaExibida={consultaExibida}
        consultaStatus={consulta.status}
        precisaComplementar={precisaComplementar}
        saldoAposRecebimento={saldoAposRecebimento}
        reciboSnapshot={reciboSnapshot}
        error={error}
        loading={loading}
        onClose={onClose}
        onComplementar={() => reiniciarFormularioComplemento(consultaParaComplemento)}
        onEstornar={handleEstornar}
        onImprimir={handleImprimir}
        onEmail={handleEnviarEmail}
        onWhatsApp={handleEnviarWhatsApp}
      />
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
            <ReceberDadosAtendimento
              consulta={consulta}
              valorConsulta={valorConsulta}
              valorProcedimentos={valorProcedimentos}
              total={total}
              saldoAtual={saldoAtual}
              desconto={desconto}
              onDescontoChange={setDesconto}
              totalLiquido={totalLiquido}
            />

            <ReceberFormasPagamento
              entradas={entradas}
              distribuido={distribuido}
              totalLiquido={totalLiquido}
              somaOk={somaOk}
              onAdd={addEntrada}
              onRemove={removeEntrada}
              onUpdate={updateEntrada}
            />
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
