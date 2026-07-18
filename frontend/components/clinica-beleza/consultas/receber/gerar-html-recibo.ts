import { CLINICA_FORMA_PAGAMENTO_LABEL } from "@/lib/clinica-beleza-constants";
import { formatCep, formatCpfCnpj, formatTelefone } from "@/lib/format-br";
import { type Consulta } from "../consultas-types";
import {
  parseMoneyInput,
  type EntradaPagamentoLinha,
} from "../modal-receber-consulta-utils";

function labelDocumentoLoja(cpfCnpj?: string): string {
  const d = (cpfCnpj || "").replace(/\D/g, "");
  if (d.length === 11) return "CPF";
  if (d.length === 14) return "CNPJ";
  return "CPF/CNPJ";
}

function linhaTelCep(telefone?: string, cep?: string): string {
  const partes: string[] = [];
  const tel = formatTelefone(telefone || "");
  const cepFmt = formatCep(cep || "");
  if (tel) partes.push(`Tel: ${tel}`);
  if (cepFmt) partes.push(`CEP ${cepFmt}`);
  return partes.join("  ·  ");
}

export function gerarHtmlRecibo(params: {
  consulta: Consulta;
  valorPago: number;
  desconto: number;
  entradas: EntradaPagamentoLinha[];
  lojaData: {
    nome?: string;
    cpf_cnpj?: string;
    endereco?: string;
    telefone?: string;
    email?: string;
    cep?: string;
  };
  saldoRestante?: number;
}): string {
  const { consulta, valorPago, desconto, entradas, lojaData, saldoRestante = 0 } = params;
  const dataHora = consulta.payment_date
    ? new Date(consulta.payment_date).toLocaleString("pt-BR", {
        timeZone: "America/Sao_Paulo",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : new Date().toLocaleString("pt-BR", {
        timeZone: "America/Sao_Paulo",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
  const valorConsulta = Number(consulta.valor_consulta ?? 0);
  const valorProcs = Number(consulta.valor_procedimentos ?? 0);
  const totalGeral = valorConsulta + valorProcs;
  const telCep = linhaTelCep(lojaData.telefone, lojaData.cep);

  const formasHtml = entradas
    .filter((e) => parseMoneyInput(e.valor) > 0)
    .map((e) => {
      const label =
        CLINICA_FORMA_PAGAMENTO_LABEL[e.payment_method as keyof typeof CLINICA_FORMA_PAGAMENTO_LABEL] ||
        e.payment_method;
      const nParc = Number(e.parcelas) || 1;
      const parcInfo =
        e.payment_method === "CREDIT_CARD" && nParc > 1
          ? ` (${nParc}x R$ ${e.valorParcela || (parseMoneyInput(e.valor) / nParc).toFixed(2)})`
          : "";
      return `<tr><td>${label}${parcInfo}</td><td style="text-align:right">R$ ${parseMoneyInput(e.valor).toFixed(2)}</td></tr>`;
    })
    .join("");

  const procs = consulta.procedures_list ?? [];
  const procsHtml =
    procs.length > 0
      ? procs
          .map(
            (p) =>
              `<tr><td style="padding-left:8px">• ${p.nome}</td><td style="text-align:right">R$ ${Number(p.valor).toFixed(2)}</td></tr>`,
          )
          .join("")
      : `<tr><td style="padding-left:8px">• ${consulta.procedure_name || "Consulta"}</td><td style="text-align:right">R$ ${valorProcs.toFixed(2)}</td></tr>`;

  return `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>Recibo de Pagamento</title>
<style>
  @page { size: 80mm auto; margin: 4mm; }
  body { font-family: 'Courier New', monospace; width: 72mm; margin: 0 auto; padding: 8px; font-size: 11px; line-height: 1.4; }
  .header { text-align: center; border-bottom: 1px dashed #333; padding-bottom: 6px; margin-bottom: 8px; }
  .header h1 { font-size: 13px; margin: 0 0 2px; }
  .header p { margin: 1px 0; font-size: 10px; color: #444; }
  .section { margin: 6px 0; }
  .section-title { font-weight: bold; font-size: 10px; text-transform: uppercase; border-bottom: 1px dotted #aaa; margin-bottom: 4px; }
  table { width: 100%; border-collapse: collapse; font-size: 11px; }
  td { padding: 2px 0; vertical-align: top; }
  .divider { border-top: 1px dashed #333; margin: 8px 0; }
  .total { font-size: 14px; font-weight: bold; text-align: center; margin: 8px 0; }
  .footer { text-align: center; font-size: 9px; color: #666; margin-top: 10px; border-top: 1px dashed #333; padding-top: 6px; }
  @media print { body { margin: 0; width: 72mm; } }
</style>
</head><body>
<div class="header">
  <h1>${lojaData.nome || consulta.local_atendimento_name || "CLÍNICA"}</h1>
  ${lojaData.cpf_cnpj ? `<p>${labelDocumentoLoja(lojaData.cpf_cnpj)}: ${formatCpfCnpj(lojaData.cpf_cnpj)}</p>` : ""}
  ${lojaData.endereco ? `<p>${lojaData.endereco}</p>` : ""}
  ${telCep ? `<p>${telCep}</p>` : ""}
  ${lojaData.email ? `<p>${lojaData.email}</p>` : ""}
  <p style="margin-top:4px;font-weight:bold">RECIBO DE PAGAMENTO</p>
  <p>${dataHora}</p>
</div>

<div class="section">
  <div class="section-title">Cliente</div>
  <table>
    <tr><td>${consulta.patient_name}</td></tr>
  </table>
</div>

<div class="section">
  <div class="section-title">Profissional</div>
  <table>
    <tr><td>${consulta.professional_name || "—"}</td></tr>
  </table>
</div>

<div class="section">
  <div class="section-title">Data/Hora do atendimento</div>
  <table>
    <tr><td>${consulta.appointment_date ? new Date(consulta.appointment_date).toLocaleString("pt-BR", {
      timeZone: "America/Sao_Paulo",
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }) : "—"}</td></tr>
  </table>
</div>

<div class="section">
  <div class="section-title">Serviços</div>
  <table>
    ${valorConsulta > 0 ? `<tr><td>Taxa de consulta</td><td style="text-align:right">R$ ${valorConsulta.toFixed(2)}</td></tr>` : ""}
    ${procsHtml}
  </table>
</div>

<div class="divider"></div>
<table>
  <tr><td><strong>Subtotal</strong></td><td style="text-align:right"><strong>R$ ${(totalGeral + desconto).toFixed(2)}</strong></td></tr>
  ${desconto > 0 ? `<tr><td>Desconto</td><td style="text-align:right">- R$ ${desconto.toFixed(2)}</td></tr>` : ""}
  <tr><td><strong>Total</strong></td><td style="text-align:right"><strong>R$ ${(totalGeral - desconto).toFixed(2)}</strong></td></tr>
</table>

<div class="section">
  <div class="section-title">Formas de pagamento:</div>
  <table>
    ${formasHtml || `<tr><td>Pagamento</td><td style="text-align:right">R$ ${valorPago.toFixed(2)}</td></tr>`}
  </table>
</div>

<div class="total">VALOR PAGO: R$ ${valorPago.toFixed(2)}</div>
${
  saldoRestante > 0.009
    ? `<div class="total" style="font-size:12px;">SALDO: R$ ${saldoRestante.toFixed(2)}</div>`
    : `<div class="footer" style="border-top:none;margin-top:0;"><p style="font-weight:bold;color:#333;">Quitado</p></div>`
}

<div class="footer">
  <p>Agradecemos pela confiança!</p>
  <p>Documento não fiscal — gerado pelo sistema.</p>
  <button onclick="window.print()" style="margin-top:8px;padding:6px 16px;font-size:12px;cursor:pointer;border:1px solid #333;border-radius:4px;background:#fff;">Imprimir</button>
</div>
</body></html>`;
}
