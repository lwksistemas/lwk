"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { CalendarDays, CalendarPlus, Check, Clock, Gift, Percent, Scissors, Search, Users, Wallet } from "lucide-react";
import { STATUS_PADRAO, useStatusSalao } from "@/components/salao/cores-salao";
import { SalaoAPI, type AgendamentoSalao, type BloqueioSalao, type JornadaDia, type PainelSalao, type ProfissionalSalao, type ResumoSalao } from "@/lib/salao-api";
import { agendaDemonstracao, bloqueiosDemonstracao, jornadasDemonstracao, profissionaisDemonstracao, resumoDemonstracao } from "@/components/salao/demonstracao-salao";

export function PainelDoSalao({ painel, demonstracao = false }: { painel: PainelSalao; demonstracao?: boolean }) {
  const params = useParams();
  const slug = params.slug as string;
  const [resumo, setResumo] = useState<ResumoSalao | null>(null);
  const [profissionais, setProfissionais] = useState(0);
  const [servicos, setServicos] = useState(0);
  const [erro, setErro] = useState("");

  useEffect(() => {
    if (demonstracao) {
      setResumo(resumoDemonstracao());
      setProfissionais(profissionaisDemonstracao().length);
      setServicos(6);
      setErro("");
      return;
    }
    Promise.all([SalaoAPI.resumo(), SalaoAPI.profissionais(), SalaoAPI.servicos()])
      .then(([dados, listaProfissionais, listaServicos]) => {
        setResumo(dados);
        setProfissionais(listaProfissionais.length);
        setServicos(listaServicos.length);
      })
      .catch((exc: Error) => setErro(exc.message));
  }, [demonstracao]);

  if (erro) return <p className="text-sm text-red-700">{erro}</p>;
  if (!resumo) return <p className="text-sm text-[#8a6e74]">Carregando o painel...</p>;

  const cadastro = { profissionais, servicos };
  const miolo = painel === "gestao"
    ? <PainelGestao resumo={resumo} slug={slug} cadastro={cadastro} />
    : painel === "semana"
      ? <PainelSemana resumo={resumo} slug={slug} cadastro={cadastro} demonstracao={demonstracao} />
      : <PainelOperacao resumo={resumo} slug={slug} cadastro={cadastro} demonstracao={demonstracao} />;
  if (!demonstracao) return miolo;
  return (
    <div
      onClickCapture={(evento) => {
        const link = (evento.target as HTMLElement).closest("a");
        if (!link) return;
        evento.preventDefault();
        evento.stopPropagation();
      }}
    >
      {miolo}
    </div>
  );
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

function PainelOperacao({ resumo, slug, cadastro, demonstracao = false }: { resumo: ResumoSalao; slug: string; cadastro: { profissionais: number; servicos: number }; demonstracao?: boolean }) {
  const [equipe, setEquipe] = useState<ProfissionalSalao[]>([]);
  const [jornadas, setJornadas] = useState<Record<number, JornadaDia[]>>({});
  const [agenda, setAgenda] = useState<AgendamentoSalao[]>([]);
  const maior = Math.max(...resumo.semana.map((dia) => dia.total), 1);
  const hoje = new Date();
  const rotuloHoje = hoje.toLocaleDateString("pt-BR", { weekday: "short", day: "numeric", month: "short" });
  const base = `/loja/${slug}/salao-cabeleireiro`;
  const livres = useMemo(() => horariosLivres(equipe, jornadas, agenda, `${base}/agenda`), [equipe, jornadas, agenda, base]);

  useEffect(() => {
    if (demonstracao) {
      setEquipe(profissionaisDemonstracao());
      setJornadas(jornadasDemonstracao());
      setAgenda(agendaDemonstracao());
      return;
    }
    const inicio = new Date();
    inicio.setHours(0, 0, 0, 0);
    const fim = new Date(inicio);
    fim.setDate(fim.getDate() + 1);
    Promise.all([SalaoAPI.profissionais(), SalaoAPI.agenda(paraApi(inicio), paraApi(fim))])
      .then(async ([lista, eventos]) => {
        setEquipe(lista);
        setAgenda(eventos);
        const pares = await Promise.all(lista.map(async (pessoa) => [pessoa.id, await SalaoAPI.jornada(pessoa.id)] as const));
        setJornadas(Object.fromEntries(pares));
      })
      .catch(() => undefined);
  }, [demonstracao]);

  return (
    <div>
      <Cabeca titulo="Dashboard" texto="Gestão do salão de beleza" acao={{ href: `${base}/agenda`, nome: "Novo agendamento", cor: "#7A3044" }} />
      <AvisosCadastro slug={slug} cadastro={cadastro} />
      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Cartao titulo="Agendamentos de hoje" valor={resumo.hoje.agendamentos} cor="#7A3044" icone={<CalendarDays size={16} />} detalhe={textoVariacao(resumo.hoje.agendamentos, resumo.hoje.agendamentos_ontem, "em relação a ontem")} />
        <Cartao titulo="Faturamento do mês" valor={resumo.mes.receita} cor="#7A3044" icone={<Wallet size={16} />} detalhe={textoVariacao(resumo.mes.receita_valor, resumo.mes.receita_anterior_valor, "em relação ao mês anterior")} />
        <Cartao titulo="Clientes ativos" valor={resumo.mes.clientes_ativos} cor="#7A3044" icone={<Users size={16} />} detalhe="Total cadastrado" />
        <Cartao titulo="Taxa de ocupação" valor={`${resumo.hoje.ocupacao}%`} cor="#9a3412" icone={<Percent size={16} />} detalhe="Dos horários de hoje" />
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
                <span className="truncate text-[10px] text-[#b08990]">{dataCurta(dia.data)}</span>
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
              <Link key={item.id} href={`${base}/agenda?horario=${item.id}`} className="grid grid-cols-[3.2rem_auto_minmax(0,1fr)_auto] items-center gap-2 border-t border-[#f6ecee] py-2 text-sm hover:bg-[#fbf6f4]">
                <span className="font-medium text-[#7A3044]">{item.hora}</span>
                <Iniciais nome={item.cliente} cor="#7A3044" />
                <span className="min-w-0">
                  <span className="block truncate font-medium">{item.cliente}</span>
                  <small className="block truncate text-[#8a6e74]">{item.servico}</small>
                </span>
                <Selo status={item.status} texto={item.status_label} />
              </Link>
            ))}
          </div>
        </section>
      </div>
      <section className="mt-3 rounded-3xl border border-[#f0e4e6] bg-white p-4">
        <h2 className="mb-2 flex items-center gap-2 text-sm font-medium"><Clock size={16} /> Próximos horários</h2>
        {livres.length === 0 ? <p className="text-sm text-[#8a6e74]">Nenhum horário livre no restante de hoje.</p> : null}
        {livres.map((item) => (
          <div key={`${item.profissionalId}-${item.hora}`} className="grid grid-cols-1 items-center gap-2 border-t border-[#f6ecee] py-2 text-sm sm:grid-cols-[72px_1fr_auto_auto]">
            <span className="inline-flex items-center gap-1 text-[#7A3044]"><CalendarDays size={14} />{item.hora}</span>
            <span>{item.rotulo}<small className="block text-[#8a6e74]">{item.profissional}</small></span>
            <span className="text-emerald-600">Disponível</span>
            <Link href={item.href} className="justify-self-start rounded-full bg-[#7A3044] px-3 py-1 text-xs text-white">Agendar</Link>
          </div>
        ))}
      </section>
    </div>
  );
}

function PainelSemana({ resumo, slug, cadastro, demonstracao = false }: { resumo: ResumoSalao; slug: string; cadastro: { profissionais: number; servicos: number }; demonstracao?: boolean }) {
  const [profissionais, setProfissionais] = useState<ProfissionalSalao[]>([]);
  const [eventos, setEventos] = useState<AgendamentoSalao[]>([]);
  const [jornadas, setJornadas] = useState<Record<number, JornadaDia[]>>({});
  const [bloqueios, setBloqueios] = useState<BloqueioSalao[]>([]);
  const [cursor, setCursor] = useState(() => inicioDaSemana(new Date()));
  const [filtro, setFiltro] = useState<number | "todos">("todos");
  const [busca, setBusca] = useState("");
  const [nomeUsuario, setNomeUsuario] = useState("");
  const [visao, setVisao] = useState<"dia" | "semana">("semana");
  const semana = useMemo(() => {
    const inicio = inicioDaSemana(cursor);
    const fim = new Date(inicio);
    fim.setDate(fim.getDate() + 7);
    return { inicio, fim };
  }, [cursor]);
  const diasSemana = Array.from({ length: 7 }, (_, indice) => {
    const data = new Date(semana.inicio);
    data.setDate(semana.inicio.getDate() + indice);
    return data;
  });
  const hojeCalendario = new Date();
  hojeCalendario.setHours(12, 0, 0, 0);
  const dias = visao === "dia" ? [hojeCalendario] : diasSemana;
  const base = `/loja/${slug}/salao-cabeleireiro`;

  useEffect(() => {
    if (demonstracao) {
      setProfissionais(profissionaisDemonstracao());
      setEventos(agendaDemonstracao().filter((item) => item.status !== "CANCELLED"));
      setBloqueios(bloqueiosDemonstracao());
      setJornadas(jornadasDemonstracao());
      return;
    }
    SalaoAPI.config().then((dados) => setNomeUsuario(dados.operador_nome || "")).catch(() => undefined);
    Promise.all([
      SalaoAPI.profissionais(),
      SalaoAPI.agenda(paraApi(semana.inicio), paraApi(semana.fim)),
      SalaoAPI.bloqueios(),
    ]).then(async ([lista, agenda, folgas]) => {
      setProfissionais(lista);
      setEventos(agenda.filter((item) => item.status !== "CANCELLED"));
      setBloqueios(folgas);
      const pares = await Promise.all(lista.map(async (pessoa) => [pessoa.id, await SalaoAPI.jornada(pessoa.id)] as const));
      setJornadas(Object.fromEntries(pares));
    }).catch(() => undefined);
  }, [demonstracao, semana]);

  const termo = busca.trim().toLocaleLowerCase();
  const visiveis = (filtro === "todos" ? eventos : eventos.filter((item) => fatiasDo(item).some((fatia) => fatia.profissional === filtro)))
    .filter((item) => !termo || `${item.cliente_nome} ${item.servico_nome} ${item.profissional_nome} ${fatiasDo(item).map((fatia) => `${fatia.servico_nome} ${fatia.profissional_nome}`).join(" ")}`.toLocaleLowerCase().includes(termo));
  const jornadaFiltro = filtro === "todos" ? Object.values(jornadas).flat() : jornadas[filtro];
  const faixa = faixaHoras(Array.isArray(jornadaFiltro) ? jornadaFiltro : undefined);
  const horas = Array.from({ length: Math.max(faixa.fim - faixa.inicio, 1) }, (_, indice) => faixa.inicio + indice);
  const emAtendimento = resumo.agenda_hoje.filter((item) => item.status === "IN_PROGRESS");
  const horaAgora = new Date().getHours();
  const saudacao = horaAgora < 12 ? "Bom dia" : horaAgora < 18 ? "Boa tarde" : "Boa noite";
  const primeiroNome = nomeUsuario.trim().split(" ")[0];
  const coresProfissional = new Map(profissionais.map((pessoa, indice) => [pessoa.id, COR_PROFISSIONAL[indice % COR_PROFISSIONAL.length]]));

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold sm:text-3xl">{saudacao}{primeiroNome ? `, ${primeiroNome}!` : ""}</h1>
          <p className="text-sm text-[#6d6480]">Aqui está a agenda e a operação do seu salão hoje.</p>
        </div>
        <label className="flex min-w-[14rem] flex-1 items-center gap-2 rounded-full border border-[#ece7f5] bg-white px-3 py-2 text-sm text-[#6d6480]">
          <Search size={15} />
          <input value={busca} onChange={(evento) => setBusca(evento.target.value)} placeholder="Buscar cliente, serviço, profissional..." className="w-full bg-transparent outline-none" />
        </label>
        <Link href={`${base}/agenda`} className="rounded-full bg-[#4c1d78] px-4 py-2 text-sm text-white">Novo agendamento</Link>
      </div>
      <AvisosCadastro slug={slug} cadastro={cadastro} />
      <div className="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-5">
        <Cartao titulo="Atendimentos hoje" valor={resumo.hoje.agendamentos} cor="#4c1d78" icone={<CalendarDays size={16} />} detalhe={textoVariacao(resumo.hoje.agendamentos, resumo.hoje.agendamentos_ontem, "em relação a ontem")} />
        <Cartao titulo="Em atendimento" valor={resumo.hoje.em_andamento} cor="#7c3aed" icone={<Clock size={16} />} />
        <Cartao titulo="Concluídos" valor={resumo.hoje.concluidos} cor="#059669" icone={<Check size={16} />} />
        <Cartao titulo="Taxa de ocupação" valor={`${resumo.hoje.ocupacao}%`} cor="#6d28d9" icone={<Percent size={16} />} detalhe="Dos horários de hoje" />
        <Cartao titulo="Faturamento do dia" valor={resumo.hoje.faturamento} cor="#4c1d78" icone={<Wallet size={16} />} />
      </div>
      <div className="grid gap-3 xl:grid-cols-[minmax(0,1.5fr)_minmax(16rem,0.7fr)]">
        <section className="min-w-0 overflow-auto rounded-3xl border border-[#ece7f5] bg-white p-4">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-medium">Agenda semanal</h2>
            <div className="flex flex-wrap items-center gap-2">
              <button type="button" className="rounded-full border px-3 py-1 text-xs" onClick={() => setCursor(new Date(semana.inicio.getFullYear(), semana.inicio.getMonth(), semana.inicio.getDate() - 7))}>Anterior</button>
              <button type="button" className="rounded-full border px-3 py-1 text-xs" onClick={() => { setVisao("dia"); setCursor(inicioDaSemana(new Date())); }}>Dia</button>
              <button type="button" className={`rounded-full border px-3 py-1 text-xs ${visao === "semana" ? "bg-[#4c1d78] text-white" : ""}`} onClick={() => setVisao("semana")}>Semana</button>
              <Link href={`${base}/agenda`} className="rounded-full border px-3 py-1 text-xs">Mês</Link>
              <button type="button" className="rounded-full border px-3 py-1 text-xs" onClick={() => setCursor(new Date(semana.inicio.getFullYear(), semana.inicio.getMonth(), semana.inicio.getDate() + 7))}>Próxima</button>
              <span className="text-xs text-[#6d6480]">{(dias[0] || semana.inicio).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })} – {(dias[dias.length - 1] || new Date(semana.fim.getTime() - 86400000)).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })}</span>
            </div>
          </div>
          <label className="mb-3 flex items-center gap-2 text-sm text-[#6d6480]">
            Profissional
            <select className="rounded-lg border px-2 py-1" value={filtro} onChange={(evento) => setFiltro(evento.target.value === "todos" ? "todos" : Number(evento.target.value))}>
              <option value="todos">Todos</option>
              {profissionais.map((pessoa) => <option key={pessoa.id} value={pessoa.id}>{pessoa.nome}</option>)}
            </select>
          </label>
          {visiveis.length === 0 ? <Vazio texto="Nenhum agendamento nesta semana." href={`${base}/agenda`} acao="Novo agendamento" /> : null}
          <div className="grid min-w-[640px]" style={{ gridTemplateColumns: `52px repeat(${Math.max(dias.length, 1)}, minmax(0, 1fr))` }}>
            <span />
            {dias.map((dia) => (
              <span key={dia.toISOString()} className={`px-1 pb-2 text-center text-xs ${mesmoDia(dia, new Date()) ? "font-semibold text-[#4c1d78]" : "text-[#6d6480]"}`}>
                {dia.toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit" })}
              </span>
            ))}
            {horas.map((hora) => (
              <div key={hora} className="contents">
                <span className="py-2 text-xs text-[#6d6480]">{String(hora).padStart(2, "0")}:00</span>
                {dias.map((dia) => {
                  const aberto = diaTemAtendimento(dia, filtro, profissionais, jornadas);
                  if (!aberto) {
                    return (
                      <div key={`${hora}-${dia.toDateString()}`} className="grid min-h-12 place-items-center border-t border-[#f3eef8] bg-[#f7f5fb] text-[10px] text-[#b3a8c4]">
                        {hora === horas[Math.floor(horas.length / 2)] ? "Fechado" : ""}
                      </div>
                    );
                  }
                  const lista = visiveis.flatMap((item) => fatiasDo(item)
                    .filter((fatia) => (filtro === "todos" || fatia.profissional === filtro) && mesmoDia(new Date(fatia.inicio), dia) && new Date(fatia.inicio).getHours() === hora)
                    .map((fatia) => ({ ...item, profissional: fatia.profissional, profissional_nome: fatia.profissional_nome, servico_nome: fatia.servico_nome, inicio: fatia.inicio })));
                  const vaga = vagaDaHora(filtro, profissionais, jornadas, bloqueios, dia, hora);
                  const ocupados = new Set(lista.map((item) => item.profissional));
                  const podeCriar = vaga === "livre" && (filtro === "todos"
                    ? profissionais.some((pessoa) => !ocupados.has(pessoa.id) && situacaoHora(jornadas[pessoa.id] || [], bloqueios, pessoa.id, dia, hora) === "livre")
                    : lista.length === 0);
                  const momento = new Date(dia);
                  momento.setHours(hora, 0, 0, 0);
                  const destino = `${base}/agenda?novo=${encodeURIComponent(paraApi(momento))}${filtro === "todos" ? "" : `&profissional=${filtro}`}`;
                  const fundo = vaga === "livre" ? (mesmoDia(dia, new Date()) ? "bg-[#faf8ff]" : "") : "bg-[#f3f0f7]";
                  return (
                    <div key={`${hora}-${dia.toDateString()}`} className={`min-h-12 border-t border-[#f3eef8] p-0.5 ${fundo}`}>
                      {lista.map((item) => (
                        <Link key={`${item.id}-${item.profissional}-${item.inicio}`} href={`${base}/agenda?horario=${item.id}&dia=${dataLocal(new Date(item.inicio))}`} className="mb-0.5 block truncate rounded px-1 py-0.5 text-[10px] leading-tight" style={{ background: `${coresProfissional.get(item.profissional) || "#4c1d78"}22`, color: coresProfissional.get(item.profissional) || "#4c1d78" }} title={`${new Date(item.inicio).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })} · ${item.profissional_nome} · ${item.servico_nome} · ${item.cliente_nome}`}>
                          <span className="block truncate font-medium">{primeiro(item.profissional_nome)} · {item.servico_nome}</span>
                          <span className="block truncate">{item.cliente_nome}</span>
                        </Link>
                      ))}
                      {podeCriar ? <Link href={destino} className="block px-1 py-2 text-[10px] text-[#6d6480]" title="Novo agendamento">+</Link> : null}
                      {lista.length === 0 && vaga !== "livre" ? <span className="block px-1 py-2 text-[10px] text-[#b3a8c4]">{vaga === "intervalo" ? "Intervalo" : vaga === "folga" ? "Folga" : "Não atende"}</span> : null}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-3 text-xs text-[#6d6480]">
            {profissionais.map((pessoa) => (
              <span key={pessoa.id} className="inline-flex items-center gap-1">
                <i className="h-2 w-2 rounded-full" style={{ background: coresProfissional.get(pessoa.id) }} />
                {primeiro(pessoa.nome)}
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
            <p className="text-xs text-[#6d6480]">{resumo.hoje.em_andamento} em atendimento · {resumo.hoje.agendamentos - resumo.hoje.em_andamento - resumo.hoje.concluidos} agendados · {resumo.hoje.concluidos} concluídos</p>
          </div>
        </section>
        <section className="rounded-3xl border border-[#ece7f5] bg-white p-4">
          <h2 className="mb-2 text-sm font-medium">Serviços do mês</h2>
          {resumo.servicos.length === 0 ? <p className="text-sm text-[#6d6480]">Nenhum recebimento no período.</p> : null}
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
              <Link key={item.id} href={`${base}/agenda?horario=${item.id}`} className="text-center text-xs" title={`${item.cliente} · ${item.servico}`}>
                <Iniciais nome={item.profissional} cor="#4c1d78" />
                <span className="mt-1 block max-w-16 truncate">{primeiro(item.profissional)}</span>
                <span className="block max-w-16 truncate text-[10px] text-[#6d6480]">{equipeEspecialidade(profissionais, item.profissional)}</span>
              </Link>
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
          <p className="text-sm text-[#607064]">Recebido no caixa em {mes}. Atendimento concluído sem recebimento não entra aqui.</p>
        </div>
        <span className="rounded-full border border-black/10 bg-white px-3 py-2 text-sm text-[#607064]">Este mês</span>
        <Link href={`${base}/clientes`} className="inline-flex items-center gap-1 rounded-full bg-[#3d5244] px-4 py-2 text-sm text-white">
          <Users size={15} /> Novo cliente
        </Link>
      </div>
      <AvisosCadastro slug={slug} cadastro={cadastro} />
      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Cartao titulo="Receita do mês" valor={resumo.mes.receita} cor="#3d5244" icone={<Wallet size={16} />} detalhe={textoVariacao(resumo.mes.receita_valor, resumo.mes.receita_anterior_valor, "em relação ao mês anterior")} />
        <Cartao titulo="Novos clientes" valor={resumo.mes.novos_clientes} cor="#3d5244" icone={<Users size={16} />} detalhe={textoVariacao(resumo.mes.novos_clientes, resumo.mes.novos_anterior, "em relação ao mês anterior")} />
        <Cartao titulo="Ticket médio" valor={resumo.mes.ticket} cor="#3d5244" icone={<Scissors size={16} />} detalhe="Por recebimento no mês" />
        <Cartao titulo="Clientes ativos" valor={resumo.mes.clientes_ativos} cor="#3d5244" icone={<Users size={16} />} detalhe="Total cadastrado" />
      </div>
      <div className="grid gap-3 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,0.8fr)]">
        <section className="min-w-0 rounded-3xl border border-[#e4eadf] bg-white p-4">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-medium">Faturamento do período</h2>
            <span className="text-sm text-[#3d5244]">{resumo.mes.receita} {textoVariacao(resumo.mes.receita_valor, resumo.mes.receita_anterior_valor, "")}</span>
          </div>
          {semReceita ? <Vazio texto="Nenhum recebimento no período." href={`${base}/agenda`} acao="Abrir a agenda" /> : null}
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
          {resumo.servicos.length === 0 ? <p className="text-sm text-[#607064]">Nenhum recebimento no período.</p> : null}
          <div className="grid grid-cols-[28px_minmax(0,1fr)_72px_auto] gap-2 pb-1 text-[11px] uppercase tracking-wide text-[#8aaa78]">
            <span />
            <span>Serviço</span>
            <span>Qtd.</span>
            <span className="text-right">Receita</span>
          </div>
          {resumo.servicos.map((item, indice) => (
            <div key={item.nome} className="grid grid-cols-[28px_minmax(0,1fr)_72px_auto] items-center gap-2 border-t border-[#eef3ea] py-2 text-sm">
              <span className="grid h-5 w-5 place-items-center rounded-full bg-[#e7f0df] text-xs text-[#3d5244]">{indice + 1}</span>
              <span className="truncate">{item.nome}</span>
              <span className="text-[#607064]">{item.quantidade}</span>
              <span className="text-right">{item.receita}</span>
            </div>
          ))}
        </section>
      </div>
      <div className="mt-3 grid gap-3 lg:grid-cols-2">
      <section className="rounded-3xl border border-[#e4eadf] bg-white p-4">
        <h2 className="mb-2 flex items-center gap-2 text-sm font-medium"><Gift size={16} /> Aniversariantes do mês</h2>
        {resumo.aniversariantes.length === 0 ? (
          <Vazio texto="Nenhum aniversário com data cadastrada." href={`${base}/clientes`} acao="Cadastrar cliente" />
        ) : null}
        <div className="grid gap-2 md:grid-cols-2">
          {resumo.aniversariantes.map((item) => {
            const digitos = (item.telefone || "").replace(/\D/g, "");
            const fone = digitos.startsWith("55") && digitos.length >= 12 ? digitos : `55${digitos}`;
            const texto = `Parabéns, ${primeiro(item.nome)}! A equipe do salão deseja um ótimo dia.`;
            return (
              <div key={`${item.nome}-${item.dia}`} className="flex items-center justify-between gap-2 rounded-2xl bg-[#f7f4ee] px-3 py-2 text-sm">
                <span className="inline-flex min-w-0 items-center gap-2"><Iniciais nome={item.nome} cor="#3d5244" /><span className="min-w-0"><span className="block truncate">{item.nome}</span><small className="text-[#607064]">{rotuloAniversario(item.dia)}</small></span></span>
                {fone.length >= 10 ? (
                  <a href={`https://wa.me/${fone}?text=${encodeURIComponent(texto)}`} target="_blank" rel="noreferrer" className="shrink-0 rounded-full border border-[#c5d4bc] px-3 py-1 text-xs text-[#3d5244]">Parabenizar</a>
                ) : (
                  <span className="shrink-0 text-xs text-[#607064]">Sem WhatsApp</span>
                )}
              </div>
            );
          })}
        </div>
      </section>
      <section className="rounded-3xl border border-[#e4eadf] bg-white p-4">
        <h2 className="mb-2 text-sm font-medium">Comissões do mês</h2>
        {(resumo.comissoes || []).length === 0 ? (
          <Vazio texto="A comissão entra quando o atendimento é recebido no caixa." href={`${base}/agenda`} acao="Abrir a agenda" />
        ) : null}
        {(resumo.comissoes || []).map((item) => (
          <div key={item.nome} className="flex items-center justify-between gap-2 border-t border-[#eef3ea] py-2 text-sm">
            <span className="truncate">{item.nome}<small className="block text-[#607064]">{item.quantidade}</small></span>
            <span>{item.comissao}</span>
          </div>
        ))}
      </section>
      </div>
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
      <span className="rounded-full border border-black/10 bg-white px-3 py-2 text-sm text-[#6b5c60]">Este mês</span>
      <Link href={acao.href} className="inline-flex items-center gap-1 rounded-full px-4 py-2 text-sm text-white" style={{ background: acao.cor }}>
        <CalendarPlus size={15} /> {acao.nome}
      </Link>
    </div>
  );
}

function Cartao({ titulo, valor, cor, detalhe, icone }: { titulo: string; valor: string | number; cor: string; detalhe?: string | null; icone?: ReactNode }) {
  const percentual = Boolean(detalhe?.includes("%"));
  const queda = Boolean(detalhe?.startsWith("-"));
  return (
    <article className="min-h-[104px] rounded-3xl border border-black/5 bg-white p-4">
      <div className="mb-2 flex items-center gap-2">
        <span className="grid h-8 w-8 place-items-center rounded-full text-white" style={{ background: cor }}>{icone}</span>
        <p className="text-sm text-[#6b5c60]">{titulo}</p>
      </div>
      <p className="text-2xl font-semibold text-[#2b2426]">{valor}</p>
      {detalhe ? <p className={`mt-1 text-xs font-medium ${percentual ? (queda ? "text-red-600" : "text-emerald-600") : "text-[#8a6e74]"}`}>{detalhe}</p> : null}
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
  const cores = useStatusSalao();
  const cor = cores[status] || STATUS_PADRAO[status] || STATUS_PADRAO.SCHEDULED;
  return <span className="shrink-0 rounded-full px-2 py-0.5 text-[11px]" style={{ color: cor, background: `${cor}18` }}>{texto}</span>;
}

const COR_PROFISSIONAL = ["#7c3aed", "#059669", "#d97706", "#db2777", "#2563eb", "#0d9488"];

function primeiro(nome: string) {
  return nome.trim().split(" ")[0] || nome;
}

function textoVariacao(atual: number | undefined, anterior: number | undefined, complemento: string) {
  if (atual == null || anterior == null) return null;
  if (anterior <= 0) return null;
  const pct = Math.round(((atual - anterior) / anterior) * 100);
  const sinal = pct > 0 ? "+" : "";
  return `${sinal}${pct}% ${complemento}`.trim();
}

function dataCurta(iso: string) {
  const data = new Date(`${iso}T12:00:00`);
  return `${data.getDate()} ${data.toLocaleDateString("pt-BR", { month: "short" }).replace(".", "")}`;
}

function rotuloAniversario(dia: string) {
  const [numero, mes] = dia.split("/");
  const meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
  const nome = meses[Number(mes) - 1] || mes;
  const hoje = new Date();
  const ehHoje = hoje.getDate() === Number(numero) && hoje.getMonth() + 1 === Number(mes);
  return `${numero} de ${nome}${ehHoje ? " (hoje)" : ""}`;
}

function equipeEspecialidade(profissionais: ProfissionalSalao[], nome: string) {
  return profissionais.find((pessoa) => pessoa.nome === nome)?.especialidade || "";
}

function fatiasDo(item: AgendamentoSalao) {
  if (item.fatias && item.fatias.length > 0) return item.fatias;
  return [{
    profissional: item.profissional,
    profissional_nome: item.profissional_nome,
    servico_nome: item.servico_nome,
    inicio: item.inicio,
    fim: item.fim,
    duracao_minutos: item.duracao_minutos,
  }];
}

function horaOcupada(item: AgendamentoSalao, profissionalId: number, dia: Date, hora: number) {
  return fatiasDo(item).some((fatia) => {
    if (fatia.profissional !== profissionalId || !mesmoDia(new Date(fatia.inicio), dia)) return false;
    const inicio = new Date(fatia.inicio);
    const fim = new Date(fatia.fim);
    const comeco = inicio.getHours() + inicio.getMinutes() / 60;
    const termina = fim.getHours() + fim.getMinutes() / 60;
    return comeco < hora + 1 && termina > hora;
  });
}

function horariosLivres(profissionais: ProfissionalSalao[], jornadas: Record<number, JornadaDia[]>, agenda: AgendamentoSalao[], baseAgenda: string) {
  const agora = new Date();
  const vagas: { hora: string; rotulo: string; profissional: string; profissionalId: number; href: string }[] = [];
  for (const pessoa of profissionais) {
    if (vagas.length >= 3) break;
    for (let hora = agora.getHours(); hora < 20; hora += 1) {
      if (hora === agora.getHours() && agora.getMinutes() > 40) continue;
      if (situacaoHora(jornadas[pessoa.id] || [], [], pessoa.id, agora, hora) !== "livre") continue;
      const ocupado = agenda.some((item) => horaOcupada(item, pessoa.id, agora, hora));
      if (ocupado) continue;
      const momento = new Date(agora);
      momento.setHours(hora, 0, 0, 0);
      vagas.push({
        hora: `${dois(hora)}:00`,
        rotulo: pessoa.especialidade || "Horário livre",
        profissional: pessoa.nome,
        profissionalId: pessoa.id,
        href: `${baseAgenda}?novo=${encodeURIComponent(paraApi(momento))}&profissional=${pessoa.id}`,
      });
      break;
    }
  }
  return vagas.slice(0, 3);
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

export function diaTemAtendimento(
  dia: Date,
  filtro: number | "todos",
  profissionais: { id: number }[],
  jornadas: Record<number, JornadaDia[]>,
) {
  const pessoas = filtro === "todos" ? profissionais : profissionais.filter((pessoa) => pessoa.id === filtro);
  const comJornada = pessoas.filter((pessoa) => (jornadas[pessoa.id] || []).length > 0);
  if (!comJornada.length) return true;
  const indice = (dia.getDay() + 6) % 7;
  return comJornada.some((pessoa) => (jornadas[pessoa.id] || []).some((linha) => linha.dia_semana === indice && linha.ativo));
}

function mesmoDia(esquerda: Date, direita: Date) {
  return esquerda.getFullYear() === direita.getFullYear() && esquerda.getMonth() === direita.getMonth() && esquerda.getDate() === direita.getDate();
}

function minutos(valor: string) {
  const [hora, minuto] = valor.slice(0, 5).split(":").map(Number);
  return hora * 60 + (minuto || 0);
}

function dataLocal(data: Date) {
  return `${data.getFullYear()}-${dois(data.getMonth() + 1)}-${dois(data.getDate())}`;
}

function faixaHoras(dias?: JornadaDia[]) {
  const ativos = (dias || []).filter((dia) => dia.ativo && dia.hora_entrada && dia.hora_saida);
  if (!ativos.length) return { inicio: 9, fim: 19 };
  const inicio = Math.min(...ativos.map((dia) => Math.floor(minutos(dia.hora_entrada) / 60)));
  const fim = Math.max(...ativos.map((dia) => Math.ceil(minutos(dia.hora_saida) / 60)));
  return { inicio: Math.max(0, inicio), fim: Math.min(24, Math.max(inicio + 1, fim)) };
}

function situacaoHora(
  jornada: JornadaDia[],
  bloqueios: BloqueioSalao[],
  profissionalId: number,
  dia: Date,
  hora: number,
): "livre" | "folga" | "intervalo" | "fechado" {
  if (!jornada.length) return "livre";
  const diaSemana = (dia.getDay() + 6) % 7;
  const item = jornada.find((linha) => linha.dia_semana === diaSemana);
  const inicio = hora * 60;
  const fim = inicio + 60;
  const data = dataLocal(dia);
  const bloqueio = bloqueios.find((folga) => {
    if (folga.profissional && folga.profissional !== profissionalId) return false;
    const de = folga.data_inicio.slice(0, 10);
    const ate = folga.data_fim.slice(0, 10);
    if (data < de || data > ate) return false;
    if (!folga.horario_inicio || !folga.horario_fim) return true;
    return inicio < minutos(folga.horario_fim) && minutos(folga.horario_inicio) < fim;
  });
  if (bloqueio) return "folga";
  if (!item || !item.ativo) return "fechado";
  const entrada = minutos(item.hora_entrada);
  const saida = minutos(item.hora_saida);
  if (fim <= entrada || inicio >= saida) return "fechado";
  if (item.intervalo_inicio && item.intervalo_fim && inicio < minutos(item.intervalo_fim) && minutos(item.intervalo_inicio) < fim) return "intervalo";
  return "livre";
}

function vagaDaHora(
  filtro: number | "todos",
  profissionais: ProfissionalSalao[],
  jornadas: Record<number, JornadaDia[]>,
  bloqueios: BloqueioSalao[],
  dia: Date,
  hora: number,
) {
  if (filtro !== "todos") {
    if (!jornadas[filtro]) return "livre" as const;
    return situacaoHora(jornadas[filtro], bloqueios, filtro, dia, hora);
  }
  if (!profissionais.length || !Object.keys(jornadas).length) return "livre" as const;
  const situacoes = profissionais.map((pessoa) => situacaoHora(jornadas[pessoa.id] || [], bloqueios, pessoa.id, dia, hora));
  if (situacoes.some((item) => item === "livre")) return "livre" as const;
  if (situacoes.some((item) => item === "intervalo")) return "intervalo" as const;
  if (situacoes.some((item) => item === "folga")) return "folga" as const;
  return "fechado" as const;
}
