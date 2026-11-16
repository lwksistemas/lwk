"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Banknote, Check, CreditCard, Download, Layers, Mail, MessageCircle, Minus, Plus, Printer, QrCode, Scissors, ShoppingBag, Trash2, UserRound, X } from "lucide-react";
import { SalaoAPI, type AgendamentoSalao, type ClienteSalao, type LocalRecebimentoSalao, type PapelSalao, type ProdutoSalao } from "@/lib/salao-api";

type ItemCarrinho = { produto: number; nome: string; preco: string; saldo: number; quantidade: number };
type Linha = { id: string; forma: string; valor: string };
type FormaRapida = "dinheiro" | "pix" | "debito" | "credito" | "multiplas";

const FORMAS: { id: FormaRapida; nome: string; icone: typeof Banknote }[] = [
  { id: "dinheiro", nome: "Dinheiro", icone: Banknote },
  { id: "pix", nome: "Pix", icone: QrCode },
  { id: "debito", nome: "Débito", icone: CreditCard },
  { id: "credito", nome: "Crédito", icone: CreditCard },
  { id: "multiplas", nome: "Múltiplas", icone: Layers },
];

const ROTULO: Record<string, string> = { dinheiro: "Dinheiro", pix: "Pix", debito: "Débito", credito: "Crédito" };

function lerReais(texto: string) {
  const numero = Number(String(texto).replace(",", "."));
  return Number.isFinite(numero) ? Math.round(numero * 100) / 100 : 0;
}

function reais(valor: number) {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function diaIso(data: Date) {
  const mes = String(data.getMonth() + 1).padStart(2, "0");
  const dia = String(data.getDate()).padStart(2, "0");
  return `${data.getFullYear()}-${mes}-${dia}`;
}

function hora(valor: string) {
  return new Date(valor).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

function telefoneLegivel(valor: string) {
  const digitos = (valor || "").replace(/\D/g, "");
  if (digitos.length === 11) return `(${digitos.slice(0, 2)}) ${digitos.slice(2, 7)}-${digitos.slice(7)}`;
  if (digitos.length === 10) return `(${digitos.slice(0, 2)}) ${digitos.slice(2, 6)}-${digitos.slice(6)}`;
  return valor;
}

function iniciais(nome: string) {
  return nome.split(" ").filter(Boolean).slice(0, 2).map((parte) => parte[0]?.toUpperCase()).join("");
}

type DocumentosRecibo = { comprovante: boolean; nfse: boolean; nfce: boolean };
type LinhaRecibo = { nome: string; detalhe: string; total: string };
type ReciboPronto = {
  cliente: string;
  numero: number;
  valor: string;
  forma: string;
  quando: string;
  linhas: LinhaRecibo[];
  desconto: string;
  telefone: string;
  email: string;
  documentos: DocumentosRecibo;
  tipo: "servicos" | "produtos" | "misto";
};

function situacaoDocumento(chave: keyof DocumentosRecibo, tipo: ReciboPronto["tipo"] | "vazio", marcado: boolean, pago: boolean) {
  const aplicavel = chave === "comprovante" || (chave === "nfse" && tipo === "servicos") || (chave === "nfce" && tipo === "produtos");
  if (!aplicavel || tipo === "vazio") return "Não aplicável";
  if (!marcado) return "Não solicitado";
  if (chave === "comprovante" && pago) return "Emitido";
  return "Pendente de emissão";
}

function textoDocumento(chave: keyof DocumentosRecibo, tipo: ReciboPronto["tipo"] | "vazio") {
  if (chave === "comprovante") return "Resumo do pagamento. Serve para serviço, produto ou os dois juntos.";
  if (chave === "nfse") {
    if (tipo === "misto") return "Não se aplica. Serviço e produto juntos saem só no comprovante não fiscal.";
    if (tipo !== "servicos") return "Não se aplica sem serviço.";
    return "Nota Fiscal de Serviço Eletrônica. A emissão neste caixa ainda não está ligada.";
  }
  if (tipo === "misto") return "Não se aplica. Serviço e produto juntos saem só no comprovante não fiscal.";
  if (tipo !== "produtos") return "Não se aplica sem produto.";
  return "Cupom Fiscal Eletrônico de Produtos. A emissão neste caixa ainda não está ligada.";
}

function escaparHtml(valor: string) {
  return valor.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function numeroWhatsapp(telefone: string) {
  const digitos = (telefone || "").replace(/\D/g, "");
  if (digitos.length === 10 || digitos.length === 11) return `55${digitos}`;
  if (digitos.length >= 12) return digitos;
  return "";
}

function textoRecibo(recibo: ReciboPronto, loja: string) {
  const linhas = [
    loja || "Salão",
    "COMPROVANTE DE PAGAMENTO (NÃO FISCAL)",
    `Nº ${String(recibo.numero).padStart(6, "0")} · ${recibo.quando}`,
    `Cliente: ${recibo.cliente}`,
    ...recibo.linhas.flatMap((linha) => [linha.detalhe ? `${linha.nome} — ${reais(lerReais(linha.total))}\n${linha.detalhe}` : `${linha.nome} — ${reais(lerReais(linha.total))}`]),
  ];
  if (lerReais(recibo.desconto) > 0) linhas.push(`Desconto: ${reais(lerReais(recibo.desconto))}`);
  linhas.push(`Total pago: ${reais(lerReais(recibo.valor))}`);
  linhas.push(`Forma de pagamento: ${recibo.forma}`);
  if (recibo.documentos.nfse) linhas.push("NFS-e de serviço: não emitida neste caixa.");
  if (recibo.documentos.nfce) linhas.push("NFC-e de produto: não emitida neste caixa.");
  linhas.push("Este comprovante não substitui a emissão de Nota Fiscal (NFS-e) ou Cupom Fiscal (NFC-e).");
  return linhas.join("\n");
}

function baixarPdfRecibo(recibo: ReciboPronto, loja: string) {
  const escapar = (texto: string) => texto.replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");
  const comandos = textoRecibo(recibo, loja).split("\n").slice(0, 42).map((linha, indice) => {
    const segura = escapar(linha).replace(/[^\x00-\xff]/g, "?");
    return `BT /F1 10 Tf 36 ${800 - indice * 14} Td (${segura}) Tj ET`;
  }).join("\n");
  const objetos = [
    "1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj",
    "2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj",
    "3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj",
    `4 0 obj<< /Length ${comandos.length} >>stream\n${comandos}\nendstream endobj`,
    "5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>endobj",
  ];
  let pdf = "%PDF-1.4\n";
  const offsets = [0];
  objetos.forEach((objeto) => {
    offsets.push(pdf.length);
    pdf += `${objeto}\n`;
  });
  const xref = pdf.length;
  pdf += `xref\n0 ${objetos.length + 1}\n0000000000 65535 f \n`;
  offsets.slice(1).forEach((offset) => {
    pdf += `${String(offset).padStart(10, "0")} 00000 n \n`;
  });
  pdf += `trailer<< /Size ${objetos.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF`;
  const bytes = Uint8Array.from(pdf, (caractere) => caractere.charCodeAt(0) & 255);
  const url = URL.createObjectURL(new Blob([bytes], { type: "application/pdf" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `comprovante-${String(recibo.numero).padStart(6, "0")}.pdf`;
  link.click();
  URL.revokeObjectURL(url);
}

export default function CaixaPdvPage() {
  const slug = (useParams()?.slug as string) ?? "";
  const [aba, setAba] = useState<"atendimentos" | "produtos">("atendimentos");
  const [busca, setBusca] = useState("");
  const [fila, setFila] = useState<AgendamentoSalao[]>([]);
  const [clientes, setClientes] = useState<ClienteSalao[]>([]);
  const [produtos, setProdutos] = useState<ProdutoSalao[]>([]);
  const [carrinho, setCarrinho] = useState<ItemCarrinho[]>([]);
  const [escolhidos, setEscolhidos] = useState<number[]>([]);
  const [desconto, setDesconto] = useState("");
  const [formaRapida, setFormaRapida] = useState<FormaRapida>("dinheiro");
  const [linhas, setLinhas] = useState<Linha[]>([{ id: "1", forma: "dinheiro", valor: "" }]);
  const [entregue, setEntregue] = useState("");
  const [local, setLocal] = useState<LocalRecebimentoSalao>("caixa");
  const [papel, setPapel] = useState<PapelSalao | "">("");
  const [operador, setOperador] = useState("");
  const [abertura, setAbertura] = useState("");
  const [previaAberta, setPreviaAberta] = useState(true);
  const [erro, setErro] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [sucesso, setSucesso] = useState<ReciboPronto | null>(null);
  const [avisoEntrega, setAvisoEntrega] = useState("");
  const [avisoOk, setAvisoOk] = useState(false);
  const [enviando, setEnviando] = useState<"email" | "whatsapp" | null>(null);
  const [documentos, setDocumentos] = useState<DocumentosRecibo>({ comprovante: true, nfse: false, nfce: false });

  function carregar() {
    const fim = new Date();
    fim.setHours(23, 59, 0, 0);
    const inicio = new Date(fim);
    inicio.setDate(inicio.getDate() - 7);
    inicio.setHours(0, 0, 0, 0);
    return SalaoAPI.agenda(`${diaIso(inicio)}T00:00:00`, `${diaIso(fim)}T23:59:00`)
      .then((lista) => {
        const pendentes = lista.filter((item) => item.status === "COMPLETED" && !item.recebido);
        setFila(pendentes);
        setEscolhidos((atual) => atual.filter((id) => pendentes.some((item) => item.id === id)));
      })
      .catch((exc: Error) => setErro(exc.message));
  }

  useEffect(() => {
    SalaoAPI.config().then((dados) => {
      setLocal(dados.local_recebimento || "caixa");
      setOperador(dados.operador_nome || "");
      setAbertura(dados.caixa_abertura || "");
      setPapel(dados.papel || "");
    }).catch(() => undefined);
    SalaoAPI.produtos().then(setProdutos).catch(() => undefined);
    SalaoAPI.clientes().then(setClientes).catch(() => undefined);
    carregar();
  }, []);

  const visiveis = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    if (!termo) return fila;
    return fila.filter((item) => `${item.cliente_nome} ${item.servico_nome} ${item.profissional_nome}`.toLowerCase().includes(termo));
  }, [busca, fila]);

  const produtosVisiveis = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    if (!termo) return produtos;
    return produtos.filter((item) => `${item.nome} ${item.codigo_barras}`.toLowerCase().includes(termo));
  }, [busca, produtos]);

  const selecionados = escolhidos
    .map((id) => fila.find((item) => item.id === id))
    .filter((item): item is AgendamentoSalao => Boolean(item));
  const atual = selecionados[0] || null;
  const cliente = clientes.find((item) => item.id === atual?.cliente);
  const preco = Math.round(selecionados.reduce((acc, item) => acc + lerReais(item.preco), 0) * 100) / 100;
  const temServico = selecionados.length > 0;
  const temProduto = carrinho.length > 0;
  const tipoOperacao: ReciboPronto["tipo"] | "vazio" = temServico && temProduto ? "misto" : temServico ? "servicos" : temProduto ? "produtos" : "vazio";
  const valorDesconto = Math.min(preco, Math.max(0, lerReais(desconto)));
  const totalProdutos = Math.round(carrinho.reduce((acc, item) => acc + lerReais(item.preco) * item.quantidade, 0) * 100) / 100;
  const subtotal = Math.round((preco + totalProdutos) * 100) / 100;
  const total = Math.round((preco - valorDesconto + totalProdutos) * 100) / 100;
  const soma = Math.round(linhas.reduce((acc, linha) => acc + Math.max(0, lerReais(linha.valor)), 0) * 100) / 100;
  const falta = Math.round((total - soma) * 100) / 100;
  const formaRepetida = linhas.filter((linha) => lerReais(linha.valor) > 0).some((linha, indice, lista) => lista.findIndex((item) => item.forma === linha.forma) !== indice);
  const valorNegativo = linhas.some((linha) => lerReais(linha.valor) < 0) || lerReais(entregue) < 0;
  const valorRecebido = entregue === "" ? total : lerReais(entregue);
  const troco = formaRapida === "dinheiro" && valorRecebido > total ? Math.round((valorRecebido - total) * 100) / 100 : 0;
  const hoje = new Date();
  const formaLabel = formaRapida === "multiplas"
    ? linhas.map((linha) => ROTULO[linha.forma] || linha.forma).join(" e ")
    : ROTULO[formaRapida];

  useEffect(() => {
    if (formaRapida === "multiplas") return;
    setLinhas([{ id: "1", forma: formaRapida, valor: total > 0 ? total.toFixed(2) : "" }]);
  }, [total, formaRapida]);

  useEffect(() => {
    setDocumentos((atualDocs) => ({
      comprovante: tipoOperacao === "misto" ? true : atualDocs.comprovante,
      nfse: tipoOperacao === "servicos" ? atualDocs.nfse : false,
      nfce: tipoOperacao === "produtos" ? atualDocs.nfce : false,
    }));
  }, [tipoOperacao]);

  function escolherForma(proxima: FormaRapida) {
    setFormaRapida(proxima);
    setEntregue("");
    if (proxima === "multiplas") {
      setLinhas([
        { id: "1", forma: "dinheiro", valor: total > 0 ? total.toFixed(2) : "" },
        { id: "2", forma: "pix", valor: "" },
      ]);
    }
  }

  function selecionar(item: AgendamentoSalao) {
    setSucesso(null);
    setEntregue("");
    if (escolhidos.includes(item.id)) {
      setEscolhidos(escolhidos.filter((id) => id !== item.id));
      setErro("");
      return;
    }
    if (atual && atual.cliente !== item.cliente) {
      setErro("Receba um cliente por vez.");
      return;
    }
    setErro("");
    setEscolhidos([...escolhidos, item.id]);
    setDesconto("");
  }

  function colocarProduto(produto: ProdutoSalao) {
    const existente = carrinho.find((item) => item.produto === produto.id);
    const proxima = (existente?.quantidade || 0) + 1;
    if (proxima > produto.saldo) {
      setErro(`${produto.nome} tem ${produto.saldo} no estoque.`);
      return;
    }
    setErro("");
    setSucesso(null);
    if (existente) setCarrinho(carrinho.map((item) => item.produto === produto.id ? { ...item, quantidade: proxima } : item));
    else setCarrinho([...carrinho, { produto: produto.id, nome: produto.nome, preco: produto.preco, saldo: produto.saldo, quantidade: 1 }]);
  }

  function mudarQuantidade(produtoId: number, delta: number) {
    setCarrinho(carrinho.flatMap((item) => {
      if (item.produto !== produtoId) return [item];
      const proxima = item.quantidade + delta;
      if (proxima <= 0) return [];
      if (proxima > item.saldo) return [item];
      return [{ ...item, quantidade: proxima }];
    }));
  }

  async function confirmar() {
    if (salvando || (!atual && carrinho.length === 0) || (atual && local === "agenda")) return;
    if (atual && lerReais(desconto) > preco) {
      setErro("O desconto não pode passar do valor do serviço.");
      return;
    }
    if (valorNegativo) {
      setErro("O valor da forma de pagamento não pode ser negativo.");
      return;
    }
    if (formaRapida === "multiplas" && formaRepetida) {
      setErro("Use cada forma de pagamento uma vez.");
      return;
    }
    if (formaRapida === "multiplas" && total > 0 && Math.abs(soma - total) > 0.009) {
      setErro(`A soma das formas precisa fechar ${reais(total)}. Pagamento parcial não está habilitado.`);
      return;
    }
    if (formaRapida !== "multiplas" && entregue !== "") {
      const recebido = lerReais(entregue);
      if (formaRapida === "dinheiro" && recebido + 0.009 < total) {
        setErro(`Falta ${reais(total - recebido)} para fechar o total.`);
        return;
      }
      if (formaRapida !== "dinheiro" && Math.abs(recebido - total) > 0.009) {
        setErro("Essa forma precisa receber o total. O troco fica só no dinheiro.");
        return;
      }
    }
    setErro("");
    setSalvando(true);
    try {
      const venda = await SalaoAPI.vender({
        agendamentos: selecionados.map((item) => item.id),
        desconto: valorDesconto.toFixed(2),
        origem: "caixa",
        nfse: tipoOperacao === "servicos" && documentos.nfse,
        nfce: tipoOperacao === "produtos" && documentos.nfce,
        formas: total > 0 ? linhas.filter((linha) => lerReais(linha.valor) > 0).map((linha) => ({ forma: linha.forma, valor: lerReais(linha.valor).toFixed(2) })) : [],
        itens: carrinho.map((item) => ({ produto: item.produto, quantidade: item.quantidade })),
      });
      const tipoRecibo: ReciboPronto["tipo"] = tipoOperacao === "vazio" ? "produtos" : tipoOperacao;
      setAvisoEntrega("");
      setSucesso({
        cliente: venda.cliente,
        numero: venda.numero,
        valor: venda.valor,
        forma: venda.forma_label,
        quando: venda.quando,
        desconto: venda.desconto || valorDesconto.toFixed(2),
        telefone: cliente?.telefone || "",
        email: cliente?.email || "",
        documentos: {
          comprovante: documentos.comprovante || tipoRecibo === "misto",
          nfse: tipoRecibo === "servicos" && documentos.nfse,
          nfce: tipoRecibo === "produtos" && documentos.nfce,
        },
        tipo: tipoRecibo,
        linhas: [
          ...(venda.servicos || []).map((item) => ({ nome: `${item.nome} (Serviço)`, detalhe: item.profissional ? `Profissional: ${item.profissional}` : "", total: item.total })),
          ...(venda.itens || []).map((item) => ({ nome: `${item.quantidade}× ${item.nome}`, detalhe: "", total: item.total })),
        ],
      });
      setEscolhidos([]);
      setAbertura((atualAbertura) => atualAbertura || venda.quando);
      setCarrinho([]);
      setDesconto("");
      setEntregue("");
      await carregar();
      await SalaoAPI.produtos().then(setProdutos).catch(() => undefined);
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível receber.");
    } finally {
      setSalvando(false);
    }
  }

  const temConteudo = selecionados.length > 0 || carrinho.length > 0;
  const linhasPrevia = sucesso
    ? sucesso.linhas
    : [
        ...selecionados.map((item) => ({ nome: `${item.servico_nome} (Serviço)`, detalhe: item.profissional_nome ? `Profissional: ${item.profissional_nome}` : "", total: lerReais(item.preco).toFixed(2) })),
        ...carrinho.map((item) => ({ nome: `${item.quantidade}× ${item.nome}`, detalhe: "", total: (lerReais(item.preco) * item.quantidade).toFixed(2) })),
      ];

  function fecharRecibo() {
    setSucesso(null);
    setAvisoEntrega("");
    setAvisoOk(false);
    setEnviando(null);
  }

  function marcarDocumento(chave: keyof DocumentosRecibo, marcado: boolean) {
    const tipo = sucesso?.tipo || tipoOperacao;
    if (tipo === "misto" && chave !== "comprovante") return;
    if (tipo === "misto" && chave === "comprovante" && !marcado) return;
    if ((tipo === "servicos" || tipo === "vazio") && chave === "nfce") return;
    if ((tipo === "produtos" || tipo === "vazio") && chave === "nfse") return;
    setDocumentos((atualDocs) => ({ ...atualDocs, [chave]: marcado }));
    setSucesso((atualRecibo) => atualRecibo ? { ...atualRecibo, documentos: { ...atualRecibo.documentos, [chave]: marcado } } : atualRecibo);
    setAvisoEntrega("");
    setAvisoOk(false);
  }

  function exigirComprovante(recibo: ReciboPronto) {
    if (recibo.documentos.comprovante) return true;
    setAvisoEntrega("Marque o comprovante não fiscal. A nota de serviço e o cupom fiscal não são emitidos neste caixa.");
    setAvisoOk(false);
    return false;
  }

  function imprimirRecibo(recibo: ReciboPronto) {
    if (!exigirComprovante(recibo)) return;
    const itens = recibo.linhas.map((linha) => `<p style="display:flex;justify-content:space-between;gap:12px;margin:0"><span>${escaparHtml(linha.nome)}</span><span>${escaparHtml(reais(lerReais(linha.total)))}</span></p>${linha.detalhe ? `<p style="margin:0 0 8px;color:#555;font-size:12px">${escaparHtml(linha.detalhe)}</p>` : ""}`).join("");
    const descontoHtml = lerReais(recibo.desconto) > 0 ? `<p style="display:flex;justify-content:space-between"><span>Desconto</span><span>${escaparHtml(reais(lerReais(recibo.desconto)))}</span></p>` : "";
    const fiscal = `${recibo.documentos.nfse ? "<p>NFS-e de serviço: não emitida neste caixa.</p>" : ""}${recibo.documentos.nfce ? "<p>NFC-e de produto: não emitida neste caixa.</p>" : ""}`;
    const html = `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Comprovante ${recibo.numero}</title></head><body style="font-family:sans-serif;max-width:360px;margin:24px auto;font-size:14px"><h1 style="font-size:16px;text-align:center">${escaparHtml(operador || "Salão")}</h1><p style="text-align:center;letter-spacing:.04em">COMPROVANTE DE PAGAMENTO<br>(NÃO FISCAL)</p><p style="display:flex;justify-content:space-between"><span>Nº ${String(recibo.numero).padStart(6, "0")}</span><span>${escaparHtml(recibo.quando)}</span></p><p>Cliente: ${escaparHtml(recibo.cliente)}</p>${itens}${descontoHtml}<p style="display:flex;justify-content:space-between;font-weight:700;border-top:1px solid #ddd;padding-top:8px"><span>Total pago</span><span>${escaparHtml(reais(lerReais(recibo.valor)))}</span></p><p>Forma de pagamento: ${escaparHtml(recibo.forma)}</p>${fiscal}<p style="font-size:12px;color:#666">Este comprovante não substitui a emissão de Nota Fiscal (NFS-e) ou Cupom Fiscal (NFC-e).</p></body></html>`;
    const quadro = document.createElement("iframe");
    quadro.setAttribute("title", "Impressão do comprovante");
    quadro.style.position = "fixed";
    quadro.style.right = "0";
    quadro.style.bottom = "0";
    quadro.style.width = "0";
    quadro.style.height = "0";
    quadro.style.border = "0";
    document.body.appendChild(quadro);
    const documento = quadro.contentDocument;
    const janela = quadro.contentWindow;
    if (!documento || !janela) {
      quadro.remove();
      setAvisoEntrega("Não foi possível preparar a impressão.");
      setAvisoOk(false);
      return;
    }
    documento.open();
    documento.write(html);
    documento.close();
    window.setTimeout(() => {
      janela.focus();
      janela.print();
      window.setTimeout(() => quadro.remove(), 1000);
    }, 50);
  }

  async function enviarRecibo(recibo: ReciboPronto, canal: "email" | "whatsapp") {
    if (!exigirComprovante(recibo) || enviando) return;
    if (canal === "email" && !recibo.email) return;
    if (canal === "whatsapp" && !numeroWhatsapp(recibo.telefone)) return;
    setEnviando(canal);
    setAvisoEntrega("");
    setAvisoOk(false);
    try {
      const resposta = await SalaoAPI.enviarRecibo(recibo.numero, canal);
      setAvisoEntrega(resposta.message);
      setAvisoOk(true);
    } catch (exc) {
      setAvisoEntrega(exc instanceof Error ? exc.message : "Não foi possível enviar o recibo.");
      setAvisoOk(false);
    } finally {
      setEnviando(null);
    }
  }

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Caixa / PDV</h1>
          <p className="text-sm text-[#8a6e74]">Recebimento de atendimentos e venda de produtos</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="rounded-full bg-[#e7f6ee] px-3 py-1 font-medium text-[#1f8a4c]">{abertura ? "Caixa aberto" : "Caixa sem sessão"}</span>
          <span className="rounded-full bg-white px-3 py-1 text-[#5c3d45]">Abertura: {abertura || "na primeira venda"}</span>
          <span className="ml-1 flex items-center gap-2 rounded-full bg-white px-2 py-1 pr-3">
            <span className="grid h-8 w-8 place-items-center rounded-full bg-[#7a3044] text-xs font-semibold text-white">{iniciais(operador || "Caixa")}</span>
            <span className="font-medium">{operador || "Caixa"}</span>
          </span>
        </div>
      </header>

      <div className="grid items-start gap-4 xl:grid-cols-[300px_minmax(0,1fr)_320px]">
        <section className="rounded-3xl bg-white p-4">
          <div className="grid grid-cols-2 gap-2">
            <button type="button" onClick={() => { setAba("atendimentos"); setBusca(""); }} className={`rounded-xl px-3 py-2 text-sm font-medium ${aba === "atendimentos" ? "bg-[#7a3044] text-white" : "bg-[#f6eef0] text-[#5c3d45]"}`}>
              Atendimentos ({fila.length})
            </button>
            <button type="button" onClick={() => { setAba("produtos"); setBusca(""); }} className={`rounded-xl px-3 py-2 text-sm font-medium ${aba === "produtos" ? "bg-[#7a3044] text-white" : "bg-[#f6eef0] text-[#5c3d45]"}`}>
              Venda de produtos
            </button>
          </div>
          <input value={busca} onChange={(evento) => setBusca(evento.target.value)} placeholder={aba === "atendimentos" ? "Buscar cliente ou atendimento..." : "Nome ou código de barras"} className="mt-3 w-full rounded-xl border border-[#eadfe2] px-3 py-2 text-sm" />
          {aba === "atendimentos" ? <p className="mt-2 text-xs text-[#8a6e74]">Pode marcar vários atendimentos do mesmo cliente.</p> : null}
          <div className="mt-3 space-y-2">
            {aba === "atendimentos" ? visiveis.map((item) => (
              <button key={item.id} type="button" onClick={() => selecionar(item)} className={`flex w-full items-center justify-between gap-3 rounded-2xl border px-3 py-3 text-left ${escolhidos.includes(item.id) ? "border-[#f3c3cf] bg-[#fdecef]" : "border-[#f0e4e7]"}`}>
                <span>
                  <span className="block font-medium">{item.cliente_nome}</span>
                  <span className="block text-sm text-[#8a6e74]">{item.servico_nome} · {reais(lerReais(item.preco))}</span>
                </span>
                <span className="text-sm text-[#8a6e74]">{hora(item.inicio)}</span>
              </button>
            )) : produtosVisiveis.map((produto) => (
              <button key={produto.id} type="button" onClick={() => colocarProduto(produto)} className="flex w-full items-center justify-between gap-3 rounded-2xl border border-[#f0e4e7] px-3 py-3 text-left">
                <span>
                  <span className="block font-medium">{produto.nome}</span>
                  <span className="block text-sm text-[#8a6e74]">{reais(lerReais(produto.preco))} · saldo {produto.saldo}</span>
                </span>
                <Plus size={16} className="text-[#7a3044]" />
              </button>
            ))}
            {aba === "atendimentos" && visiveis.length === 0 ? <p className="text-sm text-[#8a6e74]">Nenhum atendimento concluído aguardando pagamento.</p> : null}
            {aba === "produtos" && produtosVisiveis.length === 0 ? <p className="text-sm text-[#8a6e74]">Nenhum produto encontrado.</p> : null}
            {aba === "produtos" && (papel === "administrador" || papel === "autonomo") ? (
              <Link href={`/loja/${slug}/salao-cabeleireiro/estoque`} className="inline-block text-sm text-[#7a3044]">Cadastrar produto</Link>
            ) : null}
          </div>
        </section>

        <section className="rounded-3xl bg-white p-4">
          <div className="flex items-start justify-between gap-3 rounded-2xl border border-[#f0e4e7] p-3">
            <div className="flex gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-full bg-[#f6eef0] text-[#7a3044]"><UserRound size={18} /></span>
              <div>
                <p className="font-semibold">{atual?.cliente_nome || (carrinho.length ? "Venda de produto" : "Nenhum cliente selecionado")}</p>
                {cliente?.telefone ? <p className="text-sm text-[#8a6e74]">{telefoneLegivel(cliente.telefone)}</p> : null}
                {cliente?.email ? <p className="text-sm text-[#8a6e74]">{cliente.email}</p> : null}
              </div>
            </div>
            {selecionados.length ? <button type="button" className="text-sm font-medium text-[#7a3044]" onClick={() => { setEscolhidos([]); setDesconto(""); }}>Trocar cliente</button> : null}
          </div>

          <div className="mt-4">
            <p className="text-sm font-medium">Itens do recebimento</p>
            <div className="mt-2 space-y-2">
              {selecionados.map((item) => (
                <div key={item.id} className="flex items-center gap-3 rounded-2xl border border-[#f0e4e7] px-3 py-3">
                  <Scissors size={16} className="text-[#7a3044]" />
                  <span className="min-w-0 flex-1">
                    <span className="block font-medium">{item.servico_nome} (Serviço)</span>
                    <span className="block text-sm text-[#8a6e74]">Profissional: {item.profissional_nome}</span>
                  </span>
                  <span className="font-medium">{reais(lerReais(item.preco))}</span>
                  <button type="button" aria-label="Remover serviço" onClick={() => setEscolhidos(escolhidos.filter((id) => id !== item.id))} className="text-[#8a6e74]"><Trash2 size={16} /></button>
                </div>
              ))}
              {carrinho.map((item) => (
                <div key={item.produto} className="flex items-center gap-3 rounded-2xl border border-[#f0e4e7] px-3 py-3">
                  <ShoppingBag size={16} className="text-[#7a3044]" />
                  <span className="min-w-0 flex-1">
                    <span className="block font-medium">{item.nome}</span>
                    <span className="block text-sm text-[#8a6e74]">Produto</span>
                  </span>
                  <span className="flex items-center gap-2 rounded-full border border-[#eadfe2] px-2 py-1">
                    <button type="button" aria-label="Diminuir" onClick={() => mudarQuantidade(item.produto, -1)}><Minus size={14} /></button>
                    <span className="w-4 text-center text-sm">{item.quantidade}</span>
                    <button type="button" aria-label="Aumentar" onClick={() => mudarQuantidade(item.produto, 1)}><Plus size={14} /></button>
                  </span>
                  <span className="font-medium">{reais(lerReais(item.preco) * item.quantidade)}</span>
                  <button type="button" aria-label="Remover produto" onClick={() => setCarrinho(carrinho.filter((atualItem) => atualItem.produto !== item.produto))} className="text-[#8a6e74]"><Trash2 size={16} /></button>
                </div>
              ))}
              {!temConteudo ? <p className="text-sm text-[#8a6e74]">Escolha um atendimento concluído ou um produto.</p> : null}
            </div>
            <button type="button" className="mt-3 text-sm font-medium text-[#7a3044]" onClick={() => { setAba("produtos"); setBusca(""); }}>+ Adicionar item</button>
          </div>

          <div className="mt-4 space-y-2 text-sm">
            <div className="flex items-center justify-between"><span>Subtotal</span><span>{reais(subtotal)}</span></div>
            <div className="flex items-center justify-between gap-3">
              <span>Desconto (R$)</span>
              <input value={desconto} onChange={(evento) => setDesconto(evento.target.value)} placeholder="0,00" className="w-28 rounded-xl border border-[#eadfe2] px-3 py-1.5 text-right" />
            </div>
            <div className="flex items-center justify-between rounded-2xl bg-[#fdecef] px-3 py-3 text-base font-semibold text-[#7a3044]">
              <span>Total a receber</span><span>{reais(total)}</span>
            </div>
          </div>

          <div className="mt-4">
            <p className="text-sm font-medium">Forma de pagamento</p>
            <div className="mt-2 grid grid-cols-5 gap-2">
              {FORMAS.map((forma) => {
                const Icone = forma.icone;
                const ativa = formaRapida === forma.id;
                return (
                  <button key={forma.id} type="button" onClick={() => escolherForma(forma.id)} className={`flex flex-col items-center gap-1 rounded-2xl border px-2 py-3 text-xs font-medium ${ativa ? "border-[#7a3044] bg-[#fdecef] text-[#7a3044]" : "border-[#f0e4e7] text-[#5c3d45]"}`}>
                    <Icone size={18} />
                    {forma.nome}
                  </button>
                );
              })}
            </div>
            {formaRapida === "multiplas" ? (
              <div className="mt-3 space-y-2">
                {linhas.map((linha) => (
                  <div key={linha.id} className="grid grid-cols-[1fr_8rem] gap-2">
                    <select value={linha.forma} onChange={(evento) => setLinhas(linhas.map((item) => item.id === linha.id ? { ...item, forma: evento.target.value } : item))} className="rounded-xl border border-[#eadfe2] px-3 py-2 text-sm">
                      {FORMAS.filter((forma) => forma.id !== "multiplas").map((forma) => <option key={forma.id} value={forma.id}>{forma.nome}</option>)}
                    </select>
                    <input value={linha.valor} onChange={(evento) => setLinhas(linhas.map((item) => item.id === linha.id ? { ...item, valor: evento.target.value } : item))} className="rounded-xl border border-[#eadfe2] px-3 py-2 text-sm" />
                  </div>
                ))}
                <button type="button" className="text-sm text-[#7a3044]" onClick={() => setLinhas([...linhas, { id: String(Date.now()), forma: linhas.some((linha) => linha.forma === "pix") ? "debito" : "pix", valor: "" }])}>Adicionar forma</button>
                <p className="text-sm text-[#5c3d45]">Distribuído: {reais(soma)}</p>
                <p className={`text-sm ${Math.abs(falta) < 0.009 ? "text-[#1f8a4c]" : "text-red-700"}`}>{falta > 0.009 ? `Falta distribuir ${reais(falta)}` : falta < -0.009 ? `Passou ${reais(Math.abs(falta))} do total` : "A soma fecha o total."}</p>
                <p className="text-xs text-[#8a6e74]">Pagamento parcial não está habilitado. Cada forma entra uma vez, sem valor negativo.</p>
              </div>
            ) : (
              <div className="mt-3 grid grid-cols-2 gap-3">
                <label className="text-sm">Valor recebido (R$)
                  <input value={entregue === "" ? (total > 0 ? total.toFixed(2) : "") : entregue} onChange={(evento) => setEntregue(evento.target.value)} className="mt-1 w-full rounded-xl border border-[#eadfe2] px-3 py-2" />
                </label>
                <div className="text-sm">Troco
                  <p className="mt-1 rounded-xl bg-[#e7f6ee] px-3 py-2 font-semibold text-[#1f8a4c]">{reais(troco)}</p>
                </div>
              </div>
            )}
          </div>

          {selecionados.length > 0 && local === "agenda" ? <p className="mt-3 text-sm text-[#8a6e74]">Neste salão o serviço é recebido na agenda.</p> : null}
          {erro ? <p className="mt-3 text-sm text-red-700">{erro}</p> : null}
          <button type="button" onClick={confirmar} disabled={salvando || !temConteudo || valorNegativo || formaRepetida || (formaRapida === "multiplas" && total > 0 && Math.abs(falta) > 0.009) || (selecionados.length > 0 && local === "agenda")} className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl bg-[#7a3044] px-4 py-3 text-sm font-semibold text-white disabled:opacity-60">
            <Check size={16} />
            {salvando ? "Registrando…" : "Confirmar recebimento"}
          </button>
        </section>

        <section className="space-y-4">
          <div className="rounded-3xl bg-white p-4">
            <p className="font-medium">Documentos (após o recebimento)</p>
            <p className="mt-1 text-xs text-[#8a6e74]">
              {tipoOperacao === "misto"
                ? "Serviço e produto juntos saem só no comprovante não fiscal."
                : tipoOperacao === "servicos"
                  ? "Serviços podem sair no comprovante não fiscal e na NFS-e."
                  : tipoOperacao === "produtos"
                    ? "Produtos podem sair no comprovante não fiscal e na NFC-e."
                    : "Escolha o atendimento ou o produto para ver os documentos."}
            </p>
            {([
              ["comprovante", "Comprovante não fiscal"],
              ["nfse", "NFS-e (Serviços)"],
              ["nfce", "NFC-e (Produtos)"],
            ] as const).map(([chave, titulo]) => {
              const liberado = chave === "comprovante" || (chave === "nfse" ? tipoOperacao === "servicos" : tipoOperacao === "produtos");
              return (
                <label key={chave} className={`mt-3 flex items-start justify-between gap-3 text-sm ${liberado ? "" : "opacity-50"}`}>
                  <span>
                    <span className="block font-medium">{titulo}</span>
                    <span className="block text-[#8a6e74]">{textoDocumento(chave, tipoOperacao)}</span>
                    <span className="block text-xs text-[#5c3d45]">{situacaoDocumento(chave, tipoOperacao, documentos[chave], false)}</span>
                  </span>
                  <input type="checkbox" checked={liberado && documentos[chave]} disabled={!liberado || (chave === "comprovante" && tipoOperacao === "misto")} onChange={(evento) => setDocumentos({ ...documentos, [chave]: evento.target.checked })} className="mt-1 h-4 w-4 accent-[#7a3044]" />
                </label>
              );
            })}
          </div>
          <div className="rounded-3xl bg-white p-4 text-sm">
            <div className="flex items-center justify-between gap-2">
              <p className="font-medium">Prévia do comprovante</p>
              <button type="button" className="text-xs text-[#7a3044]" onClick={() => setPreviaAberta((aberta) => !aberta)}>{previaAberta ? "Recolher" : "Mostrar"}</button>
            </div>
            {previaAberta ? <div className="mt-3 rounded-2xl border border-[#f0e4e7] p-4 text-center">
              <p className="font-semibold">{operador || "Salão"}</p>
              <p className="mt-2 text-xs tracking-wide">COMPROVANTE DE PAGAMENTO</p>
              <p className="text-xs text-[#8a6e74]">(NÃO FISCAL)</p>
              <div className="mt-3 flex justify-between text-left text-xs text-[#8a6e74]">
                <span>{sucesso ? `Nº ${String(sucesso.numero).padStart(6, "0")}` : "Prévia"}</span>
                <span>{sucesso?.quando || hoje.toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" })}</span>
              </div>
              <p className="mt-2 text-left text-xs">Cliente: {atual?.cliente_nome || sucesso?.cliente || "—"}</p>
              <div className="mt-3 space-y-1 text-left text-xs">
                {linhasPrevia.map((linha) => (
                  <div key={linha.nome}>
                    <p className="flex justify-between gap-2"><span>{linha.nome}</span><span>{reais(lerReais(linha.total))}</span></p>
                    {linha.detalhe ? <p className="text-[#8a6e74]">{linha.detalhe}</p> : null}
                  </div>
                ))}
              </div>
              <p className="mt-3 flex justify-between border-t border-[#f0e4e7] pt-2 font-semibold"><span>{sucesso ? "Total pago" : "Total a receber"}</span><span>{reais(sucesso ? lerReais(sucesso.valor) : total)}</span></p>
              <p className="mt-2 text-left text-xs">Forma de pagamento: {sucesso?.forma || formaLabel}</p>
              <p className="mt-3 text-left text-[11px] text-[#8a6e74]">Este comprovante não substitui a emissão de Nota Fiscal (NFS-e) ou Cupom Fiscal (NFC-e).</p>
            </div> : null}
          </div>
        </section>
      </div>
      {sucesso ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-2xl rounded-2xl bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-[#f0e4e7] p-4">
              <h2 className="text-lg font-bold text-green-700">✓ Pagamento registrado</h2>
              <button type="button" onClick={fecharRecibo} aria-label="Fechar" className="rounded-lg p-2 hover:bg-[#f6eef0]"><X size={18} /></button>
            </div>
            <div className="space-y-4 p-6">
              <div className="space-y-1 rounded-lg bg-green-50 p-4 text-sm">
                <p><strong>Cliente:</strong> {sucesso.cliente}</p>
                {sucesso.linhas.filter((linha) => linha.detalhe).map((linha) => <p key={linha.nome}><strong>{linha.detalhe}</strong></p>)}
                <p><strong>Valor:</strong> {reais(lerReais(sucesso.valor))}</p>
                <p><strong>Valor recebido nesta operação:</strong> {reais(lerReais(sucesso.valor))}</p>
                <p><strong>Formas nesta operação:</strong> {sucesso.forma}</p>
                <p className="pt-1 text-xs text-[#8a6e74]">O recibo impresso, o WhatsApp e o e-mail listam as formas e o total pago. Comprovante {String(sucesso.numero).padStart(6, "0")} · {sucesso.quando}</p>
              </div>
              <div>
                <p className="text-sm font-medium">Documentos para o cliente</p>
                {([
                  ["comprovante", "Comprovante não fiscal"],
                  ["nfse", "NFS-e (Serviços)"],
                  ["nfce", "NFC-e (Produtos)"],
                ] as const).map(([chave, titulo]) => {
                  const liberado = chave === "comprovante" || (chave === "nfse" ? sucesso.tipo === "servicos" : sucesso.tipo === "produtos");
                  return (
                    <label key={chave} className={`mt-3 flex items-start justify-between gap-3 text-sm ${liberado ? "" : "opacity-50"}`}>
                      <span>
                        <span className="block font-medium">{titulo}</span>
                        <span className="block text-[#8a6e74]">{textoDocumento(chave, sucesso.tipo)}</span>
                        <span className="block text-xs text-[#5c3d45]">{situacaoDocumento(chave, sucesso.tipo, sucesso.documentos[chave], true)}</span>
                      </span>
                      <input type="checkbox" checked={liberado && sucesso.documentos[chave]} disabled={!liberado || (chave === "comprovante" && sucesso.tipo === "misto")} onChange={(evento) => marcarDocumento(chave, evento.target.checked)} className="mt-1 h-4 w-4 accent-[#7a3044]" />
                    </label>
                  );
                })}
                <p className="mt-3 text-xs text-[#8a6e74]">A NFS-e e a NFC-e não são emitidas neste caixa. Se ficarem pendentes, não são enviadas ao cliente. O comprovante não fiscal não substitui essa nota.</p>
              </div>
              <p className="text-sm text-[#5c3d45]">Envie o recibo de pagamento para o cliente:</p>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <button type="button" onClick={() => imprimirRecibo(sucesso)} className="flex flex-col items-center gap-2 rounded-xl border border-[#eadfe2] p-4 hover:bg-[#f6eef0]">
                  <Printer size={24} />
                  <span className="text-xs font-medium">Imprimir</span>
                </button>
                <button type="button" onClick={() => { if (exigirComprovante(sucesso)) baixarPdfRecibo(sucesso, operador); }} className="flex flex-col items-center gap-2 rounded-xl border border-[#eadfe2] p-4 hover:bg-[#f6eef0]">
                  <Download size={24} />
                  <span className="text-xs font-medium">Baixar PDF</span>
                </button>
                <button type="button" onClick={() => void enviarRecibo(sucesso, "email")} disabled={!sucesso.email || enviando !== null} className="flex flex-col items-center gap-2 rounded-xl border border-[#eadfe2] p-4 hover:bg-[#f6eef0] disabled:opacity-40">
                  <Mail size={24} />
                  <span className="text-xs font-medium">{enviando === "email" ? "Enviando..." : "Enviar por e-mail"}</span>
                  <span className="text-center text-[11px] text-[#8a6e74]">{sucesso.email ? "Enviar o recibo por e-mail" : "Cliente sem e-mail"}</span>
                </button>
                <button type="button" onClick={() => void enviarRecibo(sucesso, "whatsapp")} disabled={!numeroWhatsapp(sucesso.telefone) || enviando !== null} className="flex flex-col items-center gap-2 rounded-xl border border-[#eadfe2] p-4 hover:bg-[#f6eef0] disabled:opacity-40">
                  <MessageCircle size={24} />
                  <span className="text-xs font-medium">{enviando === "whatsapp" ? "Enviando..." : "Enviar por WhatsApp"}</span>
                  <span className="text-center text-[11px] text-[#8a6e74]">{numeroWhatsapp(sucesso.telefone) ? "Enviar o recibo pelo WhatsApp" : "Cliente sem telefone"}</span>
                </button>
              </div>
              {avisoEntrega ? <p className={`text-sm ${avisoOk ? "text-green-700" : "text-red-700"}`}>{avisoEntrega}</p> : null}
              <div className="flex justify-end">
                <button type="button" onClick={fecharRecibo} className="rounded-lg bg-[#7a3044] px-4 py-2 text-sm text-white">Fechar</button>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
