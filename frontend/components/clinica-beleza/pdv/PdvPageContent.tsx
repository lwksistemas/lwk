"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  CalendarDays,
  Check,
  ChevronDown,
  DollarSign,
  FileText,
  History,
  Printer,
  Lock,
  Mail,
  MessageCircle,
  Package,
  PenLine,
  Plus,
  ShoppingCart,
  Trash2,
  UserRound,
  Users,
  X,
} from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ConsultaTermoConsentimentoButton } from "@/components/clinica-beleza/consultas/ConsultaTermoConsentimentoButton";
import { ModalReceberConsulta } from "@/components/clinica-beleza/consultas/ModalReceberConsulta";
import { EnviarReciboAssinaturaAcao } from "@/components/clinica-beleza/consultas/receber/EnviarReciboAssinaturaAcao";
import { ReceberReciboActions } from "@/components/clinica-beleza/consultas/receber/ReceberReciboActions";
import { useToast } from "@/components/ui/Toast";
import { formatApiErrorBody } from "@/lib/api-errors";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import { formatarAgendaEvento } from "@/hooks/clinica-beleza/agenda-data/agenda-event-mappers";
import { consultaPagamentoUi } from "@/hooks/clinica-beleza/consulta-detail-actions/consulta-detail-actions-utils";
import { ClinicaBelezaAPI, clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { CLINICA_FORMA_PAGAMENTO_LABEL } from "@/lib/clinica-beleza-constants";
import { createQuickPatient } from "@/hooks/clinica-beleza/criar-agendamento/criar-agendamento-submit-api";
import { formatCurrency } from "@/lib/financeiro-helpers";
import {
  FORMAS_PDV,
  clientePresente,
  hojeIso,
  horaCurta,
  quandoRecibo,
  classeStatusPdv,
  exibirReciboNoPdv,
  paymentIdReciboPdv,
  pdvPodeReceberAtendimento,
  seloCaixaPdv,
  podeAlterarServico,
  podeMarcarPresente,
  reais,
  rotuloStatusPdv,
} from "./pdv-utils";

type ProdutoLinha = {
  id: number;
  produto: number;
  produto_nome: string;
  quantidade: number | string;
  preco_unitario?: number | string;
  desconto?: number | string;
  finalidade?: string;
};

type ProdutoOpcao = {
  id: number;
  nome: string;
  preco_venda?: number | string;
  vende_ao_cliente?: boolean;
  is_active?: boolean;
};

type ConsultaDia = Consulta & { appointment?: number | null };

type VendaLinha = { produto: number; nome: string; quantidade: string; preco: string; desconto: string };

type EntregaRecibo = {
  paymentId: number;
  cliente: string;
  numero: number;
  total: string;
  forma: string;
  quando: string;
  telefone: string;
  email: string;
};

type VendaHistorico = {
  id: number;
  payment_id: number;
  cliente: string;
  total: string;
  status: string;
  operador: string;
  telefone?: string;
  email?: string;
  forma?: string;
  criada_em?: string;
};

type FechamentoCaixa = {
  id: number;
  nome: string;
  operador: string;
  aberta_em: string;
  fechada_em: string;
  vendas_produtos: number;
  recebido: number;
  a_receber: number;
  vendas: VendaHistorico[];
};

const rosa = "var(--cb-primary, #8B3D52)";

function listaDe<T>(corpo: unknown): T[] {
  if (Array.isArray(corpo)) return corpo as T[];
  if (corpo && typeof corpo === "object" && Array.isArray((corpo as { results?: T[] }).results)) {
    return (corpo as { results: T[] }).results;
  }
  return [];
}

function mensagemErro(erro: unknown, fallback: string): string {
  if (erro && typeof erro === "object" && "error" in erro) return String((erro as { error?: string }).error || fallback);
  if (erro instanceof Error && erro.message) return erro.message;
  return fallback;
}

export function PdvPageContent() {
  const toast = useToast();
  const params = useParams();
  const slug = String(params.slug || "");
  const dia = hojeIso();
  const [eventos, setEventos] = useState<AgendaEventData[]>([]);
  const [consultas, setConsultas] = useState<ConsultaDia[]>([]);
  const [resumo, setResumo] = useState({ total_pago: 0, a_receber: 0, vendas_produtos: 0, vendas_balcao: 0, recebido_balcao: 0 });
  const [selecionadoId, setSelecionadoId] = useState<number | null>(null);
  const [aba, setAba] = useState<"servico" | "venda">("servico");
  const [produtosConsulta, setProdutosConsulta] = useState<ProdutoLinha[]>([]);
  const [catalogo, setCatalogo] = useState<ProdutoOpcao[]>([]);
  const [procedimentosCat, setProcedimentosCat] = useState<{ id: number; nome: string }[]>([]);
  const [forma, setForma] = useState("PIX");
  const [receberAberto, setReceberAberto] = useState(false);
  const [formasPagas, setFormasPagas] = useState<{ id: number; rotulo: string; valor: number }[]>([]);
  const [desconto, setDesconto] = useState("");
  const [editandoDesconto, setEditandoDesconto] = useState(false);
  const [observacao, setObservacao] = useState("");
  const [erro, setErro] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [caixaAberto, setCaixaAberto] = useState(false);
  const [caixaNome, setCaixaNome] = useState("");
  const [caixaResponsavel, setCaixaResponsavel] = useState("");
  const [podeFecharCaixa, setPodeFecharCaixa] = useState(false);
  const [caixaRecebido, setCaixaRecebido] = useState(0);
  const [caixaAReceber, setCaixaAReceber] = useState(0);
  const [caixaVendas, setCaixaVendas] = useState(0);
  const [funcionarios, setFuncionarios] = useState<{ id: number; nome: string }[]>([]);
  const [abrindoCaixa, setAbrindoCaixa] = useState(false);
  const [responsavelCaixa, setResponsavelCaixa] = useState("");
  const [menuCaixa, setMenuCaixa] = useState(false);
  const [painel, setPainel] = useState<"historico" | "fechamento" | null>(null);
  const [incluindo, setIncluindo] = useState<"produto" | "servico" | null>(null);
  const [escolha, setEscolha] = useState("");
  const [buscaCliente, setBuscaCliente] = useState("");
  const [clientes, setClientes] = useState<{ id: number; nome: string; telefone?: string; email?: string }[]>([]);
  const [pacienteVenda, setPacienteVenda] = useState<number | "">("");
  const [telefoneRecibo, setTelefoneRecibo] = useState("");
  const [emailRecibo, setEmailRecibo] = useState("");
  const [linhasVenda, setLinhasVenda] = useState<VendaLinha[]>([]);
  const [buscaProduto, setBuscaProduto] = useState("");
  const [sugestoes, setSugestoes] = useState<ProdutoOpcao[]>([]);
  const [produtosConsultados, setProdutosConsultados] = useState(false);
  const [novoCliente, setNovoCliente] = useState(false);
  const [nomeNovo, setNomeNovo] = useState("");
  const [telefoneNovo, setTelefoneNovo] = useState("");
  const [cpfNovo, setCpfNovo] = useState("");
  const [recibo, setRecibo] = useState<{ paymentId: number; consultaId?: number; telefone?: string; email?: string; cadastrado?: boolean } | null>(null);
  const [entrega, setEntrega] = useState<EntregaRecibo | null>(null);
  const [avisoEntrega, setAvisoEntrega] = useState("");
  const [enviandoRecibo, setEnviandoRecibo] = useState<"whatsapp" | "email" | null>(null);
  const [fechamentos, setFechamentos] = useState<FechamentoCaixa[]>([]);
  const [resumoCaixa, setResumoCaixa] = useState<FechamentoCaixa | null>(null);
  const chaveVenda = useRef("");

  const carregar = useCallback(async () => {
    const [agendaRes, consultasRes, resumoRes] = await Promise.all([
      clinicaBelezaFetch(`/agenda/?start=${dia}T00:00:00&end=${dia}T23:59:59`),
      clinicaBelezaFetch(`/consultas/?data_inicio=${dia}&data_fim=${dia}&page_size=100`),
      ClinicaBelezaAPI.consultas.resumoFinanceiro({ data_inicio: dia, data_fim: dia, pdv: 1 }) as Promise<{
        total_pago: number;
        a_receber: number;
        vendas_produtos?: number;
        vendas_balcao?: number;
        recebido_balcao?: number;
      }>,
    ]);
    const agenda = agendaRes.ok ? listaDe<Record<string, unknown>>(await agendaRes.json()) : [];
    setEventos(
      agenda
        .map((evento) => formatarAgendaEvento(evento, false))
        .filter((evento) => !evento.extendedProps?.isBloqueio && !evento.extendedProps?.isIntervalo),
    );
    const corpoConsultas = consultasRes.ok ? await consultasRes.json() : [];
    setConsultas(listaDe<ConsultaDia>(corpoConsultas));
    setResumo({
      total_pago: Number(resumoRes.total_pago || 0),
      a_receber: Number(resumoRes.a_receber || 0),
      vendas_produtos: Number(resumoRes.vendas_produtos || 0),
      vendas_balcao: Number(resumoRes.vendas_balcao || 0),
      recebido_balcao: Number(resumoRes.recebido_balcao || 0),
    });
  }, [dia]);

  const aplicarCaixa = useCallback((sessao: {
    aberta: boolean;
    nome?: string;
    responsavel?: string;
    operador?: string;
    pode_fechar?: boolean;
    vendas_produtos?: number;
    recebido?: number;
    a_receber?: number;
    funcionarios?: { id: number; nome: string }[];
  }) => {
    const aberto = Boolean(sessao.aberta);
    setCaixaAberto(aberto);
    setCaixaNome(aberto ? sessao.nome || "" : "");
    setCaixaResponsavel(aberto ? sessao.responsavel || sessao.operador || "" : "");
    setPodeFecharCaixa(aberto && Boolean(sessao.pode_fechar));
    setCaixaRecebido(aberto ? Number(sessao.recebido || 0) : 0);
    setCaixaVendas(aberto ? Number(sessao.vendas_produtos || 0) : 0);
    setCaixaAReceber(aberto ? Number(sessao.a_receber || 0) : 0);
    if (Array.isArray(sessao.funcionarios)) setFuncionarios(sessao.funcionarios);
  }, []);

  const carregarCaixa = useCallback(() => {
    return ClinicaBelezaAPI.estoque.caixa().then(aplicarCaixa).catch(() => {
      setCaixaAberto(false);
      setCaixaRecebido(0);
      setCaixaVendas(0);
      setCaixaAReceber(0);
    });
  }, [aplicarCaixa]);

  useEffect(() => {
    void carregar();
    void carregarCaixa();
  }, [carregar, carregarCaixa]);

  useEffect(() => {
    setReceberAberto(false);
    setIncluindo((atual) => (atual === "produto" ? null : atual));
  }, [selecionadoId]);

  useEffect(() => {
    const atualizar = () => {
      if (document.visibilityState !== "visible") return;
      void carregar();
    };
    const timer = window.setInterval(atualizar, 15000);
    document.addEventListener("visibilitychange", atualizar);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", atualizar);
    };
  }, [carregar]);

  useEffect(() => {
    ClinicaBelezaAPI.estoque.list({ page_size: 200 }).then((res) => {
      setCatalogo(listaDe<ProdutoOpcao>(res).filter((item) => item.vende_ao_cliente && item.is_active !== false));
    }).catch(() => setCatalogo([]));
    ClinicaBelezaAPI.procedures.list({ active: true, all: 1 }).then((res) => {
      setProcedimentosCat(listaDe<{ id: number; nome?: string; name?: string }>(res).map((item) => ({
        id: item.id,
        nome: item.nome || item.name || "Procedimento",
      })));
    }).catch(() => setProcedimentosCat([]));
  }, []);

  const agendaHoje = useMemo(
    () => [...eventos].sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime()),
    [eventos],
  );
  const selecionado = agendaHoje.find((evento) => Number(evento.extendedProps?.dbId) === selecionadoId) || null;
  const consulta = consultas.find((item) => item.appointment === selecionadoId) || null;

  const carregarProdutos = useCallback(async (consultaId: number) => {
    const lista = await ClinicaBelezaAPI.consultas.produtos.list(consultaId);
    setProdutosConsulta(listaDe<ProdutoLinha>(lista).filter((item) => item.finalidade === "venda"));
  }, []);

  useEffect(() => {
    setErro("");
    setRecibo(null);
    setDesconto(consulta?.desconto ? String(consulta.desconto) : "");
    setObservacao(consulta?.observacoes_gerais || "");
    if (!consulta?.id || aba !== "servico") {
      setProdutosConsulta([]);
      return;
    }
    void carregarProdutos(consulta.id).catch(() => setProdutosConsulta([]));
  }, [aba, carregarProdutos, consulta?.id, consulta?.desconto, consulta?.observacoes_gerais]);

  useEffect(() => {
    const pagamentoId = Number(consulta?.payment_id || 0);
    if (aba !== "servico" || pagamentoId <= 0) {
      setFormasPagas([]);
      return;
    }
    let ativo = true;
    ClinicaBelezaAPI.financeiro.payments.parcelas.list(pagamentoId).then((corpo) => {
      if (!ativo) return;
      const lista = (corpo as { parcelas?: { id: number; valor?: string | number; payment_method?: string; payment_method_label?: string; status?: string }[] }).parcelas || [];
      setFormasPagas(
        lista
          .filter((item) => item.status !== "CANCELLED")
          .map((item) => ({
            id: item.id,
            rotulo: item.payment_method_label || CLINICA_FORMA_PAGAMENTO_LABEL[item.payment_method || ""] || item.payment_method || "Pagamento",
            valor: Number(item.valor || 0),
          })),
      );
    }).catch(() => {
      if (ativo) setFormasPagas([]);
    });
    return () => {
      ativo = false;
    };
  }, [aba, consulta?.payment_id]);

  useEffect(() => {
    const termo = buscaCliente.trim();
    if (aba !== "venda" || termo.length < 2 || pacienteVenda) {
      setClientes([]);
      return;
    }
    const timer = window.setTimeout(() => {
      ClinicaBelezaAPI.getList<{ id: number; nome: string; telefone?: string; email?: string }>(
        "/patients/",
        { search: termo, page_size: 12 },
      ).then((lista) => {
        setClientes(listaDe(lista));
      }).catch(() => setClientes([]));
    }, 250);
    return () => window.clearTimeout(timer);
  }, [aba, buscaCliente, pacienteVenda]);

  useEffect(() => {
    const termo = buscaProduto.trim();
    if (aba !== "venda" || termo.length < 2) {
      setSugestoes([]);
      setProdutosConsultados(false);
      return;
    }
    const timer = window.setTimeout(() => {
      ClinicaBelezaAPI.estoque.list({ search: termo, page_size: 20, vende_ao_cliente: 1 }).then((res) => {
        setSugestoes(listaDe<ProdutoOpcao>(res).filter((item) => item.vende_ao_cliente !== false && item.is_active !== false));
        setProdutosConsultados(true);
      }).catch(() => {
        setSugestoes([]);
        setProdutosConsultados(true);
      });
    }, 200);
    return () => window.clearTimeout(timer);
  }, [aba, buscaProduto]);

  useEffect(() => {
    if (painel !== "historico") return;
    ClinicaBelezaAPI.estoque.fechamentos({ data: dia }).then((lista) => {
      setFechamentos(listaDe(lista));
    }).catch(() => setFechamentos([]));
  }, [dia, painel]);

  const adicionarProduto = (produto: ProdutoOpcao) => {
    setLinhasVenda((atual) => {
      const indice = atual.findIndex((linha) => linha.produto === produto.id);
      if (indice >= 0) {
        return atual.map((linha, i) => i === indice ? { ...linha, quantidade: String(Number(linha.quantidade || 0) + 1) } : linha);
      }
      return [...atual, { produto: produto.id, nome: produto.nome, quantidade: "1", preco: String(produto.preco_venda || 0), desconto: "0" }];
    });
    setBuscaProduto("");
    setSugestoes([]);
  };

  const servicos = Number(consulta?.valor_pagamento || selecionado?.extendedProps?.procedure_price || 0);
  const produtosValor = reais(produtosConsulta.reduce((acc, item) => {
    const bruto = Number(item.quantidade || 0) * Number(item.preco_unitario || 0);
    return acc + Math.max(0, bruto - Number(item.desconto || 0));
  }, 0));
  const vendaValor = reais(linhasVenda.reduce((acc, linha) => {
    const bruto = Number(linha.quantidade || 0) * Number(linha.preco || 0);
    return acc + Math.max(0, bruto - Number(linha.desconto || 0));
  }, 0));
  const descontoNum = reais(Number(desconto || 0));
  const pago = Number(consulta?.valor_pago || 0);
  const subtotal = aba === "venda" ? vendaValor : reais(servicos + (pago > 0.009 ? 0 : produtosValor));
  const total = aba === "venda"
    ? reais(Math.max(0, vendaValor - descontoNum))
    : pago > 0.009
      ? reais(Number(consulta?.valor_restante || 0))
      : reais(Math.max(0, servicos - descontoNum) + produtosValor);

  const presentes = agendaHoje.filter((evento) => clientePresente(evento.extendedProps?.status)).length;
  const recebidoHoje = caixaAberto ? reais(caixaRecebido) : 0;
  const vendasProdutos = caixaAberto ? reais(caixaVendas) : 0;

  const fecharCaixa = async () => {
    setMenuCaixa(false);
    if (!podeFecharCaixa) {
      setErro(`Só ${caixaResponsavel || "quem abriu"} pode fechar este caixa.`);
      return;
    }
    setErro("");
    try {
      await ClinicaBelezaAPI.estoque.fecharCaixa();
      setPainel(null);
      setCaixaAberto(false);
      setCaixaNome("");
      setCaixaResponsavel("");
      setPodeFecharCaixa(false);
      setCaixaRecebido(0);
      setCaixaVendas(0);
      setCaixaAReceber(0);
    } catch (erroCaixa) {
      setErro(mensagemErro(erroCaixa, "Não foi possível fechar o caixa."));
    }
  };

  const confirmarAbertura = async () => {
    setErro("");
    if (!responsavelCaixa) {
      setErro("Escolha o operador do caixa.");
      return;
    }
    setSalvando(true);
    try {
      const sessao = await ClinicaBelezaAPI.estoque.abrirCaixa({
        nome: "Recepção",
        responsavel_id: Number(responsavelCaixa),
      });
      aplicarCaixa({
        ...sessao,
        aberta: true,
        nome: "Recepção",
        responsavel: sessao.responsavel || funcionarios.find((pessoa) => pessoa.id === Number(responsavelCaixa))?.nome || "",
      });
      setAbrindoCaixa(false);
      setResponsavelCaixa("");
    } catch (erroCaixa) {
      setErro(mensagemErro(erroCaixa, "Não foi possível abrir o caixa."));
    } finally {
      setSalvando(false);
    }
  };

  const marcarPresente = async (id: number) => {
    setErro("");
    setSalvando(true);
    try {
      const res = await clinicaBelezaFetch(`/agenda/${id}/update/`, {
        method: "PATCH",
        body: JSON.stringify({ status: "CONFIRMED" }),
      });
      const corpo = await res.json().catch(() => ({}));
      if (!res.ok) throw corpo;
      setSelecionadoId(id);
      setAba("servico");
      await carregar();
    } catch (erroMarcar) {
      setErro(mensagemErro(erroMarcar, "Não foi possível marcar a cliente como presente."));
    } finally {
      setSalvando(false);
    }
  };

  const incluirProduto = async () => {
    if (!consulta?.id || !escolha) return;
    const produto = catalogo.find((item) => item.id === Number(escolha));
    setSalvando(true);
    setErro("");
    try {
      await ClinicaBelezaAPI.consultas.produtos.add(consulta.id, {
        produto: Number(escolha),
        quantidade: 1,
        finalidade: "venda",
        preco_unitario: Number(produto?.preco_venda || 0),
      });
      setEscolha("");
      setIncluindo(null);
      await carregarProdutos(consulta.id);
      await carregar();
    } catch (erroAdd) {
      setErro(mensagemErro(erroAdd, "Não foi possível incluir o produto."));
    } finally {
      setSalvando(false);
    }
  };

  const incluirServico = async () => {
    if (!consulta?.id || !escolha) return;
    setSalvando(true);
    setErro("");
    try {
      await ClinicaBelezaAPI.consultas.procedimentos.add(consulta.id, Number(escolha));
      setEscolha("");
      setIncluindo(null);
      await carregar();
    } catch (erroAdd) {
      setErro(mensagemErro(erroAdd, "Não foi possível incluir o serviço."));
    } finally {
      setSalvando(false);
    }
  };

  const removerServico = async (consultaId: number, procedimentoId: number) => {
    setErro("");
    try {
      await ClinicaBelezaAPI.consultas.procedimentos.remove(consultaId, procedimentoId);
      await carregar();
    } catch (erroRemover) {
      setErro(mensagemErro(erroRemover, "Não foi possível remover o serviço."));
    }
  };

  const receber = async () => {
    if (!caixaAberto) {
      setErro("Abra o caixa para receber.");
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      if (aba === "venda") {
        const itens = linhasVenda.filter((linha) => linha.produto).map((linha) => ({
          produto: linha.produto,
          quantidade: Number(linha.quantidade || 0),
          preco_unitario: Number(linha.preco || 0),
          desconto: Number(linha.desconto || 0),
        }));
        if (!itens.length) throw { error: "Adicione um produto à venda." };
        if (descontoNum > 0 && itens[0]) itens[0].desconto = reais(itens[0].desconto + descontoNum);
        if (!chaveVenda.current) chaveVenda.current = crypto.randomUUID();
        const criada = await ClinicaBelezaAPI.estoque.vender({
          paciente: pacienteVenda ? Number(pacienteVenda) : null,
          nome_cliente: buscaCliente.trim(),
          telefone: telefoneRecibo.trim(),
          email: emailRecibo.trim(),
          chave: chaveVenda.current,
          payment_method: forma,
          itens,
        });
        setEntrega({
          paymentId: criada.payment_id,
          cliente: criada.cliente || buscaCliente.trim() || "Consumidor não identificado",
          numero: criada.payment_id,
          total: criada.total || String(total),
          forma: FORMAS_PDV.find((item) => item.id === forma)?.label || forma,
          quando: quandoRecibo(criada.criada_em),
          telefone: criada.telefone || telefoneRecibo.trim(),
          email: criada.email || emailRecibo.trim(),
        });
        setAvisoEntrega("");
        chaveVenda.current = "";
        setLinhasVenda([]);
        setBuscaCliente("");
        setPacienteVenda("");
        setTelefoneRecibo("");
        setEmailRecibo("");
        setDesconto("");
        await carregar();
        await carregarCaixa();
      }
    } catch (erroReceber) {
      setErro(mensagemErro(erroReceber, "Não foi possível receber."));
    } finally {
      setSalvando(false);
    }
  };

  const imprimirHtml = async (caminho: string, aviso: string) => {
    const resp = await clinicaBelezaFetch(caminho);
    if (!resp.ok) {
      setAvisoEntrega(aviso);
      return;
    }
    const html = await resp.text();
    const janela = window.open("", "_blank");
    if (!janela) {
      setAvisoEntrega("O navegador bloqueou a janela de impressão.");
      return;
    }
    janela.document.write(html);
    janela.document.close();
    const pronto = janela as Window & { imprimirReciboPronto?: () => void };
    window.setTimeout(() => {
      if (typeof pronto.imprimirReciboPronto === "function") {
        pronto.imprimirReciboPronto();
        return;
      }
      janela.focus();
      janela.print();
    }, 50);
  };

  const imprimirRecibo = (paymentId: number) => imprimirHtml(
    `/payments/${paymentId}/recibo-html/`,
    "Não foi possível abrir o recibo para impressão.",
  );

  const imprimirResumoCaixa = (resumo: FechamentoCaixa) => imprimirHtml(
    `/estoque/caixa/fechamentos/${resumo.id}/html/`,
    "Não foi possível abrir o resumo do caixa para impressão.",
  );

  const enviarReciboEscolhido = async (canal: "whatsapp" | "email") => {
    if (!entrega) return;
    setEnviandoRecibo(canal);
    setAvisoEntrega("");
    try {
      await ClinicaBelezaAPI.payments.enviarRecibo(entrega.paymentId, canal);
      setAvisoEntrega(canal === "whatsapp" ? "Recibo enviado pelo WhatsApp." : "Recibo enviado por e-mail.");
    } catch (erroEnvio) {
      setAvisoEntrega(mensagemErro(erroEnvio, "Não foi possível enviar o recibo."));
    } finally {
      setEnviandoRecibo(null);
    }
  };

  const alteraServico = podeAlterarServico(selecionado?.extendedProps?.status);
  const consultaFinalizada = selecionado?.extendedProps?.status === "COMPLETED";
  const pagamentoUi = consulta ? consultaPagamentoUi(consulta) : null;
  const atendimentoIsento = Boolean(pagamentoUi?.mostrarIsento);
  const clienteNaClinica = clientePresente(selecionado?.extendedProps?.status);
  const aguardandoChegada = aba === "servico" && Boolean(selecionado) && !clienteNaClinica;
  const vendaAPrazo = aba === "servico" && !atendimentoIsento && !aguardandoChegada && !pdvPodeReceberAtendimento(consulta);
  const paymentRecibo = paymentIdReciboPdv(consulta, recibo);
  const quitado = seloCaixaPdv(consulta) === "pago";
  const formasExibidas = formasPagas.length
    ? formasPagas
    : consulta?.payment_method
      ? [{
          id: 0,
          rotulo: CLINICA_FORMA_PAGAMENTO_LABEL[consulta.payment_method] || consulta.payment_method,
          valor: pago > 0.009 ? pago : Number(consulta.valor_restante || 0),
        }]
      : [];
  const mostrarFormas = aba === "servico" && (quitado || vendaAPrazo) && formasExibidas.length > 0;
  const mostrarRecibo = aba === "servico" && exibirReciboNoPdv(
    selecionado?.extendedProps?.status,
    consulta,
    atendimentoIsento && Boolean(pagamentoUi?.consultaFinalizada),
  );
  const enviarReciboAtendimento = async (canal: "email" | "whatsapp") => {
    if (paymentRecibo <= 0) return;
    try {
      await ClinicaBelezaAPI.payments.enviarRecibo(paymentRecibo, canal);
      toast.success(canal === "email" ? "Recibo enviado por email!" : "Recibo enviado por WhatsApp!");
    } catch (erroEnvio: unknown) {
      const corpo = erroEnvio as { response?: { data?: { error?: string } } };
      toast.error(corpo?.response?.data?.error || formatApiErrorBody(erroEnvio) || (canal === "email" ? "Erro ao enviar email." : "Erro ao enviar WhatsApp."));
    }
  };

  const procedimentos = consulta?.procedures_list?.length
    ? consulta.procedures_list
    : selecionado?.extendedProps?.procedure_name
      ? [{ id: 0, appointment_procedure_id: 0, nome: selecionado.extendedProps.procedure_name, valor: Number(selecionado.extendedProps.procedure_price || 0) }]
      : [];

  return (
    <ClinicaBelezaPageContent className="!pt-4">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl text-white" style={{ backgroundColor: rosa }}>
            <ShoppingCart size={20} />
          </span>
          <div>
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">PDV / Caixa</h1>
            <p className="text-sm text-gray-500">Recepção • Atendimentos • Vendas</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button type="button" onClick={() => setPainel("historico")} className="inline-flex items-center gap-1.5 rounded-full border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700">
            <History size={15} /> Caixa fechado
          </button>
          {caixaAberto && (
            <button type="button" onClick={() => { setMenuCaixa(false); setPainel("fechamento"); }} className="inline-flex items-center gap-1.5 rounded-full border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700">
              <Lock size={15} /> Fechamento do caixa
            </button>
          )}
          <div className="relative">
            {caixaAberto ? (
              <button type="button" onClick={() => setMenuCaixa((atual) => !atual)} className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700">
                <DollarSign size={15} />
                <span>Caixa Aberto</span>
                {caixaResponsavel && <span>{caixaResponsavel}</span>}
                <ChevronDown size={14} />
              </button>
            ) : (
              <button type="button" onClick={() => { setErro(""); setAbrindoCaixa(true); }} className="inline-flex items-center gap-1.5 rounded-full px-3 py-2 text-sm font-medium text-white" style={{ backgroundColor: rosa }}>
                <DollarSign size={15} /> Abrir caixa
              </button>
            )}
            {menuCaixa && caixaAberto && (
              <div className="absolute right-0 z-20 mt-1 w-64 rounded-xl border bg-white p-2 shadow-lg">
                <p className="px-2 py-1 text-xs text-gray-500">Responsável pelo recebimento</p>
                <p className="px-2 pb-1 text-sm font-medium text-gray-800">{caixaResponsavel || "—"}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-3 xl:grid-cols-5">
        <Indicador icone={<CalendarDays size={16} />} cor="bg-pink-50 text-pink-600" titulo="Agendamentos hoje" valor={String(agendaHoje.length)} />
        <Indicador icone={<Users size={16} />} cor="bg-sky-50 text-sky-600" titulo="Presentes" valor={String(presentes)} />
        <Indicador icone={<DollarSign size={16} />} cor="bg-pink-50 text-pink-600" titulo="A receber" valor={formatCurrency(resumo.a_receber)} />
        <Indicador icone={<Check size={16} />} cor="bg-emerald-50 text-emerald-600" titulo="Recebido hoje" valor={formatCurrency(recebidoHoje)} />
        <Indicador icone={<Package size={16} />} cor="bg-violet-50 text-violet-600" titulo="Vendas de produtos" valor={formatCurrency(vendasProdutos)} />
      </div>

      <div className="grid items-start gap-4 xl:grid-cols-[minmax(240px,0.9fr)_minmax(320px,1.4fr)_minmax(260px,0.85fr)]">
        <section className="rounded-2xl border border-gray-200 bg-white p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">Próximos agendamentos</h2>
            <Link href={`/loja/${slug}/agenda`} className="text-sm font-medium" style={{ color: rosa }}>Ver agenda &gt;</Link>
          </div>
          <div className="space-y-2">
            {agendaHoje.length === 0 && <p className="text-sm text-gray-500">Nenhum agendamento hoje.</p>}
            {agendaHoje.map((evento) => {
              const id = Number(evento.extendedProps?.dbId);
              const status = evento.extendedProps?.status;
              const consultaItem = consultas.find((item) => item.appointment === id);
              const selo = seloCaixaPdv(consultaItem);
              const isento = Boolean(consultaItem && consultaPagamentoUi(consultaItem).mostrarIsento);
              const ativo = id === selecionadoId;
              const termoNoPdv = (status === "CONFIRMED" || status === "IN_PROGRESS")
                && Boolean(consultaItem?.id)
                && Boolean(consultaItem?.exige_termo_consentimento);
              return (
                <div key={evento.id} className={`flex w-full items-center gap-2 rounded-xl border px-3 py-2.5 text-left ${ativo ? "border-pink-200 bg-pink-50/60" : "border-transparent hover:bg-gray-50"}`}>
                  <button type="button" onClick={() => { setSelecionadoId(id); setAba("servico"); }} className="flex min-w-0 flex-1 items-center gap-3 text-left">
                    <span className="w-12 text-sm font-medium text-gray-500">{horaCurta(evento.start)}</span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-semibold text-gray-900">{evento.extendedProps?.patient_name || evento.title}</span>
                      <span className="block truncate text-xs text-gray-500">{evento.extendedProps?.procedure_name || "Consulta"} • {evento.extendedProps?.professional_name || "Profissional"}</span>
                    </span>
                  </button>
                  {podeMarcarPresente(status) ? (
                    <button type="button" onClick={() => void marcarPresente(id)} className="rounded-full border px-2 py-1 text-[11px] font-medium" style={{ color: rosa, borderColor: rosa }}>Marcar presente</button>
                  ) : (
                    <span className={`rounded-full px-2 py-1 text-[11px] font-medium ${isento ? "bg-sky-100 text-sky-800" : classeStatusPdv(status, selo)}`}>{isento ? "Isento" : rotuloStatusPdv(status, selo)}</span>
                  )}
                  {termoNoPdv && consultaItem?.id && (
                    <ConsultaTermoConsentimentoButton
                      consultaId={consultaItem.id}
                      compacto
                      permitirAssinaturaProfissional={false}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </section>

        <section className="rounded-2xl border border-gray-200 bg-white p-4">
          <div className="mb-4 flex gap-2">
            <button type="button" onClick={() => setAba("servico")} className="rounded-full px-4 py-2 text-sm font-medium" style={aba === "servico" ? { backgroundColor: rosa, color: "white" } : { color: "#6b7280" }}>Serviço do atendimento</button>
            <button type="button" onClick={() => setAba("venda")} className="rounded-full px-4 py-2 text-sm font-medium" style={aba === "venda" ? { backgroundColor: rosa, color: "white" } : { color: "#6b7280" }}>Venda de produtos</button>
          </div>

          {aba === "servico" ? (
            <div className="space-y-4">
              <div>
                <p className="mb-1 text-xs font-medium text-gray-500">Cliente</p>
                <div className="flex items-center gap-2 rounded-xl border px-3 py-2">
                  <UserRound size={16} className="text-gray-400" />
                  <span className="flex-1 text-sm">{selecionado?.extendedProps?.patient_name || "Selecione um agendamento"}</span>
                  {selecionado && <button type="button" onClick={() => setSelecionadoId(null)} aria-label="Limpar cliente"><X size={14} /></button>}
                </div>
              </div>
              <Bloco titulo="Procedimentos / Serviços">
                {procedimentos.map((item) => {
                  const procedimentoId = item.appointment_procedure_id || 0;
                  return (
                    <LinhaCarrinho key={`${procedimentoId || item.id}-${item.nome}`} tipo="Serviço" nome={item.nome} detalhe="" valor={Number(item.valor || 0)} onRemove={alteraServico && consulta?.id && procedimentoId ? () => void removerServico(consulta.id, procedimentoId) : undefined} />
                  );
                })}
              </Bloco>
              {(!consultaFinalizada || produtosConsulta.length > 0) && (
                <Bloco titulo="Produtos (cosméticos)">
                  {produtosConsulta.map((item) => (
                    <LinhaCarrinho key={item.id} tipo="Produto" nome={item.produto_nome} detalhe={`${Number(item.quantidade)} × ${formatCurrency(Number(item.preco_unitario || 0))}`} valor={Math.max(0, Number(item.quantidade) * Number(item.preco_unitario || 0) - Number(item.desconto || 0))} onRemove={!consultaFinalizada && consulta?.id ? () => void ClinicaBelezaAPI.consultas.produtos.remove(consulta.id, item.id).then(() => carregarProdutos(consulta.id)) : undefined} />
                  ))}
                </Bloco>
              )}
              {incluindo && ((incluindo === "produto" && !consultaFinalizada) || (incluindo === "servico" && alteraServico)) && (
                <div className="flex gap-2">
                  <select value={escolha} onChange={(e) => setEscolha(e.target.value)} className="flex-1 rounded-xl border px-3 py-2 text-sm">
                    <option value="">{incluindo === "produto" ? "Produto" : "Serviço"}</option>
                    {(incluindo === "produto" ? catalogo : procedimentosCat).map((item) => (
                      <option key={item.id} value={item.id}>{item.nome}</option>
                    ))}
                  </select>
                  <button type="button" disabled={salvando || !escolha} onClick={() => void (incluindo === "produto" ? incluirProduto() : incluirServico())} className="rounded-xl px-3 text-sm text-white" style={{ backgroundColor: rosa }}>Incluir</button>
                </div>
              )}
              <div className="flex flex-wrap gap-2">
                {!consultaFinalizada && <button type="button" onClick={() => setIncluindo("produto")} className="inline-flex items-center gap-1 rounded-full border px-3 py-2 text-sm" style={{ color: rosa, borderColor: rosa }}><ShoppingCart size={14} /> + Adicionar produto</button>}
                {alteraServico && <button type="button" onClick={() => setIncluindo("servico")} className="inline-flex items-center gap-1 rounded-full border px-3 py-2 text-sm" style={{ color: rosa, borderColor: rosa }}><Plus size={14} /> + Adicionar serviço</button>}
              </div>
              {selecionado && !alteraServico && (
                <p className="text-xs text-gray-500">
                  {selecionado.extendedProps?.status === "COMPLETED"
                    ? "Com a consulta finalizada não é possível incluir ou remover procedimentos."
                    : "Procedimentos só podem ser incluídos ou removidos com a cliente presente ou em atendimento."}
                </p>
              )}
              <label className="block text-sm text-gray-600">
                Observações (opcional)
                <textarea value={observacao} onChange={(e) => setObservacao(e.target.value)} onBlur={() => { if (consulta?.id) void ClinicaBelezaAPI.consultas.update(consulta.id, { observacoes_gerais: observacao }); }} placeholder="Adicionar uma observação à cobrança..." className="mt-1 w-full rounded-xl border px-3 py-2 text-sm" rows={3} />
              </label>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <div className="mb-1 flex items-center justify-between">
                  <p className="text-xs font-medium text-gray-500">Cliente (opcional)</p>
                  <button type="button" className="text-xs font-medium" style={{ color: rosa }} onClick={() => setNovoCliente((atual) => !atual)}>Cadastrar cliente</button>
                </div>
                <input value={buscaCliente} onChange={(e) => { setBuscaCliente(e.target.value); setPacienteVenda(""); }} placeholder="Nome, ou deixe em branco" className="w-full rounded-xl border px-3 py-2 text-sm" />
                <p className="mt-1 text-xs text-gray-500">{pacienteVenda ? "Cliente cadastrado" : clientes.length > 0 ? "Selecione o cadastro ou continue só com o nome" : buscaCliente.trim().length >= 2 ? "Só o nome, sem cadastro" : buscaCliente.trim() ? "Digite ao menos 2 letras" : "Consumidor não identificado"}</p>
                {clientes.length > 0 && (
                  <div className="mt-1 max-h-32 overflow-y-auto rounded-xl border">
                    {clientes.map((cliente) => (
                      <button key={cliente.id} type="button" className="block w-full px-3 py-2 text-left text-sm hover:bg-gray-50" onClick={() => { setPacienteVenda(cliente.id); setBuscaCliente(cliente.nome); setTelefoneRecibo(cliente.telefone || ""); setEmailRecibo(cliente.email || ""); setClientes([]); }}>{cliente.nome}</button>
                    ))}
                  </div>
                )}
                <div className="mt-2 grid gap-2 sm:grid-cols-2">
                  <input value={telefoneRecibo} onChange={(e) => setTelefoneRecibo(e.target.value)} placeholder="WhatsApp (opcional)" className="rounded-xl border px-3 py-2 text-sm" />
                  <input value={emailRecibo} onChange={(e) => setEmailRecibo(e.target.value)} placeholder="E-mail (opcional)" className="rounded-xl border px-3 py-2 text-sm" />
                </div>
                {novoCliente && (
                  <div className="mt-2 grid gap-2 sm:grid-cols-3">
                    <input value={nomeNovo} onChange={(e) => setNomeNovo(e.target.value)} placeholder="Nome" className="rounded-xl border px-3 py-2 text-sm" />
                    <input value={telefoneNovo} onChange={(e) => setTelefoneNovo(e.target.value)} placeholder="Telefone" className="rounded-xl border px-3 py-2 text-sm" />
                    <input value={cpfNovo} onChange={(e) => setCpfNovo(e.target.value)} placeholder="CPF" className="rounded-xl border px-3 py-2 text-sm" />
                    <button type="button" className="rounded-xl px-3 py-2 text-sm text-white sm:col-span-3" style={{ backgroundColor: rosa }} onClick={() => void createQuickPatient({ nome: nomeNovo, telefone: telefoneNovo, cpf: cpfNovo }).then((criado) => { setPacienteVenda(criado.id); setBuscaCliente(criado.nome || nomeNovo); setTelefoneRecibo(telefoneNovo); setNovoCliente(false); })}>Salvar cadastro</button>
                  </div>
                )}
              </div>
              <div>
                <input
                  value={buscaProduto}
                  onChange={(e) => setBuscaProduto(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && sugestoes.length === 1) {
                      e.preventDefault();
                      adicionarProduto(sugestoes[0]);
                    }
                  }}
                  placeholder="Produto ou código de barras"
                  className="w-full rounded-xl border px-3 py-2 text-sm"
                />
                {sugestoes.length > 0 && (
                  <div className="mt-1 max-h-40 overflow-y-auto rounded-xl border">
                    {sugestoes.map((produto) => (
                      <button key={produto.id} type="button" className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-gray-50" onClick={() => adicionarProduto(produto)}>
                        <span>{produto.nome}</span>
                        <span className="text-gray-500">{formatCurrency(Number(produto.preco_venda || 0))}</span>
                      </button>
                    ))}
                  </div>
                )}
                {produtosConsultados && sugestoes.length === 0 && (
                  <p className="mt-1 text-xs text-gray-500">Nenhum produto liberado para venda com esse nome. No cadastro do estoque, marque “Pode vender ao cliente” e informe o preço de venda.</p>
                )}
              </div>
              {linhasVenda.map((linha, indice) => (
                <div key={`${linha.produto}-${indice}`} className="grid grid-cols-[1fr_64px_88px_72px_32px] items-center gap-2">
                  <span className="truncate text-sm">{linha.nome}</span>
                  <input value={linha.quantidade} onChange={(e) => setLinhasVenda((atual) => atual.map((item, i) => i === indice ? { ...item, quantidade: e.target.value } : item))} className="rounded-xl border px-2 py-2 text-sm" aria-label="Quantidade" />
                  <span className="text-sm text-gray-600">{formatCurrency(Number(linha.preco || 0))}</span>
                  <input value={linha.desconto} onChange={(e) => setLinhasVenda((atual) => atual.map((item, i) => i === indice ? { ...item, desconto: e.target.value } : item))} className="rounded-xl border px-2 py-2 text-sm" aria-label="Desconto" placeholder="Desc." />
                  <button type="button" onClick={() => setLinhasVenda((atual) => atual.filter((_, i) => i !== indice))} aria-label="Remover"><Trash2 size={14} /></button>
                </div>
              ))}
            </div>
          )}
          {erro && <p className="mt-3 text-sm text-red-600">{erro}</p>}
        </section>

        <section className="rounded-2xl border border-gray-200 bg-white p-4">
          <h2 className="mb-3 font-semibold text-gray-900">Resumo e pagamento</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-gray-500">Subtotal</span><span>{formatCurrency(subtotal)}</span></div>
            <div className="flex justify-between">
              <span className="text-gray-500">Desconto</span>
              {aba === "venda" && editandoDesconto ? (
                <input autoFocus value={desconto} onChange={(e) => setDesconto(e.target.value)} onBlur={() => setEditandoDesconto(false)} className="w-24 rounded border px-2 py-1 text-right text-sm" />
              ) : aba === "venda" ? (
                <button type="button" className="inline-flex items-center gap-1" onClick={() => setEditandoDesconto(true)}>{formatCurrency(descontoNum)} <PenLine size={12} /></button>
              ) : (
                <span>{formatCurrency(descontoNum)}</span>
              )}
            </div>
            {pago > 0.009 && aba === "servico" && <div className="flex justify-between"><span className="text-gray-500">Já recebido</span><span>{formatCurrency(pago)}</span></div>}
          </div>
          <div className="my-4 flex items-center justify-between rounded-xl bg-pink-50 px-3 py-3">
            <span className="text-sm font-medium" style={{ color: rosa }}>Total a receber</span>
            <span className="text-lg font-semibold" style={{ color: rosa }}>{formatCurrency(total)}</span>
          </div>
          {vendaAPrazo ? (
            <p className="mb-4 rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-800">
              Esta venda está a prazo. O recebimento fica no{" "}
              <Link href={`/loja/${slug}/clinica-beleza/financeiro`} className="font-medium underline">Financeiro</Link>.
            </p>
          ) : atendimentoIsento ? (
            <p className="mb-4 rounded-xl bg-sky-50 px-3 py-2 text-sm text-sky-800">Retorno isento. Sem valor a receber.</p>
          ) : aguardandoChegada ? (
            <p className="mb-4 rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-800">
              A cliente ainda não chegou. Marque como presente para o caixa receber.
            </p>
          ) : aba === "venda" ? (
            <>
              <label className="mb-1 block text-sm text-gray-600">Forma de pagamento</label>
              <select value={forma} onChange={(e) => setForma(e.target.value)} className="mb-3 w-full rounded-xl border px-3 py-2 text-sm">
                {FORMAS_PDV.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
              </select>
            </>
          ) : null}
          {!vendaAPrazo && !atendimentoIsento && !aguardandoChegada && !caixaAberto && (
            <p className="mb-3 rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-800">Abra o caixa para vender ou receber um atendimento.</p>
          )}
          {mostrarFormas && (
            <div className="mb-3 space-y-2">
              <p className="text-sm text-gray-600">Formas de pagamento</p>
              {formasExibidas.map((linha) => (
                <div key={linha.id} className="flex items-center justify-between rounded-xl border px-3 py-2 text-sm">
                  <span>{linha.rotulo}</span>
                  <strong>{formatCurrency(linha.valor)}</strong>
                </div>
              ))}
              {quitado && !consultaFinalizada && (
                <p className="rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-800">
                  Pagamento registrado. O recibo só pode ser impresso ou enviado depois de finalizar o atendimento.
                </p>
              )}
            </div>
          )}
          {!vendaAPrazo && !atendimentoIsento && !aguardandoChegada && !(aba === "servico" && quitado) && (
            <button
              type="button"
              disabled={salvando || !caixaAberto || (aba === "venda" ? total <= 0 : (!consulta?.id || total <= 0))}
              onClick={() => {
                if (aba === "servico") {
                  setReceberAberto(true);
                  return;
                }
                void receber();
              }}
              className="mb-4 flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-semibold text-white disabled:opacity-50"
              style={{ backgroundColor: rosa }}
            >
              <DollarSign size={16} /> {salvando ? "Recebendo..." : "Receber pagamento"}
            </button>
          )}
          {mostrarRecibo && paymentRecibo > 0 && (
            <div className="space-y-3">
              <ReceberReciboActions
                onImprimir={() => void imprimirRecibo(paymentRecibo)}
                onEmail={() => void enviarReciboAtendimento("email")}
                onWhatsApp={() => void enviarReciboAtendimento("whatsapp")}
              />
              {vendaAPrazo && <EnviarReciboAssinaturaAcao paymentId={paymentRecibo} />}
            </div>
          )}
        </section>
      </div>

      {receberAberto && consulta?.id ? (
        <ModalReceberConsulta
          open
          consulta={consulta}
          origem="pdv"
          onClose={() => {
            setReceberAberto(false);
            void carregar();
            void carregarCaixa();
          }}
          onSuccess={() => {
            void carregar();
            void carregarCaixa();
          }}
        />
      ) : null}

      {entrega && (
        <JanelaReciboVenda
          entrega={entrega}
          aviso={avisoEntrega}
          enviando={enviandoRecibo}
          onImprimir={() => void imprimirRecibo(entrega.paymentId)}
          onWhatsapp={() => void enviarReciboEscolhido("whatsapp")}
          onEmail={() => void enviarReciboEscolhido("email")}
          onFechar={() => { setEntrega(null); setAvisoEntrega(""); }}
        />
      )}

      {abrindoCaixa && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4" onClick={() => setAbrindoCaixa(false)}>
          <div className="w-full max-w-md rounded-2xl bg-white p-5" onClick={(clique) => clique.stopPropagation()}>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Abrir caixa</h2>
              <button type="button" onClick={() => setAbrindoCaixa(false)} aria-label="Fechar"><X size={16} /></button>
            </div>
            <p className="mb-3 text-sm text-gray-500">Caixa Recepção</p>
            <label className="mb-4 block text-sm text-gray-600">
              Operador do caixa
              <select value={responsavelCaixa} onChange={(e) => setResponsavelCaixa(e.target.value)} className="mt-1 w-full rounded-xl border px-3 py-2 text-sm">
                <option value="">Selecione o funcionário</option>
                {funcionarios.map((pessoa) => <option key={pessoa.id} value={pessoa.id}>{pessoa.nome}</option>)}
              </select>
            </label>
            {funcionarios.length === 0 && <p className="mb-3 text-sm text-gray-500">Nenhum funcionário ativo no cadastro.</p>}
            {erro && <p className="mb-3 text-sm text-red-600">{erro}</p>}
            <button type="button" disabled={salvando} onClick={() => void confirmarAbertura()} className="w-full rounded-xl py-3 text-sm font-semibold text-white disabled:opacity-50" style={{ backgroundColor: rosa }}>
              {salvando ? "Abrindo..." : "Abrir caixa"}
            </button>
          </div>
        </div>
      )}

      {painel && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4" onClick={() => { setPainel(null); setResumoCaixa(null); }}>
          <div className="max-h-[80vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-5" onClick={(clique) => clique.stopPropagation()}>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold">{resumoCaixa ? "Resumo do caixa" : painel === "historico" ? "Caixa fechado" : "Fechamento do caixa"}</h2>
              <button type="button" onClick={() => { setPainel(null); setResumoCaixa(null); }} aria-label="Fechar"><X size={16} /></button>
            </div>
            {painel === "historico" && resumoCaixa ? (
              <div className="space-y-3 text-sm">
                <button type="button" className="text-xs font-medium" style={{ color: rosa }} onClick={() => setResumoCaixa(null)}>Voltar ao histórico</button>
                <p className="flex justify-between gap-3"><span className="text-gray-500">Operador</span><strong className="text-right">{resumoCaixa.operador || "Operador"}</strong></p>
                <p className="flex justify-between gap-3"><span className="text-gray-500">Caixa</span><strong>{resumoCaixa.nome || "Recepção"}</strong></p>
                <p className="flex justify-between gap-3"><span className="text-gray-500">Aberto</span><strong className="text-right">{quandoRecibo(resumoCaixa.aberta_em)}</strong></p>
                <p className="flex justify-between gap-3"><span className="text-gray-500">Fechado</span><strong className="text-right">{quandoRecibo(resumoCaixa.fechada_em)}</strong></p>
                <p className="flex justify-between"><span>Recebido</span><strong>{formatCurrency(Number(resumoCaixa.recebido || 0))}</strong></p>
                <p className="flex justify-between"><span>Ainda a receber</span><strong>{formatCurrency(Number(resumoCaixa.a_receber || 0))}</strong></p>
                <p className="flex justify-between"><span>Vendas de produtos</span><strong>{formatCurrency(Number(resumoCaixa.vendas_produtos || 0))}</strong></p>
                <div className="space-y-2 border-t pt-2">
                  {resumoCaixa.vendas.filter((item) => item.status !== "cancelada").length === 0 && <p className="text-gray-500">Nenhuma venda de produto nesta gaveta.</p>}
                  {resumoCaixa.vendas.filter((item) => item.status !== "cancelada").map((item) => (
                    <p key={item.id} className="flex justify-between gap-3"><span>{item.cliente}</span><strong>{formatCurrency(Number(item.total || 0))}</strong></p>
                  ))}
                </div>
                <button type="button" onClick={() => imprimirResumoCaixa(resumoCaixa)} className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-white" style={{ backgroundColor: rosa }}><Printer size={14} /> Imprimir</button>
              </div>
            ) : painel === "historico" ? (
              <div className="space-y-1 text-sm">
                {fechamentos.length === 0 && <p className="text-gray-500">Nenhum caixa fechado hoje.</p>}
                {fechamentos.map((item) => (
                  <button key={item.id} type="button" onClick={() => setResumoCaixa(item)} className="flex w-full items-center justify-between gap-3 rounded-xl px-2 py-2 text-left hover:bg-gray-50">
                    <span>
                      <span className="block font-medium" style={{ color: rosa }}>{item.operador || "Operador"}</span>
                      <span className="block text-xs text-gray-500">{item.nome || "Recepção"} • fechado {quandoRecibo(item.fechada_em)}</span>
                    </span>
                    <span className="text-xs text-gray-500">Ver resumo</span>
                  </button>
                ))}
              </div>
            ) : (
              <div className="space-y-2 text-sm">
                <p className="flex justify-between"><span>Recebido hoje</span><strong>{formatCurrency(recebidoHoje)}</strong></p>
                <p className="flex justify-between"><span>Ainda a receber</span><strong>{formatCurrency(caixaAberto ? caixaAReceber : 0)}</strong></p>
                <p className="flex justify-between"><span>Vendas de produtos</span><strong>{formatCurrency(vendasProdutos)}</strong></p>
                <p className="pt-2 text-xs text-gray-500">{caixaAberto ? `Estes valores são do caixa ${caixaNome || "aberto"}${caixaResponsavel ? `, responsável ${caixaResponsavel}` : ""}. Ao fechar, o resumo zera para o próximo operador.` : "Caixa fechado. Recebido e vendas de produtos ficam zerados até a próxima abertura."} O lançamento continua no Financeiro.</p>
                {erro && <p className="pt-2 text-sm text-amber-800">{erro}</p>}
                {caixaAberto && <button type="button" onClick={() => { void fecharCaixa(); }} className="mt-3 rounded-xl px-4 py-2 text-white" style={{ backgroundColor: rosa }}>Fechar caixa</button>}
              </div>
            )}
          </div>
        </div>
      )}
    </ClinicaBelezaPageContent>
  );
}

function Indicador({ icone, cor, titulo, valor }: { icone: ReactNode; cor: string; titulo: string; valor: string }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-gray-200 bg-white px-3 py-3">
      <span className={`flex h-9 w-9 items-center justify-center rounded-full ${cor}`}>{icone}</span>
      <span>
        <span className="block text-xs text-gray-500">{titulo}</span>
        <span className="block text-lg font-semibold text-gray-900">{valor}</span>
      </span>
    </div>
  );
}

function Bloco({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <div>
      <p className="mb-2 text-sm font-medium text-gray-700">{titulo}</p>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function JanelaReciboVenda({
  entrega,
  aviso,
  enviando,
  onImprimir,
  onWhatsapp,
  onEmail,
  onFechar,
}: {
  entrega: EntregaRecibo;
  aviso: string;
  enviando: "whatsapp" | "email" | null;
  onImprimir: () => void;
  onWhatsapp: () => void;
  onEmail: () => void;
  onFechar: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex justify-end">
          <button type="button" onClick={onFechar} aria-label="Fechar"><X size={18} className="text-gray-500" /></button>
        </div>
        <div className="mb-2 flex justify-center">
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-500"><Check size={28} /></span>
        </div>
        <h2 className="mb-4 text-center text-lg font-semibold text-gray-900">Pagamento registrado com sucesso</h2>
        <div className="mb-4 space-y-2 rounded-xl bg-gray-50 px-4 py-3 text-sm">
          <p className="flex justify-between gap-3"><span className="inline-flex items-center gap-2 text-gray-500"><UserRound size={14} /> Cliente</span><strong className="text-right">{entrega.cliente}</strong></p>
          <p className="flex justify-between gap-3"><span className="inline-flex items-center gap-2 text-gray-500"><FileText size={14} /> Recibo nº</span><strong>{entrega.numero}</strong></p>
          <p className="flex justify-between gap-3"><span className="inline-flex items-center gap-2 text-gray-500"><DollarSign size={14} /> Forma de pagamento</span><strong className="text-right">{entrega.forma}</strong></p>
          <p className="flex justify-between gap-3"><span className="inline-flex items-center gap-2 text-gray-500"><DollarSign size={14} /> Valor pago</span><strong>{formatCurrency(Number(entrega.total || 0))}</strong></p>
          <p className="flex justify-between gap-3"><span className="inline-flex items-center gap-2 text-gray-500"><CalendarDays size={14} /> Data e hora</span><strong>{entrega.quando}</strong></p>
        </div>
        {aviso && <p className="mb-3 text-center text-sm text-gray-600">{aviso}</p>}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <button type="button" onClick={onImprimir} className="rounded-xl bg-sky-50 px-2 py-3 text-center text-sky-700">
            <Printer size={18} className="mx-auto" />
            <span className="mt-1 block text-sm font-semibold">Imprimir / PDF</span>
            <span className="block text-[11px]">Imprimir ou salvar em PDF</span>
          </button>
          <button type="button" disabled={!entrega.telefone || enviando !== null} onClick={onWhatsapp} className="rounded-xl bg-emerald-50 px-2 py-3 text-center text-emerald-700 disabled:opacity-40">
            <MessageCircle size={18} className="mx-auto" />
            <span className="mt-1 block text-sm font-semibold">{enviando === "whatsapp" ? "Enviando..." : "WhatsApp"}</span>
            <span className="block text-[11px]">{entrega.telefone ? "Enviar o recibo pelo WhatsApp" : "Informe um telefone"}</span>
          </button>
          <button type="button" disabled={!entrega.email || enviando !== null} onClick={onEmail} className="rounded-xl bg-violet-50 px-2 py-3 text-center text-violet-700 disabled:opacity-40">
            <Mail size={18} className="mx-auto" />
            <span className="mt-1 block text-sm font-semibold">{enviando === "email" ? "Enviando..." : "E-mail"}</span>
            <span className="block text-[11px]">{entrega.email ? "Enviar o recibo por e-mail" : "Informe um e-mail"}</span>
          </button>
          <button type="button" onClick={onFechar} className="rounded-xl bg-gray-100 px-2 py-3 text-center text-gray-600">
            <X size={18} className="mx-auto" />
            <span className="mt-1 block text-sm font-semibold">Fechar</span>
            <span className="block text-[11px]">Sem enviar agora</span>
          </button>
        </div>
      </div>
    </div>
  );
}

function LinhaCarrinho({ tipo, nome, detalhe, valor, onRemove }: { tipo: string; nome: string; detalhe: string; valor: number; onRemove?: () => void }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border px-3 py-2">
      <span className="rounded-full bg-pink-50 px-2 py-0.5 text-[11px] font-medium text-pink-700">{tipo}</span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium">{nome}</span>
        {detalhe && <span className="block text-xs text-gray-500">{detalhe}</span>}
      </span>
      <span className="text-sm font-semibold">{formatCurrency(valor)}</span>
      {onRemove && <button type="button" onClick={onRemove} aria-label={`Remover ${nome}`}><Trash2 size={14} className="text-gray-400" /></button>}
    </div>
  );
}
