"use client";

import { useEffect, useState } from "react";
import { ImportarXmlModal } from "@/components/salao/ImportarXmlModal";
import { SalaoAPI, type ProdutoSalao } from "@/lib/salao-api";

const VAZIO = { nome: "", codigo_barras: "", preco: "", saldo: "", comissao_percentual: "" };

function reais(valor: string) {
  const numero = Number(valor);
  return Number.isFinite(numero) ? numero.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) : valor;
}

export default function EstoqueSalaoPage() {
  const [produtos, setProdutos] = useState<ProdutoSalao[]>([]);
  const [form, setForm] = useState<Record<string, string> | null>(null);
  const [editando, setEditando] = useState<number | null>(null);
  const [erro, setErro] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [importar, setImportar] = useState(false);

  function carregar() {
    return SalaoAPI.produtos().then(setProdutos).catch((exc: Error) => setErro(exc.message));
  }

  useEffect(() => { carregar(); }, []);

  function abrir(produto?: ProdutoSalao) {
    setErro("");
    setEditando(produto?.id ?? null);
    setForm(produto ? {
      nome: produto.nome,
      codigo_barras: produto.codigo_barras,
      preco: produto.preco,
      saldo: String(produto.saldo),
      comissao_percentual: produto.comissao_percentual,
    } : { ...VAZIO });
  }

  async function gravar() {
    if (!form || salvando) return;
    setErro("");
    setSalvando(true);
    try {
      await SalaoAPI.salvarProduto({
        nome: form.nome,
        codigo_barras: form.codigo_barras,
        preco: form.preco || "0",
        saldo: Number(form.saldo || 0),
        comissao_percentual: form.comissao_percentual || "0",
      }, editando ?? undefined);
      setForm(null);
      await carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível gravar o produto.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Estoque</h1>
          <p className="text-sm text-[#8a6e74]">O saldo baixa só quando o caixa confirma a venda.</p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={() => setImportar(true)} className="rounded-full border border-[#eadfe2] bg-white px-4 py-2 text-sm">Importar XML</button>
          <button type="button" onClick={() => abrir()} className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white">Adicionar produto</button>
        </div>
      </div>
      {erro && !form ? <p className="mb-3 text-sm text-red-700">{erro}</p> : null}
      <div className="grid gap-3 md:grid-cols-2">
        {produtos.length === 0 ? <p className="text-sm text-[#8a6e74]">Nenhum produto cadastrado.</p> : null}
        {produtos.map((produto) => (
          <button key={produto.id} type="button" onClick={() => abrir(produto)} className="rounded-3xl bg-white p-4 text-left">
            <span className="block font-medium">{produto.nome}</span>
            <span className="mt-1 block text-sm text-[#8a6e74]">{reais(produto.preco)} · saldo {produto.saldo}</span>
            {produto.codigo_barras ? <span className="block text-sm text-[#8a6e74]">Código {produto.codigo_barras}</span> : null}
          </button>
        ))}
      </div>
      <ImportarXmlModal aberto={importar} onFechar={() => setImportar(false)} onImportou={() => { carregar(); }} />
      {form ? (
        <div className="fixed inset-0 z-40 grid place-items-center bg-black/40 p-4" role="dialog" aria-modal="true">
          <div className="w-full max-w-md rounded-3xl bg-white p-5">
            <h2 className="text-lg font-semibold">{editando ? "Editar produto" : "Adicionar produto"}</h2>
            {erro ? <p className="mt-2 text-sm text-red-700">{erro}</p> : null}
            <label className="mt-3 block text-sm">Nome<input value={form.nome} onChange={(evento) => setForm({ ...form, nome: evento.target.value })} className="mt-1 w-full rounded-xl border border-[#eadfe2] px-3 py-2" /></label>
            <label className="mt-3 block text-sm">Código de barras<input value={form.codigo_barras} onChange={(evento) => setForm({ ...form, codigo_barras: evento.target.value })} className="mt-1 w-full rounded-xl border border-[#eadfe2] px-3 py-2" /></label>
            <div className="mt-3 grid grid-cols-3 gap-2">
              <label className="text-sm">Preço<input value={form.preco} onChange={(evento) => setForm({ ...form, preco: evento.target.value })} className="mt-1 w-full rounded-xl border border-[#eadfe2] px-3 py-2" /></label>
              <label className="text-sm">Saldo<input value={form.saldo} onChange={(evento) => setForm({ ...form, saldo: evento.target.value })} className="mt-1 w-full rounded-xl border border-[#eadfe2] px-3 py-2" /></label>
              <label className="text-sm">Comissão %<input value={form.comissao_percentual} onChange={(evento) => setForm({ ...form, comissao_percentual: evento.target.value })} className="mt-1 w-full rounded-xl border border-[#eadfe2] px-3 py-2" /></label>
            </div>
            <div className="mt-4 flex gap-2">
              <button type="button" onClick={() => { setForm(null); setErro(""); }} className="rounded-full border px-4 py-2 text-sm">Cancelar</button>
              <button type="button" onClick={gravar} disabled={salvando} className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white disabled:opacity-60">{salvando ? "Gravando…" : "Gravar"}</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
