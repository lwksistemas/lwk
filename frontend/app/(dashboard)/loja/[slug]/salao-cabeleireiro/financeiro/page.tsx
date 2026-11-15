"use client";

import { useEffect, useState } from "react";
import { SalaoAPI, type CaixaSalao } from "@/lib/salao-api";

function periodo(modo: "hoje" | "mes") {
  const agora = new Date();
  const dois = (valor: number) => String(valor).padStart(2, "0");
  const texto = (data: Date) => `${data.getFullYear()}-${dois(data.getMonth() + 1)}-${dois(data.getDate())}T${dois(data.getHours())}:${dois(data.getMinutes())}:00`;
  if (modo === "hoje") {
    const inicio = new Date(agora.getFullYear(), agora.getMonth(), agora.getDate());
    const fim = new Date(inicio);
    fim.setDate(fim.getDate() + 1);
    return { inicio: texto(inicio), fim: texto(fim) };
  }
  const inicio = new Date(agora.getFullYear(), agora.getMonth(), 1);
  const fim = new Date(agora.getFullYear(), agora.getMonth() + 1, 1);
  return { inicio: texto(inicio), fim: texto(fim) };
}

export default function FinanceiroSalaoPage() {
  const [modo, setModo] = useState<"hoje" | "mes">("hoje");
  const [caixa, setCaixa] = useState<CaixaSalao | null>(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    const faixa = periodo(modo);
    SalaoAPI.caixa(faixa.inicio, faixa.fim)
      .then(setCaixa)
      .catch((exc: Error) => setErro(exc.message));
  }, [modo]);

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold sm:text-3xl">Caixa</h1>
          <p className="text-sm text-[#8a6e74]">Recebimentos de atendimentos concluídos. O preço do serviço só entra depois de receber.</p>
        </div>
        <div className="flex gap-2">
          <button type="button" className={`rounded-full px-3 py-1.5 text-sm ${modo === "hoje" ? "bg-[#7a3044] text-white" : "border"}`} onClick={() => setModo("hoje")}>Hoje</button>
          <button type="button" className={`rounded-full px-3 py-1.5 text-sm ${modo === "mes" ? "bg-[#7a3044] text-white" : "border"}`} onClick={() => setModo("mes")}>Este mês</button>
        </div>
      </div>
      {erro ? <p className="mb-3 text-sm text-red-700">{erro}</p> : null}
      <div className="mb-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <article className="rounded-3xl border border-[#f0e4e6] bg-white p-4">
          <p className="text-sm text-[#8a6e74]">Recebido</p>
          <p className="mt-1 text-2xl font-semibold text-[#7a3044]">{caixa?.total || "R$ 0,00"}</p>
        </article>
        {(caixa?.por_forma || []).map((item) => (
          <article key={item.forma} className="rounded-3xl border border-[#f0e4e6] bg-white p-4">
            <p className="text-sm text-[#8a6e74]">{item.nome}</p>
            <p className="mt-1 text-2xl font-semibold">{item.total}</p>
          </article>
        ))}
      </div>
      <div className="grid gap-3 lg:grid-cols-[minmax(0,1.4fr)_minmax(16rem,0.7fr)]">
        <section className="rounded-3xl border border-[#f0e4e6] bg-white p-4">
          <h2 className="mb-2 text-sm font-medium">Movimentação</h2>
          {(caixa?.recebimentos.length || 0) === 0 ? <p className="text-sm text-[#8a6e74]">Nenhum recebimento neste período.</p> : null}
          <ul>
            {(caixa?.recebimentos || []).map((item) => (
              <li key={item.id} className="grid gap-1 border-t border-[#f0e4e6] py-2 text-sm sm:grid-cols-[88px_minmax(0,1fr)_auto]">
                <span className="text-[#8a6e74]">{item.quando}</span>
                <span className="min-w-0">
                  <span className="block truncate">{item.cliente} · {item.servico}</span>
                  <small className="text-[#8a6e74]">{item.profissional} · {item.forma_label}{item.desconto !== "R$ 0,00" ? ` · desconto ${item.desconto}` : ""}</small>
                </span>
                <span>{item.valor}</span>
              </li>
            ))}
          </ul>
        </section>
        <section className="rounded-3xl border border-[#f0e4e6] bg-white p-4">
          <h2 className="mb-2 text-sm font-medium">Comissões</h2>
          {(caixa?.comissoes.length || 0) === 0 ? <p className="text-sm text-[#8a6e74]">Nenhuma comissão neste período.</p> : null}
          {(caixa?.comissoes || []).map((item) => (
            <div key={item.nome} className="flex items-center justify-between gap-2 border-t border-[#f0e4e6] py-2 text-sm">
              <span className="min-w-0 truncate">{item.nome}<small className="block text-[#8a6e74]">{item.quantidade} · recebido {item.recebido}</small></span>
              <span>{item.comissao}</span>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}
