"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { SalaoAPI, type AgendamentoSalao, type ClienteSalao, type ProfissionalSalao, type ServicoSalao } from "@/lib/salao-api";

const HORA_INICIO = 8;
const HORA_FIM = 20;
const ALTURA_HORA = 52;

function dois(valor: number) {
  return String(valor).padStart(2, "0");
}

function paraApi(data: Date) {
  return `${data.getFullYear()}-${dois(data.getMonth() + 1)}-${dois(data.getDate())}T${dois(data.getHours())}:${dois(data.getMinutes())}:00`;
}

function deApi(valor: string) {
  const [data, hora = "00:00"] = valor.split("T");
  const [ano, mes, dia] = data.split("-").map(Number);
  const [h, m] = hora.split(":").map(Number);
  return new Date(ano, (mes || 1) - 1, dia || 1, h || 0, m || 0, 0, 0);
}

function inicioDaSemana(data: Date) {
  const copia = new Date(data);
  copia.setHours(0, 0, 0, 0);
  copia.setDate(copia.getDate() - ((copia.getDay() + 6) % 7));
  return copia;
}

function corStatus(status: string) {
  if (status === "COMPLETED") return "#1f8a4c";
  if (status === "IN_PROGRESS") return "#1f8f86";
  if (status === "CONFIRMED") return "#7a3044";
  if (status === "CANCELLED" || status === "NO_SHOW") return "#8a6e74";
  return "#d7a3ae";
}

export default function AgendaSalaoPage() {
  const params = useParams();
  const slug = params.slug as string;
  const searchParams = useSearchParams();
  const horarioAberto = useRef(false);
  const novoPedido = useRef("");
  const [modo, setModo] = useState<"dia" | "semana" | "mes">("semana");
  const [cursor, setCursor] = useState(() => new Date());
  const [profissionais, setProfissionais] = useState<ProfissionalSalao[]>([]);
  const [servicos, setServicos] = useState<ServicoSalao[]>([]);
  const [clientes, setClientes] = useState<ClienteSalao[]>([]);
  const [eventos, setEventos] = useState<AgendamentoSalao[]>([]);
  const [erro, setErro] = useState("");
  const [form, setForm] = useState<Record<string, string> | null>(null);
  const [selecionado, setSelecionado] = useState<AgendamentoSalao | null>(null);
  const [desconto, setDesconto] = useState("");
  const [formaPagamento, setFormaPagamento] = useState("pix");

  const periodo = useMemo(() => {
    if (modo === "dia") {
      const inicio = new Date(cursor);
      inicio.setHours(0, 0, 0, 0);
      const fim = new Date(inicio);
      fim.setDate(fim.getDate() + 1);
      return { inicio: inicio.getTime(), fim: fim.getTime() };
    }
    if (modo === "mes") {
      const inicio = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
      const fim = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1);
      return { inicio: inicio.getTime(), fim: fim.getTime() };
    }
    const inicio = inicioDaSemana(cursor);
    const fim = new Date(inicio);
    fim.setDate(fim.getDate() + 7);
    return { inicio: inicio.getTime(), fim: fim.getTime() };
  }, [cursor, modo]);

  const colunas = useMemo(() => {
    const inicio = new Date(periodo.inicio);
    if (modo === "dia") {
      return profissionais.map((item) => ({ id: String(item.id), titulo: item.nome, data: inicio }));
    }
    if (modo === "mes") return [] as { id: string; titulo: string; data: Date }[];
    return Array.from({ length: 7 }, (_, indice) => {
      const data = new Date(inicio);
      data.setDate(inicio.getDate() + indice);
      return { id: data.toDateString(), titulo: data.toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit" }), data };
    });
  }, [periodo.inicio, modo, profissionais]);

  const carregar = useCallback(() => {
    setErro("");
    Promise.all([
      SalaoAPI.profissionais(),
      SalaoAPI.servicos(),
      SalaoAPI.clientes(),
      SalaoAPI.agenda(paraApi(new Date(periodo.inicio)), paraApi(new Date(periodo.fim))),
    ])
      .then(([listaProfissionais, listaServicos, listaClientes, listaEventos]) => {
        setProfissionais(listaProfissionais);
        setServicos(listaServicos);
        setClientes(listaClientes);
        setEventos(listaEventos);
      })
      .catch((exc: Error) => setErro(exc.message));
  }, [periodo.inicio, periodo.fim]);

  useEffect(() => { carregar(); }, [carregar]);

  useEffect(() => {
    const dia = searchParams.get("dia");
    if (!dia) return;
    const data = deApi(dia);
    if (Number.isNaN(data.getTime())) return;
    setCursor(data);
  }, [searchParams]);

  useEffect(() => {
    const id = searchParams.get("horario");
    if (!id || horarioAberto.current || eventos.length === 0) return;
    const item = eventos.find((evento) => String(evento.id) === id);
    if (!item) return;
    horarioAberto.current = true;
    setSelecionado(item);
    setModo("dia");
    setCursor(new Date(item.inicio));
  }, [searchParams, eventos]);

  function abrirNovo(data: Date, profissionalId = "") {
    const inicio = new Date(data);
    setSelecionado(null);
    setForm({
      inicio: paraApi(inicio).slice(0, 16),
      profissional: profissionalId || String(profissionais[0]?.id || ""),
      servico: String(servicos[0]?.id || ""),
      cliente: "",
      cliente_nome: "",
      cliente_telefone: "",
      observacoes: "",
    });
  }

  useEffect(() => {
    if (searchParams.get("horario")) return;
    const novo = searchParams.get("novo");
    if (!novo || servicos.length === 0) return;
    const profissional = searchParams.get("profissional") || "";
    if (profissional && profissionais.length === 0) return;
    const chave = `${novo}|${profissional}`;
    if (novoPedido.current === chave) return;
    const data = deApi(novo);
    if (Number.isNaN(data.getTime())) return;
    novoPedido.current = chave;
    setCursor(data);
    setModo("dia");
    abrirNovo(data, profissional);
  }, [searchParams, servicos, profissionais]);

  async function salvar() {
    if (!form) return;
    setErro("");
    const corpo: Record<string, unknown> = {
      inicio: form.inicio,
      profissional: Number(form.profissional),
      servico: Number(form.servico),
      observacoes: form.observacoes,
    };
    if (form.cliente) corpo.cliente = Number(form.cliente);
    else {
      corpo.cliente_nome = form.cliente_nome;
      corpo.cliente_telefone = form.cliente_telefone;
    }
    try {
      if (selecionado) await SalaoAPI.atualizarAgendamento(selecionado.id, corpo);
      else await SalaoAPI.criarAgendamento(corpo);
      setForm(null);
      setSelecionado(null);
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível salvar.");
    }
  }

  async function mudarStatus(status: string) {
    if (!selecionado) return;
    try {
      const atualizado = await SalaoAPI.atualizarAgendamento(selecionado.id, { status });
      setSelecionado(atualizado);
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível atualizar.");
    }
  }

  async function receber() {
    if (!selecionado) return;
    setErro("");
    try {
      const atualizado = await SalaoAPI.receber(selecionado.id, {
        desconto: desconto.replace(",", ".") || "0",
        forma: formaPagamento,
      });
      setSelecionado(atualizado);
      setDesconto("");
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível receber.");
    }
  }

  async function desfazerRecebimento() {
    if (!selecionado?.recebido) return;
    setErro("");
    try {
      await SalaoAPI.estornarRecebimento(selecionado.recebido.id);
      setSelecionado({ ...selecionado, recebido: null });
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível desfazer o recebimento.");
    }
  }

  function ajustarServico() {
    if (!selecionado) return;
    setForm({
      inicio: paraApi(new Date(selecionado.inicio)).slice(0, 16),
      profissional: String(selecionado.profissional),
      servico: String(selecionado.servico),
      cliente: String(selecionado.cliente),
      cliente_nome: "",
      cliente_telefone: "",
      observacoes: selecionado.observacoes,
    });
  }

  async function soltar(eventoId: number, data: Date, profissionalId?: string) {
    const atual = eventos.find((item) => item.id === eventoId);
    if (!atual) return;
    const inicio = new Date(atual.inicio);
    inicio.setFullYear(data.getFullYear(), data.getMonth(), data.getDate());
    inicio.setHours(data.getHours(), data.getMinutes(), 0, 0);
    try {
      await SalaoAPI.atualizarAgendamento(eventoId, {
        inicio: paraApi(inicio),
        ...(profissionalId ? { profissional: Number(profissionalId) } : {}),
      });
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Horário ocupado.");
    }
  }

  const horas = Array.from({ length: HORA_FIM - HORA_INICIO }, (_, indice) => HORA_INICIO + indice);

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-3xl font-semibold">Agenda</h1>
          <p className="text-sm text-[#8a6e74]">Dia por profissional, semana por dia e mês. O horário ocupado não aceita outro atendimento.</p>
        </div>
        <div className="flex gap-2">
          <button type="button" className="rounded-full border bg-white px-3 py-1.5 text-sm" onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth(), cursor.getDate() - (modo === "mes" ? 30 : modo === "semana" ? 7 : 1)))}>Anterior</button>
          <button type="button" className="rounded-full border bg-white px-3 py-1.5 text-sm" onClick={() => setCursor(new Date())}>Hoje</button>
          <button type="button" className="rounded-full border bg-white px-3 py-1.5 text-sm" onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth(), cursor.getDate() + (modo === "mes" ? 30 : modo === "semana" ? 7 : 1)))}>Próxima</button>
          {(["dia", "semana", "mes"] as const).map((item) => (
            <button key={item} type="button" className={`rounded-full px-3 py-1.5 text-sm ${modo === item ? "bg-[#7a3044] text-white" : "bg-white"}`} onClick={() => setModo(item)}>
              {item === "dia" ? "Dia" : item === "semana" ? "Semana" : "Mês"}
            </button>
          ))}
          <button type="button" className="rounded-full bg-[#7a3044] px-3 py-1.5 text-sm text-white" onClick={() => abrirNovo(cursor)}>+ Novo agendamento</button>
        </div>
      </div>
      {erro ? <p className="mb-2 text-sm text-red-700">{erro}</p> : null}
      {profissionais.length === 0 ? <p className="mb-2 text-sm text-[#8a6e74]">Cadastre um profissional para abrir as colunas do dia.</p> : null}
      {modo === "mes" ? (
        <Mes cursor={cursor} eventos={eventos} aoAbrir={(data) => { setCursor(data); setModo("dia"); }} />
      ) : (
        <div className="overflow-auto rounded-2xl border border-[#f0e4e6] bg-white">
          <div className="grid" style={{ gridTemplateColumns: `64px repeat(${Math.max(colunas.length, 1)}, minmax(140px, 1fr))` }}>
            <div />
            {colunas.map((coluna) => <div key={coluna.id} className="border-b border-l px-2 py-2 text-center text-xs text-[#8a6e74]">{coluna.titulo}</div>)}
            <div>
              {horas.map((hora) => <div key={hora} style={{ height: ALTURA_HORA }} className="pr-2 text-right text-xs text-[#8a6e74]">{dois(hora)}:00</div>)}
            </div>
            {colunas.map((coluna) => (
              <div
                key={coluna.id}
                className="relative border-l"
                style={{ height: horas.length * ALTURA_HORA }}
                onDragOver={(evento) => evento.preventDefault()}
                onDrop={(evento) => {
                  const id = Number(evento.dataTransfer.getData("text/plain"));
                  const retangulo = evento.currentTarget.getBoundingClientRect();
                  const hora = HORA_INICIO + (evento.clientY - retangulo.top) / ALTURA_HORA;
                  const data = new Date(coluna.data);
                  data.setHours(Math.floor(hora), Math.round((hora % 1) * 60 / 15) * 15, 0, 0);
                  soltar(id, data, modo === "dia" ? coluna.id : undefined);
                }}
                onClick={(evento) => {
                  if ((evento.target as HTMLElement).dataset.evento) return;
                  const retangulo = evento.currentTarget.getBoundingClientRect();
                  const hora = HORA_INICIO + (evento.clientY - retangulo.top) / ALTURA_HORA;
                  const data = new Date(coluna.data);
                  data.setHours(Math.floor(hora), 0, 0, 0);
                  abrirNovo(data, modo === "dia" ? coluna.id : "");
                }}
              >
                {horas.map((hora) => <div key={hora} style={{ height: ALTURA_HORA }} className="border-b border-[#f0e4e6]" />)}
                {eventos.filter((item) => item.status !== "CANCELLED").filter((item) => {
                  const inicio = new Date(item.inicio);
                  const mesmoDia = inicio.toDateString() === coluna.data.toDateString();
                  return modo === "dia" ? mesmoDia && String(item.profissional) === coluna.id : mesmoDia;
                }).map((item) => {
                  const inicio = new Date(item.inicio);
                  const topo = ((inicio.getHours() + inicio.getMinutes() / 60) - HORA_INICIO) * ALTURA_HORA;
                  return (
                    <button
                      key={item.id}
                      type="button"
                      data-evento="1"
                      draggable
                      onDragStart={(evento) => evento.dataTransfer.setData("text/plain", String(item.id))}
                      onClick={(evento) => { evento.stopPropagation(); setForm(null); setSelecionado(item); }}
                      className="absolute left-1 right-1 overflow-hidden rounded-md px-1 text-left text-[11px] text-white"
                      style={{ top: Math.max(0, topo), height: Math.max(22, (item.duracao_minutos / 60) * ALTURA_HORA), background: corStatus(item.status) }}
                    >
                      {dois(inicio.getHours())}:{dois(inicio.getMinutes())} {item.cliente_nome}
                      <span className="block opacity-80">{item.servico_nome}</span>
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      )}
      {form ? (
        <Formulario form={form} setForm={setForm} clientes={clientes} profissionais={profissionais} servicos={servicos} aoSalvar={salvar} aoFechar={() => setForm(null)} />
      ) : null}
      {selecionado && !form ? (
        <div className="mt-3 rounded-2xl border border-[#f0e4e6] bg-white p-4">
          <p className="font-medium">{selecionado.cliente_nome} · {selecionado.servico_nome}</p>
          <p className="text-sm text-[#8a6e74]">{selecionado.profissional_nome} · {new Date(selecionado.inicio).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })} · {selecionado.status_label} · {selecionado.preco}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {selecionado.status === "SCHEDULED" ? <button type="button" className="rounded-full bg-[#7a3044] px-3 py-1.5 text-sm text-white" onClick={() => mudarStatus("CONFIRMED")}>Confirmar</button> : null}
            {selecionado.status === "SCHEDULED" || selecionado.status === "CONFIRMED" ? <button type="button" className="rounded-full bg-[#1f8f86] px-3 py-1.5 text-sm text-white" onClick={() => mudarStatus("IN_PROGRESS")}>Iniciar atendimento</button> : null}
            {selecionado.status === "IN_PROGRESS" ? <button type="button" className="rounded-full bg-[#1f8a4c] px-3 py-1.5 text-sm text-white" onClick={() => mudarStatus("COMPLETED")}>Finalizar</button> : null}
            {selecionado.status === "COMPLETED" && !selecionado.recebido ? (
              <span className="flex flex-wrap items-center gap-2">
                <input className="w-28 rounded-lg border px-2 py-1.5 text-sm" inputMode="decimal" placeholder="Desconto R$" value={desconto} onChange={(evento) => setDesconto(evento.target.value)} />
                <select className="rounded-lg border px-2 py-1.5 text-sm" value={formaPagamento} onChange={(evento) => setFormaPagamento(evento.target.value)}>
                  <option value="dinheiro">Dinheiro</option>
                  <option value="pix">Pix</option>
                  <option value="debito">Débito</option>
                  <option value="credito">Crédito</option>
                </select>
                <button type="button" className="rounded-full bg-[#7a3044] px-3 py-1.5 text-sm text-white" onClick={receber}>Receber</button>
              </span>
            ) : null}
            {selecionado.recebido ? (
              <>
                <span className="rounded-full bg-[#e8f6ee] px-3 py-1.5 text-sm text-[#1f8a4c]">Recebido R$ {selecionado.recebido.valor} · {selecionado.recebido.forma_label}</span>
                <Link href={`/loja/${slug}/salao-cabeleireiro/financeiro`} className="rounded-full border px-3 py-1.5 text-sm">Ver no caixa</Link>
                <button type="button" className="rounded-full border px-3 py-1.5 text-sm" onClick={desfazerRecebimento}>Desfazer recebimento</button>
              </>
            ) : null}
            {selecionado.status !== "CANCELLED" && selecionado.status !== "COMPLETED" ? <button type="button" className="rounded-full border px-3 py-1.5 text-sm" onClick={ajustarServico}>Ajustar serviço</button> : null}
            {selecionado.status !== "CANCELLED" && selecionado.status !== "COMPLETED" ? <button type="button" className="rounded-full border px-3 py-1.5 text-sm" onClick={() => mudarStatus("CANCELLED")}>Cancelar</button> : null}
            {selecionado.status !== "NO_SHOW" && selecionado.status !== "COMPLETED" && selecionado.status !== "CANCELLED" ? <button type="button" className="rounded-full border px-3 py-1.5 text-sm" onClick={() => mudarStatus("NO_SHOW")}>Faltou</button> : null}
            <button type="button" className="text-sm text-[#8a6e74]" onClick={() => setSelecionado(null)}>Fechar</button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Formulario({
  form, setForm, clientes, profissionais, servicos, aoSalvar, aoFechar,
}: {
  form: Record<string, string>;
  setForm: (valor: Record<string, string>) => void;
  clientes: ClienteSalao[];
  profissionais: ProfissionalSalao[];
  servicos: ServicoSalao[];
  aoSalvar: () => void;
  aoFechar: () => void;
}) {
  return (
    <form className="mt-3 grid gap-2 rounded-2xl border border-[#f0e4e6] bg-white p-4 md:grid-cols-3" onSubmit={(evento) => { evento.preventDefault(); aoSalvar(); }}>
      <label className="text-sm">Cliente já cadastrado
        <select className="mt-1 w-full rounded-lg border px-2 py-2" value={form.cliente} onChange={(evento) => setForm({ ...form, cliente: evento.target.value })}>
          <option value="">Novo cliente</option>
          {clientes.map((item) => <option key={item.id} value={item.id}>{item.nome}</option>)}
        </select>
      </label>
      {form.cliente ? null : (
        <>
          <label className="text-sm">Nome<input className="mt-1 w-full rounded-lg border px-2 py-2" value={form.cliente_nome} onChange={(evento) => setForm({ ...form, cliente_nome: evento.target.value })} /></label>
          <label className="text-sm">Telefone<input className="mt-1 w-full rounded-lg border px-2 py-2" value={form.cliente_telefone} onChange={(evento) => setForm({ ...form, cliente_telefone: evento.target.value })} /></label>
        </>
      )}
      <label className="text-sm">Profissional
        <select className="mt-1 w-full rounded-lg border px-2 py-2" value={form.profissional} onChange={(evento) => setForm({ ...form, profissional: evento.target.value })}>
          {profissionais.map((item) => <option key={item.id} value={item.id}>{item.nome}</option>)}
        </select>
      </label>
      <label className="text-sm">Serviço
        <select className="mt-1 w-full rounded-lg border px-2 py-2" value={form.servico} onChange={(evento) => setForm({ ...form, servico: evento.target.value })}>
          {servicos.map((item) => <option key={item.id} value={item.id}>{item.nome} · {item.duracao_minutos} min</option>)}
        </select>
      </label>
      <label className="text-sm">Data e hora<input type="datetime-local" className="mt-1 w-full rounded-lg border px-2 py-2" value={form.inicio} onChange={(evento) => setForm({ ...form, inicio: evento.target.value })} /></label>
      <div className="flex items-end gap-2">
        <button type="submit" className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white">Salvar</button>
        <button type="button" className="text-sm text-[#8a6e74]" onClick={aoFechar}>Cancelar</button>
      </div>
    </form>
  );
}

function Mes({ cursor, eventos, aoAbrir }: { cursor: Date; eventos: AgendamentoSalao[]; aoAbrir: (data: Date) => void }) {
  const primeiro = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
  const dias = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 0).getDate();
  const offset = (primeiro.getDay() + 6) % 7;
  const celulas = [...Array(offset).fill(null), ...Array.from({ length: dias }, (_, indice) => indice + 1)];
  return (
    <div className="grid grid-cols-7 gap-2">
      {celulas.map((dia, indice) => {
        if (!dia) return <div key={`vazio-${indice}`} />;
        const data = new Date(cursor.getFullYear(), cursor.getMonth(), dia);
        const total = eventos.filter((item) => new Date(item.inicio).toDateString() === data.toDateString() && item.status !== "CANCELLED").length;
        return (
          <button key={dia} type="button" className="min-h-20 rounded-xl border border-[#f0e4e6] bg-white p-2 text-left" onClick={() => aoAbrir(data)}>
            <span className="text-sm">{dia}</span>
            {total ? <span className="mt-2 block text-xs text-[#7a3044]">{total} horário{total > 1 ? "s" : ""}</span> : null}
          </button>
        );
      })}
    </div>
  );
}
