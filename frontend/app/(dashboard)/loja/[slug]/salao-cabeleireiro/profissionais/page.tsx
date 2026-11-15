"use client";

import { useEffect, useState } from "react";
import { SalaoAPI, type ProfissionalSalao } from "@/lib/salao-api";

export default function ProfissionaisSalaoPage() {
  const [lista, setLista] = useState<ProfissionalSalao[]>([]);
  const [erro, setErro] = useState("");
  const [form, setForm] = useState({ nome: "", telefone: "", especialidade: "Cabeleireiro", comissao_percentual: "0" });

  function carregar() {
    SalaoAPI.profissionais().then(setLista).catch((exc: Error) => setErro(exc.message));
  }
  useEffect(() => { carregar(); }, []);

  async function salvar(evento: React.FormEvent) {
    evento.preventDefault();
    try {
      await SalaoAPI.salvarProfissional({ ...form, comissao_percentual: form.comissao_percentual.replace(",", ".") });
      setForm({ nome: "", telefone: "", especialidade: "Cabeleireiro", comissao_percentual: "0" });
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível salvar.");
    }
  }

  return (
    <div>
      <h1 className="mb-3 text-3xl font-semibold">Profissionais</h1>
      <p className="mb-3 text-sm text-[#8a6e74]">Cada profissional entra na coluna do dia e recebe horário de segunda a sábado, das 9h às 19h.</p>
      {erro ? <p className="mb-2 text-sm text-red-700">{erro}</p> : null}
      <form className="mb-4 grid gap-2 rounded-2xl border border-[#f0e4e6] bg-white p-4 md:grid-cols-4" onSubmit={salvar}>
        <input className="rounded-lg border px-2 py-2" placeholder="Nome" value={form.nome} onChange={(evento) => setForm({ ...form, nome: evento.target.value })} />
        <input className="rounded-lg border px-2 py-2" placeholder="Telefone" value={form.telefone} onChange={(evento) => setForm({ ...form, telefone: evento.target.value })} />
        <input className="rounded-lg border px-2 py-2" placeholder="Função" value={form.especialidade} onChange={(evento) => setForm({ ...form, especialidade: evento.target.value })} />
        <input className="rounded-lg border px-2 py-2" placeholder="Comissão %" value={form.comissao_percentual} onChange={(evento) => setForm({ ...form, comissao_percentual: evento.target.value })} />
        <button className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white md:col-span-4" type="submit">Adicionar profissional</button>
      </form>
      <ul className="rounded-2xl border border-[#f0e4e6] bg-white">
        {lista.map((item) => (
          <li key={item.id} className="flex justify-between border-t border-[#f0e4e6] px-4 py-2 text-sm">
            <span>{item.nome}<small className="block text-[#8a6e74]">{item.especialidade}</small></span>
            <span>{item.comissao_percentual}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
