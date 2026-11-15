"use client";

import { useEffect, useState } from "react";
import { SalaoAPI, type ServicoSalao } from "@/lib/salao-api";

const CAMPO = "w-full rounded-lg border px-2 py-2";
const VAZIO = { nome: "", categoria: "Corte", duracao_minutos: "60", preco: "", descricao: "" };

export default function ServicosSalaoPage() {
  const [lista, setLista] = useState<ServicoSalao[]>([]);
  const [escolhido, setEscolhido] = useState<number | null>(null);
  const [form, setForm] = useState(VAZIO);
  const [erro, setErro] = useState("");

  function carregar() {
    SalaoAPI.servicos().then(setLista).catch((exc: Error) => setErro(exc.message));
  }
  useEffect(() => { carregar(); }, []);

  function abrir(item: ServicoSalao) {
    setEscolhido(item.id);
    setForm({
      nome: item.nome,
      categoria: item.categoria,
      duracao_minutos: String(item.duracao_minutos),
      preco: String(item.preco),
      descricao: item.descricao || "",
    });
  }

  async function salvar(evento: React.FormEvent) {
    evento.preventDefault();
    setErro("");
    try {
      await SalaoAPI.salvarServico({
        ...form,
        duracao_minutos: Number(form.duracao_minutos),
        preco: form.preco.replace(",", "."),
        descricao: form.descricao,
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
      await SalaoAPI.arquivar(`/servicos/${escolhido}/`);
      setEscolhido(null);
      setForm(VAZIO);
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível arquivar.");
    }
  }

  return (
    <div>
      <h1 className="mb-1 text-2xl font-semibold sm:text-3xl">Serviços</h1>
      <p className="mb-4 text-sm text-[#8a6e74]">A duração define o tamanho do horário na agenda.</p>
      {erro ? <p className="mb-2 text-sm text-red-700">{erro}</p> : null}
      {lista.length === 0 ? <p className="mb-3 text-sm text-[#8a6e74]">Nenhum serviço registrado.</p> : null}
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <ul className="rounded-3xl border border-[#f0e4e6] bg-white">
          {lista.map((item) => (
            <li key={item.id}>
              <button type="button" className={`flex w-full justify-between gap-3 px-4 py-3 text-left text-sm ${escolhido === item.id ? "bg-[#f6ecee]" : ""}`} onClick={() => abrir(item)}>
                <span>{item.nome}<small className="block text-[#8a6e74]">{item.categoria} · {item.duracao_minutos} min</small></span>
                <span>R$ {item.preco}</span>
              </button>
            </li>
          ))}
        </ul>
        <form className="grid content-start gap-2 rounded-3xl border border-[#f0e4e6] bg-white p-4 sm:grid-cols-2" onSubmit={salvar}>
          <input className={CAMPO} placeholder="Nome" value={form.nome} onChange={(evento) => setForm({ ...form, nome: evento.target.value })} required />
          <input className={CAMPO} placeholder="Categoria" value={form.categoria} onChange={(evento) => setForm({ ...form, categoria: evento.target.value })} />
          <input className={CAMPO} placeholder="Minutos" value={form.duracao_minutos} onChange={(evento) => setForm({ ...form, duracao_minutos: evento.target.value })} required />
          <input className={CAMPO} placeholder="Preço" value={form.preco} onChange={(evento) => setForm({ ...form, preco: evento.target.value })} required />
          <textarea className={`${CAMPO} sm:col-span-2`} placeholder="Descrição" value={form.descricao} onChange={(evento) => setForm({ ...form, descricao: evento.target.value })} />
          <div className="flex flex-wrap gap-2 sm:col-span-2">
            <button className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" type="submit">{escolhido ? "Salvar" : "Adicionar serviço"}</button>
            {escolhido ? <button type="button" className="rounded-full border px-4 py-2 text-sm" onClick={arquivar}>Arquivar</button> : null}
          </div>
        </form>
      </div>
    </div>
  );
}
