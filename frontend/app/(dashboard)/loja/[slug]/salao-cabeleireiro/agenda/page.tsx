"use client";

import { ArrowLeft, CalendarDays, Save } from "lucide-react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties, type PointerEvent as ReactPointerEvent, type ReactNode } from "react";
import apiClient from "@/lib/api-client";
import { CLINICA_AGENDA_DURACAO_MIN_MIN, CLINICA_AGENDA_DURACAO_SNAP_MIN } from "@/lib/clinica-beleza-constants";
import { intervaloAgendaMinutos } from "@/lib/intervalo-agenda";
import { agendaVisualStyleVars, normalizeAgendaVisual, type AgendaVisualId } from "@/lib/clinica-agenda-visual";
import { STATUS_PADRAO, useStatusSalao } from "@/components/salao/cores-salao";
import { ModalBloqueioHorario } from "@/components/clinica-beleza/modal-bloqueio-horario/ModalBloqueioHorario";
import { diaTemAtendimento } from "@/components/salao/PaineisSalao";
import { SalaoAgendaCalendario } from "@/components/salao/SalaoAgendaCalendario";
import { SalaoAgendaLateral, useSalaoLateral } from "@/components/salao/SalaoAgendaLateral";
import { AlcaLarguraColuna, useAgendaColunaLargura } from "@/app/(dashboard)/loja/[slug]/agenda/components/useAgendaColunaLargura";
import { formatCpf, formatTelefone } from "@/lib/format-br";
import { SalaoAPI, type AgendamentoSalao, type BloqueioSalao, type ClienteSalao, type FormaPagamentoSalao, type JornadaDia, type LocalRecebimentoSalao, type ProfissionalSalao, type ServicoSalao } from "@/lib/salao-api";

const COR_MODAL = "#db2777";
const CAMPO_MODAL = "w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-pink-200";

type LinhaFormulario = { servico: number; profissional: string };

function fatiasDe(item: AgendamentoSalao) {
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

function duracaoDaVisita(linhas: { minutos: number }[]) {
  return linhas.reduce((acc, linha) => acc + linha.minutos, 0);
}

function rotuloStatus(status: string) {
  if (status === "CONFIRMED") return "Confirmado";
  if (status === "IN_PROGRESS") return "Em atendimento";
  if (status === "COMPLETED") return "Concluído";
  if (status === "CANCELLED") return "Cancelado";
  if (status === "NO_SHOW") return "Faltou";
  return "Aguardando";
}

function faixaDaLinha(inicio: string, minutosAntes: number, minutos: number) {
  const base = new Date(inicio);
  if (Number.isNaN(base.getTime())) return "";
  const comeco = new Date(base.getTime() + minutosAntes * 60_000);
  const fim = new Date(comeco.getTime() + minutos * 60_000);
  const hora = (data: Date) => `${dois(data.getHours())}:${dois(data.getMinutes())}`;
  return `${hora(comeco)}–${hora(fim)}`;
}

const HORA_INICIO = 8;
const HORA_FIM = 20;
const ALTURA_HORA = 52;

function dois(valor: number) {
  return String(valor).padStart(2, "0");
}

function diaLocalDeIso(valor: string) {
  const data = new Date(valor);
  if (Number.isNaN(data.getTime())) return valor.slice(0, 10);
  return `${data.getFullYear()}-${dois(data.getMonth() + 1)}-${dois(data.getDate())}`;
}

function tipoDoMotivo(motivo: string) {
  const texto = motivo.toLowerCase();
  if (texto.includes("férias") || texto.includes("ferias")) return "ferias";
  if (texto.includes("manutenção") || texto.includes("manutencao")) return "manutencao";
  if (texto.includes("evento") || texto.includes("reunião") || texto.includes("reuniao")) return "evento";
  if (texto.includes("feriado")) return "feriado";
  return "folga";
}

function corpoBloqueioSalao(body: Record<string, unknown>) {
  const inicioBruto = String(body.data_inicio || "");
  const fimBruto = String(body.data_fim || inicioBruto);
  const diaInteiro = Boolean(body.dia_inteiro);
  const inicio = new Date(inicioBruto);
  const fim = new Date(fimBruto);
  return {
    titulo: String(body.motivo || "Bloqueio").trim(),
    tipo: tipoDoMotivo(String(body.motivo || "")),
    profissional: body.professional ? Number(body.professional) : null,
    data_inicio: diaLocalDeIso(inicioBruto),
    data_fim: diaLocalDeIso(fimBruto),
    horario_inicio: diaInteiro || Number.isNaN(inicio.getTime()) ? "" : `${dois(inicio.getHours())}:${dois(inicio.getMinutes())}`,
    horario_fim: diaInteiro || Number.isNaN(fim.getTime()) ? "" : `${dois(fim.getHours())}:${dois(fim.getMinutes())}`,
    observacoes: String(body.observacoes || "").trim(),
  };
}

function horaDecimal(texto: string) {
  const [hora, minuto] = texto.split(":");
  return Number(hora) + Number(minuto || 0) / 60;
}

function horaTexto(valor: number) {
  const hora = Math.floor(valor);
  const minuto = Math.round((valor - hora) * 60);
  return `${dois(hora)}:${dois(minuto)}`;
}

function duracaoPeloPonteiro(origemMin: number, origemY: number, clientY: number, inicio: Date) {
  const bruto = origemMin + ((clientY - origemY) / ALTURA_HORA) * 60;
  const snap = Math.round(bruto / CLINICA_AGENDA_DURACAO_SNAP_MIN) * CLINICA_AGENDA_DURACAO_SNAP_MIN;
  const inicioMin = inicio.getHours() * 60 + inicio.getMinutes();
  const teto = Math.max(CLINICA_AGENDA_DURACAO_MIN_MIN, HORA_FIM * 60 - inicioMin);
  return Math.min(Math.max(snap, CLINICA_AGENDA_DURACAO_MIN_MIN), teto);
}

function isoDoDia(data: Date) {
  return `${data.getFullYear()}-${dois(data.getMonth() + 1)}-${dois(data.getDate())}`;
}

function dataCurta(iso: string) {
  const [, mes, dia] = iso.split("-");
  return `${dia}/${mes}`;
}

function bloqueioCabeNoFiltro(item: BloqueioSalao, filtro: string) {
  return filtro === "todos" || !item.profissional || String(item.profissional) === filtro;
}

function rotuloDoBloqueio(item: BloqueioSalao) {
  const quando = item.data_fim !== item.data_inicio ? `${dataCurta(item.data_inicio)} a ${dataCurta(item.data_fim)}` : dataCurta(item.data_inicio);
  const faixa = item.horario_inicio && item.horario_fim ? `${item.horario_inicio.slice(0, 5)}–${item.horario_fim.slice(0, 5)}` : "dia inteiro";
  return `${quando} · ${faixa}`;
}

function intervaloDoProfissional(jornadas: Record<number, JornadaDia[]>, profissionalId: string, data: Date) {
  const jornada = jornadas[Number(profissionalId)] || [];
  const diaSemana = (data.getDay() + 6) % 7;
  const item = jornada.find((linha) => linha.dia_semana === diaSemana && linha.ativo);
  if (!item?.intervalo_inicio || !item.intervalo_fim) return null;
  const inicio = horaDecimal(item.intervalo_inicio);
  const fim = horaDecimal(item.intervalo_fim);
  if (!(fim > inicio)) return null;
  return { inicio, fim };
}

type LinhaPagamento = { id: string; forma: string; valor: string };

const FORMAS_PADRAO: FormaPagamentoSalao[] = [
  { id: 0, codigo: "dinheiro", nome: "Dinheiro", ativo: true },
  { id: 0, codigo: "pix", nome: "Pix", ativo: true },
  { id: 0, codigo: "debito", nome: "Débito", ativo: true },
  { id: 0, codigo: "credito", nome: "Crédito", ativo: true },
];

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
  const ignorarClique = useRef(false);
  const redimensionando = useRef<{ id: number; origemMin: number; origemY: number; minutos: number; inicio: Date } | null>(null);
  const limparResize = useRef<(() => void) | null>(null);
  const [previewDuracao, setPreviewDuracao] = useState<{ id: number; minutos: number } | null>(null);
  const [modo, setModo] = useState<"dia" | "semana" | "mes">("semana");
  const [visual, setVisual] = useState<AgendaVisualId>("pulse");
  const [filtroProfissional, setFiltroProfissional] = useState("todos");
  const [lista, setLista] = useState(false);
  const [cursor, setCursor] = useState(() => new Date());
  const [faixa, setFaixa] = useState<{ inicio: number; fim: number } | null>(null);
  const [salto, setSalto] = useState(0);
  const pedidoAgenda = useRef(0);
  const [profissionais, setProfissionais] = useState<ProfissionalSalao[]>([]);
  const [servicos, setServicos] = useState<ServicoSalao[]>([]);
  const [clientes, setClientes] = useState<ClienteSalao[]>([]);
  const [eventos, setEventos] = useState<AgendamentoSalao[]>([]);
  const [erro, setErro] = useState("");
  const [form, setForm] = useState<Record<string, string> | null>(null);
  const [escolhidos, setEscolhidos] = useState<LinhaFormulario[]>([]);
  const [selecionado, setSelecionado] = useState<AgendamentoSalao | null>(null);
  const [desconto, setDesconto] = useState("");
  const [receberAberto, setReceberAberto] = useState(false);
  const [quitar, setQuitar] = useState(true);
  const [formasPagamento, setFormasPagamento] = useState<FormaPagamentoSalao[]>(FORMAS_PADRAO);
  const [linhas, setLinhas] = useState<LinhaPagamento[]>([{ id: "1", forma: "dinheiro", valor: "" }]);
  const [confirmaWhatsapp, setConfirmaWhatsapp] = useState(false);
  const [localRecebimento, setLocalRecebimento] = useState<LocalRecebimentoSalao>("caixa");
  const [jornadas, setJornadas] = useState<Record<number, JornadaDia[]>>({});
  const [aviso, setAviso] = useState("");
  const [confirmarExclusao, setConfirmarExclusao] = useState(false);
  const [bloqueios, setBloqueios] = useState<BloqueioSalao[]>([]);
  const [folgaAberta, setFolgaAberta] = useState(false);
  const [bloqueioAberto, setBloqueioAberto] = useState<BloqueioSalao | null>(null);
  const { ocultar: ocultarLateral, setOcultar: setOcultarLateral } = useSalaoLateral();
  const larguraColuna = useAgendaColunaLargura("salao-agenda-colunas", 220);

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
      const visiveis = filtroProfissional === "todos" ? profissionais : profissionais.filter((item) => String(item.id) === filtroProfissional);
      return visiveis.map((item) => ({ id: String(item.id), titulo: item.nome, detalhe: item.especialidade, data: inicio }));
    }
    if (modo === "mes") return [] as { id: string; titulo: string; detalhe: string; data: Date }[];
    return Array.from({ length: 7 }, (_, indice) => {
      const data = new Date(inicio);
      data.setDate(inicio.getDate() + indice);
      return { id: data.toDateString(), titulo: data.toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit" }), detalhe: "", data };
    }).filter((coluna) => diaTemAtendimento(coluna.data, "todos", profissionais, jornadas) || bloqueios.some((item) => item.data_inicio <= isoDoDia(coluna.data) && item.data_fim >= isoDoDia(coluna.data) && bloqueioCabeNoFiltro(item, filtroProfissional)));
  }, [periodo.inicio, modo, profissionais, jornadas, filtroProfissional, bloqueios]);

  const usaCalendario = !lista && !(modo === "dia" && filtroProfissional === "todos");
  const inicioBusca = usaCalendario && faixa ? faixa.inicio : periodo.inicio;
  const fimBusca = usaCalendario && faixa ? faixa.fim : periodo.fim;

  const carregar = useCallback(() => {
    const id = ++pedidoAgenda.current;
    setErro("");
    Promise.all([
      SalaoAPI.profissionais(),
      SalaoAPI.servicos(),
      SalaoAPI.clientes(),
      SalaoAPI.agenda(paraApi(new Date(inicioBusca)), paraApi(new Date(fimBusca))),
    ])
      .then(([listaProfissionais, listaServicos, listaClientes, listaEventos]) => {
        if (id !== pedidoAgenda.current) return;
        setProfissionais(listaProfissionais);
        setServicos(listaServicos);
        setClientes(listaClientes);
        setEventos(listaEventos);
      })
      .catch((exc: Error) => {
        if (id === pedidoAgenda.current) setErro(exc.message);
      });
  }, [fimBusca, inicioBusca]);

  useEffect(() => { carregar(); }, [carregar]);
  useEffect(() => {
    const chave = `lwk:salao-agenda-visual:${slug}`;
    try {
      const guardado = window.sessionStorage.getItem(chave);
      if (guardado) setVisual(normalizeAgendaVisual(guardado));
    } catch { /* o navegador pode bloquear a sessão */ }
    let vivo = true;
    const carregar = () => {
      apiClient.get<{ agenda_visual?: string }>("/salao-cabeleireiro/identidade/").then((resposta) => {
        if (!vivo) return;
        const id = normalizeAgendaVisual(resposta.data.agenda_visual);
        setVisual(id);
        try { window.sessionStorage.setItem(chave, id); } catch { /* ignora */ }
      }).catch(() => undefined);
    };
    const aoTrocar = (evento: Event) => {
      const id = normalizeAgendaVisual((evento as CustomEvent<string>).detail);
      setVisual(id);
    };
    carregar();
    window.addEventListener("salao-agenda-visual", aoTrocar);
    window.addEventListener("focus", carregar);
    return () => {
      vivo = false;
      window.removeEventListener("salao-agenda-visual", aoTrocar);
      window.removeEventListener("focus", carregar);
    };
  }, [slug]);
  useEffect(() => {
    SalaoAPI.formas().then((lista) => { if (lista.length) setFormasPagamento(lista); }).catch(() => undefined);
  }, []);
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
      cliente_cpf: "",
      observacoes: "",
    });
    setEscolhidos([]);
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
    if (escolhidos.length === 0) {
      setErro("Escolha ao menos um procedimento.");
      return;
    }
    setErro("");
    setAviso("");
    const corpo: Record<string, unknown> = {
      inicio: form.inicio,
      profissional: Number(escolhidos[0]?.profissional || form.profissional),
      servicos: escolhidos.map((linha) => linha.servico),
      procedimentos: escolhidos.map((linha) => ({ servico: linha.servico, profissional: Number(linha.profissional) })),
      observacoes: form.observacoes,
    };
    if (form.cliente) corpo.cliente = Number(form.cliente);
    else {
      corpo.cliente_nome = form.cliente_nome;
      corpo.cliente_telefone = form.cliente_telefone;
      if (form.cliente_cpf) corpo.cliente_cpf = form.cliente_cpf;
    }
    try {
      const atualizado = selecionado
        ? await SalaoAPI.atualizarAgendamento(selecionado.id, corpo)
        : await SalaoAPI.criarAgendamento(corpo);
      const quando = deApi(form.inicio);
      setCursor(quando);
      setSalto((valor) => valor + 1);
      setAviso(atualizado.aviso || "Agendamento salvo.");
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

  function abrirHorario(item: AgendamentoSalao) {
    setErro("");
    setConfirmarExclusao(false);
    setSelecionado(item);
    setForm({
      inicio: paraApi(new Date(item.inicio)).slice(0, 16),
      profissional: String(item.profissional),
      servico: String(item.servico),
      cliente: String(item.cliente),
      cliente_nome: "",
      cliente_telefone: "",
      cliente_cpf: "",
      observacoes: item.observacoes,
    });
    setEscolhidos(item.procedimentos?.length
      ? item.procedimentos.map((linha) => ({ servico: linha.id, profissional: String(linha.profissional || item.profissional) }))
      : [{ servico: item.servico, profissional: String(item.profissional) }]);
  }

  useEffect(() => () => limparResize.current?.(), []);

  function iniciarRedimensionar(evento: ReactPointerEvent, item: AgendamentoSalao) {
    evento.preventDefault();
    evento.stopPropagation();
    limparResize.current?.();
    const inicio = new Date(item.inicio);
    redimensionando.current = { id: item.id, origemMin: item.duracao_minutos, origemY: evento.clientY, minutos: item.duracao_minutos, inicio };
    setPreviewDuracao({ id: item.id, minutos: item.duracao_minutos });
    const mover = (ponteiro: PointerEvent) => {
      const atual = redimensionando.current;
      if (!atual) return;
      atual.minutos = duracaoPeloPonteiro(atual.origemMin, atual.origemY, ponteiro.clientY, atual.inicio);
      setPreviewDuracao({ id: atual.id, minutos: atual.minutos });
    };
    const encerrar = () => {
      limparResize.current = null;
      window.removeEventListener("pointermove", mover);
      window.removeEventListener("pointerup", encerrar);
      const atual = redimensionando.current;
      redimensionando.current = null;
      setPreviewDuracao(null);
      ignorarClique.current = true;
      window.setTimeout(() => { ignorarClique.current = false; }, 450);
      if (!atual || atual.minutos === atual.origemMin) return;
      const minutos = atual.minutos;
      void SalaoAPI.atualizarAgendamento(atual.id, { duracao_minutos: minutos })
        .then(() => {
          setAviso(`Tempo ajustado para ${minutos} min.`);
          carregar();
        })
        .catch((exc: Error) => setErro(exc.message || "Não foi possível ajustar o tempo."));
    };
    limparResize.current = () => {
      window.removeEventListener("pointermove", mover);
      window.removeEventListener("pointerup", encerrar);
      redimensionando.current = null;
    };
    window.addEventListener("pointermove", mover);
    window.addEventListener("pointerup", encerrar);
  }

  async function redimensionar(eventoId: number, minutos: number) {
    try {
      await SalaoAPI.atualizarAgendamento(eventoId, { duracao_minutos: minutos });
      setAviso(`Tempo ajustado para ${minutos} min.`);
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível ajustar o tempo.");
    }
  }

  async function soltar(eventoId: number, data: Date, profissionalId?: string) {
    const atual = eventos.find((item) => item.id === eventoId);
    if (!atual) return;
    const inicio = new Date(atual.inicio);
    inicio.setFullYear(data.getFullYear(), data.getMonth(), data.getDate());
    inicio.setHours(data.getHours(), data.getMinutes(), 0, 0);
    try {
      const varios = new Set(fatiasDe(atual).map((fatia) => fatia.profissional)).size > 1;
      await SalaoAPI.atualizarAgendamento(eventoId, {
        inicio: paraApi(inicio),
        ...(profissionalId && !varios ? { profissional: Number(profissionalId) } : {}),
      });
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Horário ocupado.");
    }
  }

  function abrirFolga() {
    setErro("");
    setFolgaAberta(true);
  }

  async function removerFolga(id: number) {
    setErro("");
    try {
      await SalaoAPI.removerBloqueio(id);
      setBloqueioAberto(null);
      recarregarBloqueios();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível remover a folga.");
    }
  }

  function folgasDoDia(data: Date) {
    const iso = isoDoDia(data);
    return bloqueios.filter((item) => item.data_inicio <= iso && item.data_fim >= iso && bloqueioCabeNoFiltro(item, filtroProfissional));
  }

  function almocoDaColuna(coluna: { id: string; data: Date }) {
    const pessoas = modo === "dia"
      ? profissionais.filter((pessoa) => String(pessoa.id) === coluna.id)
      : filtroProfissional === "todos"
        ? profissionais
        : profissionais.filter((pessoa) => String(pessoa.id) === filtroProfissional);
    return pessoas.flatMap((pessoa) => {
      const faixa = intervaloDoProfissional(jornadas, String(pessoa.id), coluna.data);
      return faixa ? [{ chave: String(pessoa.id), nome: pessoa.nome, ...faixa }] : [];
    });
  }

  const linhasLista = useMemo(() => {
    const ini = isoDoDia(new Date(periodo.inicio));
    const ultimo = new Date(periodo.fim);
    ultimo.setDate(ultimo.getDate() - 1);
    const fim = isoDoDia(ultimo);
    const compromissos = eventos
      .filter((item) => item.status !== "CANCELLED" && (filtroProfissional === "todos" || fatiasDe(item).some((fatia) => String(fatia.profissional) === filtroProfissional)))
      .map((item) => ({ chave: `a-${item.id}`, quando: new Date(item.inicio).getTime(), agenda: item, bloqueio: null as BloqueioSalao | null }));
    const folgas = bloqueios
      .filter((item) => item.data_inicio <= fim && item.data_fim >= ini && bloqueioCabeNoFiltro(item, filtroProfissional))
      .map((item) => ({ chave: `b-${item.id}`, quando: new Date(`${item.data_inicio}T${(item.horario_inicio || "00:00").slice(0, 5)}:00`).getTime(), agenda: null, bloqueio: item }));
    return [...compromissos, ...folgas].sort((esquerda, direita) => esquerda.quando - direita.quando);
  }, [bloqueios, eventos, filtroProfissional, periodo.fim, periodo.inicio]);

  const horas = Array.from({ length: HORA_FIM - HORA_INICIO }, (_, indice) => HORA_INICIO + indice);
  const diaGrade = isoDoDia(cursor);
  const itensDoDia = eventos.flatMap((item) => fatiasDe(item)
    .filter((fatia) => diaLocalDeIso(fatia.inicio) === diaGrade)
    .map((fatia, indice) => ({
      chave: `${item.id}-${fatia.profissional}-${indice}`,
      hora: `${dois(new Date(fatia.inicio).getHours())}:${dois(new Date(fatia.inicio).getMinutes())}`,
      cliente: item.cliente_nome,
      detalhe: `${fatia.servico_nome} · ${fatia.profissional_nome}`,
      status: rotuloStatus(item.status),
      cor: statusCores[item.status] || STATUS_PADRAO.SCHEDULED,
      id: item.id,
    })));

  const tema = agendaVisualStyleVars(visual);
  const botao = (ativo: boolean): CSSProperties => ({
    borderRadius: "var(--agenda-radius, 999px)",
    borderColor: "var(--agenda-border, #e5e7eb)",
    background: ativo ? "var(--agenda-accent)" : "#fff",
    color: ativo ? "var(--agenda-accent-fg)" : "inherit",
  });

  return (
    <div className="agenda-grade-root flex h-[calc(100dvh-2rem)] flex-col overflow-hidden sm:h-[calc(100dvh-2.5rem)]" data-agenda-visual={visual} style={tema}>
      <div className="mb-3 flex shrink-0 flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-3xl font-semibold">Agenda</h1>
          <p className="text-sm text-[#8a6e74]">Mesma agenda da clínica: dia por profissional, semana e mês no calendário.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {lista || (modo === "dia" && filtroProfissional === "todos") ? (
            <>
              <button type="button" className="border bg-white px-3 py-1.5 text-sm" style={botao(false)} onClick={() => setCursor(new Date())}>Hoje</button>
              <button type="button" className="border bg-white px-3 py-1.5 text-sm" style={botao(false)} onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth(), cursor.getDate() - (modo === "mes" ? 30 : modo === "semana" ? 7 : 1)))}>Anterior</button>
              <button type="button" className="border bg-white px-3 py-1.5 text-sm" style={botao(false)} onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth(), cursor.getDate() + (modo === "mes" ? 30 : modo === "semana" ? 7 : 1)))}>Próxima</button>
            </>
          ) : null}
          <button type="button" className="border px-3 py-1.5 text-sm" style={botao(lista)} onClick={() => setLista((aberta) => !aberta)}>Lista</button>
          <select className="border bg-white px-3 py-1.5 text-sm" style={botao(false)} value={filtroProfissional} aria-label="Profissional" onChange={(evento) => setFiltroProfissional(evento.target.value)}>
            <option value="todos">Todos os profissionais</option>
            {profissionais.map((pessoa) => <option key={pessoa.id} value={pessoa.id}>{pessoa.nome}</option>)}
          </select>
          <Link href={`/loja/${slug}/salao-cabeleireiro/configuracoes/aparencia`} className="border bg-white px-3 py-1.5 text-sm" style={botao(false)}>Configurar</Link>
          <button type="button" className="border bg-white px-3 py-1.5 text-sm" style={botao(false)} onClick={abrirFolga}>Bloquear</button>
          {modo === "dia" && filtroProfissional === "todos" && !lista ? (
            <button type="button" className="border bg-white px-3 py-1.5 text-sm" style={botao(false)} aria-pressed={ocultarLateral} onClick={() => setOcultarLateral((atual) => !atual)}>
              {ocultarLateral ? "Mostrar" : "Ocultar"}
            </button>
          ) : null}
          {lista || (modo === "dia" && filtroProfissional === "todos") ? (["dia", "semana", "mes"] as const).map((item) => (
            <button key={item} type="button" className="border px-3 py-1.5 text-sm" style={botao(modo === item && !lista)} onClick={() => { setModo(item); setLista(false); }}>
              {item === "dia" ? "Dia" : item === "semana" ? "Semana" : "Mês"}
            </button>
          )) : null}
          <button type="button" className="border px-3 py-1.5 text-sm" style={botao(true)} onClick={() => abrirNovo(cursor)}>+ Novo agendamento</button>
        </div>
      </div>
      {erro ? <p className="mb-2 text-sm text-red-700">{erro}</p> : null}
      {aviso ? <p className="mb-2 text-sm text-[#1f8a4c]">{aviso}</p> : null}
      {profissionais.length === 0 ? <p className="mb-2 text-sm text-[#8a6e74]">Cadastre um profissional para abrir as colunas do dia.</p> : null}
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
      {!lista && !(modo === "dia" && filtroProfissional === "todos") ? (
        <SalaoAgendaCalendario
          modo={modo}
          cursor={cursor}
          visual={visual}
          filtroProfissional={filtroProfissional}
          profissionais={profissionais}
          jornadas={jornadas}
          eventos={eventos}
          bloqueios={bloqueios}
          statusCores={statusCores}
          onVista={(vista) => setModo(vista)}
          onCursor={setCursor}
          onIntervalo={(inicio, fim) => {
            const proxima = { inicio: inicio.getTime(), fim: fim.getTime() };
            setFaixa((atual) => atual && atual.inicio === proxima.inicio && atual.fim === proxima.fim ? atual : proxima);
          }}
          salto={salto}
          onAbrir={abrirHorario}
          onAbrirBloqueio={setBloqueioAberto}
          onNovo={abrirNovo}
          onMover={(id, inicio) => { void soltar(id, inicio); }}
          onRedimensionar={(id, minutos) => { void redimensionar(id, minutos); }}
        />
      ) : lista ? (
        <ul className={`min-h-0 flex-1 overflow-auto border bg-white p-3 ${filtroProfissional === "todos" ? "grid grid-cols-1 gap-2 sm:grid-cols-2" : "space-y-2"}`} style={{ ...tema, borderColor: "var(--agenda-border)", borderRadius: "var(--agenda-radius, 16px)" }}>
          {linhasLista.length === 0 ? <li className={`text-sm text-[#8a6e74] ${filtroProfissional === "todos" ? "sm:col-span-2" : ""}`}>Nenhum horário neste período.</li> : null}
          {linhasLista.map((linha) => (
            <li key={linha.chave}>
              {linha.bloqueio ? (
                <button type="button" className="flex h-full w-full items-center justify-between gap-3 border-l-4 border-[#7a3044] px-3 py-2 text-left text-sm text-[#7a3044]" style={{ background: "#f6e4e8", borderRadius: "var(--agenda-card-radius, 12px)" }} onClick={() => { setForm(null); setSelecionado(null); setBloqueioAberto(linha.bloqueio); }}>
                  <span>{rotuloDoBloqueio(linha.bloqueio)} · {linha.bloqueio.titulo}</span>
                  <span className="truncate">Folga · {linha.bloqueio.profissional_nome}</span>
                </button>
              ) : linha.agenda ? (
                <button type="button" className="flex h-full w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm text-white" style={{ background: statusCores[linha.agenda.status] || STATUS_PADRAO.SCHEDULED, borderRadius: "var(--agenda-card-radius, 12px)" }} onClick={() => abrirHorario(linha.agenda)}>
                  <span>{new Date(linha.agenda.inicio).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })} · {linha.agenda.cliente_nome}</span>
                  <span className="truncate">{linha.agenda.servico_nome} · {linha.agenda.profissional_nome}</span>
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      ) : modo === "mes" ? (
        <div className="flex min-h-0 flex-1 flex-col" style={tema}>
          <Mes cursor={cursor} eventos={eventos.filter((item) => filtroProfissional === "todos" || fatiasDe(item).some((fatia) => String(fatia.profissional) === filtroProfissional))} bloqueios={bloqueios.filter((item) => bloqueioCabeNoFiltro(item, filtroProfissional))} statusCores={statusCores} aoAbrir={(data) => { setCursor(data); setModo("dia"); }} />
        </div>
      ) : (
        <div className="flex min-h-0 flex-1 overflow-hidden border bg-white" style={{ ...tema, borderColor: "var(--agenda-border, #e5e7eb)", borderRadius: "var(--agenda-radius, 16px)" }}>
          <div className="min-h-0 min-w-0 flex-1 overflow-auto">
          <div className="grid" style={{ gridTemplateColumns: `64px ${colunas.map((coluna) => ocultarLateral ? "minmax(160px, 1fr)" : larguraColuna.template(coluna.id)).join(" ") || "minmax(160px, 1fr)"}` }}>
            <div />
            {colunas.map((coluna) => {
              const folgas = folgasDoDia(coluna.data).filter((item) => modo !== "dia" || !item.profissional || String(item.profissional) === coluna.id);
              return (
                <div key={coluna.id} data-agenda-col-wrap data-agenda-col-id={coluna.id} className="relative border-b border-l px-2 py-2 text-center text-xs text-[#8a6e74]" style={coluna.data.toDateString() === new Date().toDateString() ? { background: "var(--agenda-today-bg)" } : undefined}>
                  <AlcaLarguraColuna onPointerDown={(evento) => larguraColuna.iniciar(coluna.id, evento)} />
                  <span className="block font-medium text-[#2a1c20]">{coluna.titulo}</span>
                  {coluna.detalhe ? <span className="block truncate text-[10px] uppercase">{coluna.detalhe}</span> : null}
                  {folgas.map((item) => (
                    <button key={item.id} type="button" className="mt-1 block w-full truncate text-[10px] text-[#7a3044]" title={item.titulo} onClick={(evento) => { evento.stopPropagation(); setBloqueioAberto(item); }}>
                      {item.horario_inicio && item.horario_fim ? `${item.horario_inicio.slice(0, 5)}–${item.horario_fim.slice(0, 5)} · ` : "Dia inteiro · "}Folga · {item.profissional_nome}
                    </button>
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
                data-agenda-col-wrap
                data-agenda-col-id={coluna.id}
                className="relative border-l"
                style={{ height: horas.length * ALTURA_HORA }}
                onDragOver={(evento) => evento.preventDefault()}
                onDrop={(evento) => {
                  const id = Number(evento.dataTransfer.getData("text/plain"));
                  const retangulo = evento.currentTarget.getBoundingClientRect();
                  const hora = HORA_INICIO + (evento.clientY - retangulo.top) / ALTURA_HORA;
                  const data = new Date(coluna.data);
                  const passo = intervaloAgendaMinutos(profissionais.find((pessoa) => String(pessoa.id) === (modo === "dia" ? coluna.id : filtroProfissional)));
                  data.setHours(Math.floor(hora), Math.round(((hora % 1) * 60) / passo) * passo, 0, 0);
                  soltar(id, data, modo === "dia" ? coluna.id : undefined);
                }}
                onClick={(evento) => {
                  if (ignorarClique.current || larguraColuna.deveIgnorarClick()) return;
                  if ((evento.target as HTMLElement).dataset.evento) return;
                  const retangulo = evento.currentTarget.getBoundingClientRect();
                  const hora = HORA_INICIO + (evento.clientY - retangulo.top) / ALTURA_HORA;
                  const data = new Date(coluna.data);
                  const passo = intervaloAgendaMinutos(profissionais.find((pessoa) => String(pessoa.id) === (modo === "dia" ? coluna.id : filtroProfissional)));
                  data.setHours(Math.floor(hora), Math.round(((hora % 1) * 60) / passo) * passo, 0, 0);
                  abrirNovo(data, modo === "dia" ? coluna.id : "");
                }}
              >
                <AlcaLarguraColuna onPointerDown={(evento) => larguraColuna.iniciar(coluna.id, evento)} />
                {horas.map((hora) => <div key={hora} style={{ height: ALTURA_HORA, borderColor: "var(--agenda-border)" }} className="border-b" />)}
                {(() => {
                  const agora = new Date();
                  const hora = agora.getHours() + agora.getMinutes() / 60;
                  if (coluna.data.toDateString() !== agora.toDateString() || hora < HORA_INICIO || hora > HORA_FIM) return null;
                  return <div className="pointer-events-none absolute right-0 left-0 z-10 h-0.5" style={{ top: (hora - HORA_INICIO) * ALTURA_HORA, background: "var(--agenda-now, #ef4444)" }} />;
                })()}
                {almocoDaColuna(coluna).map((faixa) => {
                  const topo = (faixa.inicio - HORA_INICIO) * ALTURA_HORA;
                  const faixaHora = `${horaTexto(faixa.inicio)}–${horaTexto(faixa.fim)}`;
                  return (
                    <div
                      key={faixa.chave}
                      className="pointer-events-none absolute right-1 left-1 overflow-hidden border-l-4 border-[#d97706] bg-[#f8e7c8] px-2 py-1"
                      style={{
                        top: Math.max(0, topo),
                        height: Math.max(28, (faixa.fim - faixa.inicio) * ALTURA_HORA),
                        borderRadius: "var(--agenda-card-radius, 8px)",
                        zIndex: 0,
                      }}
                      title={`Almoço · ${faixa.nome} · ${faixaHora}`}
                    >
                      <span className="block truncate text-[11px] font-semibold text-[#7a4b12]">Almoço</span>
                      <span className="block truncate text-[11px] text-[#7a4b12]">{faixaHora}{modo === "semana" ? ` · ${faixa.nome}` : ""}</span>
                    </div>
                  );
                })}
                {folgasDoDia(coluna.data).filter((item) => modo !== "dia" || !item.profissional || String(item.profissional) === coluna.id).map((item) => {
                  const diaInteiro = !item.horario_inicio || !item.horario_fim;
                  const faixaCurta = modo === "semana" && diaInteiro && Boolean(item.profissional);
                  const inicioHora = !diaInteiro && item.horario_inicio ? horaDecimal(item.horario_inicio) : HORA_INICIO;
                  const fimHora = faixaCurta ? HORA_INICIO + 0.7 : !diaInteiro && item.horario_fim ? horaDecimal(item.horario_fim) : HORA_FIM;
                  const topo = (inicioHora - HORA_INICIO) * ALTURA_HORA;
                  const cobreAColuna = modo === "dia" || !item.profissional;
                  return (
                    <button key={item.id} type="button" data-evento="1" className={`absolute border-l-4 border-[#7a3044] bg-[#f6e4e8] px-1 py-0.5 text-left text-[11px] text-[#7a3044] ${cobreAColuna ? "right-1 left-1" : "left-1 w-[46%]"}`} style={{ top: Math.max(0, topo), height: Math.max(22, (fimHora - inicioHora) * ALTURA_HORA), borderRadius: "var(--agenda-card-radius, 8px)", zIndex: cobreAColuna ? 2 : 3 }} title={`${item.titulo} · ${item.profissional_nome}`} onClick={(evento) => { evento.stopPropagation(); setBloqueioAberto(item); }}>
                      Folga · {item.profissional_nome}
                      <span className="block truncate">{item.titulo}</span>
                    </button>
                  );
                })}
                {eventos.flatMap((item) => {
                  const varios = fatiasDe(item).length > 1 && new Set(fatiasDe(item).map((fatia) => fatia.profissional)).size > 1;
                  const pedacos = modo === "dia"
                    ? fatiasDe(item).filter((fatia) => String(fatia.profissional) === coluna.id && diaLocalDeIso(fatia.inicio) === isoDoDia(coluna.data))
                    : fatiasDe(item).filter((fatia) => diaLocalDeIso(fatia.inicio) === isoDoDia(coluna.data) && (filtroProfissional === "todos" || String(fatia.profissional) === filtroProfissional));
                  return pedacos.map((fatia, indice) => {
                    const inicio = new Date(fatia.inicio);
                    const minutos = !varios && previewDuracao?.id === item.id ? previewDuracao.minutos : fatia.duracao_minutos;
                    const fim = new Date(inicio.getTime() + minutos * 60_000);
                    const faixa = `${dois(inicio.getHours())}:${dois(inicio.getMinutes())}–${dois(fim.getHours())}:${dois(fim.getMinutes())}`;
                    const topo = ((inicio.getHours() + inicio.getMinutes() / 60) - HORA_INICIO) * ALTURA_HORA;
                    return (
                      <button
                        key={`${item.id}-${fatia.profissional}-${indice}`}
                        type="button"
                        data-evento="1"
                        draggable={!item.recebido}
                        onDragStart={(evento) => {
                          if ((evento.target as HTMLElement).closest("[data-resize]")) {
                            evento.preventDefault();
                            return;
                          }
                          evento.dataTransfer.setData("text/plain", String(item.id));
                        }}
                        onClick={(evento) => { evento.stopPropagation(); if (ignorarClique.current) return; abrirHorario(item); }}
                        title={`${faixa} · ${minutos} min · Profissional ${fatia.profissional_nome} · Cliente ${item.cliente_nome}`}
                        className="absolute right-1 left-1 overflow-hidden px-1.5 py-0.5 text-left text-[11px] leading-tight text-white"
                        style={{ top: Math.max(0, topo), height: Math.max(48, (minutos / 60) * ALTURA_HORA), background: statusCores[item.status] || STATUS_PADRAO.SCHEDULED, borderRadius: "var(--agenda-card-radius, 12px)", boxShadow: "var(--agenda-card-shadow, none)", zIndex: 1 }}
                      >
                        <span className="block truncate font-medium">{faixa}</span>
                        <span className="block truncate font-semibold">{rotuloStatus(item.status)}</span>
                        <span className="block truncate uppercase">{item.cliente_nome}</span>
                        <span className="block truncate">{fatia.servico_nome}{modo === "semana" ? ` · ${fatia.profissional_nome}` : ""}</span>
                        {item.recebido || varios ? null : (
                          <span
                            data-resize="1"
                            className="absolute right-0 bottom-0 left-0 z-10 flex h-3 cursor-ns-resize touch-none items-end justify-center"
                            title="Arraste para aumentar ou diminuir o tempo"
                            onPointerDown={(evento) => iniciarRedimensionar(evento, item)}
                            onClick={(evento) => evento.stopPropagation()}
                          >
                            <span className="mb-0.5 block h-1 w-8 rounded-full bg-white/70" />
                          </span>
                        )}
                      </button>
                    );
                  });
                })}
              </div>
            ))}
          </div>
          </div>
          {ocultarLateral ? null : (
            <SalaoAgendaLateral
              diaIso={diaGrade}
              hojeIso={isoDoDia(new Date())}
              itens={itensDoDia}
              aoEscolherDia={(iso) => setCursor(deApi(`${iso}T12:00:00`))}
              aoAbrir={(chave) => {
                const item = eventos.find((agenda) => chave.startsWith(`${agenda.id}-`));
                if (item) abrirHorario(item);
              }}
            />
          )}
        </div>
      )}
      </div>
      <p className="mt-2 flex shrink-0 flex-wrap gap-x-3 gap-y-1 border-t border-[#f0e4e6] bg-white px-3 py-2 text-[11px] text-[#5c3d45]" role="list" aria-label="Legenda de status da agenda">
        {[["Aguardando", statusCores.SCHEDULED || STATUS_PADRAO.SCHEDULED], ["Confirmado", statusCores.CONFIRMED || STATUS_PADRAO.CONFIRMED], ["Em atendimento", statusCores.IN_PROGRESS || STATUS_PADRAO.IN_PROGRESS], ["Concluído", statusCores.COMPLETED || STATUS_PADRAO.COMPLETED], ["Cancelado", statusCores.CANCELLED || STATUS_PADRAO.CANCELLED], ["Faltou", statusCores.NO_SHOW || STATUS_PADRAO.NO_SHOW], ["Almoço", "#f8e7c8"], ["Folga", "#f6e4e8"]].map(([nome, cor]) => (
          <span key={nome} role="listitem" className="inline-flex items-center gap-1.5"><span className="inline-block h-2.5 w-2.5 shrink-0 rounded-full ring-1 ring-black/10" style={{ background: cor }} />{nome}</span>
        ))}
      </p>
      <ModalBloqueioHorario
        isOpen={folgaAberta}
        onClose={() => setFolgaAberta(false)}
        onSuccess={() => { setAviso("Horário bloqueado na agenda."); recarregarBloqueios(); }}
        professionals={profissionais.map((pessoa) => ({ id: pessoa.id, nome: pessoa.nome, specialty: pessoa.especialidade }))}
        dataInicioSugerida={cursor}
        defaultProfessionalId={filtroProfissional === "todos" ? "" : filtroProfissional}
        enviar={async (body) => {
          const corpo = corpoBloqueioSalao(body);
          await SalaoAPI.bloquear(corpo);
          setCursor(deApi(`${corpo.data_inicio}T12:00:00`));
          setLista(false);
        }}
      />
      {bloqueioAberto ? (
        <div className="fixed inset-0 z-40 grid place-items-center bg-black/40 p-4" role="dialog" aria-modal="true" aria-labelledby="folga-aberta" onClick={(evento) => { if (evento.target === evento.currentTarget) setBloqueioAberto(null); }}>
          <div className="w-full max-w-md rounded-3xl bg-white p-5">
            <h2 id="folga-aberta" className="text-lg font-semibold">{bloqueioAberto.titulo}</h2>
            <p className="mt-2 text-sm text-[#5c3d45]">{bloqueioAberto.profissional_nome}</p>
            <p className="mt-1 text-sm text-[#5c3d45]">
              {bloqueioAberto.data_inicio}{bloqueioAberto.data_fim !== bloqueioAberto.data_inicio ? ` a ${bloqueioAberto.data_fim}` : ""}
              {bloqueioAberto.horario_inicio ? ` · ${bloqueioAberto.horario_inicio.slice(0, 5)}–${bloqueioAberto.horario_fim?.slice(0, 5)}` : " · dia inteiro"}
            </p>
            {bloqueioAberto.observacoes ? <p className="mt-2 text-sm text-[#8a6e74]">{bloqueioAberto.observacoes}</p> : null}
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" className="rounded-full border px-4 py-2 text-sm" onClick={() => setBloqueioAberto(null)}>Fechar</button>
              <button type="button" className="rounded-full bg-red-600 px-4 py-2 text-sm text-white" onClick={() => removerFolga(bloqueioAberto.id)}>Excluir bloqueio</button>
            </div>
          </div>
        </div>
      ) : null}
      {form && !receberAberto ? (
        <Formulario
          titulo="Novo agendamento"
          form={form}
          setForm={setForm}
          clientes={clientes}
          profissionais={profissionais}
          servicos={servicos}
          escolhidos={escolhidos}
          aoEscolhidos={setEscolhidos}
          erro={erro}
          aoSalvar={salvar}
          aoClienteCriado={(cliente) => setClientes((lista) => lista.some((item) => item.id === cliente.id) ? lista : [...lista, cliente].sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR")))}
          aoFechar={() => { setForm(null); setSelecionado(null); setErro(""); setConfirmarExclusao(false); }}
          salvandoEdicao={Boolean(selecionado)}
          acoes={selecionado ? (
            <>
              <span className="mr-auto text-sm text-[#5c3d45]">Status: {selecionado.status_label}</span>
              {selecionado.status === "SCHEDULED" ? <button type="button" className="rounded-lg bg-[#7a3044] px-3 py-2 text-sm text-white" onClick={() => { void mudarStatus("CONFIRMED"); }}>Confirmar</button> : null}
              {confirmaWhatsapp && (selecionado.status === "SCHEDULED" || selecionado.status === "CONFIRMED") ? <button type="button" className="rounded-lg border border-gray-300 px-3 py-2 text-sm" onClick={() => { void enviarConfirmacao(); }}>Enviar confirmação</button> : null}
              {selecionado.status === "SCHEDULED" || selecionado.status === "CONFIRMED" ? <button type="button" className="rounded-lg bg-[#1f8f86] px-3 py-2 text-sm text-white" onClick={() => { void mudarStatus("IN_PROGRESS"); }}>Iniciar atendimento</button> : null}
              {selecionado.status === "IN_PROGRESS" ? <button type="button" className="rounded-lg bg-[#1f8a4c] px-3 py-2 text-sm text-white" onClick={() => { void mudarStatus("COMPLETED"); }}>Finalizar</button> : null}
              {selecionado.status === "COMPLETED" && !selecionado.recebido && localRecebimento !== "caixa" ? <button type="button" className="rounded-lg bg-[#7a3044] px-3 py-2 text-sm text-white" onClick={abrirReceber}>Receber</button> : null}
              {selecionado.status === "COMPLETED" && !selecionado.recebido && localRecebimento === "caixa" ? <Link href={`/loja/${slug}/salao-cabeleireiro/caixa`} className="rounded-lg bg-[#7a3044] px-3 py-2 text-sm text-white">Receber no Caixa/PDV</Link> : null}
              {selecionado.recebido ? (
                <>
                  <span className="rounded-lg bg-[#e8f6ee] px-3 py-2 text-sm text-[#1f8a4c]">Recebido R$ {selecionado.recebido.valor} · {selecionado.recebido.forma_label}</span>
                  <Link href={`/loja/${slug}/salao-cabeleireiro/financeiro`} className="rounded-lg border border-gray-300 px-3 py-2 text-sm">Ver no caixa</Link>
                  <button type="button" className="rounded-lg border border-gray-300 px-3 py-2 text-sm" onClick={() => { void desfazerRecebimento(); }}>Desfazer recebimento</button>
                </>
              ) : null}
              {selecionado.status !== "NO_SHOW" && selecionado.status !== "COMPLETED" && selecionado.status !== "CANCELLED" ? <button type="button" className="rounded-lg border border-gray-300 px-3 py-2 text-sm" onClick={() => { void mudarStatus("NO_SHOW"); }}>Faltou</button> : null}
              {!selecionado.recebido && selecionado.status !== "CANCELLED" ? (
                confirmarExclusao ? (
                  <>
                    <span className="text-sm text-[#8a6e74]">Excluir este agendamento?</span>
                    <button type="button" className="rounded-lg bg-red-700 px-3 py-2 text-sm text-white" onClick={() => { void excluir(); }}>Excluir</button>
                    <button type="button" className="text-sm text-[#8a6e74]" onClick={() => setConfirmarExclusao(false)}>Voltar</button>
                  </>
                ) : (
                  <button type="button" className="rounded-lg border border-red-200 px-3 py-2 text-sm text-red-700" onClick={() => setConfirmarExclusao(true)}>Excluir</button>
                )
              ) : null}
            </>
          ) : null}
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
    </div>
  );
}

function horariosDoPasso(passo: number, atual: string) {
  const minutos = Math.min(60, Math.max(5, passo || 15));
  const lista: string[] = [];
  for (let hora = 8; hora < 20; hora += 1) {
    for (let minuto = 0; minuto < 60; minuto += minutos) {
      lista.push(`${dois(hora)}:${dois(minuto)}`);
    }
  }
  if (atual && !lista.includes(atual)) lista.push(atual);
  return lista.sort();
}

function Formulario({
  titulo, form, setForm, clientes, profissionais, servicos, escolhidos, aoEscolhidos, erro, aoSalvar, aoClienteCriado, aoFechar, salvandoEdicao = false, acoes = null,
}: {
  titulo: string;
  form: Record<string, string>;
  setForm: (valor: Record<string, string>) => void;
  clientes: ClienteSalao[];
  profissionais: ProfissionalSalao[];
  servicos: ServicoSalao[];
  escolhidos: LinhaFormulario[];
  aoEscolhidos: (linhas: LinhaFormulario[]) => void;
  erro: string;
  aoSalvar: () => void;
  aoClienteCriado: (cliente: ClienteSalao) => void;
  aoFechar: () => void;
  salvandoEdicao?: boolean;
  acoes?: ReactNode;
}) {
  const [categoria, setCategoria] = useState("");
  const [salvandoCliente, setSalvandoCliente] = useState(false);
  const [erroCliente, setErroCliente] = useState("");
  const cliente = clientes.find((item) => String(item.id) === form.cliente);
  const data = form.inicio.slice(0, 10);
  const hora = form.inicio.slice(11, 16);
  const passo = intervaloAgendaMinutos(profissionais.find((pessoa) => String(pessoa.id) === form.profissional));
  const horarios = horariosDoPasso(passo, hora);
  const livres = servicos.filter((item) => !escolhidos.some((linha) => linha.servico === item.id));
  const categorias = [...new Set(livres.map((item) => item.categoria))].sort((a, b) => a.localeCompare(b, "pt-BR"));
  const daCategoria = categoria ? livres.filter((item) => item.categoria === categoria) : livres;
  const escolhidosServico = escolhidos.map((linha) => ({ linha, servico: servicos.find((item) => item.id === linha.servico) })).filter((item): item is { linha: LinhaFormulario; servico: ServicoSalao } => Boolean(item.servico));
  const minutos = duracaoDaVisita(escolhidosServico.map((item) => ({ minutos: item.servico.duracao_minutos })));
  const total = escolhidosServico.reduce((acc, item) => acc + lerReais(item.servico.preco), 0);
  const busca = form.cliente_nome.trim().toLocaleLowerCase("pt-BR");
  const digitosBusca = busca.replace(/\D/g, "");
  const encontrados = busca.length === 0 ? [] : clientes.filter((item) => item.nome.toLocaleLowerCase("pt-BR").includes(busca) || (digitosBusca.length >= 3 && (item.telefone || "").includes(digitosBusca))).slice(0, 6);

  function definirQuando(novaData: string, novaHora: string) {
    setForm({ ...form, inicio: `${novaData}T${novaHora}` });
  }

  function adicionar(id: number) {
    if (!id || !form.profissional || escolhidos.some((linha) => linha.servico === id)) return;
    aoEscolhidos([...escolhidos, { servico: id, profissional: form.profissional }]);
  }

  async function salvarCliente() {
    setErroCliente("");
    setSalvandoCliente(true);
    try {
      const criado = await SalaoAPI.salvarCliente({
        nome: form.cliente_nome.trim(),
        telefone: form.cliente_telefone,
        cpf: form.cliente_cpf || "",
      });
      aoClienteCriado(criado);
      setForm({ ...form, cliente: String(criado.id), cliente_nome: "", cliente_telefone: "", cliente_cpf: "" });
    } catch (exc) {
      setErroCliente(exc instanceof Error ? exc.message : "Não foi possível salvar o cliente.");
    } finally {
      setSalvandoCliente(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[110] flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-4 md:p-6" role="dialog" aria-modal="true" aria-labelledby="agenda-formulario" onClick={(evento) => { if (evento.target === evento.currentTarget) aoFechar(); }}>
      <div className="flex max-h-[100dvh] w-full flex-col overflow-hidden bg-white shadow-2xl sm:max-h-[92vh] sm:max-w-4xl sm:rounded-xl">
        <header className="flex shrink-0 items-center gap-2 border-b border-gray-200 bg-white px-4 py-3 sm:gap-3 sm:px-5">
          <button type="button" onClick={aoFechar} className="shrink-0 rounded-lg p-1.5 hover:bg-gray-100" aria-label="Voltar">
            <ArrowLeft className="h-5 w-5 text-gray-600" />
          </button>
          <span className="hidden h-9 w-9 shrink-0 items-center justify-center rounded-lg sm:flex" style={{ backgroundColor: "#fce7f3" }}>
            <CalendarDays className="h-4 w-4" style={{ color: COR_MODAL }} />
          </span>
          <span className="min-w-0 flex-1">
            <h1 id="agenda-formulario" className="truncate text-sm leading-tight font-semibold" style={{ color: COR_MODAL }}>{titulo}</h1>
            <p className="hidden truncate text-xs leading-snug text-gray-500 sm:block">Agendar atendimento no salão</p>
          </span>
        </header>
        <form className="flex min-h-0 flex-1 flex-col" onSubmit={(evento) => { evento.preventDefault(); aoSalvar(); }}>
          <div className="min-h-0 flex-1 overflow-y-auto bg-[#f7f2f4] p-4 sm:p-5">
            {erro ? <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{erro}</p> : null}
            <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm sm:p-6">
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2 md:gap-8">
                <div className="space-y-4">
                  <p className="border-b border-gray-100 pb-2 text-sm font-semibold text-gray-800">Cliente</p>
                  <div>
                    <p className="mb-1 text-xs font-medium text-gray-700">Cliente *</p>
                    {cliente ? (
                      <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 px-3 py-2.5">
                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-sm text-green-700">✓ <strong>{cliente.nome}</strong></span>
                          {cliente.telefone ? <span className="text-xs text-green-700/80">{formatTelefone(cliente.telefone)}</span> : null}
                        </span>
                        <button type="button" className="shrink-0 text-xs text-gray-500 hover:text-red-500" onClick={() => setForm({ ...form, cliente: "" })}>Trocar</button>
                      </div>
                    ) : (
                      <div className="space-y-2 rounded-lg border p-3" style={{ borderColor: "#f9a8d4", backgroundColor: "#fdf2f8" }}>
                        <p className="text-xs" style={{ color: COR_MODAL }}>Cadastro rápido — ao digitar, busca no cadastro pelo nome ou telefone.</p>
                        <input className={`${CAMPO_MODAL} min-h-11`} placeholder="Nome *" value={form.cliente_nome} onChange={(evento) => setForm({ ...form, cliente_nome: evento.target.value })} />
                        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                          <input className={`${CAMPO_MODAL} min-h-11`} placeholder="(00) 00000-0000" inputMode="tel" value={form.cliente_telefone} onChange={(evento) => setForm({ ...form, cliente_telefone: formatTelefone(evento.target.value) })} />
                          <input className={`${CAMPO_MODAL} min-h-11`} placeholder="CPF" value={form.cliente_cpf || ""} onChange={(evento) => setForm({ ...form, cliente_cpf: formatCpf(evento.target.value) })} />
                        </div>
                        {encontrados.length > 0 ? (
                          <div className="max-h-40 overflow-y-auto rounded-lg border border-gray-200 bg-white">
                            <p className="border-b border-gray-100 bg-gray-50 px-3 py-1.5 text-[11px] font-medium text-gray-500">Clientes encontrados — selecione ou cadastre novo abaixo</p>
                            {encontrados.map((item) => (
                              <button key={item.id} type="button" className="flex w-full items-center border-b border-gray-100 px-3 py-2 text-left text-sm last:border-b-0 hover:bg-pink-50" onClick={() => setForm({ ...form, cliente: String(item.id), cliente_nome: "", cliente_telefone: "", cliente_cpf: "" })}>
                                <span className="min-w-0">
                                  <span className="block truncate font-medium">{item.nome}</span>
                                  <span className="text-xs text-gray-500">{item.telefone ? formatTelefone(item.telefone) : ""}</span>
                                </span>
                              </button>
                            ))}
                          </div>
                        ) : null}
                        {erroCliente ? <p className="text-xs text-red-600">{erroCliente}</p> : null}
                        <button type="button" className="rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-50" style={{ backgroundColor: COR_MODAL }} disabled={salvandoCliente || form.cliente_nome.trim().length < 2} onClick={() => { void salvarCliente(); }}>
                          {salvandoCliente ? "Salvando..." : "Salvar novo cliente"}
                        </button>
                      </div>
                    )}
                  </div>
                  <div>
                    <p className="mb-2 text-sm font-medium text-gray-700">Procedimentos <span className="font-normal text-gray-400">(pode adicionar vários)</span></p>
                    {categorias.length > 1 ? (
                      <div className="mb-2 flex flex-wrap gap-1.5">
                        <button type="button" className={`rounded-full border px-2.5 py-1 text-xs font-medium ${categoria ? "border-gray-300 text-gray-600" : "border-transparent text-white"}`} style={categoria ? undefined : { backgroundColor: COR_MODAL }} onClick={() => setCategoria("")}>Todas</button>
                        {categorias.map((item) => (
                          <button key={item} type="button" className={`rounded-full border px-2.5 py-1 text-xs font-medium ${categoria === item ? "border-transparent text-white" : "border-gray-300 text-gray-600"}`} style={categoria === item ? { backgroundColor: COR_MODAL } : undefined} onClick={() => setCategoria(item)}>{item} ({livres.filter((servico) => servico.categoria === item).length})</button>
                        ))}
                      </div>
                    ) : null}
                    <select className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-pink-400 focus:ring-2 focus:ring-pink-200" value="" onChange={(evento) => adicionar(Number(evento.target.value))}>
                      <option value="">{categoria ? `Adicionar de ${categoria}...` : "Adicionar procedimento por categoria..."}</option>
                      {(categoria ? [{ nome: categoria, itens: daCategoria }] : categorias.map((nome) => ({ nome, itens: livres.filter((item) => item.categoria === nome) }))).map((grupo) => (
                        <optgroup key={grupo.nome} label={grupo.nome}>
                          {grupo.itens.map((item) => <option key={item.id} value={item.id}>{item.nome} · {item.duracao_minutos} min · {reais(lerReais(item.preco))}</option>)}
                        </optgroup>
                      ))}
                    </select>
                    {escolhidosServico.length === 0 ? <p className="mt-2 text-sm text-gray-500">Nenhum procedimento neste horário.</p> : (
                      <ul className="mt-3 space-y-2">
                        {escolhidosServico.map(({ linha, servico }, indice) => (
                          <li key={servico.id} className="flex items-center justify-between gap-2 rounded-lg border border-gray-100 px-3 py-2 text-sm">
                            <span className="min-w-0">
                              <span className="block truncate font-medium">{servico.nome}</span>
                              <span className="text-xs text-gray-500">{faixaDaLinha(form.inicio, escolhidosServico.slice(0, indice).reduce((acc, item) => acc + item.servico.duracao_minutos, 0), servico.duracao_minutos)} · {reais(lerReais(servico.preco))}</span>
                            </span>
                            <span className="flex shrink-0 items-center gap-2">
                              <select className="rounded-lg border border-gray-200 px-2 py-1 text-xs" value={linha.profissional} aria-label={`Profissional de ${servico.nome}`} onChange={(evento) => aoEscolhidos(escolhidos.map((atual) => atual.servico === servico.id ? { ...atual, profissional: evento.target.value } : atual))}>
                                {profissionais.map((pessoa) => <option key={pessoa.id} value={pessoa.id}>{pessoa.nome}</option>)}
                              </select>
                              <button type="button" className="text-xs text-gray-400 hover:text-red-500" onClick={() => aoEscolhidos(escolhidos.filter((atual) => atual.servico !== servico.id))}>Remover</button>
                            </span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
                <div className="space-y-4">
                  <p className="border-b border-gray-100 pb-2 text-sm font-semibold text-gray-800">Agendamento</p>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <label className="text-xs font-medium text-gray-600">Data *
                      <input type="date" className={`${CAMPO_MODAL} mt-1`} value={data} required onChange={(evento) => definirQuando(evento.target.value, hora || "09:00")} />
                    </label>
                    <label className="text-xs font-medium text-gray-600">Horário *
                      <select className={`${CAMPO_MODAL} mt-1`} value={hora} required onChange={(evento) => definirQuando(data, evento.target.value)}>
                        {horarios.map((item) => <option key={item} value={item}>{item}</option>)}
                      </select>
                    </label>
                    <label className="text-xs font-medium text-gray-600 sm:col-span-2">Profissional do próximo procedimento *
                      <select className={`${CAMPO_MODAL} mt-1`} value={form.profissional} required onChange={(evento) => setForm({ ...form, profissional: evento.target.value })}>
                        {profissionais.map((item) => <option key={item.id} value={item.id}>{item.nome}</option>)}
                      </select>
                    </label>
                  </div>
                  <p className="text-xs text-gray-500">O cliente passa para o próximo profissional quando o procedimento anterior termina.</p>
                  <div className="space-y-1 rounded-lg border border-gray-100 bg-gray-50 p-3 text-sm">
                    <p className="flex justify-between text-gray-600"><span>Duração</span><span>{minutos} min</span></p>
                    <p className="flex justify-between font-semibold text-gray-900"><span>Total estimado</span><span>{reais(total)}</span></p>
                  </div>
                  <label className="block text-xs font-medium text-gray-600">Observações
                    <textarea className={`${CAMPO_MODAL} mt-1 min-h-20`} value={form.observacoes} onChange={(evento) => setForm({ ...form, observacoes: evento.target.value })} />
                  </label>
                </div>
              </div>
            </div>
          </div>
          <footer className="shrink-0 border-t border-gray-200 bg-white/80 px-4 py-3 sm:px-5 sm:py-4">
            <div className="flex flex-wrap items-center justify-end gap-2">
              {acoes}
              <button type="button" className="rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-medium text-gray-700 hover:bg-white sm:min-w-[120px]" onClick={aoFechar}>Cancelar</button>
              <button type="submit" className="flex items-center justify-center gap-2 rounded-lg px-5 py-2.5 text-sm font-medium text-white sm:min-w-[180px]" style={{ backgroundColor: COR_MODAL }}>
                <Save className="h-4 w-4" />
                {salvandoEdicao ? "Salvar" : "Agendar"}
              </button>
            </div>
          </footer>
        </form>
      </div>
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
                  <button type="button" className="text-sm font-medium text-[#7a3044]" onClick={() => aoLinhas([...linhas, { id: String(Date.now()), forma: formasPagamento.find((item) => !linhas.some((linha) => linha.forma === item.codigo))?.codigo || formasPagamento[0]?.codigo || "dinheiro", valor: "" }])}>+ Adicionar forma</button>
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
                          {formasPagamento.map((forma) => <option key={forma.codigo} value={forma.codigo}>{forma.nome}</option>)}
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

function gradeDoMes(cursor: Date) {
  const ano = cursor.getFullYear();
  const mes = cursor.getMonth();
  const primeiro = new Date(ano, mes, 1);
  const quantidade = new Date(ano, mes + 1, 0).getDate();
  const offset = (primeiro.getDay() + 6) % 7;
  const inicio = new Date(ano, mes, 1 - offset);
  const total = Math.ceil((offset + quantidade) / 7) * 7;
  return Array.from({ length: total }, (_, indice) => {
    const data = new Date(inicio);
    data.setDate(inicio.getDate() + indice);
    return data;
  });
}

function Mes({ cursor, eventos, bloqueios, statusCores, aoAbrir }: { cursor: Date; eventos: AgendamentoSalao[]; bloqueios: BloqueioSalao[]; statusCores: Record<string, string>; aoAbrir: (data: Date) => void }) {
  const dias = gradeDoMes(cursor);
  const linhas = dias.length / 7;
  return (
    <div className="grid h-full min-h-0 flex-1 grid-cols-7 gap-1.5" style={{ gridTemplateRows: `auto repeat(${linhas}, minmax(0, 1fr))` }}>
      {["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"].map((nome) => (
        <div key={nome} className="px-1 text-center text-[11px] capitalize text-[#8a6e74]">{nome}</div>
      ))}
      {dias.map((data) => {
        const desteMes = data.getMonth() === cursor.getMonth();
        const iso = isoDoDia(data);
        const doDia = desteMes ? eventos.filter((item) => new Date(item.inicio).toDateString() === data.toDateString() && item.status !== "CANCELLED") : [];
        const folgas = desteMes ? bloqueios.filter((item) => item.data_inicio <= iso && item.data_fim >= iso) : [];
        const hoje = data.toDateString() === new Date().toDateString();
        const total = doDia.length + folgas.length;
        const visiveis = 6;
        return (
          <button key={iso} type="button" className="flex h-full min-h-0 w-full flex-col overflow-hidden border p-1.5 text-left" style={{ borderRadius: "var(--agenda-card-radius, 12px)", borderColor: hoje ? "var(--agenda-accent, #ad46ff)" : "var(--agenda-border, #e5e7eb)", background: hoje ? "var(--agenda-today-bg, #fff)" : desteMes ? "#fff" : "#f6f1f2" }} onClick={() => aoAbrir(data)}>
            <span className={`text-sm ${hoje ? "font-semibold" : ""} ${desteMes ? "" : "text-[#b9a4aa]"}`} style={hoje ? { color: "var(--agenda-focus-text)" } : undefined}>{data.getDate()}</span>
            <span className="mt-1 block min-h-0 flex-1 space-y-0.5 overflow-hidden">
              {folgas.slice(0, visiveis).map((item) => (
                <span key={`b-${item.id}`} className="block truncate px-1 text-[10px] text-[#7a3044]" style={{ background: "#f6e4e8", borderRadius: "var(--agenda-card-radius, 4px)", padding: "1px 4px" }}>{item.horario_inicio ? item.horario_inicio.slice(0, 5) : "Dia"} {item.titulo}</span>
              ))}
              {doDia.slice(0, Math.max(0, visiveis - folgas.length)).map((item) => (
                <span key={item.id} className="block truncate px-1 text-[10px] text-white" style={{ background: statusCores[item.status] || STATUS_PADRAO.SCHEDULED, borderRadius: "var(--agenda-card-radius, 4px)", padding: "1px 4px" }}>{dois(new Date(item.inicio).getHours())}:{dois(new Date(item.inicio).getMinutes())} {item.cliente_nome}</span>
              ))}
              {total > visiveis ? <span className="block text-[10px] text-[#8a6e74]">mais +{total - visiveis}</span> : null}
            </span>
          </button>
        );
      })}
    </div>
  );
}
