"use client";

import { useEffect, useState } from "react";
import { SalaoAPI, type PainelSalao } from "@/lib/salao-api";

const OPCOES: { id: PainelSalao; nome: string; texto: string }[] = [
  { id: "operacao", nome: "Operação do dia", texto: "Agenda de hoje, semana e ocupação." },
  { id: "gestao", nome: "Gestão do mês", texto: "Receita, serviços, clientes e aniversários." },
  { id: "semana", nome: "Agenda da semana", texto: "Horários do dia, ocupação e serviços." },
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
    if (!podeTrocar) return;
    setErro("");
    try {
      await SalaoAPI.salvarPainel(proximo);
      setPainel(proximo);
      setAviso("Painel gravado neste salão.");
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível gravar.");
    }
  }

  return (
    <div>
      <h1 className="mb-1 text-3xl font-semibold">Configurações</h1>
      <p className="mb-4 text-sm text-[#8a6e74]">
        {podeTrocar
          ? "Só o administrador troca o painel. A escolha fica gravada nesta loja."
          : "Este painel foi escolhido pelo administrador e fica fixo nesta loja."}
      </p>
      {erro ? <p className="mb-2 text-sm text-red-700">{erro}</p> : null}
      {aviso ? <p className="mb-2 text-sm text-[#1f8a4c]">{aviso}</p> : null}
      <div className="grid gap-3 md:grid-cols-3">
        {OPCOES.map((opcao) => (
          <button
            key={opcao.id}
            type="button"
            disabled={!podeTrocar}
            onClick={() => escolher(opcao.id)}
            className={`rounded-2xl border p-4 text-left ${painel === opcao.id ? "border-[#7a3044] bg-[#f6ecee]" : "border-[#f0e4e6] bg-white"} disabled:opacity-50`}
          >
            <span className="block font-medium">{opcao.nome}</span>
            <span className="text-sm text-[#8a6e74]">{opcao.texto}</span>
          </button>
        ))}
      </div>
      <p className="mt-6 text-sm text-[#8a6e74]">O login e a assinatura continuam os da loja. O menu lateral pode ser ocultado em qualquer tela para aumentar o campo de visão.</p>
    </div>
  );
}
