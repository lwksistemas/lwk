import { describe, expect, it } from "vitest";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import {
  buildProntuarioConsultasResumo,
  consultaAcaoLabel,
  consultaProcedimentoLabel,
  isConsultaAtualParaIniciar,
  isConsultaFinalizadaProntuario,
  pickConsultasAtuais,
  pickConsultasFinalizadas,
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

  it("rótulos de ação e procedimento", () => {
    expect(consultaAcaoLabel("IN_PROGRESS")).toBe("Continuar consulta");
    expect(consultaAcaoLabel("SCHEDULED")).toBe("Iniciar consulta");
    expect(consultaAcaoLabel("COMPLETED")).toBe("Abrir consulta");
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
});
