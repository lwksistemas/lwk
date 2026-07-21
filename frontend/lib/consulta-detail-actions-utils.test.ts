import { describe, expect, it } from "vitest";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import {
  computeConsultaFlags,
  consultaPagamentoUi,
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

  it("permite iniciar em RECEBER sem pagamento", () => {
    const flags = computeConsultaFlags(consulta({ status: "RECEBER" }), []);
    expect(flags.podeIniciar).toBe(true);
    expect(flags.mostrarReceber).toBe(true);
  });

  it("finaliza RECEBER com atendimento já iniciado", () => {
    const flags = computeConsultaFlags(
      consulta({ status: "RECEBER", data_inicio: "2026-07-08T10:00:00Z" }),
      [],
    );
    expect(flags.podeFinalizar).toBe(true);
    expect(flags.consultaAtiva).toBe(true);
  });

  it("consulta ativa quando IN_PROGRESS", () => {
    const flags = computeConsultaFlags(consulta({ status: "IN_PROGRESS" }), []);
    expect(flags.consultaAtiva).toBe(true);
    expect(flags.podeFinalizar).toBe(true);
  });
});

describe("consultaPagamentoUi", () => {
  it("mostra Receber em RECEBER", () => {
    expect(consultaPagamentoUi(consulta({ status: "RECEBER" }))).toEqual({
      mostrarReceber: true,
      mostrarPago: false,
      mostrarParcial: false,
      mostrarRecibo: false,
      consultaFinalizada: false,
    });
  });

  it("mostra Pago após quitar total", () => {
    expect(
      consultaPagamentoUi(
        consulta({
          status: "SCHEDULED",
          payment_status: "PAID",
          valor_pagamento: 150,
          valor_pago: 150,
        }),
      ),
    ).toEqual({
      mostrarReceber: false,
      mostrarPago: true,
      mostrarParcial: false,
      mostrarRecibo: false,
      consultaFinalizada: false,
    });
  });

  it("mostra Parcial após pagamento parcial", () => {
    expect(
      consultaPagamentoUi(
        consulta({
          status: "RECEBER",
          payment_status: "PARTIAL",
          valor_pagamento: 200,
          valor_pago: 150,
        }),
      ),
    ).toEqual({
      mostrarReceber: false,
      mostrarPago: false,
      mostrarParcial: true,
      mostrarRecibo: false,
      consultaFinalizada: false,
    });
  });

  it("mostra Pago quando valor_restante=0 mesmo com desconto (bruto > pago)", () => {
    expect(
      consultaPagamentoUi(
        consulta({
          status: "SCHEDULED",
          payment_status: "PAID",
          valor_pagamento: 200,
          valor_pago: 150,
          valor_restante: 0,
        }),
      ),
    ).toEqual({
      mostrarReceber: false,
      mostrarPago: true,
      mostrarParcial: false,
      mostrarRecibo: false,
      consultaFinalizada: false,
    });
  });

  it("mostra Recibo para retorno gratuito finalizado", () => {
    expect(
      consultaPagamentoUi(
        consulta({
          status: "COMPLETED",
          retorno_gratuito: true,
          valor_pagamento: 0,
          valor_pago: 0,
          valor_restante: 0,
        }),
      ),
    ).toEqual({
      mostrarReceber: false,
      mostrarPago: false,
      mostrarParcial: false,
      mostrarRecibo: true,
      consultaFinalizada: true,
    });
  });

  it("mostra Recibo para consulta finalizada sem pagamento", () => {
    expect(
      consultaPagamentoUi(
        consulta({
          status: "COMPLETED",
          payment_status: undefined,
          valor_pagamento: 0,
          valor_pago: 0,
          valor_restante: 0,
        }),
      ),
    ).toEqual({
      mostrarReceber: false,
      mostrarPago: false,
      mostrarParcial: false,
      mostrarRecibo: true,
      consultaFinalizada: true,
    });
  });
});
