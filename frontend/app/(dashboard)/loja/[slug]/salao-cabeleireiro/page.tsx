"use client";

import { useEffect, useState } from "react";
import { SalaoAPI, type ResumoSalao } from "@/lib/salao-api";

export default function SalaoVisaoGeralPage() {
  const [resumo, setResumo] = useState<ResumoSalao | null>(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    SalaoAPI.resumo().then(setResumo).catch((exc: Error) => setErro(exc.message));
  }, []);

  if (erro) return <p className="text-sm text-red-700">{erro}</p>;
  if (!resumo) return <p className="text-sm text-[#8a6e74]">Carregando o painel...</p>;

  return (
    <div>
      <h1 className="text-3xl font-semibold">
        {resumo.painel === "gestao" ? "Gestão do mês" : resumo.painel === "semana" ? "Agenda da semana" : "Operação do dia"}
      </h1>
      <p className="mb-4 text-sm text-[#8a6e74]">Este painel fica fixo no salão. Só o administrador troca, em Configurações.</p>
      {resumo.painel === "gestao" ? <PainelGestao resumo={resumo} /> : null}
      {resumo.painel === "semana" ? <PainelSemana resumo={resumo} /> : null}
      {resumo.painel === "operacao" ? <PainelOperacao resumo={resumo} /> : null}
    </div>
  );
}

function Cartao({ titulo, valor, detalhe }: { titulo: string; valor: string | number; detalhe?: string }) {
  return (
    <article className="rounded-2xl border border-[#f0e4e6] bg-white p-4">
      <p className="text-sm text-[#8a6e74]">{titulo}</p>
      <p className="mt-1 text-2xl font-semibold">{valor}</p>
      {detalhe ? <p className="text-xs text-[#1f8a4c]">{detalhe}</p> : null}
    </article>
  );
}

function PainelOperacao({ resumo }: { resumo: ResumoSalao }) {
  const maior = Math.max(...resumo.semana.map((dia) => dia.total), 1);
  return (
    <>
      <div className="mb-3 grid gap-3 md:grid-cols-4">
        <Cartao titulo="Agendamentos de hoje" valor={resumo.hoje.agendamentos} />
        <Cartao titulo="Faturamento do dia" valor={resumo.hoje.faturamento} />
        <Cartao titulo="Clientes ativos" valor={resumo.mes.clientes_ativos} />
        <Cartao titulo="Taxa de ocupação" valor={`${resumo.hoje.ocupacao}%`} />
      </div>
      <div className="grid gap-3 lg:grid-cols-[1.3fr_.9fr]">
        <section className="rounded-2xl border border-[#f0e4e6] bg-white p-4">
          <h2 className="mb-3 text-sm font-medium">Agendamentos da semana</h2>
          <div className="flex h-40 items-end gap-3">
            {resumo.semana.map((dia) => (
              <div key={dia.data} className="flex flex-1 flex-col items-center">
                <i className="block w-7 rounded-t-md bg-[#d7a3ae]" style={{ height: `${Math.max(4, (dia.total / maior) * 120)}px` }} />
                <span className="mt-1 text-xs text-[#8a6e74]">{dia.total}</span>
              </div>
            ))}
          </div>
        </section>
        <section className="rounded-2xl border border-[#f0e4e6] bg-white p-4">
          <h2 className="mb-2 text-sm font-medium">Agenda de hoje</h2>
          {resumo.agenda_hoje.length === 0 ? <p className="text-sm text-[#8a6e74]">Nenhum horário hoje.</p> : null}
          {resumo.agenda_hoje.map((item) => (
            <div key={item.id} className="grid grid-cols-[52px_1fr_auto] gap-2 border-t border-[#f0e4e6] py-2 text-sm">
              <span>{item.hora}</span>
              <span>{item.cliente}<small className="block text-[#8a6e74]">{item.servico}</small></span>
              <span className="rounded-full bg-[#f6ecee] px-2 py-0.5 text-xs">{item.status_label}</span>
            </div>
          ))}
        </section>
      </div>
    </>
  );
}

function PainelGestao({ resumo }: { resumo: ResumoSalao }) {
  return (
    <>
      <div className="mb-3 grid gap-3 md:grid-cols-4">
        <Cartao titulo="Receita do mês" valor={resumo.mes.receita} />
        <Cartao titulo="Novos clientes" valor={resumo.mes.novos_clientes} />
        <Cartao titulo="Ticket médio" valor={resumo.mes.ticket} />
        <Cartao titulo="Clientes ativos" valor={resumo.mes.clientes_ativos} />
      </div>
      <div className="grid gap-3 lg:grid-cols-2">
        <section className="rounded-2xl border border-[#f0e4e6] bg-white p-4">
          <h2 className="mb-2 text-sm font-medium">Serviços mais vendidos</h2>
          {resumo.servicos.length === 0 ? <p className="text-sm text-[#8a6e74]">Ainda não há serviços concluídos neste mês.</p> : null}
          {resumo.servicos.map((item) => (
            <div key={item.nome} className="grid grid-cols-[1fr_auto_auto] gap-3 border-t border-[#f0e4e6] py-2 text-sm">
              <span>{item.nome}</span><span>{item.quantidade}</span><span>{item.receita}</span>
            </div>
          ))}
        </section>
        <section className="rounded-2xl border border-[#f0e4e6] bg-white p-4">
          <h2 className="mb-2 text-sm font-medium">Aniversariantes do mês</h2>
          {resumo.aniversariantes.length === 0 ? <p className="text-sm text-[#8a6e74]">Nenhum aniversário com data cadastrada.</p> : null}
          {resumo.aniversariantes.map((item) => (
            <div key={`${item.nome}-${item.dia}`} className="flex justify-between border-t border-[#f0e4e6] py-2 text-sm">
              <span>{item.nome}</span><span>{item.dia}</span>
            </div>
          ))}
        </section>
      </div>
    </>
  );
}

function PainelSemana({ resumo }: { resumo: ResumoSalao }) {
  return (
    <>
      <div className="mb-3 grid gap-3 md:grid-cols-4">
        <Cartao titulo="Agendamentos hoje" valor={resumo.hoje.agendamentos} />
        <Cartao titulo="Em atendimento" valor={resumo.hoje.em_andamento} />
        <Cartao titulo="Concluídos" valor={resumo.hoje.concluidos} />
        <Cartao titulo="Ocupação" valor={`${resumo.hoje.ocupacao}%`} detalhe={resumo.hoje.faturamento} />
      </div>
      <section className="rounded-2xl border border-[#f0e4e6] bg-white p-4">
        <h2 className="mb-2 text-sm font-medium">Agenda de hoje</h2>
        {resumo.agenda_hoje.map((item) => (
          <div key={item.id} className="grid grid-cols-[52px_1fr_auto] gap-2 border-t border-[#f0e4e6] py-2 text-sm">
            <span>{item.hora}</span>
            <span>{item.cliente} · {item.servico}<small className="block text-[#8a6e74]">{item.profissional}</small></span>
            <span>{item.status_label}</span>
          </div>
        ))}
      </section>
    </>
  );
}
