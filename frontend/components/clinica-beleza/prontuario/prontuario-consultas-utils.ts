import {
  consultaEstaConcluida,
  type Consulta,
} from "@/components/clinica-beleza/consultas/consultas-types";

const STATUS_ATUAL = new Set(["IN_PROGRESS", "RECEBER", "SCHEDULED"]);
const STATUS_FINALIZADA = "COMPLETED";

const ORDEM_ATUAL: Record<string, number> = {
  IN_PROGRESS: 0,
  RECEBER: 1,
  SCHEDULED: 2,
};

export function isConsultaAtualParaIniciar(status: string): boolean {
  return STATUS_ATUAL.has(status);
}

export function isConsultaFinalizadaProntuario(status: string): boolean {
  return status === STATUS_FINALIZADA;
}

function consultaSortTime(c: Consulta): number {
  const raw = c.data_inicio || c.appointment_date || c.data_fim || "";
  const t = Date.parse(raw);
  return Number.isNaN(t) ? 0 : t;
}

/** Consultas em andamento / aguardando início, mais relevantes primeiro. */
export function pickConsultasAtuais(consultas: Consulta[]): Consulta[] {
  return consultas
    .filter((c) => isConsultaAtualParaIniciar(c.status))
    .sort((a, b) => {
      const ordem = (ORDEM_ATUAL[a.status] ?? 9) - (ORDEM_ATUAL[b.status] ?? 9);
      if (ordem !== 0) return ordem;
      return consultaSortTime(b) - consultaSortTime(a);
    });
}

/** Consultas finalizadas, mais recentes primeiro. */
export function pickConsultasFinalizadas(consultas: Consulta[]): Consulta[] {
  return consultas
    .filter((c) => isConsultaFinalizadaProntuario(c.status))
    .sort((a, b) => consultaSortTime(b) - consultaSortTime(a));
}

export interface ProntuarioConsultasResumo {
  atuais: Consulta[];
  finalizadas: Consulta[];
  total: number;
  consultaParaFotosId: number | null;
}

export function buildProntuarioConsultasResumo(consultas: Consulta[]): ProntuarioConsultasResumo {
  const atuais = pickConsultasAtuais(consultas);
  const finalizadas = pickConsultasFinalizadas(consultas);
  const consultaParaFotosId = atuais[0]?.id ?? finalizadas[0]?.id ?? consultas[0]?.id ?? null;
  return {
    atuais,
    finalizadas,
    total: consultas.length,
    consultaParaFotosId,
  };
}

export function consultaAcaoLabel(status: string): string {
  if (status === "IN_PROGRESS") return "Continuar consulta";
  if (status === "RECEBER" || status === "SCHEDULED") return "Iniciar consulta";
  return "Abrir consulta";
}

/** Ainda não entrou em atendimento — o botão Iniciar dispara a API e abre a ficha. */
export function consultaPodeIniciarAtendimento(c: Pick<Consulta, "status" | "data_inicio">): boolean {
  return (c.status === "SCHEDULED" || c.status === "RECEBER") && !c.data_inicio;
}

export function consultaPodeExcluirNoProntuario(
  c: Pick<Consulta, "status" | "data_fim" | "appointment_status">,
): boolean {
  return !consultaEstaConcluida(c) && c.status !== "CANCELLED";
}

export interface ProntuarioConsultaAtualAcoes {
  podeExcluir: boolean;
  podeIniciar: boolean;
  mostrarContinuar: boolean;
  bloqueadaPorOutraEmAndamento: boolean;
}

/** Ações do card da consulta atual no resumo do prontuário. */
export function prontuarioConsultaAtualAcoes(
  consulta: Consulta,
  todas: Consulta[],
): ProntuarioConsultaAtualAcoes {
  const podeIniciarBase = consultaPodeIniciarAtendimento(consulta);
  const bloqueadaPorOutraEmAndamento =
    podeIniciarBase && todas.some((c) => c.id !== consulta.id && c.status === "IN_PROGRESS");
  const mostrarContinuar =
    consulta.status === "IN_PROGRESS" ||
    (!!consulta.data_inicio && consulta.status !== "COMPLETED" && consulta.status !== "CANCELLED");
  return {
    podeExcluir: consultaPodeExcluirNoProntuario(consulta),
    podeIniciar: podeIniciarBase && !bloqueadaPorOutraEmAndamento,
    mostrarContinuar,
    bloqueadaPorOutraEmAndamento,
  };
}

export function consultaProcedimentoLabel(c: Consulta): string {
  if (c.procedures_list?.length) {
    return c.procedures_list.map((p) => p.nome).filter(Boolean).join(", ");
  }
  return c.procedure_name || "Consulta";
}
