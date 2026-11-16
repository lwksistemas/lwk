"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { SalaoAPI, type LocalRecebimentoSalao, type ModeloSalao } from "@/lib/salao-api";

const MODELOS: { id: ModeloSalao; nome: string; texto: string }[] = [
  { id: "recepcionista", nome: "Salão com recepção", texto: "Os profissionais atendem. Quem recebe é a recepção, no Caixa/PDV." },
  { id: "autonomo", nome: "Profissional autônomo", texto: "A mesma pessoa cuida da agenda, do serviço, do pagamento e dos produtos." },
];

const LOCAIS: { id: LocalRecebimentoSalao; nome: string; texto: string }[] = [
  { id: "caixa", nome: "Somente no Caixa/PDV", texto: "A agenda manda o atendimento concluído para a fila do caixa." },
  { id: "agenda", nome: "Diretamente pela agenda", texto: "O pagamento é registrado no próprio agendamento." },
  { id: "ambos", nome: "Agenda ou Caixa/PDV", texto: "Os dois caminhos usam o mesmo recebimento. Um atendimento quitado não é cobrado de novo." },
];

export default function FuncionamentoSalaoPage() {
  const slug = (useParams()?.slug as string) ?? "";
  const [modelo, setModelo] = useState<ModeloSalao>("recepcionista");
  const [local, setLocal] = useState<LocalRecebimentoSalao>("caixa");
  const [podeSalvar, setPodeSalvar] = useState(false);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    SalaoAPI.config()
      .then((dados) => {
        setModelo(dados.modelo || "recepcionista");
        setLocal(dados.local_recebimento || "caixa");
        setPodeSalvar(dados.pode_trocar);
      })
      .catch((exc: Error) => setErro(exc.message));
  }, []);

  function escolherModelo(proximo: ModeloSalao) {
    setModelo(proximo);
    setLocal(proximo === "autonomo" ? "ambos" : "caixa");
    setAviso("");
  }

  async function gravar() {
    setErro("");
    setAviso("");
    setSalvando(true);
    try {
      const dados = await SalaoAPI.salvarFuncionamento({ modelo, local_recebimento: local });
      setModelo(dados.modelo);
      setLocal(dados.local_recebimento);
      setAviso("O funcionamento ficou gravado. Agenda, clientes e pagamentos continuam no salão.");
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível gravar.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="space-y-4">
      <Link href={`/loja/${slug}/salao-cabeleireiro/configuracoes`} className="inline-flex items-center gap-2 text-sm text-[#8a6e74]">
        <ArrowLeft size={16} /> Voltar às configurações
      </Link>
      <div>
        <h1 className="text-2xl font-semibold">Funcionamento do salão</h1>
        <p className="mt-1 text-sm text-[#8a6e74]">Tipo de estabelecimento, recebimentos e permissões.</p>
      </div>
      {erro ? <p className="text-sm text-red-700">{erro}</p> : null}
      {aviso ? <p className="text-sm text-[#1f8a4c]">{aviso}</p> : null}
      <section className="rounded-3xl bg-white p-5">
        <h2 className="font-medium">Modelo</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          {MODELOS.map((opcao) => (
            <button key={opcao.id} type="button" onClick={() => escolherModelo(opcao.id)} className={`rounded-2xl border p-4 text-left ${modelo === opcao.id ? "border-[#7a3044] bg-[#fbf6f4]" : "border-[#eadfe2]"}`}>
              <span className="font-medium">{opcao.nome}</span>
              <span className="mt-1 block text-sm text-[#8a6e74]">{opcao.texto}</span>
            </button>
          ))}
        </div>
      </section>
      <section className="rounded-3xl bg-white p-5">
        <h2 className="font-medium">Onde o pagamento é recebido</h2>
        <div className="mt-3 grid gap-3">
          {LOCAIS.map((opcao) => (
            <button key={opcao.id} type="button" onClick={() => { setLocal(opcao.id); setAviso(""); }} className={`rounded-2xl border p-4 text-left ${local === opcao.id ? "border-[#7a3044] bg-[#fbf6f4]" : "border-[#eadfe2]"}`}>
              <span className="font-medium">{opcao.nome}</span>
              <span className="mt-1 block text-sm text-[#8a6e74]">{opcao.texto}</span>
            </button>
          ))}
        </div>
      </section>
      {podeSalvar ? (
        <button type="button" onClick={gravar} disabled={salvando} className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white disabled:opacity-60">
          {salvando ? "Gravando…" : "Gravar funcionamento"}
        </button>
      ) : (
        <p className="text-sm text-[#8a6e74]">Só o administrador grava o funcionamento deste salão.</p>
      )}
    </div>
  );
}
