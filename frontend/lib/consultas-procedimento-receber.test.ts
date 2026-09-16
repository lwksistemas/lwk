import { describe, expect, it } from "vitest";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import {
  consultaProcedimentoLabel,
  consultaTemProcedimento,
} from "@/components/clinica-beleza/consultas/consultas-types";

const consulta = (overrides: Partial<Consulta> = {}): Consulta =>
  ({
    id: 1,
    patient: 1,
    procedure: 1,
    patient_name: "Paciente",
    professional_name: "Dr.",
    procedure_name: "",
    status: "IN_PROGRESS",
    valor_consulta: 150,
    valor_procedimentos: 0,
    valor_pagamento: 150,
    total_evolucoes: 0,
    ...overrides,
  }) as Consulta;

describe("consultaTemProcedimento", () => {
  it("é falso quando só há taxa de consulta", () => {
    expect(consultaTemProcedimento(consulta())).toBe(false);
    expect(consultaTemProcedimento(consulta({ procedure_name: "Consulta" }))).toBe(false);
    expect(consultaProcedimentoLabel(consulta({ procedure_name: "Consulta" }))).toBeNull();
  });

  it("é verdadeiro quando há procedimento cobrável", () => {
    expect(
      consultaTemProcedimento(
        consulta({
          procedure_name: "Botox",
          valor_procedimentos: 80,
          procedures_list: [{ id: 2, nome: "Botox", valor: 80 }],
        }),
      ),
    ).toBe(true);
    expect(
      consultaProcedimentoLabel(
        consulta({
          procedure_name: "Botox",
          valor_procedimentos: 80,
          procedures_list: [{ id: 2, nome: "Botox", valor: 80 }],
        }),
      ),
    ).toBe("BOTOX");
  });
});
