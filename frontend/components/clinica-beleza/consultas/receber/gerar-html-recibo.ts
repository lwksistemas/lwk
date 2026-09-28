import { CLINICA_FORMA_PAGAMENTO_LABEL } from "@/lib/clinica-beleza-constants";
import { formatCep, formatCpfCnpj, formatTelefone } from "@/lib/format-br";
import { type Consulta } from "../consultas-types";
import {
  parseMoneyInput,
  type EntradaPagamentoLinha,
} from "../modal-receber-consulta-utils";

function escapeHtml(value: unknown): string {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function labelDocumentoLoja(cpfCnpj?: string): string {
  const d = (cpfCnpj || "").replace(/\D/g, "");
  if (d.length === 11) return "CPF";
  if (d.length === 14) return "CNPJ";
  return "CPF/CNPJ";
}

function nomeSoConsulta(nome: string): boolean {
  const n = nome.trim().toLowerCase();
  return !n || n === "consulta" || n === "taxa de consulta";
}

function formatarMoedaRecibo(valor: number): string {
  const negativo = valor < -0.004;
  const [inteiro, frac] = Math.abs(valor).toFixed(2).split(".");
  const grupos = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${negativo ? "-" : ""}R$ ${grupos},${frac}`;
}

function formatarDataHoraBr(data: Date): string {
  const parts = new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).formatToParts(data);
  const ler = (tipo: string) => parts.find((p) => p.type === tipo)?.value ?? "";
  return `${ler("day")}/${ler("month")}/${ler("year")} ${ler("hour")}:${ler("minute")}`;
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
  vencimento?: string | null;
}): string {
  const { consulta, valorPago, desconto, entradas, lojaData, saldoRestante = 0, vencimento = null } = params;
  const vencimentoBr = vencimento
    ? vencimento.split("-").reverse().join("/")
    : "";
  // Data/hora da EMISSÃO do comprovante (impressão) — sempre o momento atual.
  const dataHoraEmissao = formatarDataHoraBr(new Date());
  const valorConsulta = Number(consulta.valor_consulta ?? 0);
  const valorProcs = Number(consulta.valor_procedimentos ?? 0);
  const retornoGratuito = Boolean(consulta.retorno_gratuito);
  const valorConsultaReferencia = Number(
    consulta.local_atendimento_valor_consulta ?? valorConsulta,
  );
  const retornoAviso = (consulta.retorno_aviso_recibo || "").trim();
  const procsPrevios = consulta.procedures_list ?? [];
  const soConsultaSemRetorno =
    !retornoGratuito &&
    valorProcs <= 0.009 &&
    procsPrevios.every((p) => nomeSoConsulta(p.nome || "")) &&
    nomeSoConsulta(consulta.procedure_name || "");
  const taxaExibida = retornoGratuito
    ? valorConsultaReferencia
    : valorConsulta > 0.009
      ? valorConsulta
      : soConsultaSemRetorno
        ? valorConsultaReferencia
        : valorConsulta;
  const descontoRetorno =
    retornoGratuito && valorConsultaReferencia > 0 ? valorConsultaReferencia : 0;
  const telCep = escapeHtml(linhaTelCep(lojaData.telefone, lojaData.cep));
  const nomeLoja = escapeHtml(lojaData.nome || consulta.local_atendimento_name || "CLÍNICA");
  const enderecoLoja = escapeHtml(lojaData.endereco || "");
  const emailLoja = escapeHtml(lojaData.email || "");
  const nomeCliente = escapeHtml(consulta.patient_name || "");
  const nomeProfissional = escapeHtml(consulta.professional_name || "—");
  const avisoRetorno = escapeHtml(retornoAviso);

  const taxaConsultaHtml =
    taxaExibida > 0
      ? `<tr><td>Taxa de consulta</td><td style="text-align:right">${formatarMoedaRecibo(taxaExibida)}</td></tr>`
      : "";
  const descontosHtml = [
    descontoRetorno > 0
      ? `<tr><td>Desconto retorno</td><td style="text-align:right">- ${formatarMoedaRecibo(descontoRetorno)}</td></tr>`
      : "",
    desconto > 0
      ? `<tr><td>Desconto</td><td style="text-align:right">- ${formatarMoedaRecibo(desconto)}</td></tr>`
      : "",
  ].join("");

  const fmtDataBr = (iso?: string | null): string =>
    iso ? String(iso).slice(0, 10).split("-").reverse().join("/") : "";

  // Sempre mostra a data em que o cliente pagou cada forma (não confundir com a emissão do recibo).
  // Agrupa por forma + data do pagamento.
  const formasAgrupadas = new Map<
    string,
    { label: string; valor: number; parcInfo: string; dataInfo: string }
  >();
  for (const e of entradas) {
    const valor = parseMoneyInput(e.valor);
    if (valor <= 0) continue;
    const label =
      CLINICA_FORMA_PAGAMENTO_LABEL[e.payment_method as keyof typeof CLINICA_FORMA_PAGAMENTO_LABEL] ||
      e.payment_method;
    const nParc = Number(e.parcelas) || 1;
    const parcInfo =
      e.payment_method === "CREDIT_CARD" && nParc > 1
        ? ` (${nParc}x ${formatarMoedaRecibo(Number(e.valorParcela) || valor / nParc)})`
        : "";
    const dataKey = String(e.payment_date || "").slice(0, 10);
    const dataInfo = dataKey ? ` (${fmtDataBr(dataKey)})` : "";
    const key = `${e.payment_method}|${parcInfo}|${dataKey}`;
    const prev = formasAgrupadas.get(key);
    if (prev) {
      prev.valor += valor;
    } else {
      formasAgrupadas.set(key, { label, valor, parcInfo, dataInfo });
    }
  }
  const formasHtml = Array.from(formasAgrupadas.values())
    .map(
      (f) =>
        `<tr><td>${escapeHtml(f.label)}${escapeHtml(f.parcInfo)}${escapeHtml(f.dataInfo)}</td><td style="text-align:right">${formatarMoedaRecibo(f.valor)}</td></tr>`,
    )
    .join("");


  const procs = consulta.procedures_list ?? [];
  // Filtrar procedimentos redundantes: se já mostra "Taxa de consulta" e o procedimento é
  // apenas "Consulta" com valor 0, não exibir linha repetida
  const procsVisiveis = procs.filter((p) => {
    if (taxaExibida > 0 && Number(p.valor || 0) === 0) {
      const nome = (p.nome || "").toLowerCase().trim();
      if (nome === "consulta" || nome === "taxa de consulta") return false;
    }
    return true;
  });
  const procsSoma =
    procsVisiveis.length > 0
      ? procsVisiveis.reduce((acc, p) => acc + Number(p.valor || 0), 0)
      : procs.length > 0
        ? procs.reduce((acc, p) => acc + Number(p.valor || 0), 0)
        : valorProcs;
  const subtotalBruto = taxaExibida + procsSoma;
  const totalFinal = Math.max(0, subtotalBruto - descontoRetorno - desconto);
  let procsHtml =
    procsVisiveis.length > 0
      ? procsVisiveis
          .map(
            (p) =>
              `<tr><td style="padding-left:8px">• ${escapeHtml(p.nome)}</td><td style="text-align:right">${formatarMoedaRecibo(Number(p.valor))}</td></tr>`,
          )
          .join("")
      : procs.length > 0
        ? ""
        : valorProcs > 0
          ? `<tr><td style="padding-left:8px">• ${escapeHtml(consulta.procedure_name || "Procedimento")}</td><td style="text-align:right">${formatarMoedaRecibo(valorProcs)}</td></tr>`
          : "";
  if (!taxaConsultaHtml && !procsHtml) {
    const nomeConsulta = (consulta.procedure_name || "").trim() || "Consulta";
    procsHtml = `<tr><td style="padding-left:8px">• ${escapeHtml(nomeConsulta)}</td><td style="text-align:right">${formatarMoedaRecibo(valorConsulta)}</td></tr>`;
  }
  const soConsulta =
    procsVisiveis.length > 0
      ? procsVisiveis.every((p) => nomeSoConsulta(p.nome || ""))
      : nomeSoConsulta(consulta.procedure_name || "");
  const localNome = (consulta.local_atendimento_name || "").trim();
  const convenioNome = (consulta.convenio_name || "").trim() || "Particular";
  const localConvenioHtml = soConsulta
    ? `${localNome ? `<tr><td colspan="2">Local<br>${escapeHtml(localNome)}</td></tr>` : ""}<tr><td colspan="2">Convênio<br>${escapeHtml(convenioNome)}</td></tr>`
    : "";
  const saldo = Math.max(saldoRestante, totalFinal - valorPago);
  const semSaldo = totalFinal <= 0.009 && valorPago <= 0.009;
  const emAberto = saldo > 0.009 && valorPago <= 0.009;
  const parcial = saldo > 0.009 && valorPago > 0.009;
  let tituloDoc = "RECIBO DE PAGAMENTO";
  let subtituloDoc = "";
  if (semSaldo) {
    tituloDoc = "COMPROVANTE DE ATENDIMENTO";
    subtituloDoc = "Sem saldo — consulta integralmente descontada";
  } else if (emAberto) {
    tituloDoc = "COMPROVANTE DE ATENDIMENTO";
    subtituloDoc = "Valor em aberto";
  } else if (parcial) {
    tituloDoc = "COMPROVANTE DE ATENDIMENTO";
    subtituloDoc = "Pagamento parcial — saldo em aberto";
  }
  const numeroRecibo = consulta.payment_id;
  const dataAtendimento = consulta.appointment_date
    ? formatarDataHoraBr(new Date(consulta.appointment_date))
    : "—";
  const formasBloco = formasHtml
    ? `<div class="section"><div class="section-title">Formas de pagamento:</div><table>${formasHtml}</table></div>`
    : emAberto && vencimentoBr
      ? `<p style="text-align:center">Condição de cobrança: a prazo — vencimento ${escapeHtml(vencimentoBr)}</p>`
      : valorPago > 0
        ? `<div class="section"><div class="section-title">Formas de pagamento:</div><table><tr><td>Pagamento</td><td style="text-align:right">${formatarMoedaRecibo(valorPago)}</td></tr></table></div>`
        : "";
  const pagoBloco = semSaldo
    ? ""
    : `<div class="total">${parcial ? "PAGO" : "VALOR PAGO"}: ${formatarMoedaRecibo(valorPago)}</div>`;
  const recebidoAMaior = Math.round((valorPago - totalFinal) * 100) / 100;
  const extraBloco =
    recebidoAMaior > 0.009
      ? `<div class="total" style="font-size:12px;">RECEBIDO A MAIOR: ${formatarMoedaRecibo(recebidoAMaior)}</div>`
      : "";
  const statusBloco = semSaldo
    ? `<div class="footer" style="border-top:none;margin-top:0;"><p style="font-weight:bold;color:#333;">${escapeHtml(subtituloDoc)}</p></div>`
    : saldo > 0.009
      ? `<div class="total" style="font-size:12px;">SALDO A PAGAR: ${formatarMoedaRecibo(saldo)}${vencimentoBr && !emAberto ? ` — vencimento ${escapeHtml(vencimentoBr)}` : ""}</div>`
      : `<div class="footer" style="border-top:none;margin-top:0;"><p style="font-weight:bold;color:#333;">Quitado</p></div>`;

  return `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>Recibo de Pagamento</title>
<style>
  /* Largura do cupom. size:auto deixa o Chrome com preview em branco. */
  @page { size: 80mm 297mm; margin: 4mm; }
  html, body { background: #fff; color: #000; }
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
  @media print {
    html, body { width: 72mm !important; max-width: 72mm !important; margin: 0 !important; padding: 4px !important; background: #fff !important; }
    .no-print, button { display: none !important; }
  }
</style>
</head><body>
<div class="header">
  <h1>${nomeLoja}</h1>
  ${lojaData.cpf_cnpj ? `<p>${escapeHtml(labelDocumentoLoja(lojaData.cpf_cnpj))}: ${escapeHtml(formatCpfCnpj(lojaData.cpf_cnpj))}</p>` : ""}
  ${enderecoLoja ? `<p>${enderecoLoja}</p>` : ""}
  ${telCep ? `<p>${telCep}</p>` : ""}
  ${emailLoja ? `<p>${emailLoja}</p>` : ""}
  <p style="margin-top:4px;font-weight:bold">${tituloDoc}</p>
  ${subtituloDoc ? `<p>${escapeHtml(subtituloDoc)}</p>` : ""}
  <p>Emitido em ${dataHoraEmissao}</p>
  ${numeroRecibo ? `<p>Recibo nº ${escapeHtml(numeroRecibo)}</p>` : ""}
</div>

<div class="section">
  <div class="section-title">Cliente</div>
  <table>
    <tr><td>${nomeCliente}</td></tr>
  </table>
</div>

<div class="section">
  <div class="section-title">Profissional</div>
  <table>
    <tr><td>${nomeProfissional}</td></tr>
  </table>
</div>

<div class="section">
  <div class="section-title">Data/Hora do atendimento</div>
  <table>
    <tr><td>${dataAtendimento}</td></tr>
  </table>
</div>

<div class="section">
  <div class="section-title">Serviços</div>
  <table>
    ${taxaConsultaHtml}
    ${procsHtml}
    ${localConvenioHtml}
  </table>
</div>

<div class="divider"></div>
<table>
  <tr><td><strong>Subtotal</strong></td><td style="text-align:right"><strong>${formatarMoedaRecibo(subtotalBruto)}</strong></td></tr>
  ${descontosHtml}
  <tr><td><strong>Total</strong></td><td style="text-align:right"><strong>${formatarMoedaRecibo(totalFinal)}</strong></td></tr>
</table>

${formasBloco}

${pagoBloco}
${extraBloco}
${statusBloco}

<div class="footer">
  ${avisoRetorno ? `<p style="color:#333;margin-bottom:6px;">${avisoRetorno}</p>` : ""}
  <p>Agradecemos pela confiança!</p>
  <p>Documento não fiscal — gerado pelo sistema.</p>
  <button type="button" class="no-print" onclick="try{window.focus()}catch(e){};setTimeout(function(){window.print()},50)" style="margin-top:8px;padding:6px 16px;font-size:12px;cursor:pointer;border:1px solid #333;border-radius:4px;background:#fff;">Imprimir</button>
</div>
</body></html>`;
}
