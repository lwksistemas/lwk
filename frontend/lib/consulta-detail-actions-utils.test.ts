import { describe, expect, it } from "vitest";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import {
  computeConsultaFlags,
  valorPagamentoConsulta,
} from "@/hooks/clinica-beleza/consulta-detail-actions/consulta-detail-actions-utils";

const consulta = (overrides: Partial<Consulta>): Consulta =>
  ({
    id: 1,
    patient: 1,
    procedure: 1,
    patient_name: "Paciente",
    professional_name: "Dr.",
    procedure_name: "Botox",
    status: "SCHEDULED",
    valor_consulta: 100,
    valor_procedimentos: 50,
    valor_pagamento: 0,
    total_evolucoes: 0,
    ...overrides,
  }) as Consulta;

describe("valorPagamentoConsulta", () => {
  it("usa valor_pagamento quando positivo", () => {
    expect(valorPagamentoConsulta(consulta({ valor_pagamento: 200 }))).toBe(200);
  });

  it("soma taxa e procedimentos quando valor_pagamento zero", () => {
    expect(valorPagamentoConsulta(consulta({ valor_pagamento: 0 }))).toBe(150);
  });
});

describe("computeConsultaFlags", () => {
  it("bloqueia iniciar se outra consulta em andamento", () => {
    const flags = computeConsultaFlags(consulta({ id: 1, status: "SCHEDULED" }), [
      consulta({ id: 2, status: "IN_PROGRESS" }),
    ]);
    expect(flags.podeIniciar).toBe(false);
    expect(flags.outraConsultaEmAndamento?.id).toBe(2);
  });

  it("consulta ativa quando IN_PROGRESS", () => {
    const flags = computeConsultaFlags(consulta({ status: "IN_PROGRESS" }), []);
    expect(flags.consultaAtiva).toBe(true);
    expect(flags.podeFinalizar).toBe(true);
  });
});
