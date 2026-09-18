import { describe, expect, it } from "vitest";
import { gerarHtmlRecibo } from "@/components/clinica-beleza/consultas/receber/gerar-html-recibo";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";

const consulta = {
  id: 1,
  patient: 1,
  procedure: 1,
  patient_name: "TAMIRES FURONI",
  professional_name: "MARINA GARCIA RAMOS",
  procedure_name: "DEPILAÇÃO A LASER",
  procedures_list: [{ id: 1, nome: "DEPILAÇÃO A LASER", valor: 300 }],
  status: "COMPLETED",
  valor_consulta: 150,
  valor_procedimentos: 300,
  total_evolucoes: 0,
} as Consulta;

describe("gerarHtmlRecibo", () => {
  it("mostra a linha Desconto (R$) quando houve desconto comercial", () => {
    const html = gerarHtmlRecibo({
      consulta,
      valorPago: 300,
      desconto: 150,
      entradas: [{ id: "1", payment_method: "CASH", valor: "300" }],
      lojaData: { nome: "HARMONIS" },
    });
    expect(html).toContain("Desconto");
    expect(html).toContain("- R$ 150.00");
  });

  it("omite Desconto quando o valor é zero", () => {
    const html = gerarHtmlRecibo({
      consulta,
      valorPago: 450,
      desconto: 0,
      entradas: [{ id: "1", payment_method: "CASH", valor: "450" }],
      lojaData: { nome: "HARMONIS" },
    });
    expect(html).not.toContain(">Desconto<");
  });
});
