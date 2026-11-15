"use client";

import { useEffect, useState } from "react";
import { SalaoAPI, type AgendamentoSalao } from "@/lib/salao-api";

function paraApi(data: Date) {
  const dois = (valor: number) => String(valor).padStart(2, "0");
  return `${data.getFullYear()}-${dois(data.getMonth() + 1)}-${dois(data.getDate())}T${dois(data.getHours())}:${dois(data.getMinutes())}:00`;
}

export default function FinanceiroSalaoPage() {
  const [lista, setLista] = useState<AgendamentoSalao[]>([]);
  const [erro, setErro] = useState("");

  useEffect(() => {
    const agora = new Date();
    const inicio = new Date(agora.getFullYear(), agora.getMonth(), 1);
    const fim = new Date(agora.getFullYear(), agora.getMonth() + 1, 1);
    SalaoAPI.agenda(paraApi(inicio), paraApi(fim))
      .then((itens) => setLista(itens.filter((item) => item.status === "COMPLETED")))
      .catch((exc: Error) => setErro(exc.message));
  }, []);

  const total = lista.reduce((soma, item) => soma + Number(item.preco), 0);

  return (
    <div>
      <h1 className="mb-1 text-3xl font-semibold">Financeiro</h1>
      <p className="mb-3 text-sm text-[#8a6e74]">Serviços concluídos neste mês. Total {total.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}.</p>
      {erro ? <p className="text-sm text-red-700">{erro}</p> : null}
      <ul className="rounded-2xl border border-[#f0e4e6] bg-white">
        {lista.map((item) => (
          <li key={item.id} className="grid grid-cols-[120px_1fr_auto] gap-2 border-t border-[#f0e4e6] px-4 py-2 text-sm">
            <span>{new Date(item.inicio).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}</span>
            <span>{item.cliente_nome} · {item.servico_nome}<small className="block text-[#8a6e74]">{item.profissional_nome}</small></span>
            <span>R$ {item.preco}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
