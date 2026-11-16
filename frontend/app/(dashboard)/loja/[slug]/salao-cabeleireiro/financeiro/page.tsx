"use client";

import { useEffect, useState } from "react";
import { SalaoAPI, type CaixaSalao, type FormaPagamentoSalao } from "@/lib/salao-api";

function periodo(modo: "hoje" | "mes") {
  const agora = new Date();
  const dois = (valor: number) => String(valor).padStart(2, "0");
  const texto = (data: Date) => `${data.getFullYear()}-${dois(data.getMonth() + 1)}-${dois(data.getDate())}T${dois(data.getHours())}:${dois(data.getMinutes())}:00`;
  if (modo === "hoje") {
    const inicio = new Date(agora.getFullYear(), agora.getMonth(), agora.getDate());
    const fim = new Date(inicio);
    fim.setDate(fim.getDate() + 1);
    return { inicio: texto(inicio), fim: texto(fim) };
  }
  const inicio = new Date(agora.getFullYear(), agora.getMonth(), 1);
  const fim = new Date(agora.getFullYear(), agora.getMonth() + 1, 1);
  return { inicio: texto(inicio), fim: texto(fim) };
}

export default function FinanceiroSalaoPage() {
  const [modo, setModo] = useState<"hoje" | "mes">("hoje");
  const [caixa, setCaixa] = useState<CaixaSalao | null>(null);
  const [erro, setErro] = useState("");
  const [formas, setFormas] = useState<FormaPagamentoSalao[]>([]);
  const [nomeForma, setNomeForma] = useState("");
  const [editando, setEditando] = useState<number | null>(null);
  const [confirmar, setConfirmar] = useState<number | null>(null);
  const [nomeEdicao, setNomeEdicao] = useState("");
  const [avisoForma, setAvisoForma] = useState("");

  function carregarFormas() {
    SalaoAPI.formas().then(setFormas).catch((exc: Error) => setErro(exc.message));
  }

  async function criarForma(evento: React.FormEvent) {
    evento.preventDefault();
    setErro("");
    setAvisoForma("");
    try {
      await SalaoAPI.criarForma(nomeForma);
      setNomeForma("");
      carregarFormas();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível criar a forma.");
    }
  }

  async function salvarNome(id: number) {
    setErro("");
    setAvisoForma("");
    try {
      await SalaoAPI.renomearForma(id, nomeEdicao);
      setEditando(null);
      carregarFormas();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível editar a forma.");
    }
  }

  async function excluirForma(id: number) {
    setErro("");
    setAvisoForma("");
    try {
      const resposta = await SalaoAPI.excluirForma(id);
      setAvisoForma(resposta.message);
      carregarFormas();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível excluir a forma.");
    }
  }

  async function reimprimir(numero: number) {
    try {
      const venda = await SalaoAPI.venda(numero);
      const linhas = [
        "COMPROVANTE DE PAGAMENTO (NÃO FISCAL)",
        `Nº ${String(venda.numero).padStart(6, "0")} · ${venda.quando}`,
        `Cliente: ${venda.cliente}`,
        ...(venda.servicos || []).map((item) => `${item.nome} — ${item.total}${item.profissional ? ` (${item.profissional})` : ""}`),
        ...(venda.itens || []).map((item) => `${item.quantidade}× ${item.nome} — ${item.total}`),
        `Total pago: ${venda.valor}`,
        `Forma de pagamento: ${venda.forma_label}`,
        venda.operador ? `Operador: ${venda.operador}` : "",
        venda.estornado ? "Este recebimento foi estornado." : "",
      ].filter(Boolean);
      const html = `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Comprovante ${venda.numero}</title></head><body style="font-family:sans-serif;max-width:360px;margin:24px auto;font-size:14px">${linhas.map((linha) => `<p>${linha.replace(/&/g, "&amp;").replace(/</g, "&lt;")}</p>`).join("")}</body></html>`;
      const quadro = document.createElement("iframe");
      quadro.style.position = "fixed";
      quadro.style.width = "0";
      quadro.style.height = "0";
      quadro.style.border = "0";
      document.body.appendChild(quadro);
      const documento = quadro.contentDocument;
      const janela = quadro.contentWindow;
      if (!documento || !janela) {
        quadro.remove();
        setErro("Não foi possível preparar a impressão.");
        return;
      }
      documento.open();
      documento.write(html);
      documento.close();
      window.setTimeout(() => {
        janela.focus();
        janela.print();
        window.setTimeout(() => quadro.remove(), 1000);
      }, 50);
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível reimprimir.");
    }
  }

  useEffect(() => {
    carregarFormas();
  }, []);

  useEffect(() => {
    const faixa = periodo(modo);
    SalaoAPI.caixa(faixa.inicio, faixa.fim)
      .then(setCaixa)
      .catch((exc: Error) => setErro(exc.message));
  }, [modo]);

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold sm:text-3xl">Caixa</h1>
          <p className="text-sm text-[#8a6e74]">Recebimentos de atendimentos concluídos. O preço do serviço só entra depois de receber.</p>
        </div>
        <div className="flex gap-2">
          <button type="button" className={`rounded-full px-3 py-1.5 text-sm ${modo === "hoje" ? "bg-[#7a3044] text-white" : "border"}`} onClick={() => setModo("hoje")}>Hoje</button>
          <button type="button" className={`rounded-full px-3 py-1.5 text-sm ${modo === "mes" ? "bg-[#7a3044] text-white" : "border"}`} onClick={() => setModo("mes")}>Este mês</button>
        </div>
      </div>
      {erro ? <p className="mb-3 text-sm text-red-700">{erro}</p> : null}
      <section className="mb-4 rounded-3xl border border-[#f0e4e6] bg-white p-4">
        <h2 className="text-sm font-medium">Formas de pagamento</h2>
        <p className="mt-1 text-xs text-[#8a6e74]">O caixa usa estas formas. Excluir uma forma já recebida tira ela dos próximos pagamentos e mantém o histórico.</p>
        <form className="mt-3 flex flex-wrap gap-2" onSubmit={criarForma}>
          <input value={nomeForma} onChange={(evento) => setNomeForma(evento.target.value)} placeholder="Nova forma" className="min-w-40 flex-1 rounded-xl border border-[#eadfe2] px-3 py-2 text-sm" />
          <button type="submit" className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white">Adicionar</button>
        </form>
        {avisoForma ? <p className="mt-2 text-sm text-[#1f8a4c]">{avisoForma}</p> : null}
        <ul className="mt-3">
          {formas.map((item) => (
            <li key={item.id} className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f0e4e6] py-2 text-sm">
              {editando === item.id ? (
                <input value={nomeEdicao} onChange={(evento) => setNomeEdicao(evento.target.value)} className="min-w-40 flex-1 rounded-xl border border-[#eadfe2] px-3 py-1.5" />
              ) : <span>{item.nome}</span>}
              <span className="flex gap-3">
                {editando === item.id ? (
                  <>
                    <button type="button" className="text-[#7a3044]" onClick={() => salvarNome(item.id)}>Salvar</button>
                    <button type="button" className="text-[#8a6e74]" onClick={() => setEditando(null)}>Cancelar</button>
                  </>
                ) : (
                  <>
                    <button type="button" className="text-[#7a3044]" onClick={() => { setEditando(item.id); setNomeEdicao(item.nome); setConfirmar(null); }}>Editar</button>
                    {confirmar === item.id ? (
                      <>
                        <button type="button" className="text-red-700" onClick={() => excluirForma(item.id)}>Confirmar exclusão</button>
                        <button type="button" className="text-[#8a6e74]" onClick={() => setConfirmar(null)}>Cancelar</button>
                      </>
                    ) : <button type="button" className="text-red-700" onClick={() => setConfirmar(item.id)}>Excluir</button>}
                  </>
                )}
              </span>
            </li>
          ))}
        </ul>
      </section>
      <div className="mb-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <article className="rounded-3xl border border-[#f0e4e6] bg-white p-4">
          <p className="text-sm text-[#8a6e74]">Recebido</p>
          <p className="mt-1 text-2xl font-semibold text-[#7a3044]">{caixa?.total || "R$ 0,00"}</p>
        </article>
        {(caixa?.por_forma || []).map((item) => (
          <article key={item.forma} className="rounded-3xl border border-[#f0e4e6] bg-white p-4">
            <p className="text-sm text-[#8a6e74]">{item.nome}</p>
            <p className="mt-1 text-2xl font-semibold">{item.total}</p>
          </article>
        ))}
      </div>
      <div className="grid gap-3 lg:grid-cols-[minmax(0,1.4fr)_minmax(16rem,0.7fr)]">
        <section className="rounded-3xl border border-[#f0e4e6] bg-white p-4">
          <h2 className="mb-2 text-sm font-medium">Movimentação</h2>
          {(caixa?.recebimentos.length || 0) === 0 ? <p className="text-sm text-[#8a6e74]">Nenhum recebimento neste período.</p> : null}
          <ul>
            {(caixa?.recebimentos || []).map((item) => (
              <li key={item.id} className="grid gap-1 border-t border-[#f0e4e6] py-2 text-sm sm:grid-cols-[88px_minmax(0,1fr)_auto]">
                <span className="text-[#8a6e74]">{item.quando}</span>
                <span className="min-w-0">
                  <span className="block truncate">{item.cliente} · {item.servico}</span>
                  <small className="text-[#8a6e74]">{item.profissional}{item.operador ? ` · operador ${item.operador}` : ""} · {item.forma_label}{item.desconto !== "R$ 0,00" ? ` · desconto ${item.desconto}` : ""}{item.numero ? ` · comprovante ${String(item.numero).padStart(6, "0")}` : ""}</small>
                </span>
                <span className="text-right">
                  <span className="block">{item.valor}</span>
                  {item.numero ? <button type="button" className="text-xs text-[#7a3044]" onClick={() => reimprimir(item.numero as number)}>Reimprimir</button> : null}
                </span>
              </li>
            ))}
          </ul>
          {(caixa?.estornos?.length || 0) > 0 ? (
            <div className="mt-4">
              <h2 className="mb-2 text-sm font-medium">Estornos</h2>
              <ul>
                {caixa?.estornos?.map((item) => (
                  <li key={`estorno-${item.id}-${item.numero || 0}`} className="grid gap-1 border-t border-[#f0e4e6] py-2 text-sm text-[#8a6e74] sm:grid-cols-[88px_minmax(0,1fr)_auto]">
                    <span>{item.quando}</span>
                    <span>{item.cliente} · {item.servico} · {item.forma_label}{item.operador ? ` · ${item.operador}` : ""}</span>
                    <span>{item.valor}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>
        <section className="rounded-3xl border border-[#f0e4e6] bg-white p-4">
          <h2 className="mb-2 text-sm font-medium">Comissões</h2>
          {(caixa?.comissoes.length || 0) === 0 ? <p className="text-sm text-[#8a6e74]">Nenhuma comissão neste período.</p> : null}
          {(caixa?.comissoes || []).map((item) => (
            <div key={item.nome} className="flex items-center justify-between gap-2 border-t border-[#f0e4e6] py-2 text-sm">
              <span className="min-w-0 truncate">{item.nome}<small className="block text-[#8a6e74]">{item.quantidade} · recebido {item.recebido}</small></span>
              <span>{item.comissao}</span>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}
