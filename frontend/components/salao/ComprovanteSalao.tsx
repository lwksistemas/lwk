"use client";

import type { ComprovanteSalao } from "@/lib/salao-api";

function telefoneLegivel(valor?: string) {
  const digitos = String(valor || "").replace(/\D/g, "");
  const local = digitos.startsWith("55") && (digitos.length === 12 || digitos.length === 13) ? digitos.slice(2) : digitos;
  if (local.length === 11) return `(${local.slice(0, 2)}) ${local.slice(2, 7)}-${local.slice(7)}`;
  if (local.length === 10) return `(${local.slice(0, 2)}) ${local.slice(2, 6)}-${local.slice(6)}`;
  return valor || "";
}

function reais(valor: string | number | undefined) {
  const numero = Number(String(valor ?? "0").replace(",", "."));
  const quantia = Number.isFinite(numero) ? numero : 0;
  return quantia.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function ComprovanteSalaoCard({ dados }: { dados: ComprovanteSalao }) {
  const salao = dados.salao;
  const cor = salao?.cor || "#7A3044";
  const servicos = dados.servicos || [];
  const produtos = dados.produtos || [];
  const formas = dados.formas || [];
  const numero = dados.numero ? String(dados.numero).padStart(6, "0") : "";
  const previa = !dados.numero;
  const telefone = telefoneLegivel(salao?.telefone);
  return (
    <article className="folha mx-auto bg-white px-3.5 py-4 text-[#2a1c20]" style={{ width: "72mm", maxWidth: "100%", fontFamily: "Georgia, serif" }}>
      <div className="flex items-center justify-center gap-2.5">
        {salao?.logo ? <img src={salao.logo} alt="" style={{ height: 56, width: "auto", objectFit: "contain" }} /> : null}
        <div>
          <div className="text-[22px] font-bold leading-tight" style={{ color: cor }}>{salao?.nome || "Salão"}</div>
          {salao?.subtitulo ? <div className="text-[11px] uppercase tracking-[0.14em]" style={{ color: cor }}>{salao.subtitulo}</div> : null}
        </div>
      </div>
      <div className="mt-2.5 text-center font-sans text-[11px] text-[#5c3d45]">
        {salao?.endereco ? <div>{salao.endereco}</div> : null}
        {(telefone || salao?.email) ? <div>{[telefone, salao?.email].filter(Boolean).join(" | ")}</div> : null}
      </div>
      <div className="mt-3 px-1.5 py-2 text-center font-sans text-xs font-bold tracking-wide text-white" style={{ background: cor }}>
        {previa ? "PRÉVIA — NÃO É COMPROVANTE DE PAGAMENTO" : <>COMPROVANTE DE PAGAMENTO<br />(NÃO FISCAL)</>}
      </div>
      {dados.cancelado ? (
        <div className="mt-2 text-center font-sans text-[#9f1239]">
          <p className="text-sm font-bold">CANCELADO</p>
          <p className="text-[11px]">Pagamento cancelado{dados.cancelado_em ? ` em ${dados.cancelado_em}` : ""}{dados.cancelado_por ? ` por ${dados.cancelado_por}` : ""}.{dados.motivo ? ` Motivo: ${dados.motivo}.` : ""}{dados.estorno ? ` ${dados.estorno}.` : ""}</p>
        </div>
      ) : null}
      <div className="mt-2.5 flex justify-between gap-2 font-sans text-xs">
        <span>{numero ? `Nº ${numero}` : "Sem número"}</span>
        <span>{dados.quando}</span>
      </div>
      <div className="mt-2 rounded-lg border border-[#f0e4e7] px-2 py-2 font-sans text-[13px]">
        Cliente: <strong>{dados.cliente || "Consumidor"}</strong>
        {dados.operador ? <div className="mt-1 text-xs text-[#5c3d45]">Operador: {dados.operador}</div> : null}
      </div>
      <table className="mt-2 w-full border-collapse font-sans text-[13px]">
        <tbody>
          {servicos.length > 0 ? <tr><td colSpan={2} className="pb-1 pt-2 text-xs tracking-wide text-[#6b4a52]">SERVIÇOS</td></tr> : null}
          {servicos.map((item) => (
            <tr key={`s-${item.nome}-${item.profissional || ""}`}>
              <td className="border-t border-[#f0e4e7] py-1.5"><strong>{item.nome}</strong>{item.profissional ? <div className="text-xs text-[#8a6e74]">Profissional: {item.profissional}</div> : null}</td>
              <td className="border-t border-[#f0e4e7] py-1.5 text-right whitespace-nowrap">{reais(item.total)}</td>
            </tr>
          ))}
          {produtos.length > 0 ? <tr><td colSpan={2} className="pb-1 pt-2 text-xs tracking-wide text-[#6b4a52]">PRODUTOS</td></tr> : null}
          {produtos.map((item) => (
            <tr key={`p-${item.nome}`}>
              <td className="border-t border-[#f0e4e7] py-1.5">{item.quantidade || 1}× {item.nome}</td>
              <td className="border-t border-[#f0e4e7] py-1.5 text-right whitespace-nowrap">{reais(item.total)}</td>
            </tr>
          ))}
          {Number(dados.desconto || 0) > 0 ? (
            <tr>
              <td className="py-1.5">Desconto</td>
              <td className="py-1.5 text-right">{reais(dados.desconto)}</td>
            </tr>
          ) : null}
        </tbody>
      </table>
      <div className="mt-2 flex justify-between px-2.5 py-2 font-sans font-bold text-white" style={{ background: cor }}>
        <span>{dados.cancelado ? "Valor original" : "Total pago"}</span>
        <span>{reais(dados.valor)}</span>
      </div>
      {formas.length > 0 ? (
        <div className="mt-2 font-sans text-[13px]">
          <strong>Formas de pagamento</strong>
          <table className="w-full border-collapse">
            <tbody>
              {formas.map((item) => (
                <tr key={item.nome}>
                  <td className="border-t border-[#f0e4e7] py-1">{item.nome}</td>
                  <td className="border-t border-[#f0e4e7] py-1 text-right">{reais(item.valor)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
      <p className="mt-2.5 rounded-lg border border-[#f0e4e7] p-2 font-sans text-[11px] text-[#5c3d45]">Este comprovante não substitui a emissão de Nota Fiscal (NFS-e) ou Cupom Fiscal (NFC-e).</p>
      <p className="mt-3.5 text-center italic" style={{ color: cor }}>Obrigado pela preferência!</p>
    </article>
  );
}
