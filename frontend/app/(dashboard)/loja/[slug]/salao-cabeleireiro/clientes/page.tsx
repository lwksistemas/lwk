"use client";

import { useEffect, useState } from "react";
import { SalaoAPI, type ClienteSalao } from "@/lib/salao-api";

export default function ClientesSalaoPage() {
  const [lista, setLista] = useState<ClienteSalao[]>([]);
  const [erro, setErro] = useState("");
  const [form, setForm] = useState({ nome: "", telefone: "", email: "", data_nascimento: "" });

  function carregar() {
    SalaoAPI.clientes().then(setLista).catch((exc: Error) => setErro(exc.message));
  }
  useEffect(() => { carregar(); }, []);

  async function salvar(evento: React.FormEvent) {
    evento.preventDefault();
    setErro("");
    try {
      await SalaoAPI.salvarCliente({ ...form, email: form.email || null, data_nascimento: form.data_nascimento || null });
      setForm({ nome: "", telefone: "", email: "", data_nascimento: "" });
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível salvar.");
    }
  }

  return (
    <div>
      <h1 className="mb-3 text-3xl font-semibold">Clientes</h1>
      {erro ? <p className="mb-2 text-sm text-red-700">{erro}</p> : null}
      <form className="mb-4 grid gap-2 rounded-2xl border border-[#f0e4e6] bg-white p-4 md:grid-cols-4" onSubmit={salvar}>
        <input className="rounded-lg border px-2 py-2" placeholder="Nome" value={form.nome} onChange={(evento) => setForm({ ...form, nome: evento.target.value })} />
        <input className="rounded-lg border px-2 py-2" placeholder="Telefone" value={form.telefone} onChange={(evento) => setForm({ ...form, telefone: evento.target.value })} />
        <input className="rounded-lg border px-2 py-2" placeholder="E-mail" value={form.email} onChange={(evento) => setForm({ ...form, email: evento.target.value })} />
        <input type="date" className="rounded-lg border px-2 py-2" value={form.data_nascimento} onChange={(evento) => setForm({ ...form, data_nascimento: evento.target.value })} />
        <button className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white md:col-span-4" type="submit">Adicionar cliente</button>
      </form>
      <ul className="rounded-2xl border border-[#f0e4e6] bg-white">
        {lista.map((item) => (
          <li key={item.id} className="flex justify-between border-t border-[#f0e4e6] px-4 py-2 text-sm">
            <span>{item.nome}</span><span className="text-[#8a6e74]">{item.telefone}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
