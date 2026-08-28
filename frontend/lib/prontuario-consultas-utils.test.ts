import { describe, expect, it } from "vitest";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import {
  buildProntuarioConsultasResumo,
  consultaPodeExcluirNoProntuario,
  consultaPodeIniciarAtendimento,
  consultaProcedimentoLabel,
  isConsultaAtualParaIniciar,
  isConsultaFinalizadaProntuario,
  pickConsultasAtuais,
  pickConsultasFinalizadas,
  ordenarConsultasProntuarioLista,
  prontuarioConsultaAtualAcoes,
} from "@/components/clinica-beleza/prontuario/prontuario-consultas-utils";

const consulta = (partial: Partial<Consulta> & Pick<Consulta, "id" | "status">): Consulta =>
  ({
    patient: 1,
    procedure: 1,
    patient_name: "Ana",
    professional_name: "Dra. Lia",
    procedure_name: "Limpeza de pele",
    valor_consulta: 0,
    total_evolucoes: 0,
    ...partial,
  }) as Consulta;

describe("prontuario consultas", () => {
  it("reconhece consulta atual e finalizada", () => {
    expect(isConsultaAtualParaIniciar("IN_PROGRESS")).toBe(true);
    expect(isConsultaAtualParaIniciar("SCHEDULED")).toBe(true);
    expect(isConsultaAtualParaIniciar("COMPLETED")).toBe(false);
    expect(isConsultaFinalizadaProntuario("COMPLETED")).toBe(true);
  });

  it("prioriza em atendimento na lista atual", () => {
    const atuais = pickConsultasAtuais([
      consulta({ id: 1, status: "SCHEDULED", appointment_date: "2026-08-28T10:00:00" }),
      consulta({ id: 2, status: "IN_PROGRESS", data_inicio: "2026-08-28T09:00:00" }),
    ]);
    expect(atuais.map((c) => c.id)).toEqual([2, 1]);
  });

  it("lista finalizadas da mais recente", () => {
    const finalizadas = pickConsultasFinalizadas([
      consulta({ id: 1, status: "COMPLETED", data_fim: "2026-01-01T10:00:00" }),
      consulta({ id: 2, status: "COMPLETED", data_fim: "2026-08-01T10:00:00" }),
      consulta({ id: 3, status: "CANCELLED" }),
    ]);
    expect(finalizadas.map((c) => c.id)).toEqual([2, 1]);
  });

  it("monta resumo e escolhe consulta para fotos", () => {
    const resumo = buildProntuarioConsultasResumo([
      consulta({ id: 10, status: "SCHEDULED" }),
      consulta({ id: 11, status: "COMPLETED", data_fim: "2026-08-01T10:00:00" }),
    ]);
    expect(resumo.atuais).toHaveLength(1);
    expect(resumo.finalizadas).toHaveLength(1);
    expect(resumo.consultaParaFotosId).toBe(10);
  });

  it("lista unica do prontuario inclui todas as consultas", () => {
    const lista = ordenarConsultasProntuarioLista([
      consulta({ id: 1, status: "COMPLETED", data_fim: "2026-01-01T10:00:00" }),
      consulta({ id: 2, status: "CANCELLED" }),
      consulta({ id: 3, status: "IN_PROGRESS", data_inicio: "2026-08-28T09:00:00" }),
      consulta({ id: 4, status: "SCHEDULED", appointment_date: "2026-08-29T10:00:00" }),
    ]);
    expect(lista.map((c) => c.id)).toEqual([3, 4, 1, 2]);
  });

  it("rótulos de procedimento", () => {
    expect(
      consultaProcedimentoLabel(
        consulta({
          id: 1,
          status: "COMPLETED",
          procedures_list: [
            { id: 1, nome: "Botox", valor: 0 },
            { id: 2, nome: "Peeling", valor: 0 },
          ],
        }),
      ),
    ).toBe("Botox, Peeling");
  });

  it("define ações da consulta atual no prontuário", () => {
    const atual = consulta({ id: 12, status: "RECEBER" });
    const acoes = prontuarioConsultaAtualAcoes(atual, [atual]);
    expect(consultaPodeIniciarAtendimento(atual)).toBe(true);
    expect(consultaPodeExcluirNoProntuario(atual)).toBe(true);
    expect(acoes.podeIniciar).toBe(true);
    expect(acoes.podeExcluir).toBe(true);
    expect(acoes.mostrarContinuar).toBe(false);

    const emAndamento = consulta({
      id: 13,
      status: "IN_PROGRESS",
      data_inicio: "2026-08-28T09:00:00",
    });
    const acoesAndamento = prontuarioConsultaAtualAcoes(emAndamento, [emAndamento]);
    expect(acoesAndamento.podeIniciar).toBe(false);
    expect(acoesAndamento.mostrarContinuar).toBe(true);
    expect(acoesAndamento.podeExcluir).toBe(true);

    const outra = consulta({ id: 14, status: "SCHEDULED" });
    const bloqueada = prontuarioConsultaAtualAcoes(outra, [emAndamento, outra]);
    expect(bloqueada.podeIniciar).toBe(false);
    expect(bloqueada.bloqueadaPorOutraEmAndamento).toBe(true);

    const finalizada = consulta({
      id: 15,
      status: "COMPLETED",
      data_fim: "2026-08-10T20:00:00",
    });
    expect(consultaPodeExcluirNoProntuario(finalizada)).toBe(false);
    expect(consultaPodeIniciarAtendimento(finalizada)).toBe(false);
  });
});
