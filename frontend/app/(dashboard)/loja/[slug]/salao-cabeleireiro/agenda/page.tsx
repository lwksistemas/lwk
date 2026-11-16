"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { STATUS_PADRAO, useStatusSalao } from "@/components/salao/cores-salao";
import { diaTemAtendimento } from "@/components/salao/PaineisSalao";
import { SalaoAPI, type AgendamentoSalao, type BloqueioSalao, type ClienteSalao, type JornadaDia, type LocalRecebimentoSalao, type ProfissionalSalao, type ServicoSalao } from "@/lib/salao-api";

const HORA_INICIO = 8;
const HORA_FIM = 20;
const ALTURA_HORA = 52;

function dois(valor: number) {
  return String(valor).padStart(2, "0");
}

type LinhaPagamento = { id: string; forma: string; valor: string };

const FORMAS_SALAO = [
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

export default function AgendaSalaoPage() {
  const statusCores = useStatusSalao();
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
  const [receberAberto, setReceberAberto] = useState(false);
  const [quitar, setQuitar] = useState(true);
  const [linhas, setLinhas] = useState<LinhaPagamento[]>([{ id: "1", forma: "dinheiro", valor: "" }]);
  const [confirmaWhatsapp, setConfirmaWhatsapp] = useState(false);
  const [localRecebimento, setLocalRecebimento] = useState<LocalRecebimentoSalao>("caixa");
  const [jornadas, setJornadas] = useState<Record<number, JornadaDia[]>>({});
  const [aviso, setAviso] = useState("");
  const [confirmarExclusao, setConfirmarExclusao] = useState(false);
  const [bloqueios, setBloqueios] = useState<BloqueioSalao[]>([]);
  const [folgaAberta, setFolgaAberta] = useState(false);
  const [folga, setFolga] = useState({ titulo: "", profissional: "", data_inicio: "", data_fim: "", horario_inicio: "", horario_fim: "" });

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
    }).filter((coluna) => diaTemAtendimento(coluna.data, "todos", profissionais, jornadas));
  }, [periodo.inicio, modo, profissionais, jornadas]);

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
    SalaoAPI.config().then((dados) => setLocalRecebimento(dados.local_recebimento || "caixa")).catch(() => undefined);
  }, []);

  const recarregarBloqueios = useCallback(() => {
    SalaoAPI.bloqueios().then(setBloqueios).catch(() => undefined);
  }, []);
  useEffect(() => { recarregarBloqueios(); }, [recarregarBloqueios]);

  const profissionaisIds = profissionais.map((pessoa) => pessoa.id).join(",");
  useEffect(() => {
    if (!profissionaisIds) return;
    let vivo = true;
    Promise.all(profissionais.map(async (pessoa) => [pessoa.id, await SalaoAPI.jornada(pessoa.id)] as const))
      .then((pares) => { if (vivo) setJornadas(Object.fromEntries(pares)); })
      .catch(() => undefined);
    return () => { vivo = false; };
  }, [profissionaisIds, profissionais]);

  useEffect(() => {
    SalaoAPI.comunicacao().then((dados) => setConfirmaWhatsapp(dados.confirmacao)).catch(() => undefined);
  }, []);

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
    setConfirmarExclusao(false);
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
    setAviso("");
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
      const atualizado = selecionado
        ? await SalaoAPI.atualizarAgendamento(selecionado.id, corpo)
        : await SalaoAPI.criarAgendamento(corpo);
      setAviso(atualizado.aviso || "");
      setForm(null);
      setSelecionado(null);
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível salvar.");
    }
  }

  async function mudarStatus(status: string) {
    if (!selecionado) return;
    setAviso("");
    try {
      const atualizado = await SalaoAPI.atualizarAgendamento(selecionado.id, { status });
      setSelecionado(atualizado);
      setAviso(atualizado.aviso || "");
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível atualizar.");
    }
  }

  async function enviarConfirmacao() {
    if (!selecionado) return;
    setErro("");
    setAviso("");
    try {
      await SalaoAPI.enviarWhatsapp(selecionado.id, "confirmacao");
      setAviso("Confirmação enviada no WhatsApp.");
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível enviar o WhatsApp.");
    }
  }

  function abrirReceber() {
    if (!selecionado) return;
    const preco = Number(selecionado.preco || 0);
    setErro("");
    setDesconto("");
    setQuitar(true);
    setLinhas([{ id: "1", forma: "dinheiro", valor: preco.toFixed(2) }]);
    setReceberAberto(true);
  }

  function mudarDesconto(texto: string) {
    setDesconto(texto);
    if (!selecionado || linhas.length !== 1) return;
    const liquido = Math.max(0, Math.round((Number(selecionado.preco || 0) - lerReais(texto)) * 100) / 100);
    setLinhas([{ ...linhas[0], valor: liquido.toFixed(2) }]);
  }

  async function receber() {
    if (!selecionado) return;
    const preco = Number(selecionado.preco || 0);
    const valorDesconto = lerReais(desconto);
    const total = Math.round((preco - valorDesconto) * 100) / 100;
    if (valorDesconto < 0 || valorDesconto > preco) {
      setErro("O desconto não pode passar do valor do serviço.");
      return;
    }
    const soma = Math.round(linhas.reduce((acc, linha) => acc + lerReais(linha.valor), 0) * 100) / 100;
    if (total > 0) {
      if (linhas.some((linha) => lerReais(linha.valor) <= 0)) {
        setErro("Informe o valor de cada forma de pagamento.");
        return;
      }
      if (soma > total + 0.001) {
        setErro(`A soma das formas passa do total a receber (${reais(total)}).`);
        return;
      }
      if (Math.abs(soma - total) > 0.009) {
        setErro(`Para quitar, a soma das formas deve ser igual ao total a receber (${reais(total)}).`);
        return;
      }
    }
    setErro("");
    try {
      const atualizado = await SalaoAPI.receber(selecionado.id, {
        desconto: valorDesconto.toFixed(2),
        origem: "agenda",
        formas: total > 0 ? linhas.map((linha) => ({ forma: linha.forma, valor: lerReais(linha.valor).toFixed(2) })) : [],
      });
      setSelecionado(atualizado);
      setDesconto("");
      setReceberAberto(false);
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível receber.");
    }
  }

  async function excluir() {
    if (!selecionado) return;
    setErro("");
    setAviso("");
    try {
      const atualizado = await SalaoAPI.excluirAgendamento(selecionado.id);
      setAviso(atualizado.aviso || "Agendamento excluído.");
      setSelecionado(null);
      setForm(null);
      setConfirmarExclusao(false);
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível excluir.");
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

  function abrirFolga() {
    const dia = `${cursor.getFullYear()}-${dois(cursor.getMonth() + 1)}-${dois(cursor.getDate())}`;
    setErro("");
    setFolga({
      titulo: "",
      profissional: String(profissionais[0]?.id || ""),
      data_inicio: dia,
      data_fim: dia,
      horario_inicio: "",
      horario_fim: "",
    });
    setFolgaAberta(true);
  }

  async function criarFolga(evento: React.FormEvent) {
    evento.preventDefault();
    setErro("");
    try {
      await SalaoAPI.bloquear({
        titulo: folga.titulo,
        tipo: "folga",
        profissional: Number(folga.profissional),
        data_inicio: folga.data_inicio,
        data_fim: folga.data_fim || folga.data_inicio,
        horario_inicio: folga.horario_inicio,
        horario_fim: folga.horario_fim,
      });
      setFolga({ ...folga, titulo: "", horario_inicio: "", horario_fim: "" });
      recarregarBloqueios();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível gravar a folga.");
    }
  }

  async function removerFolga(id: number) {
    setErro("");
    try {
      await SalaoAPI.removerBloqueio(id);
      recarregarBloqueios();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível remover a folga.");
    }
  }

  function folgasDoDia(data: Date) {
    const iso = `${data.getFullYear()}-${dois(data.getMonth() + 1)}-${dois(data.getDate())}`;
    return bloqueios.filter((item) => item.data_inicio <= iso && item.data_fim >= iso);
  }

  const horas = Array.from({ length: HORA_FIM - HORA_INICIO }, (_, indice) => HORA_INICIO + indice);

  return (
    <div className={modo === "mes" ? "flex h-[calc(100dvh-2rem)] flex-col sm:h-[calc(100dvh-2.5rem)]" : undefined}>
      <div className="mb-3 flex shrink-0 flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-3xl font-semibold">Agenda</h1>
          <p className="text-sm text-[#8a6e74]">Dia por profissional, semana por dia e mês. O horário ocupado não aceita outro atendimento.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="rounded-full border bg-white px-3 py-1.5 text-sm" onClick={abrirFolga}>Folgas e bloqueios</button>
          <button type="button" className="rounded-full border bg-white px-3 py-1.5 text-sm" onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth(), cursor.getDate() - (modo === "mes" ? 30 : modo === "semana" ? 7 : 1)))}>Anterior</button>
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
      {aviso ? <p className="mb-2 text-sm text-[#1f8a4c]">{aviso}</p> : null}
      {profissionais.length === 0 ? <p className="mb-2 text-sm text-[#8a6e74]">Cadastre um profissional para abrir as colunas do dia.</p> : null}
      {modo === "mes" ? (
        <Mes cursor={cursor} eventos={eventos} aoAbrir={(data) => { setCursor(data); setModo("dia"); }} />
      ) : (
        <div className="overflow-auto rounded-2xl border border-[#f0e4e6] bg-white">
          <div className="grid" style={{ gridTemplateColumns: `64px repeat(${Math.max(colunas.length, 1)}, minmax(140px, 1fr))` }}>
            <div />
            {colunas.map((coluna) => {
              const folgas = folgasDoDia(coluna.data).filter((item) => modo !== "dia" || !item.profissional || String(item.profissional) === coluna.id);
              return (
                <div key={coluna.id} className="border-b border-l px-2 py-2 text-center text-xs text-[#8a6e74]">
                  {coluna.titulo}
                  {folgas.map((item) => (
                    <span key={item.id} className="mt-1 block truncate text-[10px] text-[#7a3044]" title={item.titulo}>Folga · {item.profissional_nome}</span>
                  ))}
                </div>
              );
            })}
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
                {modo === "dia" ? folgasDoDia(coluna.data).filter((item) => !item.profissional || String(item.profissional) === coluna.id).map((item) => {
                  const inicioHora = item.horario_inicio ? Number(item.horario_inicio.slice(0, 2)) + Number(item.horario_inicio.slice(3, 5)) / 60 : HORA_INICIO;
                  const fimHora = item.horario_fim ? Number(item.horario_fim.slice(0, 2)) + Number(item.horario_fim.slice(3, 5)) / 60 : HORA_FIM;
                  const topo = (inicioHora - HORA_INICIO) * ALTURA_HORA;
                  return (
                    <div key={item.id} data-evento="1" className="absolute left-1 right-1 rounded-md bg-[#f3e6ea] px-1 py-0.5 text-[11px] text-[#7a3044]" style={{ top: Math.max(0, topo), height: Math.max(22, (fimHora - inicioHora) * ALTURA_HORA) }} title={item.titulo}>
                      Folga · {item.titulo}
                    </div>
                  );
                }) : null}
                {eventos.filter((item) => item.status !== "CANCELLED").filter((item) => {
                  const inicio = new Date(item.inicio);
                  const mesmoDia = inicio.toDateString() === coluna.data.toDateString();
                  return modo === "dia" ? mesmoDia && String(item.profissional) === coluna.id : mesmoDia;
                }).map((item) => {
                  const inicio = new Date(item.inicio);
                  const fim = new Date(item.fim);
                  const faixa = `${dois(inicio.getHours())}:${dois(inicio.getMinutes())}–${dois(fim.getHours())}:${dois(fim.getMinutes())}`;
                  const topo = ((inicio.getHours() + inicio.getMinutes() / 60) - HORA_INICIO) * ALTURA_HORA;
                  return (
                    <button
                      key={item.id}
                      type="button"
                      data-evento="1"
                      draggable
                      onDragStart={(evento) => evento.dataTransfer.setData("text/plain", String(item.id))}
                      onClick={(evento) => { evento.stopPropagation(); setForm(null); setConfirmarExclusao(false); setSelecionado(item); }}
                      title={`${faixa} · Profissional ${item.profissional_nome} · Cliente ${item.cliente_nome}`}
                      className="absolute left-1 right-1 overflow-hidden rounded-md px-1 py-0.5 text-left text-[11px] leading-tight text-white"
                      style={{ top: Math.max(0, topo), height: Math.max(48, (item.duracao_minutos / 60) * ALTURA_HORA), background: statusCores[item.status] || STATUS_PADRAO.SCHEDULED }}
                    >
                      <span className="block truncate">{faixa}</span>
                      <span className="block truncate">Profissional {item.profissional_nome}</span>
                      <span className="block truncate">Cliente {item.cliente_nome}</span>
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      )}
      {folgaAberta ? (
        <div className="fixed inset-0 z-40 grid place-items-center bg-black/40 p-4" role="dialog" aria-modal="true" aria-labelledby="folga-formulario" onClick={(evento) => { if (evento.target === evento.currentTarget) setFolgaAberta(false); }}>
          <div className="max-h-[90vh] w-full max-w-2xl overflow-auto rounded-3xl bg-white p-5">
            <h2 id="folga-formulario" className="text-lg font-semibold">Folgas e bloqueios</h2>
            <p className="mt-1 text-sm text-[#8a6e74]">A secretaria registra a folga de qualquer profissional. Sem horário, o dia inteiro fica bloqueado.</p>
            {erro ? <p className="mt-2 text-sm text-red-700">{erro}</p> : null}
            <form className="mt-3 grid gap-2 sm:grid-cols-2" onSubmit={criarFolga}>
              <label className="text-sm sm:col-span-2">Profissional
                <select className="mt-1 w-full rounded-lg border px-2 py-2" value={folga.profissional} onChange={(evento) => setFolga({ ...folga, profissional: evento.target.value })} required>
                  {profissionais.map((pessoa) => <option key={pessoa.id} value={pessoa.id}>{pessoa.nome}</option>)}
                </select>
              </label>
              <label className="text-sm sm:col-span-2">Motivo
                <input className="mt-1 w-full rounded-lg border px-2 py-2" value={folga.titulo} onChange={(evento) => setFolga({ ...folga, titulo: evento.target.value })} required />
              </label>
              <label className="text-sm">Começa
                <input type="date" className="mt-1 w-full rounded-lg border px-2 py-2" value={folga.data_inicio} onChange={(evento) => setFolga({ ...folga, data_inicio: evento.target.value })} required />
              </label>
              <label className="text-sm">Termina
                <input type="date" className="mt-1 w-full rounded-lg border px-2 py-2" value={folga.data_fim} onChange={(evento) => setFolga({ ...folga, data_fim: evento.target.value })} />
              </label>
              <label className="text-sm">Das
                <input type="time" className="mt-1 w-full rounded-lg border px-2 py-2" value={folga.horario_inicio} onChange={(evento) => setFolga({ ...folga, horario_inicio: evento.target.value })} />
              </label>
              <label className="text-sm">Até
                <input type="time" className="mt-1 w-full rounded-lg border px-2 py-2" value={folga.horario_fim} onChange={(evento) => setFolga({ ...folga, horario_fim: evento.target.value })} />
              </label>
              <div className="mt-1 flex justify-end gap-2 sm:col-span-2">
                <button type="button" className="rounded-full border px-4 py-2 text-sm" onClick={() => setFolgaAberta(false)}>Fechar</button>
                <button className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" type="submit">Registrar</button>
              </div>
            </form>
            <ul className="mt-4">
              {bloqueios.length === 0 ? <li className="text-sm text-[#8a6e74]">Nenhuma folga cadastrada.</li> : null}
              {bloqueios.map((item) => (
                <li key={item.id} className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f0e4e6] py-2 text-sm">
                  <span>{item.profissional_nome} · {item.titulo} · {item.data_inicio}{item.data_fim !== item.data_inicio ? ` a ${item.data_fim}` : ""}{item.horario_inicio ? ` · ${item.horario_inicio.slice(0, 5)}–${item.horario_fim?.slice(0, 5)}` : " · dia inteiro"}</span>
                  <button type="button" className="text-[#8a6e74]" onClick={() => removerFolga(item.id)}>Remover</button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
      {form ? (
        <Formulario
          titulo={selecionado ? "Editar agendamento" : "Novo agendamento"}
          form={form}
          setForm={setForm}
          clientes={clientes}
          profissionais={profissionais}
          servicos={servicos}
          erro={erro}
          aoSalvar={salvar}
          aoFechar={() => { setForm(null); setErro(""); if (!selecionado) setConfirmarExclusao(false); }}
        />
      ) : null}
      {selecionado && receberAberto ? (
        <ModalReceber
          cliente={selecionado.cliente_nome}
          servico={selecionado.servico_nome}
          profissional={selecionado.profissional_nome}
          preco={Number(selecionado.preco || 0)}
          desconto={desconto}
          linhas={linhas}
          quitar={quitar}
          erro={erro}
          aoDesconto={mudarDesconto}
          aoLinhas={setLinhas}
          aoQuitar={setQuitar}
          aoConfirmar={receber}
          aoFechar={() => { setReceberAberto(false); setErro(""); }}
        />
      ) : null}
      {selecionado && !form && !receberAberto ? (
        <div className="fixed inset-0 z-40 grid place-items-center bg-black/40 p-4" role="dialog" aria-modal="true" aria-labelledby="agenda-detalhe" onClick={(evento) => { if (evento.target === evento.currentTarget) { setSelecionado(null); setConfirmarExclusao(false); } }}>
          <div className="max-h-[90vh] w-full max-w-lg overflow-auto rounded-3xl bg-white p-5">
          <p id="agenda-detalhe" className="font-medium">{selecionado.cliente_nome}</p>
          <p className="text-sm text-[#8a6e74]">{selecionado.profissional_nome} · {selecionado.servico_nome}</p>
          <p className="text-sm text-[#8a6e74]">{new Date(selecionado.inicio).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })} · {selecionado.status_label} · {selecionado.preco}</p>
          {erro ? <p className="mt-2 text-sm text-red-700">{erro}</p> : null}
          <div className="mt-3 flex flex-wrap gap-2">
            {selecionado.status === "SCHEDULED" ? <button type="button" className="rounded-full bg-[#7a3044] px-3 py-1.5 text-sm text-white" onClick={() => mudarStatus("CONFIRMED")}>Confirmar</button> : null}
            {confirmaWhatsapp && (selecionado.status === "SCHEDULED" || selecionado.status === "CONFIRMED") ? <button type="button" className="rounded-full border px-3 py-1.5 text-sm" onClick={enviarConfirmacao}>Enviar confirmação</button> : null}
            {selecionado.status === "SCHEDULED" || selecionado.status === "CONFIRMED" ? <button type="button" className="rounded-full bg-[#1f8f86] px-3 py-1.5 text-sm text-white" onClick={() => mudarStatus("IN_PROGRESS")}>Iniciar atendimento</button> : null}
            {selecionado.status === "IN_PROGRESS" ? <button type="button" className="rounded-full bg-[#1f8a4c] px-3 py-1.5 text-sm text-white" onClick={() => mudarStatus("COMPLETED")}>Finalizar</button> : null}
            {selecionado.status === "COMPLETED" && !selecionado.recebido && localRecebimento !== "caixa" ? (
              <button type="button" className="rounded-full bg-[#7a3044] px-3 py-1.5 text-sm text-white" onClick={abrirReceber}>Receber</button>
            ) : null}
            {selecionado.status === "COMPLETED" && !selecionado.recebido && localRecebimento === "caixa" ? (
              <Link href={`/loja/${slug}/salao-cabeleireiro/caixa`} className="rounded-full bg-[#7a3044] px-3 py-1.5 text-sm text-white">Receber no Caixa/PDV</Link>
            ) : null}
            {selecionado.recebido ? (
              <>
                <span className="rounded-full bg-[#e8f6ee] px-3 py-1.5 text-sm text-[#1f8a4c]">Recebido R$ {selecionado.recebido.valor} · {selecionado.recebido.forma_label}</span>
                <Link href={`/loja/${slug}/salao-cabeleireiro/financeiro`} className="rounded-full border px-3 py-1.5 text-sm">Ver no caixa</Link>
                <button type="button" className="rounded-full border px-3 py-1.5 text-sm" onClick={desfazerRecebimento}>Desfazer recebimento</button>
              </>
            ) : null}
            {!selecionado.recebido && selecionado.status !== "CANCELLED" ? <button type="button" className="rounded-full border px-3 py-1.5 text-sm" onClick={ajustarServico}>Editar</button> : null}
            {selecionado.status !== "NO_SHOW" && selecionado.status !== "COMPLETED" && selecionado.status !== "CANCELLED" ? <button type="button" className="rounded-full border px-3 py-1.5 text-sm" onClick={() => mudarStatus("NO_SHOW")}>Faltou</button> : null}
            {!selecionado.recebido && selecionado.status !== "CANCELLED" ? (
              confirmarExclusao ? (
                <span className="flex flex-wrap items-center gap-2">
                  <span className="text-sm text-[#8a6e74]">Excluir este agendamento?</span>
                  <button type="button" className="rounded-full bg-red-700 px-3 py-1.5 text-sm text-white" onClick={excluir}>Excluir</button>
                  <button type="button" className="text-sm text-[#8a6e74]" onClick={() => setConfirmarExclusao(false)}>Voltar</button>
                </span>
              ) : (
                <button type="button" className="rounded-full border border-red-200 px-3 py-1.5 text-sm text-red-700" onClick={() => setConfirmarExclusao(true)}>Excluir</button>
              )
            ) : null}
            <button type="button" className="text-sm text-[#8a6e74]" onClick={() => { setSelecionado(null); setConfirmarExclusao(false); }}>Fechar</button>
          </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Formulario({
  titulo, form, setForm, clientes, profissionais, servicos, erro, aoSalvar, aoFechar,
}: {
  titulo: string;
  form: Record<string, string>;
  setForm: (valor: Record<string, string>) => void;
  clientes: ClienteSalao[];
  profissionais: ProfissionalSalao[];
  servicos: ServicoSalao[];
  erro: string;
  aoSalvar: () => void;
  aoFechar: () => void;
}) {
  return (
    <div className="fixed inset-0 z-40 grid place-items-center bg-black/40 p-4" role="dialog" aria-modal="true" aria-labelledby="agenda-formulario" onClick={(evento) => { if (evento.target === evento.currentTarget) aoFechar(); }}>
    <form className="max-h-[90vh] w-full max-w-lg overflow-auto rounded-3xl bg-white p-5" onSubmit={(evento) => { evento.preventDefault(); aoSalvar(); }}>
      <h2 id="agenda-formulario" className="mb-3 text-lg font-semibold">{titulo}</h2>
      {erro ? <p className="mb-2 text-sm text-red-700">{erro}</p> : null}
      <div className="grid gap-2">
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
      <div className="mt-2 flex items-center justify-end gap-2">
        <button type="button" className="rounded-full border px-4 py-2 text-sm" onClick={aoFechar}>Cancelar</button>
        <button type="submit" className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white">Salvar</button>
      </div>
      </div>
    </form>
    </div>
  );
}

function ModalReceber({
  cliente, servico, profissional, preco, desconto, linhas, quitar, erro,
  aoDesconto, aoLinhas, aoQuitar, aoConfirmar, aoFechar,
}: {
  cliente: string;
  servico: string;
  profissional: string;
  preco: number;
  desconto: string;
  linhas: LinhaPagamento[];
  quitar: boolean;
  erro: string;
  aoDesconto: (valor: string) => void;
  aoLinhas: (linhas: LinhaPagamento[]) => void;
  aoQuitar: (valor: boolean) => void;
  aoConfirmar: () => void;
  aoFechar: () => void;
}) {
  const valorDesconto = lerReais(desconto);
  const total = Math.round((preco - valorDesconto) * 100) / 100;
  const distribuido = Math.round(linhas.reduce((acc, linha) => acc + lerReais(linha.valor), 0) * 100) / 100;
  const somaOk = total <= 0 || Math.abs(distribuido - total) < 0.01;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/50 p-4" role="dialog" aria-modal="true" aria-labelledby="receber-pagamento" onClick={(evento) => { if (evento.target === evento.currentTarget) aoFechar(); }}>
      <div className="max-h-[90vh] w-full max-w-3xl overflow-auto rounded-2xl bg-white shadow-xl">
        <div className="flex items-center justify-between border-b px-4 py-3">
          <h2 id="receber-pagamento" className="text-lg font-bold">Receber pagamento</h2>
          <button type="button" className="rounded-lg px-2 py-1 text-lg leading-none" onClick={aoFechar} aria-label="Fechar">×</button>
        </div>
        <div className="space-y-4 p-5">
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2 text-sm">
              <p className="text-xs font-semibold uppercase text-gray-500">Dados do atendimento</p>
              <p><strong>Cliente:</strong> {cliente}</p>
              <p><strong>Serviço:</strong> {servico}</p>
              <p><strong>Profissional:</strong> {profissional}</p>
              <p><strong>Valor do serviço:</strong> {reais(preco)}</p>
              <p className="border-t pt-1 font-semibold">Total: {reais(preco)}</p>
              <label className="block pt-2 text-sm font-medium">Desconto (R$)
                <input type="number" step="0.01" min="0" className="mt-1 w-full rounded-lg border px-3 py-2" value={desconto} placeholder="0,00" onChange={(evento) => aoDesconto(evento.target.value)} />
              </label>
              <p className="pt-1 text-base font-bold text-[#7a3044]">Total a receber: {reais(Math.max(0, total))}</p>
            </div>
            {total <= 0 ? (
              <p className="rounded-lg border p-3 text-sm text-gray-600">Desconto integral. Nada a receber — confirme para quitar o atendimento.</p>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold uppercase text-gray-500">Formas de pagamento</p>
                  <button type="button" className="text-sm font-medium text-[#7a3044]" onClick={() => aoLinhas([...linhas, { id: String(Date.now()), forma: "pix", valor: "" }])}>+ Adicionar forma</button>
                </div>
                {linhas.map((linha, indice) => (
                  <div key={linha.id} className="space-y-2 rounded-lg border p-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-500">Forma {indice + 1}</span>
                      {linhas.length > 1 ? <button type="button" className="text-xs text-red-600" onClick={() => aoLinhas(linhas.filter((item) => item.id !== linha.id))}>Remover</button> : null}
                    </div>
                    <div className="grid gap-2 sm:grid-cols-2">
                      <label className="text-xs font-medium">Forma
                        <select className="mt-1 w-full rounded-lg border px-3 py-2 text-sm" value={linha.forma} onChange={(evento) => aoLinhas(linhas.map((item) => item.id === linha.id ? { ...item, forma: evento.target.value } : item))}>
                          {FORMAS_SALAO.map(([valor, nome]) => <option key={valor} value={valor}>{nome}</option>)}
                        </select>
                      </label>
                      <label className="text-xs font-medium">Valor (R$)
                        <input type="number" step="0.01" min="0" className="mt-1 w-full rounded-lg border px-3 py-2 text-sm" value={linha.valor} onChange={(evento) => aoLinhas(linhas.map((item) => item.id === linha.id ? { ...item, valor: evento.target.value } : item))} />
                      </label>
                    </div>
                  </div>
                ))}
                <p className={`text-sm font-medium ${somaOk ? "text-green-700" : "text-amber-700"}`}>
                  Distribuído: {reais(distribuido)} / {reais(Math.max(0, total))}{somaOk ? " ✓" : ""}
                </p>
              </div>
            )}
          </div>
          {erro ? <p className="rounded-lg bg-red-50 p-2 text-sm text-red-700">{erro}</p> : null}
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={quitar || total <= 0} disabled={total <= 0} onChange={(evento) => aoQuitar(evento.target.checked)} />
            Quitar pagamento completo
          </label>
          <div className="flex gap-2 border-t pt-2">
            <button type="button" className="flex-1 rounded-lg border py-2" onClick={aoFechar}>Cancelar</button>
            <button type="button" className="flex-1 rounded-lg bg-[#7a3044] py-2 text-white" onClick={aoConfirmar}>Confirmar</button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Mes({ cursor, eventos, aoAbrir }: { cursor: Date; eventos: AgendamentoSalao[]; aoAbrir: (data: Date) => void }) {
  const primeiro = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
  const dias = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 0).getDate();
  const offset = (primeiro.getDay() + 6) % 7;
  const celulas: Array<number | null> = [...Array(offset).fill(null), ...Array.from({ length: dias }, (_, indice) => indice + 1)];
  while (celulas.length % 7 !== 0) celulas.push(null);
  const linhas = celulas.length / 7;
  return (
    <div className="grid min-h-0 flex-1 grid-cols-7 gap-2" style={{ gridTemplateRows: `repeat(${linhas}, minmax(0, 1fr))` }}>
      {celulas.map((dia, indice) => {
        if (!dia) return <div key={`vazio-${indice}`} className="rounded-xl border border-[#f0e4e6] bg-white" />;
        const data = new Date(cursor.getFullYear(), cursor.getMonth(), dia);
        const total = eventos.filter((item) => new Date(item.inicio).toDateString() === data.toDateString() && item.status !== "CANCELLED").length;
        return (
          <button key={dia} type="button" className="h-full min-h-0 rounded-xl border border-[#f0e4e6] bg-white p-2 text-left" onClick={() => aoAbrir(data)}>
            <span className="text-sm">{dia}</span>
            {total ? <span className="mt-2 block text-xs text-[#7a3044]">{total} horário{total > 1 ? "s" : ""}</span> : null}
          </button>
        );
      })}
    </div>
  );
}
