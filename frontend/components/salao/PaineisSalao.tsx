"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { CalendarPlus, Gift, Scissors, Users } from "lucide-react";
import { SalaoAPI, type AgendamentoSalao, type PainelSalao, type ProfissionalSalao, type ResumoSalao } from "@/lib/salao-api";

const CORES_PROFISSIONAL = ["#7c3aed", "#db2777", "#2563eb", "#ea580c", "#059669", "#be185d"];

export function PainelDoSalao({ painel }: { painel: PainelSalao }) {
  const params = useParams();
  const slug = params.slug as string;
  const [resumo, setResumo] = useState<ResumoSalao | null>(null);
  const [profissionais, setProfissionais] = useState(0);
  const [servicos, setServicos] = useState(0);
  const [erro, setErro] = useState("");

  useEffect(() => {
    Promise.all([SalaoAPI.resumo(), SalaoAPI.profissionais(), SalaoAPI.servicos()])
      .then(([dados, listaProfissionais, listaServicos]) => {
        setResumo(dados);
        setProfissionais(listaProfissionais.length);
        setServicos(listaServicos.length);
      })
      .catch((exc: Error) => setErro(exc.message));
  }, []);

  if (erro) return <p className="text-sm text-red-700">{erro}</p>;
  if (!resumo) return <p className="text-sm text-[#8a6e74]">Carregando o painel...</p>;

  const cadastro = { profissionais, servicos };
  if (painel === "gestao") return <PainelGestao resumo={resumo} slug={slug} cadastro={cadastro} />;
  if (painel === "semana") return <PainelSemana resumo={resumo} slug={slug} cadastro={cadastro} />;
  return <PainelOperacao resumo={resumo} slug={slug} cadastro={cadastro} />;
}

function AvisosCadastro({ slug, cadastro }: { slug: string; cadastro: { profissionais: number; servicos: number } }) {
  if (cadastro.profissionais > 0 && cadastro.servicos > 0) return null;
  return (
    <div className="mb-4 grid gap-3 sm:grid-cols-2">
      {cadastro.profissionais === 0 ? (
        <Vazio texto="Nenhum profissional cadastrado." href={`/loja/${slug}/salao-cabeleireiro/profissionais`} acao="Cadastrar profissional" />
      ) : null}
      {cadastro.servicos === 0 ? (
        <Vazio texto="Nenhum serviço registrado." href={`/loja/${slug}/salao-cabeleireiro/servicos`} acao="Cadastrar serviço" />
      ) : null}
    </div>
  );
}

function PainelOperacao({ resumo, slug, cadastro }: { resumo: ResumoSalao; slug: string; cadastro: { profissionais: number; servicos: number } }) {
  const maior = Math.max(...resumo.semana.map((dia) => dia.total), 1);
  const hoje = new Date();
  const rotuloHoje = hoje.toLocaleDateString("pt-BR", { weekday: "short", day: "numeric", month: "short" });
  const base = `/loja/${slug}/salao-cabeleireiro`;
  return (
    <div>
      <Cabeca titulo="Dashboard" texto="Gestão do salão" acao={{ href: `${base}/agenda`, nome: "Novo agendamento", cor: "#7A3044" }} />
      <AvisosCadastro slug={slug} cadastro={cadastro} />
      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Cartao titulo="Agendamentos de hoje" valor={resumo.hoje.agendamentos} cor="#7A3044" />
        <Cartao titulo="Faturamento do dia" valor={resumo.hoje.faturamento} cor="#a16207" />
        <Cartao titulo="Clientes ativos" valor={resumo.mes.clientes_ativos} cor="#7A3044" />
        <Cartao titulo="Taxa de ocupação" valor={`${resumo.hoje.ocupacao}%`} cor="#9a3412" />
      </div>
      <div className="grid gap-3 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,0.9fr)]">
        <section className="min-w-0 rounded-3xl border border-[#f0e4e6] bg-white p-4">
          <h2 className="mb-4 text-sm font-medium">Agendamentos da semana</h2>
          {resumo.semana.every((dia) => dia.total === 0) ? (
            <Vazio texto="Nenhum agendamento nesta semana." href={`${base}/agenda`} acao="Novo agendamento" />
          ) : null}
          <div className="mt-3 flex h-44 items-end gap-1 sm:gap-2">
            {resumo.semana.map((dia) => (
              <div key={dia.data} className="flex min-w-0 flex-1 flex-col items-center justify-end">
                <span className="mb-1 text-xs text-[#8a6e74]">{dia.total}</span>
                <i className="block w-full max-w-8 rounded-t-lg" style={{ height: `${Math.max(6, (dia.total / maior) * 130)}px`, background: diaDaSemana(dia.data) === hoje.getDay() ? "#7A3044" : "#e7b7c0" }} />
                <span className="mt-2 truncate text-[11px] capitalize text-[#8a6e74] sm:text-xs">{diaCurto(dia.data)}</span>
              </div>
            ))}
          </div>
        </section>
        <section className="min-w-0 rounded-3xl border border-[#f0e4e6] bg-white p-4">
          <div className="mb-2 flex items-center justify-between gap-2">
            <h2 className="text-sm font-medium">Agenda de hoje</h2>
            <span className="text-xs capitalize text-[#8a6e74]">{rotuloHoje}</span>
          </div>
          {resumo.agenda_hoje.length === 0 ? <Vazio texto="Nenhum agendamento hoje." href={`${base}/agenda`} acao="Novo agendamento" /> : null}
          <div className="max-h-72 overflow-auto">
            {resumo.agenda_hoje.map((item) => (
              <Link key={item.id} href={`${base}/agenda?horario=${item.id}`} className="block border-t border-[#f6ecee] py-2 text-sm hover:bg-[#fbf6f4]">
                <span className="flex items-start justify-between gap-2">
                  <span className="min-w-0">
                    <span className="font-medium">{item.hora}</span>
                    <span className="ml-2">{item.cliente}</span>
                    <small className="mt-0.5 block text-[#8a6e74]">{item.servico} · {item.profissional}</small>
                  </span>
                  <Selo status={item.status} texto={item.status_label} />
                </span>
              </Link>
            ))}
          </div>
        </section>
      </div>
      <section className="mt-3 rounded-3xl border border-[#f0e4e6] bg-white p-4">
        <h2 className="mb-2 text-sm font-medium">Próximos horários</h2>
        {proximos(resumo).length === 0 ? <p className="text-sm text-[#8a6e74]">Nenhum horário marcado daqui para frente.</p> : null}
        {proximos(resumo).map((item) => (
          <Link key={item.id} href={`${base}/agenda?horario=${item.id}`} className="grid grid-cols-1 gap-1 border-t border-[#f6ecee] py-2 text-sm hover:bg-[#fbf6f4] sm:grid-cols-[72px_1fr_auto] sm:items-center">
            <span>{item.hora}</span>
            <span>{item.servico}<small className="block text-[#8a6e74]">{item.cliente} · {item.profissional}</small></span>
            <Selo status={item.status} texto={item.status_label} />
          </Link>
        ))}
      </section>
    </div>
  );
}

function PainelSemana({ resumo, slug, cadastro }: { resumo: ResumoSalao; slug: string; cadastro: { profissionais: number; servicos: number } }) {
  const [profissionais, setProfissionais] = useState<ProfissionalSalao[]>([]);
  const [eventos, setEventos] = useState<AgendamentoSalao[]>([]);
  const semana = useMemo(() => {
    const inicio = inicioDaSemana(new Date());
    const fim = new Date(inicio);
    fim.setDate(fim.getDate() + 7);
    return { inicio, fim };
  }, []);
  const dias = Array.from({ length: 7 }, (_, indice) => {
    const data = new Date(semana.inicio);
    data.setDate(semana.inicio.getDate() + indice);
    return data;
  });
  const base = `/loja/${slug}/salao-cabeleireiro`;

  useEffect(() => {
    Promise.all([
      SalaoAPI.profissionais(),
      SalaoAPI.agenda(paraApi(semana.inicio), paraApi(semana.fim)),
    ]).then(([lista, agenda]) => {
      setProfissionais(lista);
      setEventos(agenda.filter((item) => item.status !== "CANCELLED"));
    }).catch(() => undefined);
  }, [semana]);

  const corDe = new Map(profissionais.map((item, indice) => [item.id, CORES_PROFISSIONAL[indice % CORES_PROFISSIONAL.length]]));
  const emAtendimento = resumo.agenda_hoje.filter((item) => item.status === "IN_PROGRESS");
  const horaAgora = new Date().getHours();
  const saudacao = horaAgora < 12 ? "Bom dia" : horaAgora < 18 ? "Boa tarde" : "Boa noite";

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold sm:text-3xl">{saudacao}</h1>
          <p className="text-sm text-[#6d6480]">Aqui está a agenda e a operação do seu salão hoje.</p>
        </div>
        <Link href={`${base}/agenda`} className="rounded-full bg-[#4c1d78] px-4 py-2 text-sm text-white">Novo agendamento</Link>
      </div>
      <AvisosCadastro slug={slug} cadastro={cadastro} />
      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <Cartao titulo="Agendamentos hoje" valor={resumo.hoje.agendamentos} cor="#4c1d78" />
        <Cartao titulo="Em atendimento" valor={resumo.hoje.em_andamento} cor="#7c3aed" />
        <Cartao titulo="Concluídos" valor={resumo.hoje.concluidos} cor="#059669" />
        <Cartao titulo="Taxa de ocupação" valor={`${resumo.hoje.ocupacao}%`} cor="#6d28d9" />
        <Cartao titulo="Faturamento do dia" valor={resumo.hoje.faturamento} cor="#4c1d78" />
      </div>
      <div className="grid gap-3 xl:grid-cols-[minmax(0,1.5fr)_minmax(16rem,0.7fr)]">
        <section className="min-w-0 overflow-auto rounded-3xl border border-[#ece7f5] bg-white p-4">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-medium">Agenda semanal</h2>
            <span className="text-xs text-[#6d6480]">{semana.inicio.toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })} – {new Date(semana.fim.getTime() - 86400000).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })}</span>
          </div>
          {eventos.length === 0 ? <Vazio texto="Nenhum agendamento nesta semana." href={`${base}/agenda`} acao="Novo agendamento" /> : null}
          <div className="grid min-w-[640px]" style={{ gridTemplateColumns: "52px repeat(7, minmax(0, 1fr))" }}>
            <span />
            {dias.map((dia) => (
              <span key={dia.toISOString()} className={`px-1 pb-2 text-center text-xs ${mesmoDia(dia, new Date()) ? "font-semibold text-[#4c1d78]" : "text-[#6d6480]"}`}>
                {dia.toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit" })}
              </span>
            ))}
            {Array.from({ length: 11 }, (_, indice) => indice + 9).map((hora) => (
              <div key={hora} className="contents">
                <span className="py-2 text-xs text-[#6d6480]">{String(hora).padStart(2, "0")}:00</span>
                {dias.map((dia) => {
                  const lista = eventos.filter((item) => mesmoDia(new Date(item.inicio), dia) && new Date(item.inicio).getHours() === hora);
                  return (
                    <div key={`${hora}-${dia.toDateString()}`} className={`min-h-10 border-t border-[#f3eef8] p-0.5 ${mesmoDia(dia, new Date()) ? "bg-[#faf8ff]" : ""}`}>
                      {lista.map((item) => (
                        <Link key={item.id} href={`${base}/agenda?horario=${item.id}`} className="mb-0.5 block truncate rounded px-1 py-0.5 text-[10px] leading-tight text-white" style={{ background: corDe.get(item.profissional) || "#7c3aed" }} title={`${item.cliente_nome} · ${item.servico_nome} · ${item.profissional_nome}`}>
                          {item.cliente_nome}
                        </Link>
                      ))}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-3 text-xs text-[#6d6480]">
            {profissionais.map((item) => (
              <span key={item.id} className="inline-flex items-center gap-1">
                <i className="h-2 w-2 rounded-full" style={{ background: corDe.get(item.id) }} />
                {item.nome}
              </span>
            ))}
          </div>
        </section>
        <section className="min-w-0 rounded-3xl border border-[#ece7f5] bg-white p-4">
          <h2 className="mb-2 text-sm font-medium">Clientes de hoje ({resumo.agenda_hoje.length})</h2>
          {resumo.agenda_hoje.length === 0 ? <Vazio texto="Nenhum agendamento hoje." href={`${base}/agenda`} acao="Novo agendamento" /> : null}
          <div className="max-h-[28rem] overflow-auto">
            {resumo.agenda_hoje.map((item) => (
              <Link key={item.id} href={`${base}/agenda?horario=${item.id}`} className="flex items-center gap-2 border-t border-[#f3eef8] py-2 text-sm hover:bg-[#faf8ff]">
                <Iniciais nome={item.cliente} cor="#4c1d78" />
                <span className="min-w-0 flex-1">
                  <span className="block truncate">{item.cliente}</span>
                  <small className="text-[#6d6480]">{item.servico} · {item.profissional} · {item.hora}</small>
                </span>
                <Selo status={item.status} texto={item.status_label} />
              </Link>
            ))}
          </div>
        </section>
      </div>
      <div className="mt-3 grid gap-3 lg:grid-cols-3">
        <section className="flex items-center gap-4 rounded-3xl border border-[#ece7f5] bg-white p-4">
          <div className="grid h-20 w-20 shrink-0 place-items-center rounded-full text-sm font-semibold" style={{ background: `conic-gradient(#4c1d78 ${resumo.hoje.ocupacao * 3.6}deg, #ece7f5 0)` }}>
            <span className="grid h-14 w-14 place-items-center rounded-full bg-white">{resumo.hoje.ocupacao}%</span>
          </div>
          <div>
            <h2 className="text-sm font-medium">Ocupação do salão</h2>
            <p className="text-xs text-[#6d6480]">{resumo.hoje.em_andamento} em atendimento · {resumo.hoje.concluidos} concluídos</p>
          </div>
        </section>
        <section className="rounded-3xl border border-[#ece7f5] bg-white p-4">
          <h2 className="mb-2 text-sm font-medium">Serviços do mês</h2>
          {resumo.servicos.length === 0 ? <p className="text-sm text-[#6d6480]">Nenhum atendimento concluído no período.</p> : null}
          {resumo.servicos.map((item) => (
            <div key={item.nome} className="mb-2 text-sm">
              <div className="flex justify-between gap-2"><span className="truncate">{item.nome}</span><span>{item.quantidade}</span></div>
              <i className="mt-1 block h-1.5 rounded-full bg-[#ddd6fe]" style={{ width: `${Math.max(8, (item.quantidade / Math.max(...resumo.servicos.map((servico) => servico.quantidade), 1)) * 100)}%` }} />
            </div>
          ))}
        </section>
        <section className="rounded-3xl border border-[#ece7f5] bg-white p-4">
          <h2 className="mb-2 flex items-center gap-2 text-sm font-medium"><Users size={16} /> Em atendimento ({emAtendimento.length})</h2>
          {emAtendimento.length === 0 ? <p className="text-sm text-[#6d6480]">Ninguém em atendimento agora.</p> : null}
          <div className="flex flex-wrap gap-3">
            {emAtendimento.map((item) => (
              <span key={item.id} className="text-center text-xs">
                <Iniciais nome={item.profissional} cor="#4c1d78" />
                <span className="mt-1 block max-w-16 truncate">{item.profissional.split(" ")[0]}</span>
              </span>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

function PainelGestao({ resumo, slug, cadastro }: { resumo: ResumoSalao; slug: string; cadastro: { profissionais: number; servicos: number } }) {
  const serie = resumo.serie_mes || [];
  const maior = Math.max(...serie.map((dia) => dia.valor), 1);
  const hoje = new Date().getDate();
  const hora = new Date().getHours();
  const saudacao = hora < 12 ? "Bom dia" : hora < 18 ? "Boa tarde" : "Boa noite";
  const mes = new Date().toLocaleDateString("pt-BR", { month: "long" });
  const base = `/loja/${slug}/salao-cabeleireiro`;
  const semReceita = serie.every((dia) => dia.valor === 0);
  return (
    <div>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold sm:text-3xl">{saudacao}, equipe</h1>
          <p className="text-sm text-[#607064]">Receita dos atendimentos concluídos em {mes}.</p>
        </div>
        <Link href={`${base}/clientes`} className="inline-flex items-center gap-1 rounded-full bg-[#3d5244] px-4 py-2 text-sm text-white">
          <Users size={15} /> Novo cliente
        </Link>
      </div>
      <AvisosCadastro slug={slug} cadastro={cadastro} />
      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Cartao titulo="Receita do mês" valor={resumo.mes.receita} cor="#3d5244" />
        <Cartao titulo="Novos clientes" valor={resumo.mes.novos_clientes} cor="#3d5244" />
        <Cartao titulo="Ticket médio" valor={resumo.mes.ticket} cor="#3d5244" />
        <Cartao titulo="Clientes ativos" valor={resumo.mes.clientes_ativos} cor="#3d5244" />
      </div>
      <div className="grid gap-3 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,0.8fr)]">
        <section className="min-w-0 rounded-3xl border border-[#e4eadf] bg-white p-4">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-medium">Faturamento do período</h2>
            <span className="text-sm text-[#3d5244]">{resumo.mes.receita}</span>
          </div>
          {semReceita ? <Vazio texto="Nenhum atendimento concluído no período." href={`${base}/agenda`} acao="Abrir a agenda" /> : null}
          <div className="mt-3 flex h-40 items-end gap-px overflow-x-auto">
            {serie.map((dia) => (
              <i
                key={dia.dia}
                title={`${dia.dia}: ${dia.valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}`}
                className="min-w-[6px] flex-1 rounded-t"
                style={{ height: `${Math.max(dia.valor > 0 ? 6 : 2, (dia.valor / maior) * 140)}px`, background: dia.dia === hoje ? "#3d5244" : "#b7c9a8" }}
              />
            ))}
          </div>
        </section>
        <section className="min-w-0 rounded-3xl border border-[#e4eadf] bg-white p-4">
          <h2 className="mb-2 flex items-center gap-2 text-sm font-medium"><Scissors size={16} /> Serviços mais vendidos</h2>
          {resumo.servicos.length === 0 ? <p className="text-sm text-[#607064]">Nenhum atendimento concluído no período.</p> : null}
          {resumo.servicos.map((item, indice) => (
            <div key={item.nome} className="grid grid-cols-[20px_minmax(0,1fr)_auto] gap-2 border-t border-[#eef3ea] py-2 text-sm">
              <span className="text-[#8aaa78]">{indice + 1}</span>
              <span className="truncate">{item.nome}<small className="block text-[#607064]">{item.quantidade}</small></span>
              <span>{item.receita}</span>
            </div>
          ))}
        </section>
      </div>
      <section className="mt-3 rounded-3xl border border-[#e4eadf] bg-white p-4">
        <h2 className="mb-2 flex items-center gap-2 text-sm font-medium"><Gift size={16} /> Aniversariantes do mês</h2>
        {resumo.aniversariantes.length === 0 ? (
          <Vazio texto="Nenhum aniversário com data cadastrada." href={`${base}/clientes`} acao="Cadastrar cliente" />
        ) : null}
        <div className="grid gap-2 md:grid-cols-2">
          {resumo.aniversariantes.map((item) => (
            <div key={`${item.nome}-${item.dia}`} className="flex items-center justify-between gap-2 rounded-2xl bg-[#f7f4ee] px-3 py-2 text-sm">
              <span className="inline-flex min-w-0 items-center gap-2"><Iniciais nome={item.nome} cor="#3d5244" /><span className="truncate">{item.nome}</span></span>
              <span className="shrink-0 text-[#607064]">{item.dia}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function Cabeca({ titulo, texto, acao }: { titulo: string; texto: string; acao: { href: string; nome: string; cor: string } }) {
  return (
    <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
      <div className="min-w-0">
        <h1 className="text-2xl font-semibold sm:text-3xl">{titulo}</h1>
        <p className="text-sm text-[#8a6e74]">{texto}</p>
      </div>
      <Link href={acao.href} className="inline-flex items-center gap-1 rounded-full px-4 py-2 text-sm text-white" style={{ background: acao.cor }}>
        <CalendarPlus size={15} /> {acao.nome}
      </Link>
    </div>
  );
}

function Cartao({ titulo, valor, cor }: { titulo: string; valor: string | number; cor: string }) {
  return (
    <article className="min-h-[92px] rounded-3xl border border-black/5 bg-white p-4">
      <p className="text-sm text-[#8a6e74]">{titulo}</p>
      <p className="mt-1 text-2xl font-semibold" style={{ color: cor }}>{valor}</p>
    </article>
  );
}

function Vazio({ texto, href, acao }: { texto: string; href: string; acao: string }) {
  return (
    <p className="rounded-2xl bg-black/[0.03] px-3 py-2 text-sm text-[#8a6e74]">
      {texto} <Link href={href} className="font-medium text-inherit underline">{acao}</Link>
    </p>
  );
}

function Iniciais({ nome, cor }: { nome: string; cor: string }) {
  const letras = nome.split(" ").filter(Boolean).slice(0, 2).map((parte) => parte[0]?.toUpperCase() || "").join("");
  return <span className="inline-grid h-7 w-7 shrink-0 place-items-center rounded-full text-[10px] text-white" style={{ background: cor }}>{letras || "?"}</span>;
}

function Selo({ status, texto }: { status: string; texto: string }) {
  const cor = status === "COMPLETED" ? "#1f8a4c" : status === "IN_PROGRESS" ? "#4c1d78" : status === "CONFIRMED" ? "#1d4ed8" : "#a16207";
  return <span className="shrink-0 rounded-full px-2 py-0.5 text-[11px]" style={{ color: cor, background: `${cor}18` }}>{texto}</span>;
}

function proximos(resumo: ResumoSalao) {
  const agora = new Date();
  const marca = `${String(agora.getHours()).padStart(2, "0")}:${String(agora.getMinutes()).padStart(2, "0")}`;
  return resumo.agenda_hoje.filter((item) => item.hora >= marca && item.status !== "CANCELLED" && item.status !== "COMPLETED" && item.status !== "NO_SHOW");
}

function diaCurto(iso: string) {
  return new Date(`${iso}T12:00:00`).toLocaleDateString("pt-BR", { weekday: "short" }).replace(".", "");
}

function diaDaSemana(iso: string) {
  return new Date(`${iso}T12:00:00`).getDay();
}

function dois(valor: number) {
  return String(valor).padStart(2, "0");
}

function paraApi(data: Date) {
  return `${data.getFullYear()}-${dois(data.getMonth() + 1)}-${dois(data.getDate())}T${dois(data.getHours())}:${dois(data.getMinutes())}:00`;
}

function inicioDaSemana(data: Date) {
  const copia = new Date(data);
  copia.setHours(0, 0, 0, 0);
  copia.setDate(copia.getDate() - ((copia.getDay() + 6) % 7));
  return copia;
}

function mesmoDia(esquerda: Date, direita: Date) {
  return esquerda.getFullYear() === direita.getFullYear() && esquerda.getMonth() === direita.getMonth() && esquerda.getDate() === direita.getDate();
}
