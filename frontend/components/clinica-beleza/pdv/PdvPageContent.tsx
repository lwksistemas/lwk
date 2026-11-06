"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ModalReceberConsulta } from "@/components/clinica-beleza/consultas/ModalReceberConsulta";
import { useToast } from "@/components/ui/Toast";
import { formatApiErrorBody } from "@/lib/api-errors";
import type { Consulta, ConsultaProcedimento } from "@/components/clinica-beleza/consultas/consultas-types";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import { formatarAgendaEvento } from "@/hooks/clinica-beleza/agenda-data/agenda-event-mappers";
import { consultaPagamentoUi } from "@/hooks/clinica-beleza/consulta-detail-actions/consulta-detail-actions-utils";
import { ClinicaBelezaAPI, clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { CLINICA_FORMA_PAGAMENTO_LABEL } from "@/lib/clinica-beleza-constants";
import { JanelaReciboVenda } from "./JanelaReciboVenda";
import { PdvAbrirCaixa, PdvPainelCaixa } from "./PdvModaisCaixa";
import { PdvCabecalho } from "./PdvCabecalho";
import { PdvColunaMeio } from "./PdvColunaMeio";
import { PdvIndicadores } from "./PdvIndicadores";
import { PdvListaAgenda } from "./PdvListaAgenda";
import { PdvResumo } from "./PdvResumo";
import {
  FORMAS_PDV,
  clientePresente,
  hojeIso,
  quandoRecibo,
  exibirReciboNoPdv,
  paymentIdReciboPdv,
  pdvPodeReceberAtendimento,
  seloCaixaPdv,
  podeAlterarServico,
  reais,
} from "./pdv-utils";
import {
  listaDe,
  mensagemErro,
  type EntregaRecibo,
  type FechamentoCaixa,
  type ProdutoLinha,
  type ProdutoOpcao,
  type VendaLinha,
} from "./pdv-tipos";

type ConsultaDia = Consulta & { appointment?: number | null };

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

  const procedimentos: ConsultaProcedimento[] = consulta?.procedures_list?.length
    ? consulta.procedures_list
    : selecionado?.extendedProps?.procedure_name
      ? [{ id: 0, appointment_procedure_id: 0, nome: selecionado.extendedProps.procedure_name, valor: Number(selecionado.extendedProps.procedure_price || 0) }]
      : [];

  return (
    <ClinicaBelezaPageContent className="!pt-4">
      <PdvCabecalho
        onHistorico={() => setPainel("historico")}
        caixaAberto={caixaAberto}
        onFechamento={() => { setMenuCaixa(false); setPainel("fechamento"); }}
        onAlternarMenu={() => setMenuCaixa((atual) => !atual)}
        caixaResponsavel={caixaResponsavel}
        onAbrirCaixa={() => { setErro(""); setAbrindoCaixa(true); }}
        menuCaixa={menuCaixa}
      />
      <PdvIndicadores
        agendamentos={agendaHoje.length}
        presentes={presentes}
        aReceber={resumo.a_receber}
        recebidoHoje={recebidoHoje}
        vendasProdutos={vendasProdutos}
      />
      <div className="grid items-start gap-4 xl:grid-cols-[minmax(240px,0.9fr)_minmax(320px,1.4fr)_minmax(260px,0.85fr)]">
        <PdvListaAgenda
          slug={slug}
          agendaHoje={agendaHoje}
          consultas={consultas}
          selecionadoId={selecionadoId}
          onSelecionar={(id) => { setSelecionadoId(id); setAba("servico"); }}
          onMarcarPresente={(id) => void marcarPresente(id)}
        />
        <PdvColunaMeio
          aba={aba}
          onAba={setAba}
          erro={erro}
          servico={{
            selecionado,
            onLimparCliente: () => setSelecionadoId(null),
            procedimentos,
            alteraServico,
            consulta,
            onRemoverServico: (consultaId, procedimentoId) => void removerServico(consultaId, procedimentoId),
            produtosConsulta,
            consultaFinalizada,
            onRecarregarProdutos: (consultaId) => void carregarProdutos(consultaId),
            incluindo,
            escolha,
            onEscolha: setEscolha,
            salvando,
            catalogo,
            procedimentosCat,
            onIncluirProduto: () => void incluirProduto(),
            onIncluirServico: () => void incluirServico(),
            onIncluir: setIncluindo,
            observacao,
            onObservacao: setObservacao,
          }}
          venda={{
            onAlternarNovoCliente: () => setNovoCliente((atual) => !atual),
            buscaCliente,
            onBuscaCliente: (valor) => { setBuscaCliente(valor); setPacienteVenda(""); },
            pacienteVenda,
            clientes,
            onEscolherCliente: (cliente) => {
              setPacienteVenda(cliente.id);
              setBuscaCliente(cliente.nome);
              setTelefoneRecibo(cliente.telefone || "");
              setEmailRecibo(cliente.email || "");
              setClientes([]);
            },
            telefoneRecibo,
            onTelefoneRecibo: setTelefoneRecibo,
            emailRecibo,
            onEmailRecibo: setEmailRecibo,
            novoCliente,
            nomeNovo,
            onNomeNovo: setNomeNovo,
            telefoneNovo,
            onTelefoneNovo: setTelefoneNovo,
            cpfNovo,
            onCpfNovo: setCpfNovo,
            onClienteCriado: (id, nome, telefone) => {
              setPacienteVenda(id);
              setBuscaCliente(nome);
              setTelefoneRecibo(telefone);
              setNovoCliente(false);
            },
            buscaProduto,
            onBuscaProduto: setBuscaProduto,
            onEnterProduto: () => { if (sugestoes[0]) adicionarProduto(sugestoes[0]); },
            sugestoes,
            onAdicionarProduto: adicionarProduto,
            produtosConsultados,
            linhasVenda,
            setLinhasVenda,
          }}
        />
        <PdvResumo
          subtotal={subtotal}
          aba={aba}
          editandoDesconto={editandoDesconto}
          desconto={desconto}
          onDesconto={setDesconto}
          onEditarDesconto={setEditandoDesconto}
          descontoNum={descontoNum}
          pago={pago}
          total={total}
          vendaAPrazo={vendaAPrazo}
          slug={slug}
          atendimentoIsento={atendimentoIsento}
          aguardandoChegada={aguardandoChegada}
          forma={forma}
          onForma={setForma}
          caixaAberto={caixaAberto}
          mostrarFormas={mostrarFormas}
          formasExibidas={formasExibidas}
          quitado={quitado}
          consultaFinalizada={consultaFinalizada}
          salvando={salvando}
          consultaId={consulta?.id}
          onReceberServico={() => setReceberAberto(true)}
          onReceberVenda={() => void receber()}
          mostrarRecibo={mostrarRecibo}
          paymentRecibo={paymentRecibo}
          onImprimirRecibo={() => void imprimirRecibo(paymentRecibo)}
          onEnviarRecibo={(canal) => void enviarReciboAtendimento(canal)}
        />
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

      <PdvAbrirCaixa
        aberto={abrindoCaixa}
        onFechar={() => setAbrindoCaixa(false)}
        responsavelCaixa={responsavelCaixa}
        onResponsavel={setResponsavelCaixa}
        funcionarios={funcionarios}
        erro={erro}
        salvando={salvando}
        onConfirmar={() => void confirmarAbertura()}
      />
      <PdvPainelCaixa
        painel={painel}
        onFechar={() => { setPainel(null); setResumoCaixa(null); }}
        resumoCaixa={resumoCaixa}
        onVoltarHistorico={() => setResumoCaixa(null)}
        onVerResumo={setResumoCaixa}
        fechamentos={fechamentos}
        recebidoHoje={recebidoHoje}
        caixaAberto={caixaAberto}
        caixaAReceber={caixaAReceber}
        vendasProdutos={vendasProdutos}
        caixaNome={caixaNome}
        caixaResponsavel={caixaResponsavel}
        erro={erro}
        onFecharCaixa={() => { void fecharCaixa(); }}
        onImprimir={imprimirResumoCaixa}
      />
    </ClinicaBelezaPageContent>
  );
}
