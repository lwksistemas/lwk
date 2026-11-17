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

function chaveForma(nome: string) {
  const texto = nome.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  if (texto.includes("pix")) return "pix";
  if (texto.includes("dinheiro")) return "dinheiro";
  if (texto.includes("debito") || texto.includes("credito") || texto.includes("cart")) return "cartao";
  return "outro";
}

function Icone({ nome, tamanho = 16 }: { nome: string; tamanho?: number }) {
  const comum = { width: tamanho, height: tamanho, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.7, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true };
  if (nome === "pin") return <svg {...comum}><path d="M12 21s6.2-5.4 6.2-10.2a6.2 6.2 0 1 0-12.4 0C5.8 15.6 12 21 12 21z" /><circle cx="12" cy="10.7" r="2" /></svg>;
  if (nome === "telefone") return <svg {...comum}><path d="M7 3.5h2.4l1.2 3-1.7 1a12 12 0 0 0 5.6 5.6l1-1.7 3 1.2V15a2 2 0 0 1-2.2 2A14.5 14.5 0 0 1 5 6.7 2 2 0 0 1 7 3.5z" /></svg>;
  if (nome === "email") return <svg {...comum}><rect x="3" y="5" width="18" height="14" rx="2" /><path d="m4 7 8 6 8-6" /></svg>;
  if (nome === "pessoa") return <svg {...comum}><circle cx="12" cy="8" r="3.1" /><path d="M5.6 19.4c.8-3.3 3-4.8 6.4-4.8s5.6 1.5 6.4 4.8" /></svg>;
  if (nome === "calendario") return <svg {...comum}><rect x="4" y="5" width="16" height="15" rx="2" /><path d="M8 3.5v4M16 3.5v4M4 10h16" /></svg>;
  if (nome === "dinheiro") return <svg {...comum}><rect x="2.5" y="6" width="19" height="12" rx="2" /><circle cx="12" cy="12" r="2.2" /></svg>;
  if (nome === "pix") return <svg {...comum}><path d="m12 3 3.2 3.2L12 9.4 8.8 6.2zM12 14.6l3.2 3.2L12 21l-3.2-3.2zM3 12l3.2-3.2L9.4 12 6.2 15.2zM14.6 12l3.2-3.2L21 12l-3.2 3.2z" /></svg>;
  if (nome === "cartao") return <svg {...comum}><rect x="2.5" y="5" width="19" height="14" rx="2" /><path d="M2.5 10h19" /></svg>;
  if (nome === "info") return <svg {...comum}><circle cx="12" cy="12" r="8.5" /><path d="M12 11v5M12 8h.01" /></svg>;
  return <svg {...comum}><circle cx="12" cy="12" r="8" /></svg>;
}

function Tesoura({ tamanho = 64 }: { tamanho?: number }) {
  return (
    <svg width={tamanho} height={tamanho} viewBox="0 0 72 72" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M36 8c-16 3-26 14-28 28 8-10 16-14 28-14s20 4 28 14C62 22 52 11 36 8z" />
      <circle cx="24" cy="52" r="7" />
      <circle cx="48" cy="52" r="7" />
      <path d="M29 47 47 16" />
      <path d="M43 47 25 16" />
    </svg>
  );
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
  const borda = "#ead8dc";
  return (
    <article className="mx-auto overflow-hidden bg-white text-[#2a1c20]" style={{ width: "100%", maxWidth: "170mm", fontFamily: "Georgia, 'Times New Roman', serif" }}>
      <div className="px-5 pb-2 pt-5">
        <div className="flex items-center justify-center gap-3">
          <div className="shrink-0" style={{ color: cor }}>
            {salao?.logo ? <img src={salao.logo} alt="" style={{ height: 64, width: "auto", maxWidth: 88, objectFit: "contain" }} /> : <Tesoura />}
          </div>
          <div className="h-14 w-px" style={{ background: cor }} />
          <div>
            <div className="text-[26px] font-bold leading-none" style={{ color: cor }}>{salao?.nome || "Salão"}</div>
            {salao?.subtitulo ? <div className="mt-1 text-[11px] uppercase tracking-[0.22em]" style={{ color: cor }}>{salao.subtitulo}</div> : null}
            <div className="mt-1.5 h-px w-16" style={{ background: cor }} />
          </div>
        </div>
        <div className="mt-3 space-y-1 font-sans text-[12px] text-[#3a2a2e]">
          {salao?.endereco ? <div className="flex items-start gap-1.5" style={{ color: cor }}><Icone nome="pin" /><span className="text-[#3a2a2e]">{salao.endereco}</span></div> : null}
          {(telefone || salao?.email) ? (
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
              {telefone ? <span className="inline-flex items-center gap-1" style={{ color: cor }}><Icone nome="telefone" /><span className="text-[#3a2a2e]">{telefone}</span></span> : null}
              {telefone && salao?.email ? <span className="text-[#b7a4a8]">|</span> : null}
              {salao?.email ? <span className="inline-flex items-center gap-1" style={{ color: cor }}><Icone nome="email" /><span className="text-[#3a2a2e]">{salao.email}</span></span> : null}
            </div>
          ) : null}
          {salao?.documento ? <div>{salao.documento}</div> : null}
        </div>
        <div className="mt-3 h-px" style={{ background: cor }} />
        <div className="mt-3 rounded-xl px-3 py-2.5 text-center font-sans text-[13px] font-bold tracking-wide text-white" style={{ background: cor }}>
          {previa ? "PRÉVIA — NÃO É COMPROVANTE DE PAGAMENTO" : <>COMPROVANTE DE PAGAMENTO<br />(NÃO FISCAL)</>}
        </div>
        {dados.cancelado ? (
          <div className="mt-2 text-center font-sans text-[#9f1239]">
            <p className="text-sm font-bold">CANCELADO</p>
            <p className="text-[11px]">Pagamento cancelado{dados.cancelado_em ? ` em ${dados.cancelado_em}` : ""}{dados.cancelado_por ? ` por ${dados.cancelado_por}` : ""}.{dados.motivo ? ` Motivo: ${dados.motivo}.` : ""}{dados.estorno ? ` ${dados.estorno}.` : ""}</p>
          </div>
        ) : null}
        <div className="mt-3 flex items-center justify-between gap-2 font-sans text-[13px]">
          <span><strong>Nº:</strong> {numero || "Sem número"}</span>
          <span className="inline-flex items-center gap-1" style={{ color: cor }}><Icone nome="calendario" tamanho={15} /><span className="text-[#2a1c20]">{dados.quando}</span></span>
        </div>
        <div className="mt-2.5 flex items-start gap-2 rounded-xl border px-3 py-2.5 font-sans text-[13px]" style={{ borderColor: borda }}>
          <span className="mt-0.5" style={{ color: cor }}><Icone nome="pessoa" /></span>
          <span>
            <span>Cliente: <strong>{dados.cliente || "Consumidor"}</strong></span>
            {dados.operador ? <span className="mt-0.5 block text-xs text-[#5c3d45]">Operador: {dados.operador}</span> : null}
          </span>
        </div>
        <div className="mt-2.5 overflow-hidden rounded-xl border font-sans text-[13px]" style={{ borderColor: borda }}>
          {servicos.length > 0 ? (
            <>
              <div className="flex justify-between px-3 py-2 font-bold"><span>Serviço</span><span>Valor</span></div>
              {servicos.map((item) => (
                <div key={`s-${item.nome}-${item.profissional || ""}`} className="flex items-start justify-between gap-3 border-t px-3 py-2" style={{ borderColor: borda }}>
                  <span><strong>{item.nome}</strong>{item.profissional ? <span className="mt-0.5 block text-xs text-[#6b4a52]">Profissional: {item.profissional}</span> : null}</span>
                  <span className="whitespace-nowrap">{reais(item.total)}</span>
                </div>
              ))}
            </>
          ) : null}
          {produtos.length > 0 ? (
            <>
              <div className="flex justify-between border-t px-3 py-2 font-bold" style={{ borderColor: borda }}><span>Produto</span><span>Valor</span></div>
              {produtos.map((item) => (
                <div key={`p-${item.nome}`} className="flex items-start justify-between gap-3 border-t px-3 py-2" style={{ borderColor: borda }}>
                  <span>{(item.quantidade || 1) > 1 ? `${item.quantidade}× ` : ""}{item.nome}</span>
                  <span className="whitespace-nowrap">{reais(item.total)}</span>
                </div>
              ))}
            </>
          ) : null}
          {Number(dados.desconto || 0) > 0 ? (
            <div className="flex justify-between border-t px-3 py-2" style={{ borderColor: borda }}>
              <span>Desconto</span>
              <span>{reais(dados.desconto)}</span>
            </div>
          ) : null}
        </div>
        <div className="mt-2.5 flex items-center justify-between rounded-xl px-3.5 py-2.5 font-sans text-white" style={{ background: cor }}>
          <span className="text-[15px] font-bold">{dados.cancelado ? "Valor original:" : "Total pago:"}</span>
          <span className="text-xl font-bold">{reais(dados.valor)}</span>
        </div>
        {formas.length > 0 ? (
          <div className="mt-3 font-sans text-[13px]">
            <p className="font-bold">Formas de pagamento:</p>
            {formas.map((item) => (
              <div key={item.nome} className="flex items-center justify-between gap-2 border-b py-1.5" style={{ borderColor: borda }}>
                <span className="inline-flex items-center gap-2"><span style={{ color: cor }}><Icone nome={chaveForma(item.nome)} /></span>{item.nome}</span>
                <span>{reais(item.valor)}</span>
              </div>
            ))}
          </div>
        ) : null}
        <div className="mt-3 flex items-start gap-2 rounded-xl border px-3 py-2.5 font-sans text-[11px] leading-snug text-[#5c3d45]" style={{ borderColor: borda }}>
          <span className="mt-0.5 shrink-0" style={{ color: cor }}><Icone nome="info" /></span>
          <span>Este comprovante não substitui a emissão de Nota Fiscal (NFS-e) ou Cupom Fiscal (NFC-e).</span>
        </div>
        <p className="mt-4 text-center text-[26px] leading-tight" style={{ color: cor, fontFamily: '"Segoe Script", "Brush Script MT", "URW Chancery L", cursive' }}>Obrigado pela preferência!</p>
        <div className="mt-2 flex items-center gap-3 px-6" style={{ color: cor }}>
          <span className="h-px flex-1" style={{ background: cor }} />
          <Tesoura tamanho={22} />
          <span className="h-px flex-1" style={{ background: cor }} />
        </div>
      </div>
      <svg viewBox="0 0 600 70" preserveAspectRatio="none" className="block h-14 w-full" aria-hidden>
        <path fill={cor} d="M0 38c70-26 130-28 200-6s150 30 210 6 130-28 190-8v40H0z" />
        <path fill={cor} opacity="0.55" d="M0 50c90-18 150-14 230 2s170 14 250-8 80-14 120-6v32H0z" />
      </svg>
    </article>
  );
}
