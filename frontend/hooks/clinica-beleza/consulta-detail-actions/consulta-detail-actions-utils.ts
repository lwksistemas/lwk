import {
  consultaEstaConcluida,
  consultaProcedimentos,
  consultaProcedimentosNomes,
  type Consulta,
} from "@/components/clinica-beleza/consultas/consultas-types";
import type { ConsultaPrintMeta } from "@/lib/consulta-print";
import { formatClinicaDateTime } from "@/lib/clinica-beleza-datetime";

export function formatConsultaData(d?: string | null): string {
  return d ? formatClinicaDateTime(new Date(d)) : "—";
}

export function valorPagamentoConsulta(c: Consulta): number {
  const total = Number(c.valor_pagamento ?? 0);
  if (total > 0) return total;
  const taxa = Number(c.valor_consulta ?? 0);
  const procs = Number(c.valor_procedimentos ?? 0);
  return taxa + procs;
}

export function buildConsultaPrintMeta(selected: Consulta): ConsultaPrintMeta {
  return {
    patientName: selected.patient_name,
    professionalName: selected.professional_name,
    procedureName: consultaProcedimentosNomes(selected),
    consultaId: selected.id,
    dataConsulta: formatConsultaData(selected.data_inicio),
  };
}

export function saldoReceberConsulta(c: Consulta): number {
  // API já calcula saldo_devedor (respeita desconto em valor_total)
  if (c.valor_restante != null) {
    const api = Number(c.valor_restante);
    if (!Number.isNaN(api)) return Math.max(0, api);
  }
  const total = valorPagamentoConsulta(c);
  const pago = Number(c.valor_pago ?? 0);
  return Math.max(0, total - pago);
}

/** Botão Receber (âmbar) ou Pago (verde) na lista e no detalhe da consulta. */
export function consultaPagamentoUi(c: Consulta): {
  mostrarReceber: boolean;
  mostrarPago: boolean;
  mostrarParcial: boolean;
  mostrarRecibo: boolean;
  consultaFinalizada: boolean;
} {
  const finalizada = c.status === "COMPLETED";

  if (c.status === "CANCELLED") {
    return { mostrarReceber: false, mostrarPago: false, mostrarParcial: false, mostrarRecibo: false, consultaFinalizada: false };
  }

  const saldo = saldoReceberConsulta(c);
  const isParcial = c.payment_status === "PARTIAL";
  const isPago = c.payment_status === "PAID" && saldo <= 0;

  if (isPago) {
    return { mostrarReceber: false, mostrarPago: true, mostrarParcial: false, mostrarRecibo: false, consultaFinalizada: finalizada };
  }

  if (isParcial) {
    return { mostrarReceber: false, mostrarPago: false, mostrarParcial: true, mostrarRecibo: false, consultaFinalizada: finalizada };
  }

  // Retorno gratuito finalizado: sem pagamento a cobrar, mas deve mostrar opção de recibo
  // Consulta finalizada sem saldo pendente e sem pagamento: também mostra recibo
  const isFinalizadaSemPendencia = finalizada && saldo <= 0 && !c.payment_status;
  const isRetornoGratuitoFinalizado = Boolean(c.retorno_gratuito) && finalizada && saldo <= 0;
  if (isRetornoGratuitoFinalizado || isFinalizadaSemPendencia) {
    return { mostrarReceber: false, mostrarPago: false, mostrarParcial: false, mostrarRecibo: true, consultaFinalizada: true };
  }

  // Pendente ou sem pagamento — saldo em aberto
  const mostrarReceber = !finalizada && (c.status === "RECEBER" || saldo > 0 || c.payment_status === "PENDING");
  // Se finalizada com saldo, mostra "Receber" como badge (não clicável → vai ao financeiro)
  const mostrarReceberFinanceiro = finalizada && saldo > 0;

  return {
    mostrarReceber: mostrarReceber || mostrarReceberFinanceiro,
    mostrarPago: false,
    mostrarParcial: false,
    mostrarRecibo: false,
    consultaFinalizada: finalizada,
  };
}

export function computeConsultaFlags(selected: Consulta, historico: Consulta[]) {
  const outraConsultaEmAndamento = historico.find(
    (c) => c.id !== selected.id && c.status === "IN_PROGRESS",
  );
  const consultaConcluida = consultaEstaConcluida(selected);
  const emAtendimento =
    selected.status === "IN_PROGRESS" ||
    (selected.status === "RECEBER" && !!selected.data_inicio);
  const { mostrarReceber, mostrarPago, mostrarParcial, mostrarRecibo, consultaFinalizada: _cFin } = consultaPagamentoUi(selected);
  return {
    outraConsultaEmAndamento,
    podeIniciar:
      (selected.status === "SCHEDULED" || selected.status === "RECEBER") &&
      !selected.data_inicio &&
      !outraConsultaEmAndamento,
    podeFinalizar:
      selected.status === "IN_PROGRESS" ||
      (selected.status === "RECEBER" && !!selected.data_inicio),
    podeExcluir: !consultaConcluida,
    consultaAtiva: emAtendimento,
    consultaFinalizada: consultaConcluida,
    mostrarReceber,
    mostrarPago,
    mostrarParcial,
    mostrarRecibo,
  };
}

export { consultaProcedimentos };
