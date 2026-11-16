"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Banknote, Check, CreditCard, Layers, Minus, Plus, QrCode, Scissors, ShoppingBag, Trash2, UserRound } from "lucide-react";
import { SalaoAPI, type AgendamentoSalao, type ClienteSalao, type LocalRecebimentoSalao, type PapelSalao, type ProdutoSalao } from "@/lib/salao-api";

type ItemCarrinho = { produto: number; nome: string; preco: string; saldo: number; quantidade: number };
type Linha = { id: string; forma: string; valor: string };
type FormaRapida = "dinheiro" | "pix" | "debito" | "credito" | "multiplas";

const FORMAS: { id: FormaRapida; nome: string; icone: typeof Banknote }[] = [
  { id: "dinheiro", nome: "Dinheiro", icone: Banknote },
  { id: "pix", nome: "Pix", icone: QrCode },
  { id: "debito", nome: "Débito", icone: CreditCard },
  { id: "credito", nome: "Crédito", icone: CreditCard },
  { id: "multiplas", nome: "Múltiplas", icone: Layers },
];

const ROTULO: Record<string, string> = { dinheiro: "Dinheiro", pix: "Pix", debito: "Débito", credito: "Crédito" };

function lerReais(texto: string) {
  const numero = Number(String(texto).replace(",", "."));
  return Number.isFinite(numero) ? Math.round(numero * 100) / 100 : 0;
}

function reais(valor: number) {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function diaIso(data: Date) {
  const mes = String(data.getMonth() + 1).padStart(2, "0");
  const dia = String(data.getDate()).padStart(2, "0");
  return `${data.getFullYear()}-${mes}-${dia}`;
}

function hora(valor: string) {
  return new Date(valor).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

function telefoneLegivel(valor: string) {
  const digitos = (valor || "").replace(/\D/g, "");
  if (digitos.length === 11) return `(${digitos.slice(0, 2)}) ${digitos.slice(2, 7)}-${digitos.slice(7)}`;
  if (digitos.length === 10) return `(${digitos.slice(0, 2)}) ${digitos.slice(2, 6)}-${digitos.slice(6)}`;
  return valor;
}

function iniciais(nome: string) {
  return nome.split(" ").filter(Boolean).slice(0, 2).map((parte) => parte[0]?.toUpperCase()).join("");
}

export default function CaixaPdvPage() {
  const slug = (useParams()?.slug as string) ?? "";
  const [aba, setAba] = useState<"atendimentos" | "produtos">("atendimentos");
  const [busca, setBusca] = useState("");
  const [fila, setFila] = useState<AgendamentoSalao[]>([]);
  const [clientes, setClientes] = useState<ClienteSalao[]>([]);
  const [produtos, setProdutos] = useState<ProdutoSalao[]>([]);
  const [carrinho, setCarrinho] = useState<ItemCarrinho[]>([]);
  const [escolhido, setEscolhido] = useState<number | null>(null);
  const [desconto, setDesconto] = useState("");
  const [formaRapida, setFormaRapida] = useState<FormaRapida>("dinheiro");
  const [linhas, setLinhas] = useState<Linha[]>([{ id: "1", forma: "dinheiro", valor: "" }]);
  const [entregue, setEntregue] = useState("");
  const [local, setLocal] = useState<LocalRecebimentoSalao>("caixa");
  const [papel, setPapel] = useState<PapelSalao | "">("");
  const [operador, setOperador] = useState("");
  const [erro, setErro] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [sucesso, setSucesso] = useState<{ cliente: string; numero: number; valor: string; forma: string; quando: string } | null>(null);
  const [documentos, setDocumentos] = useState({ comprovante: true, nfse: true, nfce: true });

  function carregar() {
    const fim = new Date();
    fim.setHours(23, 59, 0, 0);
    const inicio = new Date(fim);
    inicio.setDate(inicio.getDate() - 7);
    inicio.setHours(0, 0, 0, 0);
    return SalaoAPI.agenda(`${diaIso(inicio)}T00:00:00`, `${diaIso(fim)}T23:59:00`)
      .then((lista) => {
        const pendentes = lista.filter((item) => item.status === "COMPLETED" && !item.recebido);
        setFila(pendentes);
        setEscolhido((atual) => (atual != null && pendentes.some((item) => item.id === atual) ? atual : pendentes[0]?.id ?? null));
      })
      .catch((exc: Error) => setErro(exc.message));
  }

  useEffect(() => {
    SalaoAPI.config().then((dados) => {
      setLocal(dados.local_recebimento || "caixa");
      setOperador(dados.operador_nome || "");
      setPapel(dados.papel || "");
    }).catch(() => undefined);
    SalaoAPI.produtos().then(setProdutos).catch(() => undefined);
    SalaoAPI.clientes().then(setClientes).catch(() => undefined);
    carregar();
  }, []);

  const visiveis = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    if (!termo) return fila;
    return fila.filter((item) => `${item.cliente_nome} ${item.servico_nome} ${item.profissional_nome}`.toLowerCase().includes(termo));
  }, [busca, fila]);

  const produtosVisiveis = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    if (!termo) return produtos;
    return produtos.filter((item) => `${item.nome} ${item.codigo_barras}`.toLowerCase().includes(termo));
  }, [busca, produtos]);

  const atual = fila.find((item) => item.id === escolhido) || null;
  const cliente = clientes.find((item) => item.id === atual?.cliente);
  const preco = atual ? lerReais(atual.preco) : 0;
  const valorDesconto = Math.min(preco, Math.max(0, lerReais(desconto)));
  const totalProdutos = Math.round(carrinho.reduce((acc, item) => acc + lerReais(item.preco) * item.quantidade, 0) * 100) / 100;
  const subtotal = Math.round((preco + totalProdutos) * 100) / 100;
  const total = Math.round((preco - valorDesconto + totalProdutos) * 100) / 100;
  const soma = Math.round(linhas.reduce((acc, linha) => acc + lerReais(linha.valor), 0) * 100) / 100;
  const valorRecebido = entregue === "" ? total : lerReais(entregue);
  const troco = formaRapida === "dinheiro" && valorRecebido > total ? Math.round((valorRecebido - total) * 100) / 100 : 0;
  const hoje = new Date();
  const dataCabecalho = hoje.toLocaleDateString("pt-BR");
  const formaLabel = formaRapida === "multiplas"
    ? linhas.map((linha) => ROTULO[linha.forma] || linha.forma).join(" e ")
    : ROTULO[formaRapida];

  useEffect(() => {
    if (formaRapida === "multiplas") return;
    setLinhas([{ id: "1", forma: formaRapida, valor: total > 0 ? total.toFixed(2) : "" }]);
  }, [total, formaRapida]);

  function escolherForma(proxima: FormaRapida) {
    setFormaRapida(proxima);
    setEntregue("");
    if (proxima === "multiplas") {
      setLinhas([
        { id: "1", forma: "dinheiro", valor: total > 0 ? total.toFixed(2) : "" },
        { id: "2", forma: "pix", valor: "" },
      ]);
    }
  }

  function selecionar(item: AgendamentoSalao) {
    setEscolhido(item.id);
    setDesconto("");
    setEntregue("");
    setSucesso(null);
    setErro("");
  }

  function colocarProduto(produto: ProdutoSalao) {
    const existente = carrinho.find((item) => item.produto === produto.id);
    const proxima = (existente?.quantidade || 0) + 1;
    if (proxima > produto.saldo) {
      setErro(`${produto.nome} tem ${produto.saldo} no estoque.`);
      return;
    }
    setErro("");
    setSucesso(null);
    if (existente) setCarrinho(carrinho.map((item) => item.produto === produto.id ? { ...item, quantidade: proxima } : item));
    else setCarrinho([...carrinho, { produto: produto.id, nome: produto.nome, preco: produto.preco, saldo: produto.saldo, quantidade: 1 }]);
  }

  function mudarQuantidade(produtoId: number, delta: number) {
    setCarrinho(carrinho.flatMap((item) => {
      if (item.produto !== produtoId) return [item];
      const proxima = item.quantidade + delta;
      if (proxima <= 0) return [];
      if (proxima > item.saldo) return [item];
      return [{ ...item, quantidade: proxima }];
    }));
  }

  async function confirmar() {
    if (salvando || (!atual && carrinho.length === 0) || (atual && local === "agenda")) return;
    if (atual && lerReais(desconto) > preco) {
      setErro("O desconto não pode passar do valor do serviço.");
      return;
    }
    if (formaRapida === "multiplas" && total > 0 && Math.abs(soma - total) > 0.009) {
      setErro(`A soma das formas precisa fechar ${reais(total)}.`);
      return;
    }
    setErro("");
    setSalvando(true);
    try {
      const venda = await SalaoAPI.vender({
        agendamento: atual?.id,
        desconto: valorDesconto.toFixed(2),
        origem: "caixa",
        formas: total > 0 ? linhas.filter((linha) => lerReais(linha.valor) > 0).map((linha) => ({ forma: linha.forma, valor: lerReais(linha.valor).toFixed(2) })) : [],
        itens: carrinho.map((item) => ({ produto: item.produto, quantidade: item.quantidade })),
      });
      setSucesso({ cliente: venda.cliente, numero: venda.numero, valor: venda.valor, forma: venda.forma_label, quando: venda.quando });
      setEscolhido(null);
      setCarrinho([]);
      setDesconto("");
      setEntregue("");
      await carregar();
      await SalaoAPI.produtos().then(setProdutos).catch(() => undefined);
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível receber.");
    } finally {
      setSalvando(false);
    }
  }

  const temConteudo = Boolean(atual) || carrinho.length > 0;

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Caixa / PDV</h1>
          <p className="text-sm text-[#8a6e74]">Recebimento de atendimentos e venda de produtos</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="rounded-full bg-[#e7f6ee] px-3 py-1 font-medium text-[#1f8a4c]">Caixa aberto</span>
          <span className="rounded-full bg-white px-3 py-1 text-[#5c3d45]">Operador: {operador || "Caixa"}</span>
          <span className="rounded-full bg-white px-3 py-1 text-[#5c3d45]">Abertura: {dataCabecalho}</span>
          <span className="ml-1 flex items-center gap-2 rounded-full bg-white px-2 py-1 pr-3">
            <span className="grid h-8 w-8 place-items-center rounded-full bg-[#7a3044] text-xs font-semibold text-white">{iniciais(operador || "Caixa")}</span>
            <span className="font-medium">{operador || "Caixa"}</span>
          </span>
        </div>
      </header>

      <div className="grid items-start gap-4 xl:grid-cols-[300px_minmax(0,1fr)_320px]">
        <section className="rounded-3xl bg-white p-4">
          <div className="grid grid-cols-2 gap-2">
            <button type="button" onClick={() => { setAba("atendimentos"); setBusca(""); }} className={`rounded-xl px-3 py-2 text-sm font-medium ${aba === "atendimentos" ? "bg-[#7a3044] text-white" : "bg-[#f6eef0] text-[#5c3d45]"}`}>
              Atendimentos ({fila.length})
            </button>
            <button type="button" onClick={() => { setAba("produtos"); setBusca(""); }} className={`rounded-xl px-3 py-2 text-sm font-medium ${aba === "produtos" ? "bg-[#7a3044] text-white" : "bg-[#f6eef0] text-[#5c3d45]"}`}>
              Venda de produtos
            </button>
          </div>
          <input value={busca} onChange={(evento) => setBusca(evento.target.value)} placeholder={aba === "atendimentos" ? "Buscar cliente ou atendimento..." : "Nome ou código de barras"} className="mt-3 w-full rounded-xl border border-[#eadfe2] px-3 py-2 text-sm" />
          <div className="mt-3 space-y-2">
            {aba === "atendimentos" ? visiveis.map((item) => (
              <button key={item.id} type="button" onClick={() => selecionar(item)} className={`flex w-full items-center justify-between gap-3 rounded-2xl border px-3 py-3 text-left ${escolhido === item.id ? "border-[#f3c3cf] bg-[#fdecef]" : "border-[#f0e4e7]"}`}>
                <span>
                  <span className="block font-medium">{item.cliente_nome}</span>
                  <span className="block text-sm text-[#8a6e74]">{item.servico_nome} · {reais(lerReais(item.preco))}</span>
                </span>
                <span className="text-sm text-[#8a6e74]">{hora(item.inicio)}</span>
              </button>
            )) : produtosVisiveis.map((produto) => (
              <button key={produto.id} type="button" onClick={() => colocarProduto(produto)} className="flex w-full items-center justify-between gap-3 rounded-2xl border border-[#f0e4e7] px-3 py-3 text-left">
                <span>
                  <span className="block font-medium">{produto.nome}</span>
                  <span className="block text-sm text-[#8a6e74]">{reais(lerReais(produto.preco))} · saldo {produto.saldo}</span>
                </span>
                <Plus size={16} className="text-[#7a3044]" />
              </button>
            ))}
            {aba === "atendimentos" && visiveis.length === 0 ? <p className="text-sm text-[#8a6e74]">Nenhum atendimento concluído aguardando pagamento.</p> : null}
            {aba === "produtos" && produtosVisiveis.length === 0 ? <p className="text-sm text-[#8a6e74]">Nenhum produto encontrado.</p> : null}
            {aba === "produtos" && (papel === "administrador" || papel === "autonomo") ? (
              <Link href={`/loja/${slug}/salao-cabeleireiro/estoque`} className="inline-block text-sm text-[#7a3044]">Cadastrar produto</Link>
            ) : null}
          </div>
        </section>

        <section className="rounded-3xl bg-white p-4">
          {sucesso ? (
            <div className="mb-4 rounded-2xl bg-[#e7f6ee] p-4">
              <p className="font-semibold text-[#1f8a4c]">Pagamento registrado com sucesso</p>
              <p className="mt-1 text-sm">{sucesso.cliente} · comprovante {sucesso.numero}</p>
              <p className="text-sm text-[#5c3d45]">{reais(lerReais(sucesso.valor))} · {sucesso.forma} · {sucesso.quando}</p>
              <button type="button" className="mt-3 rounded-full bg-[#7a3044] px-3 py-1.5 text-sm text-white" onClick={() => setSucesso(null)}>Fechar</button>
            </div>
          ) : null}
          <div className="flex items-start justify-between gap-3 rounded-2xl border border-[#f0e4e7] p-3">
            <div className="flex gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-full bg-[#f6eef0] text-[#7a3044]"><UserRound size={18} /></span>
              <div>
                <p className="font-semibold">{atual?.cliente_nome || (carrinho.length ? "Venda de produto" : "Nenhum cliente selecionado")}</p>
                {cliente?.telefone ? <p className="text-sm text-[#8a6e74]">{telefoneLegivel(cliente.telefone)}</p> : null}
                {cliente?.email ? <p className="text-sm text-[#8a6e74]">{cliente.email}</p> : null}
              </div>
            </div>
            {atual ? <button type="button" className="text-sm font-medium text-[#7a3044]" onClick={() => { setEscolhido(null); setDesconto(""); }}>Trocar cliente</button> : null}
          </div>

          <div className="mt-4">
            <p className="text-sm font-medium">Itens do recebimento</p>
            <div className="mt-2 space-y-2">
              {atual ? (
                <div className="flex items-center gap-3 rounded-2xl border border-[#f0e4e7] px-3 py-3">
                  <Scissors size={16} className="text-[#7a3044]" />
                  <span className="min-w-0 flex-1">
                    <span className="block font-medium">{atual.servico_nome} (Serviço)</span>
                    <span className="block text-sm text-[#8a6e74]">Profissional: {atual.profissional_nome}</span>
                  </span>
                  <span className="font-medium">{reais(preco)}</span>
                  <button type="button" aria-label="Remover serviço" onClick={() => setEscolhido(null)} className="text-[#8a6e74]"><Trash2 size={16} /></button>
                </div>
              ) : null}
              {carrinho.map((item) => (
                <div key={item.produto} className="flex items-center gap-3 rounded-2xl border border-[#f0e4e7] px-3 py-3">
                  <ShoppingBag size={16} className="text-[#7a3044]" />
                  <span className="min-w-0 flex-1">
                    <span className="block font-medium">{item.nome}</span>
                    <span className="block text-sm text-[#8a6e74]">Produto</span>
                  </span>
                  <span className="flex items-center gap-2 rounded-full border border-[#eadfe2] px-2 py-1">
                    <button type="button" aria-label="Diminuir" onClick={() => mudarQuantidade(item.produto, -1)}><Minus size={14} /></button>
                    <span className="w-4 text-center text-sm">{item.quantidade}</span>
                    <button type="button" aria-label="Aumentar" onClick={() => mudarQuantidade(item.produto, 1)}><Plus size={14} /></button>
                  </span>
                  <span className="font-medium">{reais(lerReais(item.preco) * item.quantidade)}</span>
                  <button type="button" aria-label="Remover produto" onClick={() => setCarrinho(carrinho.filter((atualItem) => atualItem.produto !== item.produto))} className="text-[#8a6e74]"><Trash2 size={16} /></button>
                </div>
              ))}
              {!temConteudo ? <p className="text-sm text-[#8a6e74]">Escolha um atendimento concluído ou um produto.</p> : null}
            </div>
            <button type="button" className="mt-3 text-sm font-medium text-[#7a3044]" onClick={() => { setAba("produtos"); setBusca(""); }}>+ Adicionar item</button>
          </div>

          <div className="mt-4 space-y-2 text-sm">
            <div className="flex items-center justify-between"><span>Subtotal</span><span>{reais(subtotal)}</span></div>
            <div className="flex items-center justify-between gap-3">
              <span>Desconto (R$)</span>
              <input value={desconto} onChange={(evento) => setDesconto(evento.target.value)} placeholder="0,00" className="w-28 rounded-xl border border-[#eadfe2] px-3 py-1.5 text-right" />
            </div>
            <div className="flex items-center justify-between rounded-2xl bg-[#fdecef] px-3 py-3 text-base font-semibold text-[#7a3044]">
              <span>Total a receber</span><span>{reais(total)}</span>
            </div>
          </div>

          <div className="mt-4">
            <p className="text-sm font-medium">Forma de pagamento</p>
            <div className="mt-2 grid grid-cols-5 gap-2">
              {FORMAS.map((forma) => {
                const Icone = forma.icone;
                const ativa = formaRapida === forma.id;
                return (
                  <button key={forma.id} type="button" onClick={() => escolherForma(forma.id)} className={`flex flex-col items-center gap-1 rounded-2xl border px-2 py-3 text-xs font-medium ${ativa ? "border-[#7a3044] bg-[#fdecef] text-[#7a3044]" : "border-[#f0e4e7] text-[#5c3d45]"}`}>
                    <Icone size={18} />
                    {forma.nome}
                  </button>
                );
              })}
            </div>
            {formaRapida === "multiplas" ? (
              <div className="mt-3 space-y-2">
                {linhas.map((linha) => (
                  <div key={linha.id} className="grid grid-cols-[1fr_8rem] gap-2">
                    <select value={linha.forma} onChange={(evento) => setLinhas(linhas.map((item) => item.id === linha.id ? { ...item, forma: evento.target.value } : item))} className="rounded-xl border border-[#eadfe2] px-3 py-2 text-sm">
                      {FORMAS.filter((forma) => forma.id !== "multiplas").map((forma) => <option key={forma.id} value={forma.id}>{forma.nome}</option>)}
                    </select>
                    <input value={linha.valor} onChange={(evento) => setLinhas(linhas.map((item) => item.id === linha.id ? { ...item, valor: evento.target.value } : item))} className="rounded-xl border border-[#eadfe2] px-3 py-2 text-sm" />
                  </div>
                ))}
                <button type="button" className="text-sm text-[#7a3044]" onClick={() => setLinhas([...linhas, { id: String(Date.now()), forma: "pix", valor: "" }])}>Adicionar forma</button>
              </div>
            ) : (
              <div className="mt-3 grid grid-cols-2 gap-3">
                <label className="text-sm">Valor recebido (R$)
                  <input value={entregue === "" ? (total > 0 ? total.toFixed(2) : "") : entregue} onChange={(evento) => setEntregue(evento.target.value)} className="mt-1 w-full rounded-xl border border-[#eadfe2] px-3 py-2" />
                </label>
                <div className="text-sm">Troco
                  <p className="mt-1 rounded-xl bg-[#e7f6ee] px-3 py-2 font-semibold text-[#1f8a4c]">{reais(troco)}</p>
                </div>
              </div>
            )}
          </div>

          {atual && local === "agenda" ? <p className="mt-3 text-sm text-[#8a6e74]">Neste salão o serviço é recebido na agenda.</p> : null}
          {erro ? <p className="mt-3 text-sm text-red-700">{erro}</p> : null}
          <button type="button" onClick={confirmar} disabled={salvando || !temConteudo || (Boolean(atual) && local === "agenda")} className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl bg-[#7a3044] px-4 py-3 text-sm font-semibold text-white disabled:opacity-60">
            <Check size={16} />
            {salvando ? "Registrando…" : "Confirmar recebimento"}
          </button>
        </section>

        <section className="space-y-4">
          <div className="rounded-3xl bg-white p-4">
            <p className="font-medium">Documentos (após o recebimento)</p>
            {[
              ["comprovante", "Comprovante não fiscal", "Resumo do pagamento (serviços e produtos)."],
              ["nfse", "NFS-e (Serviços)", "Nota Fiscal de Serviço Eletrônica."],
              ["nfce", "NFC-e (Produtos)", "Cupom Fiscal Eletrônico de Produtos."],
            ].map(([chave, titulo, texto]) => (
              <label key={chave} className="mt-3 flex items-start justify-between gap-3 text-sm">
                <span>
                  <span className="block font-medium">{titulo}</span>
                  <span className="block text-[#8a6e74]">{texto}</span>
                </span>
                <input type="checkbox" checked={documentos[chave as keyof typeof documentos]} onChange={(evento) => setDocumentos({ ...documentos, [chave]: evento.target.checked })} className="mt-1 h-4 w-4 accent-[#7a3044]" />
              </label>
            ))}
          </div>
          <div className="rounded-3xl bg-white p-4 text-sm">
            <p className="font-medium">Prévia do comprovante</p>
            <div className="mt-3 rounded-2xl border border-[#f0e4e7] p-4 text-center">
              <p className="font-semibold">{operador || "Salão"}</p>
              <p className="mt-2 text-xs tracking-wide">COMPROVANTE DE PAGAMENTO</p>
              <p className="text-xs text-[#8a6e74]">(NÃO FISCAL)</p>
              <div className="mt-3 flex justify-between text-left text-xs text-[#8a6e74]">
                <span>{sucesso ? `Nº ${String(sucesso.numero).padStart(6, "0")}` : "Prévia"}</span>
                <span>{sucesso?.quando || hoje.toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" })}</span>
              </div>
              <p className="mt-2 text-left text-xs">Cliente: {atual?.cliente_nome || sucesso?.cliente || "—"}</p>
              <div className="mt-3 space-y-1 text-left text-xs">
                {atual ? <p className="flex justify-between gap-2"><span>{atual.servico_nome} (Serviço)</span><span>{reais(preco)}</span></p> : null}
                {carrinho.map((item) => <p key={item.produto} className="flex justify-between gap-2"><span>{item.quantidade}× {item.nome}</span><span>{reais(lerReais(item.preco) * item.quantidade)}</span></p>)}
              </div>
              <p className="mt-3 flex justify-between border-t border-[#f0e4e7] pt-2 font-semibold"><span>Total pago</span><span>{reais(sucesso ? lerReais(sucesso.valor) : total)}</span></p>
              <p className="mt-2 text-left text-xs">Forma de pagamento: {sucesso?.forma || formaLabel}</p>
              <p className="mt-3 text-left text-[11px] text-[#8a6e74]">Este comprovante não substitui a emissão de Nota Fiscal (NFS-e) ou Cupom Fiscal (NFC-e).</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
