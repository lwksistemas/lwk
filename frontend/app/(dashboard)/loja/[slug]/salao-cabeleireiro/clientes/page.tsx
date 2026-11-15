"use client";

import { useEffect, useState } from "react";
import { SalaoAPI, type ClienteSalao } from "@/lib/salao-api";

const CAMPO = "w-full rounded-lg border px-2 py-2";
const VAZIO = { nome: "", telefone: "", email: "", data_nascimento: "" };

export default function ClientesSalaoPage() {
  const [lista, setLista] = useState<ClienteSalao[]>([]);
  const [escolhido, setEscolhido] = useState<number | null>(null);
  const [form, setForm] = useState(VAZIO);
  const [erro, setErro] = useState("");

  function carregar() {
    SalaoAPI.clientes().then(setLista).catch((exc: Error) => setErro(exc.message));
  }
  useEffect(() => { carregar(); }, []);

  function abrir(item: ClienteSalao) {
    setEscolhido(item.id);
    setForm({
      nome: item.nome,
      telefone: item.telefone,
      email: item.email || "",
      data_nascimento: item.data_nascimento || "",
    });
  }

  async function salvar(evento: React.FormEvent) {
    evento.preventDefault();
    setErro("");
    try {
      await SalaoAPI.salvarCliente({
        ...form,
        email: form.email || null,
        data_nascimento: form.data_nascimento || null,
      }, escolhido ?? undefined);
      setEscolhido(null);
      setForm(VAZIO);
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível salvar.");
    }
  }

  async function arquivar() {
    if (!escolhido) return;
    try {
      await SalaoAPI.arquivar(`/clientes/${escolhido}/`);
      setEscolhido(null);
      setForm(VAZIO);
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível arquivar.");
    }
  }

  return (
    <div>
      <h1 className="mb-1 text-2xl font-semibold sm:text-3xl">Clientes</h1>
      <p className="mb-4 text-sm text-[#8a6e74]">O aniversário entra no painel do mês quando a data está preenchida.</p>
      {erro ? <p className="mb-2 text-sm text-red-700">{erro}</p> : null}
      {lista.length === 0 ? <p className="mb-3 text-sm text-[#8a6e74]">Nenhum cliente cadastrado.</p> : null}
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <ul className="rounded-3xl border border-[#f0e4e6] bg-white">
          {lista.map((item) => (
            <li key={item.id}>
              <button type="button" className={`flex w-full justify-between gap-3 px-4 py-3 text-left text-sm ${escolhido === item.id ? "bg-[#f6ecee]" : ""}`} onClick={() => abrir(item)}>
                <span>{item.nome}<small className="block text-[#8a6e74]">{item.email || "Sem e-mail"}</small></span>
                <span className="text-[#8a6e74]">{item.telefone}</span>
              </button>
            </li>
          ))}
        </ul>
        <form className="grid gap-2 rounded-3xl border border-[#f0e4e6] bg-white p-4 sm:grid-cols-2" onSubmit={salvar}>
          <input className={CAMPO} placeholder="Nome" value={form.nome} onChange={(evento) => setForm({ ...form, nome: evento.target.value })} required />
          <input className={CAMPO} placeholder="Telefone" value={form.telefone} onChange={(evento) => setForm({ ...form, telefone: evento.target.value })} required />
          <input className={CAMPO} placeholder="E-mail" value={form.email} onChange={(evento) => setForm({ ...form, email: evento.target.value })} />
          <input type="date" className={CAMPO} value={form.data_nascimento} onChange={(evento) => setForm({ ...form, data_nascimento: evento.target.value })} />
          <div className="flex flex-wrap gap-2 sm:col-span-2">
            <button className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" type="submit">{escolhido ? "Salvar" : "Adicionar cliente"}</button>
            {escolhido ? <button type="button" className="rounded-full border px-4 py-2 text-sm" onClick={arquivar}>Arquivar</button> : null}
            {escolhido ? <button type="button" className="text-sm text-[#8a6e74]" onClick={() => { setEscolhido(null); setForm(VAZIO); }}>Cancelar</button> : null}
          </div>
        </form>
      </div>
    </div>
  );
}
