"use client";

import { useEffect, useState } from "react";
import { PainelDoSalao } from "@/components/salao/PaineisSalao";
import { SalaoAPI, type PainelSalao } from "@/lib/salao-api";

const OPCOES: { id: PainelSalao; nome: string; texto: string }[] = [
  { id: "operacao", nome: "Operação do dia", texto: "Cards do dia, gráfico da semana e a agenda de hoje." },
  { id: "semana", nome: "Agenda da semana", texto: "Grade de horários, clientes do dia e ocupação do salão." },
  { id: "gestao", nome: "Gestão do mês", texto: "Receita do mês, serviços mais vendidos e aniversariantes." },
];

export default function ConfiguracoesSalaoPage() {
  const [painel, setPainel] = useState<PainelSalao>("operacao");
  const [podeTrocar, setPodeTrocar] = useState(false);
  const [previa, setPrevia] = useState<PainelSalao | null>(null);
  const [confirmar, setConfirmar] = useState<PainelSalao | null>(null);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");

  useEffect(() => {
    SalaoAPI.config()
      .then((dados) => {
        setPainel(dados.painel);
        setPodeTrocar(dados.pode_trocar);
      })
      .catch((exc: Error) => setErro(exc.message));
  }, []);

  async function escolher(proximo: PainelSalao) {
    if (!podeTrocar || proximo === painel) return;
    setErro("");
    setAviso("");
    try {
      await SalaoAPI.salvarPainel(proximo);
      setPainel(proximo);
      setConfirmar(null);
      setPrevia(null);
      window.dispatchEvent(new CustomEvent("salao-painel", { detail: proximo }));
      setAviso("Este layout ficou gravado no salão.");
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível gravar.");
    }
  }

  const nomeConfirmar = OPCOES.find((opcao) => opcao.id === confirmar)?.nome;
  const nomePrevia = OPCOES.find((opcao) => opcao.id === previa)?.nome;

  return (
    <div>
      <h1 className="mb-1 text-2xl font-semibold sm:text-3xl">Configurações</h1>
      <p className="mb-5 max-w-2xl text-sm text-[#8a6e74]">
        {podeTrocar
          ? "Veja o layout com os dados deste salão antes de ativar. A troca pede confirmação e só o administrador grava."
          : "O layout em uso foi escolhido pelo administrador e fica fixo neste salão. A visualização não troca o modelo."}
      </p>
      {erro ? <p className="mb-3 text-sm text-red-700">{erro}</p> : null}
      {aviso ? <p className="mb-3 text-sm text-[#1f8a4c]">{aviso}</p> : null}
      {previa ? (
        <section className="mb-5 rounded-3xl border border-[#f0e4e6] bg-white p-4">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-[#8a6e74]">
              Prévia de {nomePrevia}. Os números são os deste salão.
              {previa === painel ? " Este é o layout em uso." : " Ainda não substitui o modelo em uso."}
            </p>
            <div className="flex flex-wrap gap-2">
              {podeTrocar && previa !== painel ? (
                <button type="button" className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" onClick={() => setConfirmar(previa)}>
                  Usar este layout
                </button>
              ) : null}
              <button type="button" className="rounded-full border px-4 py-2 text-sm" onClick={() => setPrevia(null)}>Fechar prévia</button>
            </div>
          </div>
          <PainelDoSalao painel={previa} />
        </section>
      ) : null}
      <div className="grid gap-4 xl:grid-cols-3">
        {OPCOES.map((opcao) => {
          const ativo = painel === opcao.id;
          return (
            <article
              key={opcao.id}
              className={`rounded-3xl border bg-white p-3 text-left shadow-sm ${ativo ? "border-[#7a3044] ring-2 ring-[#7a3044]/40" : "border-[#f0e4e6]"}`}
            >
              <Miniatura id={opcao.id} />
              <span className="mt-3 flex items-center justify-between gap-2">
                <span className="font-medium">{opcao.nome}</span>
                {ativo ? <span className="rounded-full bg-[#7a3044] px-2 py-0.5 text-xs text-white">Em uso</span> : null}
              </span>
              <span className="mt-1 block text-sm text-[#8a6e74]">{opcao.texto}</span>
              <span className="mt-3 flex flex-wrap gap-2">
                <button type="button" className="rounded-full border px-3 py-1.5 text-sm" onClick={() => setPrevia(opcao.id)}>
                  Visualizar dashboard
                </button>
                {podeTrocar && !ativo ? (
                  <button type="button" className="rounded-full bg-[#7a3044] px-3 py-1.5 text-sm text-white" onClick={() => setConfirmar(opcao.id)}>
                    Usar este layout
                  </button>
                ) : null}
              </span>
            </article>
          );
        })}
      </div>
      {confirmar ? (
        <div className="fixed inset-0 z-30 grid place-items-center bg-black/40 p-4" role="dialog" aria-modal="true" aria-labelledby="confirmar-layout">
          <div className="w-full max-w-md rounded-3xl bg-white p-5">
            <h2 id="confirmar-layout" className="text-lg font-semibold">Trocar o dashboard deste salão?</h2>
            <p className="mt-2 text-sm text-[#8a6e74]">A equipe passa a ver {nomeConfirmar}. A escolha fica gravada nesta loja.</p>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" className="rounded-full border px-4 py-2 text-sm" onClick={() => setConfirmar(null)}>Cancelar</button>
              <button type="button" className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" onClick={() => escolher(confirmar)}>Confirmar</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Miniatura({ id }: { id: PainelSalao }) {
  if (id === "semana") return <MiniaturaSemana />;
  if (id === "gestao") return <MiniaturaGestao />;
  return <MiniaturaOperacao />;
}

function MiniaturaOperacao() {
  return (
    <div className="flex h-40 overflow-hidden rounded-2xl bg-[#fbf6f4]">
      <div className="w-9 bg-[#7A3044]" />
      <div className="flex min-w-0 flex-1 flex-col gap-1.5 p-2">
        <div className="h-2 w-16 rounded bg-[#7A3044]/25" />
        <div className="grid grid-cols-4 gap-1">
          {["#f3d5dc", "#f7e4c8", "#f8d7de", "#f3e6cf"].map((cor) => (
            <div key={cor} className="h-7 rounded-md bg-white p-1">
              <i className="block h-1.5 w-3 rounded" style={{ background: cor }} />
            </div>
          ))}
        </div>
        <div className="grid min-h-0 flex-1 grid-cols-[1.3fr_.8fr] gap-1">
          <div className="flex items-end gap-1 rounded-md bg-white px-1 pb-1">
            {[28, 40, 36, 48, 62, 52, 8].map((altura) => (
              <i key={altura} className="flex-1 rounded-t bg-[#d7a3ae]" style={{ height: altura }} />
            ))}
          </div>
          <div className="flex flex-col justify-center gap-1 rounded-md bg-white px-1">
            {[0, 1, 2].map((item) => <i key={item} className="h-1.5 rounded bg-[#f3d5dc]" />)}
          </div>
        </div>
      </div>
    </div>
  );
}

function MiniaturaSemana() {
  return (
    <div className="flex h-40 overflow-hidden rounded-2xl bg-[#f6f4fb]">
      <div className="w-9 bg-[#4c1d78]" />
      <div className="flex min-w-0 flex-1 gap-1 p-2">
        <div className="grid flex-1 grid-cols-5 gap-0.5 rounded-md bg-white p-1">
          {Array.from({ length: 15 }, (_, indice) => (
            <i key={indice} className={`rounded-sm ${indice % 4 === 0 ? "bg-[#ddd6fe]" : "bg-[#f5f3ff]"}`} />
          ))}
        </div>
        <div className="flex w-12 flex-col gap-1">
          <i className="h-8 rounded-md bg-white" />
          <i className="h-8 rounded-full bg-[#c4b5fd]" />
        </div>
      </div>
    </div>
  );
}

function MiniaturaGestao() {
  return (
    <div className="flex h-40 overflow-hidden rounded-2xl bg-[#f7f4ee]">
      <div className="w-9 bg-[#3d5244]" />
      <div className="flex min-w-0 flex-1 flex-col gap-1.5 p-2">
        <div className="h-2 w-20 rounded bg-[#3d5244]/25" />
        <div className="grid grid-cols-4 gap-1">
          {Array.from({ length: 4 }, (_, indice) => <i key={indice} className="h-6 rounded-md bg-[#e7f0df]" />)}
        </div>
        <div className="grid min-h-0 flex-1 grid-cols-2 gap-1">
          <div className="flex items-end gap-0.5 rounded-md bg-white px-1 pb-1">
            {[18, 24, 20, 30, 28, 36, 32].map((altura) => (
              <i key={altura} className="flex-1 rounded-t bg-[#8aaa78]" style={{ height: altura }} />
            ))}
          </div>
          <div className="rounded-md bg-white" />
        </div>
      </div>
    </div>
  );
}
