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

  it("mostra Desconto retorno sem o prazo em dias", () => {
    const html = gerarHtmlRecibo({
      consulta: {
        ...consulta,
        retorno_gratuito: true,
        local_atendimento_valor_consulta: 150,
        retorno_dias_prazo: 30,
      } as Consulta,
      valorPago: 200,
      desconto: 0,
      entradas: [{ id: "1", payment_method: "CASH", valor: "200" }],
      lojaData: { nome: "HARMONIS" },
    });
    expect(html).toContain(">Desconto retorno<");
    expect(html).not.toContain("prazo");
  });

  it("escapa HTML no nome do cliente e da clínica", () => {
    const html = gerarHtmlRecibo({
      consulta: {
        ...consulta,
        patient_name: '<img src=x onerror="alert(1)">',
        professional_name: "<b>Dr</b>",
        procedure_name: "<script>x</script>",
        procedures_list: [{ id: 1, nome: "<svg onload=alert(1)>", valor: 300 }],
        retorno_aviso_recibo: "<i>aviso</i>",
      } as Consulta,
      valorPago: 450,
      desconto: 0,
      entradas: [{ id: "1", payment_method: "CASH", valor: "450" }],
      lojaData: {
        nome: "<Clinica>",
        endereco: 'Rua "A"',
        email: "a@b.com",
      },
    });
    expect(html).toContain("&lt;img src=x onerror=&quot;alert(1)&quot;&gt;");
    expect(html).toContain("&lt;Clinica&gt;");
    expect(html).toContain("&lt;b&gt;Dr&lt;/b&gt;");
    expect(html).toContain("&lt;svg onload=alert(1)&gt;");
    expect(html).toContain("&lt;i&gt;aviso&lt;/i&gt;");
    expect(html).not.toContain("<img src=x");
    expect(html).not.toContain("<script>");
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
