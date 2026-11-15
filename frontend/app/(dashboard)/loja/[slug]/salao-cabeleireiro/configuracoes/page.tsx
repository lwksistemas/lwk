"use client";

import { useEffect, useState } from "react";
import { SalaoAPI, type PainelSalao } from "@/lib/salao-api";

const OPCOES: { id: PainelSalao; nome: string; texto: string }[] = [
  { id: "operacao", nome: "Operação do dia", texto: "Cards do dia, gráfico da semana e a agenda de hoje." },
  { id: "semana", nome: "Agenda da semana", texto: "Grade de horários, clientes do dia e ocupação do salão." },
  { id: "gestao", nome: "Gestão do mês", texto: "Receita do mês, serviços mais vendidos e aniversariantes." },
];

export default function ConfiguracoesSalaoPage() {
  const [painel, setPainel] = useState<PainelSalao>("operacao");
  const [podeTrocar, setPodeTrocar] = useState(false);
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
      window.dispatchEvent(new CustomEvent("salao-painel", { detail: proximo }));
      setAviso("Este layout ficou gravado no salão.");
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível gravar.");
    }
  }

  return (
    <div>
      <h1 className="mb-1 text-3xl font-semibold">Configurações</h1>
      <p className="mb-5 max-w-2xl text-sm text-[#8a6e74]">
        {podeTrocar
          ? "Escolha o layout do dashboard. A opção fica fixa neste salão e só o administrador troca."
          : "O layout abaixo foi escolhido pelo administrador e fica fixo neste salão."}
      </p>
      {erro ? <p className="mb-3 text-sm text-red-700">{erro}</p> : null}
      {aviso ? <p className="mb-3 text-sm text-[#1f8a4c]">{aviso}</p> : null}
      <div className="grid gap-4 xl:grid-cols-3">
        {OPCOES.map((opcao) => {
          const ativo = painel === opcao.id;
          return (
            <button
              key={opcao.id}
              type="button"
              disabled={!podeTrocar}
              onClick={() => escolher(opcao.id)}
              className={`rounded-3xl border bg-white p-3 text-left shadow-sm transition disabled:cursor-default ${ativo ? "border-[#7a3044] ring-2 ring-[#7a3044]/30" : "border-[#f0e4e6] hover:border-[#d7a3ae]"}`}
            >
              <Miniatura id={opcao.id} />
              <span className="mt-3 flex items-center justify-between gap-2">
                <span className="font-medium">{opcao.nome}</span>
                {ativo ? <span className="rounded-full bg-[#f6ecee] px-2 py-0.5 text-xs text-[#7a3044]">Em uso</span> : null}
              </span>
              <span className="mt-1 block text-sm text-[#8a6e74]">{opcao.texto}</span>
            </button>
          );
        })}
      </div>
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
