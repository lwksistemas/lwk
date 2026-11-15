"use client";

import { useEffect, useState } from "react";
import { SalaoAPI, type ServicoSalao } from "@/lib/salao-api";

export default function ServicosSalaoPage() {
  const [lista, setLista] = useState<ServicoSalao[]>([]);
  const [erro, setErro] = useState("");
  const [form, setForm] = useState({ nome: "", categoria: "Corte", duracao_minutos: "60", preco: "" });

  function carregar() {
    SalaoAPI.servicos().then(setLista).catch((exc: Error) => setErro(exc.message));
  }
  useEffect(() => { carregar(); }, []);

  async function salvar(evento: React.FormEvent) {
    evento.preventDefault();
    try {
      await SalaoAPI.salvarServico({ ...form, duracao_minutos: Number(form.duracao_minutos), preco: form.preco.replace(",", ".") });
      setForm({ nome: "", categoria: "Corte", duracao_minutos: "60", preco: "" });
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível salvar.");
    }
  }

  return (
    <div>
      <h1 className="mb-3 text-3xl font-semibold">Serviços</h1>
      <p className="mb-3 text-sm text-[#8a6e74]">A duração do serviço define o tamanho do horário na agenda, como o procedimento faz na clínica.</p>
      {erro ? <p className="mb-2 text-sm text-red-700">{erro}</p> : null}
      <form className="mb-4 grid gap-2 rounded-2xl border border-[#f0e4e6] bg-white p-4 md:grid-cols-4" onSubmit={salvar}>
        <input className="rounded-lg border px-2 py-2" placeholder="Nome" value={form.nome} onChange={(evento) => setForm({ ...form, nome: evento.target.value })} />
        <input className="rounded-lg border px-2 py-2" placeholder="Categoria" value={form.categoria} onChange={(evento) => setForm({ ...form, categoria: evento.target.value })} />
        <input className="rounded-lg border px-2 py-2" placeholder="Minutos" value={form.duracao_minutos} onChange={(evento) => setForm({ ...form, duracao_minutos: evento.target.value })} />
        <input className="rounded-lg border px-2 py-2" placeholder="Preço" value={form.preco} onChange={(evento) => setForm({ ...form, preco: evento.target.value })} />
        <button className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white md:col-span-4" type="submit">Adicionar serviço</button>
      </form>
      <ul className="rounded-2xl border border-[#f0e4e6] bg-white">
        {lista.map((item) => (
          <li key={item.id} className="flex justify-between border-t border-[#f0e4e6] px-4 py-2 text-sm">
            <span>{item.nome}<small className="block text-[#8a6e74]">{item.categoria} · {item.duracao_minutos} min</small></span>
            <span>R$ {item.preco}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
