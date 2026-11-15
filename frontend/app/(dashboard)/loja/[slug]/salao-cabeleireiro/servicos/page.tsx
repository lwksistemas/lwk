"use client";

import { useEffect, useState } from "react";
import { SalaoAPI, type ServicoSalao } from "@/lib/salao-api";

const CAMPO = "w-full rounded-lg border px-2 py-2";
const VAZIO = { nome: "", categoria: "Corte", duracao_minutos: "60", preco: "", descricao: "" };

export default function ServicosSalaoPage() {
  const [lista, setLista] = useState<ServicoSalao[]>([]);
  const [escolhido, setEscolhido] = useState<number | null>(null);
  const [form, setForm] = useState(VAZIO);
  const [aberto, setAberto] = useState(false);
  const [erro, setErro] = useState("");

  function carregar() {
    SalaoAPI.servicos().then(setLista).catch((exc: Error) => setErro(exc.message));
  }
  useEffect(() => { carregar(); }, []);

  function novo() {
    setEscolhido(null);
    setForm(VAZIO);
    setErro("");
    setAberto(true);
  }

  function abrir(item: ServicoSalao) {
    setEscolhido(item.id);
    setErro("");
    setForm({
      nome: item.nome,
      categoria: item.categoria,
      duracao_minutos: String(item.duracao_minutos),
      preco: String(item.preco),
      descricao: item.descricao || "",
    });
    setAberto(true);
  }

  function fechar() {
    setAberto(false);
    setEscolhido(null);
    setForm(VAZIO);
    setErro("");
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
      fechar();
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível salvar.");
    }
  }

  async function arquivar() {
    if (!escolhido) return;
    try {
      await SalaoAPI.arquivar(`/servicos/${escolhido}/`);
      fechar();
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível arquivar.");
    }
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold sm:text-3xl">Serviços</h1>
          <p className="text-sm text-[#8a6e74]">A duração define o tamanho do horário na agenda.</p>
        </div>
        <button type="button" className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" onClick={novo}>Adicionar serviço</button>
      </div>
      {!aberto && erro ? <p className="mb-2 text-sm text-red-700">{erro}</p> : null}
      {lista.length === 0 ? <p className="text-sm text-[#8a6e74]">Nenhum serviço registrado.</p> : null}
      <ul className="grid gap-3 md:grid-cols-2">
        {lista.map((item) => (
          <li key={item.id}>
            <button type="button" className="flex h-full w-full items-start justify-between gap-3 rounded-3xl border border-[#f0e4e6] bg-white px-4 py-3 text-left hover:bg-[#fbf6f4]" onClick={() => abrir(item)}>
              <span>
                <span className="block font-medium">{item.nome}</span>
                <span className="mt-0.5 block text-sm text-[#8a6e74]">{item.categoria} · {item.duracao_minutos} min</span>
              </span>
              <span className="shrink-0 text-sm">R$ {item.preco}</span>
            </button>
          </li>
        ))}
      </ul>
      {aberto ? (
        <div className="fixed inset-0 z-40 grid place-items-center bg-black/40 p-4" role="dialog" aria-modal="true" aria-labelledby="servico-formulario" onClick={(evento) => { if (evento.target === evento.currentTarget) fechar(); }}>
          <form className="max-h-[90vh] w-full max-w-lg overflow-auto rounded-3xl bg-white p-5" onSubmit={salvar}>
            <h2 id="servico-formulario" className="mb-3 text-lg font-semibold">{escolhido ? "Editar serviço" : "Adicionar serviço"}</h2>
            {erro ? <p className="mb-2 text-sm text-red-700">{erro}</p> : null}
            <div className="grid gap-2 sm:grid-cols-2">
              <label className="text-sm sm:col-span-2">Nome
                <input className={`mt-1 ${CAMPO}`} value={form.nome} onChange={(evento) => setForm({ ...form, nome: evento.target.value })} required />
              </label>
              <label className="text-sm">Categoria
                <input className={`mt-1 ${CAMPO}`} value={form.categoria} onChange={(evento) => setForm({ ...form, categoria: evento.target.value })} />
              </label>
              <label className="text-sm">Minutos
                <input className={`mt-1 ${CAMPO}`} inputMode="numeric" value={form.duracao_minutos} onChange={(evento) => setForm({ ...form, duracao_minutos: evento.target.value })} required />
              </label>
              <label className="text-sm">Preço
                <input className={`mt-1 ${CAMPO}`} inputMode="decimal" value={form.preco} onChange={(evento) => setForm({ ...form, preco: evento.target.value })} required />
              </label>
              <label className="text-sm sm:col-span-2">Descrição
                <textarea className={`mt-1 ${CAMPO}`} value={form.descricao} onChange={(evento) => setForm({ ...form, descricao: evento.target.value })} />
              </label>
            </div>
            <div className="mt-4 flex flex-wrap items-center justify-end gap-2">
              {escolhido ? <button type="button" className="mr-auto rounded-full border px-4 py-2 text-sm" onClick={arquivar}>Arquivar</button> : null}
              <button type="button" className="rounded-full border px-4 py-2 text-sm" onClick={fechar}>Cancelar</button>
              <button className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" type="submit">Salvar</button>
            </div>
          </form>
        </div>
      ) : null}
    </div>
  );
}
