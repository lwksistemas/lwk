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

/** Valor da coluna da lista (taxa + procedimentos já somados pela API). */
export function valorListadoConsulta(c: Consulta): number {
  const bruto = Number(c.valor_pagamento ?? c.valor_consulta);
  if (Number.isNaN(bruto)) return 0;
  return Math.max(0, bruto);
}

export function saldoReceberConsulta(c: Consulta): number {
  const pago = Number(c.valor_pago ?? 0);
  // API já calcula saldo_devedor (respeita desconto em valor_total)
  if (c.valor_restante != null) {
    const api = Number(c.valor_restante);
    if (!Number.isNaN(api)) {
      const saldo = Math.max(0, api);
      // Retorno zera só a taxa. Se o pagamento ficou em R$ 0 e o procedimento tem valor, ainda há o que receber.
      const listado = valorListadoConsulta(c);
      if (Boolean(c.retorno_gratuito) && listado > 0.009 && pago <= 0.009 && saldo <= 0.009) {
        return listado;
      }
      return saldo;
    }
  }
  const total = valorPagamentoConsulta(c);
  return Math.max(0, total - pago);
}

/** Botão Receber (âmbar) ou Pago (verde) na lista e no detalhe da consulta. */
export function consultaPagamentoUi(c: Consulta): {
  mostrarReceber: boolean;
  mostrarPago: boolean;
  mostrarParcial: boolean;
  mostrarRecibo: boolean;
  mostrarPrazo: boolean;
  mostrarIsento: boolean;
  consultaFinalizada: boolean;
} {
  const finalizada = c.status === "COMPLETED";
  const vazio = {
    mostrarReceber: false,
    mostrarPago: false,
    mostrarParcial: false,
    mostrarRecibo: false,
    mostrarPrazo: false,
    mostrarIsento: false,
    consultaFinalizada: finalizada,
  };

  if (c.status === "CANCELLED") {
    return { ...vazio, consultaFinalizada: false };
  }

  const saldo = saldoReceberConsulta(c);
  const isParcial = c.payment_status === "PARTIAL" && saldo > 0;
  const isPago = c.payment_status === "PAID" && saldo <= 0;
  const listado = valorListadoConsulta(c);

  // Isento/Retorno só quando o atendimento inteiro está sem valor. Procedimento cobrado não é retorno.
  if (Boolean(c.retorno_gratuito) && listado <= 0.009 && saldo <= 0.009) {
    return { ...vazio, mostrarIsento: true, consultaFinalizada: finalizada };
  }

  if (isPago) {
    return { ...vazio, mostrarPago: true };
  }

  if (isParcial) {
    return { ...vazio, mostrarParcial: true };
  }

  const isFinalizadaSemPendencia = finalizada && saldo <= 0.009 && !c.payment_status;
  if (isFinalizadaSemPendencia) {
    return { ...vazio, mostrarRecibo: true, consultaFinalizada: true };
  }

  if (c.payment_method === "PRAZO" && saldo > 0) {
    return { ...vazio, mostrarPrazo: true };
  }

  const mostrarReceber = !finalizada && (c.status === "RECEBER" || saldo > 0 || c.payment_status === "PENDING");
  const mostrarReceberFinanceiro = finalizada && saldo > 0;

  return {
    ...vazio,
    mostrarReceber: mostrarReceber || mostrarReceberFinanceiro,
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

export function mensagemValidacaoEvolucao(form: {
  descricao: string;
  procedimento_realizado: string;
  satisfacao: string;
}): string | null {
  if (!form.descricao.trim() && !form.procedimento_realizado.trim()) {
    return "Preencha a evolução ou o procedimento realizado.";
  }
  if (!["1", "2", "3", "4", "5"].includes(String(form.satisfacao))) {
    return "Informe a satisfação do cliente (1 a 5). É obrigatório.";
  }
  return null;
}

export { consultaProcedimentos };
