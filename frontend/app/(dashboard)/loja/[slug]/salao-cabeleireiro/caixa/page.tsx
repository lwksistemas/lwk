"use client";

import { useEffect, useMemo, useState } from "react";
import { SalaoAPI, type AgendamentoSalao, type LocalRecebimentoSalao } from "@/lib/salao-api";

type Linha = { id: string; forma: string; valor: string };

const FORMAS = [
  ["dinheiro", "Dinheiro"],
  ["pix", "Pix"],
  ["debito", "Débito"],
  ["credito", "Crédito"],
] as const;

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

export default function CaixaPdvPage() {
  const [aba, setAba] = useState<"atendimentos" | "produtos">("atendimentos");
  const [busca, setBusca] = useState("");
  const [fila, setFila] = useState<AgendamentoSalao[]>([]);
  const [escolhido, setEscolhido] = useState<number | null>(null);
  const [desconto, setDesconto] = useState("");
  const [linhas, setLinhas] = useState<Linha[]>([{ id: "1", forma: "dinheiro", valor: "" }]);
  const [entregue, setEntregue] = useState("");
  const [local, setLocal] = useState<LocalRecebimentoSalao>("caixa");
  const [operador, setOperador] = useState("");
  const [erro, setErro] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [previa, setPrevia] = useState(true);
  const [sucesso, setSucesso] = useState<{ cliente: string; valor: string; forma: string; quando: string } | null>(null);

  function carregar() {
    const fim = new Date();
    fim.setHours(23, 59, 0, 0);
    const inicio = new Date(fim);
    inicio.setDate(inicio.getDate() - 7);
    inicio.setHours(0, 0, 0, 0);
    return SalaoAPI.agenda(`${diaIso(inicio)}T00:00:00`, `${diaIso(fim)}T23:59:00`)
      .then((lista) => setFila(lista.filter((item) => item.status === "COMPLETED" && !item.recebido)))
      .catch((exc: Error) => setErro(exc.message));
  }

  useEffect(() => {
    SalaoAPI.config().then((dados) => {
      setLocal(dados.local_recebimento || "caixa");
      setOperador(dados.operador_nome || "");
    }).catch(() => undefined);
    carregar();
  }, []);

  const visiveis = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    if (!termo) return fila;
    return fila.filter((item) => `${item.cliente_nome} ${item.servico_nome} ${item.profissional_nome}`.toLowerCase().includes(termo));
  }, [busca, fila]);

  const atual = fila.find((item) => item.id === escolhido) || null;
  const preco = atual ? lerReais(atual.preco) : 0;
  const valorDesconto = lerReais(desconto);
  const total = Math.max(0, Math.round((preco - valorDesconto) * 100) / 100);
  const soma = Math.round(linhas.reduce((acc, linha) => acc + lerReais(linha.valor), 0) * 100) / 100;
  const parteDinheiro = linhas.filter((linha) => linha.forma === "dinheiro").reduce((acc, linha) => acc + lerReais(linha.valor), 0);
  const troco = lerReais(entregue) > parteDinheiro ? Math.round((lerReais(entregue) - parteDinheiro) * 100) / 100 : 0;
  const hoje = new Date().toLocaleDateString("pt-BR", { day: "2-digit", month: "long" });

  function selecionar(item: AgendamentoSalao) {
    setEscolhido(item.id);
    setDesconto("");
    setEntregue("");
    setLinhas([{ id: "1", forma: "dinheiro", valor: item.preco }]);
    setSucesso(null);
    setErro("");
  }

  async function confirmar() {
    if (!atual || salvando || local === "agenda") return;
    if (valorDesconto < 0 || valorDesconto > preco) {
      setErro("O desconto não pode passar do valor do serviço.");
      return;
    }
    if (total > 0 && Math.abs(soma - total) > 0.009) {
      setErro(`A soma das formas precisa fechar ${reais(total)}.`);
      return;
    }
    setErro("");
    setSalvando(true);
    try {
      const atualizado = await SalaoAPI.receber(atual.id, {
        desconto: valorDesconto.toFixed(2),
        origem: "caixa",
        formas: total > 0 ? linhas.map((linha) => ({ forma: linha.forma, valor: lerReais(linha.valor).toFixed(2) })) : [],
      });
      setSucesso({
        cliente: atualizado.cliente_nome,
        valor: atualizado.recebido?.valor || total.toFixed(2),
        forma: atualizado.recebido?.forma_label || "Recebido",
        quando: new Date().toLocaleString("pt-BR"),
      });
      setEscolhido(null);
      await carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível receber.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div>
      <header className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Caixa/PDV</h1>
          <p className="text-sm text-[#8a6e74]">Movimento de {hoje}</p>
        </div>
        {operador ? <p className="text-sm font-medium">{operador}</p> : null}
      </header>
      <div className="grid items-start gap-3 lg:grid-cols-[280px_minmax(0,1fr)_280px]">
        <section className="rounded-3xl bg-white p-4">
          <div className="mb-3 grid grid-cols-2 gap-1 rounded-full bg-[#f6eef0] p-1 text-sm">
            <button type="button" className={`rounded-full px-2 py-1 ${aba === "atendimentos" ? "bg-white" : ""}`} onClick={() => setAba("atendimentos")}>Atendimentos</button>
            <button type="button" className={`rounded-full px-2 py-1 ${aba === "produtos" ? "bg-white" : ""}`} onClick={() => setAba("produtos")}>Produtos</button>
          </div>
          {aba === "produtos" ? (
            <p className="text-sm text-[#8a6e74]">A venda de produtos entra com o estoque. Nenhum item é baixado nesta etapa.</p>
          ) : (
            <>
              <input value={busca} onChange={(evento) => setBusca(evento.target.value)} placeholder="Buscar cliente ou serviço" className="mb-3 w-full rounded-xl border border-[#eadfe2] px-3 py-2 text-sm" />
              <div className="space-y-2">
                {visiveis.length === 0 ? <p className="text-sm text-[#8a6e74]">Nenhum atendimento concluído aguardando pagamento.</p> : null}
                {visiveis.map((item) => (
                  <button key={item.id} type="button" onClick={() => selecionar(item)} className={`w-full rounded-2xl border p-3 text-left ${escolhido === item.id ? "border-[#7a3044] bg-[#fbf6f4]" : "border-[#eadfe2]"}`}>
                    <span className="block font-medium">{item.cliente_nome}</span>
                    <span className="block text-sm text-[#8a6e74]">{item.servico_nome} · {reais(lerReais(item.preco))}</span>
                    <span className="block text-sm text-[#8a6e74]">{hora(item.inicio)} · {item.profissional_nome}</span>
                  </button>
                ))}
              </div>
            </>
          )}
        </section>
        <section className="rounded-3xl bg-white p-4">
          {sucesso ? (
            <div>
              <h2 className="text-lg font-semibold">Pagamento registrado com sucesso</h2>
              <p className="mt-2 text-sm">{sucesso.cliente}</p>
              <p className="text-sm text-[#8a6e74]">{reais(lerReais(sucesso.valor))} · {sucesso.forma}</p>
              <p className="text-sm text-[#8a6e74]">{sucesso.quando}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <button type="button" className="rounded-full border px-3 py-1.5 text-sm" onClick={() => window.print()}>Imprimir</button>
                <span className="rounded-full border px-3 py-1.5 text-sm text-[#8a6e74]">PDF, WhatsApp e e-mail entram com o comprovante</span>
                <button type="button" className="rounded-full bg-[#7a3044] px-3 py-1.5 text-sm text-white" onClick={() => setSucesso(null)}>Fechar</button>
              </div>
            </div>
          ) : atual ? (
            <div>
              <h2 className="text-lg font-semibold">{atual.cliente_nome}</h2>
              <p className="text-sm text-[#8a6e74]">Serviço {atual.servico_nome}</p>
              <p className="text-sm text-[#8a6e74]">Profissional {atual.profissional_nome}</p>
              <p className="mt-3 text-sm">Valor do serviço {reais(preco)}</p>
              <label className="mt-3 block text-sm">
                Desconto (R$)
                <input value={desconto} onChange={(evento) => setDesconto(evento.target.value)} className="mt-1 w-full rounded-xl border border-[#eadfe2] px-3 py-2" />
              </label>
              <p className="mt-3 font-medium">Total a receber {reais(total)}</p>
              <div className="mt-3 space-y-2">
                {linhas.map((linha) => (
                  <div key={linha.id} className="grid grid-cols-[1fr_8rem] gap-2">
                    <select value={linha.forma} onChange={(evento) => setLinhas(linhas.map((item) => item.id === linha.id ? { ...item, forma: evento.target.value } : item))} className="rounded-xl border border-[#eadfe2] px-3 py-2 text-sm">
                      {FORMAS.map(([id, nome]) => <option key={id} value={id}>{nome}</option>)}
                    </select>
                    <input value={linha.valor} onChange={(evento) => setLinhas(linhas.map((item) => item.id === linha.id ? { ...item, valor: evento.target.value } : item))} className="rounded-xl border border-[#eadfe2] px-3 py-2 text-sm" />
                  </div>
                ))}
                <button type="button" className="text-sm text-[#7a3044]" onClick={() => setLinhas([...linhas, { id: String(Date.now()), forma: "pix", valor: "" }])}>Adicionar forma</button>
              </div>
              {linhas.some((linha) => linha.forma === "dinheiro") ? (
                <label className="mt-3 block text-sm">
                  Dinheiro entregue
                  <input value={entregue} onChange={(evento) => setEntregue(evento.target.value)} className="mt-1 w-full rounded-xl border border-[#eadfe2] px-3 py-2" />
                </label>
              ) : null}
              {troco > 0 ? <p className="mt-2 text-sm">Troco {reais(troco)}</p> : null}
              {local === "agenda" ? <p className="mt-3 text-sm text-[#8a6e74]">Neste salão o pagamento é recebido na agenda.</p> : null}
              {erro ? <p className="mt-3 text-sm text-red-700">{erro}</p> : null}
              <button type="button" onClick={confirmar} disabled={salvando || local === "agenda"} className="mt-4 rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white disabled:opacity-60">
                {salvando ? "Registrando…" : "Confirmar recebimento"}
              </button>
            </div>
          ) : (
            <p className="text-sm text-[#8a6e74]">Escolha um atendimento concluído para receber. Serviço e produto entram no mesmo pagamento na etapa do estoque.</p>
          )}
        </section>
        <section className="rounded-3xl bg-white p-4">
          <button type="button" className="text-sm text-[#7a3044]" onClick={() => setPrevia((valor) => !valor)}>{previa ? "Recolher prévia" : "Abrir prévia"}</button>
          {previa ? (
            <div className="mt-3 text-sm">
              <p className="font-medium">COMPROVANTE DE PAGAMENTO — NÃO FISCAL</p>
              {atual ? (
                <>
                  <p className="mt-2">{atual.cliente_nome}</p>
                  <p>{atual.servico_nome} · {reais(preco)}</p>
                  <p>Profissional {atual.profissional_nome}</p>
                  {valorDesconto > 0 ? <p>Desconto {reais(valorDesconto)}</p> : null}
                  <p className="mt-2 font-medium">Total {reais(total)}</p>
                </>
              ) : <p className="mt-2 text-[#8a6e74]">A prévia aparece quando um atendimento é escolhido.</p>}
              <p className="mt-3 text-[#8a6e74]">A nota de serviço e o cupom de produto seguem as configurações do salão. Esta tela não emite documento fiscal.</p>
            </div>
          ) : null}
        </section>
      </div>
    </div>
  );
}
