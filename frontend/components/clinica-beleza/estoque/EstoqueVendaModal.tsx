"use client";

import { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { abrirPdfBlobFromResponse } from "@/lib/consulta-print";
import type { EstoqueProduto } from "./estoque-types";

const FORMAS = [
  { id: "PIX", label: "PIX" },
  { id: "CASH", label: "Dinheiro" },
  { id: "CREDIT_CARD", label: "Cartão de crédito" },
  { id: "DEBIT_CARD", label: "Cartão de débito" },
  { id: "TRANSFER", label: "Transferência" },
  { id: "PRAZO", label: "A prazo" },
];

type Linha = { produto: number; quantidade: string; preco: string; desconto: string };

export function EstoqueVendaModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [buscaCliente, setBuscaCliente] = useState("");
  const [clientes, setClientes] = useState<{ id: number; nome: string }[]>([]);
  const [paciente, setPaciente] = useState<number | "">("");
  const [produtos, setProdutos] = useState<EstoqueProduto[]>([]);
  const [linhas, setLinhas] = useState<Linha[]>([{ produto: 0, quantidade: "1", preco: "", desconto: "0" }]);
  const [forma, setForma] = useState("PIX");
  const [erro, setErro] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [venda, setVenda] = useState<{ id: number; payment_id: number; total: string } | null>(null);

  useEffect(() => {
    if (!open) return;
    setErro("");
    setVenda(null);
    ClinicaBelezaAPI.estoque
      .list({ page_size: 200 })
      .then((res) => {
        const lista = Array.isArray(res) ? res : (res as { results?: EstoqueProduto[] }).results || [];
        setProdutos(lista.filter((p) => p.vende_ao_cliente && p.is_active !== false));
      })
      .catch(() => setProdutos([]));
  }, [open]);

  useEffect(() => {
    const termo = buscaCliente.trim();
    if (termo.length < 2) {
      setClientes([]);
      return;
    }
    const timer = window.setTimeout(() => {
      ClinicaBelezaAPI.pedidos
        .buscarPacientes(termo)
        .then((lista) => setClientes(Array.isArray(lista) ? lista : []))
        .catch(() => setClientes([]));
    }, 250);
    return () => window.clearTimeout(timer);
  }, [buscaCliente]);

  const vendaveis = produtos;
  const total = useMemo(
    () =>
      linhas.reduce((acc, linha) => {
        const bruto = Number(linha.quantidade || 0) * Number(linha.preco || 0);
        return acc + Math.max(0, bruto - Number(linha.desconto || 0));
      }, 0),
    [linhas],
  );

  if (!open) return null;

  const escolherProduto = (indice: number, id: number) => {
    const produto = vendaveis.find((p) => p.id === id);
    setLinhas((atual) =>
      atual.map((linha, i) =>
        i === indice
          ? { ...linha, produto: id, preco: produto ? String(produto.preco_venda || 0) : linha.preco }
          : linha,
      ),
    );
  };

  const confirmar = async () => {
    setErro("");
    if (!paciente) {
      setErro("Selecione a cliente.");
      return;
    }
    const itens = linhas
      .filter((linha) => linha.produto)
      .map((linha) => ({
        produto: linha.produto,
        quantidade: Number(linha.quantidade),
        preco_unitario: Number(linha.preco || 0),
        desconto: Number(linha.desconto || 0),
      }));
    if (!itens.length) {
      setErro("Inclua ao menos um produto.");
      return;
    }
    setSalvando(true);
    try {
      const criada = await ClinicaBelezaAPI.estoque.vender({
        paciente: Number(paciente),
        payment_method: forma,
        itens,
      });
      setVenda(criada);
    } catch (e: unknown) {
      const msg = e && typeof e === "object" && "error" in e ? String((e as { error?: string }).error) : "";
      setErro(msg || "Não foi possível registrar a venda.");
    } finally {
      setSalvando(false);
    }
  };

  const abrirRecibo = async () => {
    if (!venda) return;
    const resp = await ClinicaBelezaAPI.payments.assinaturaReciboPdf(venda.payment_id);
    await abrirPdfBlobFromResponse(resp, `recibo-venda-${venda.id}.pdf`);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-2xl rounded-xl bg-white dark:bg-neutral-900 shadow-xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div>
            <h2 className="text-lg font-semibold">Venda de produtos</h2>
            <p className="text-xs text-gray-500">Recibo comercial. Não é nota fiscal.</p>
          </div>
          <button type="button" onClick={onClose} className="p-1 text-gray-500"><X size={18} /></button>
        </div>
        <div className="space-y-4 p-4">
          {venda ? (
            <div className="space-y-3">
              <p className="text-sm">Venda {venda.id} registrada. Total {Number(venda.total).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}.</p>
              <div className="flex flex-wrap gap-2">
                <button type="button" onClick={() => void abrirRecibo()} className="rounded-lg bg-[var(--cb-primary,#8B3D52)] px-3 py-2 text-sm text-white">Abrir recibo</button>
                <button type="button" onClick={() => void ClinicaBelezaAPI.payments.enviarRecibo(venda.payment_id, "whatsapp")} className="rounded-lg border px-3 py-2 text-sm">WhatsApp</button>
                <button type="button" onClick={() => void ClinicaBelezaAPI.payments.enviarRecibo(venda.payment_id, "email")} className="rounded-lg border px-3 py-2 text-sm">E-mail</button>
                <button type="button" onClick={() => void ClinicaBelezaAPI.payments.enviarReciboParaAssinatura(venda.payment_id, "whatsapp")} className="rounded-lg border px-3 py-2 text-sm">Assinatura</button>
                <button
                  type="button"
                  onClick={() => {
                    if (!window.confirm("Cancelar esta venda? O estoque volta e o pagamento fica cancelado. O histórico permanece.")) return;
                    void ClinicaBelezaAPI.estoque.cancelarVenda(venda.id).then(() => onClose());
                  }}
                  className="rounded-lg border border-red-300 px-3 py-2 text-sm text-red-700"
                >
                  Cancelar venda
                </button>
              </div>
            </div>
          ) : (
            <>
              <div>
                <label className="mb-1 block text-sm font-medium">Cliente</label>
                <input value={buscaCliente} onChange={(e) => setBuscaCliente(e.target.value)} placeholder="Nome ou CPF" className="w-full rounded-lg border px-3 py-2 text-sm dark:border-neutral-600 dark:bg-neutral-800" />
                {clientes.length > 0 && (
                  <div className="mt-1 max-h-32 overflow-y-auto rounded-lg border">
                    {clientes.map((cliente) => (
                      <button key={cliente.id} type="button" onClick={() => { setPaciente(cliente.id); setBuscaCliente(cliente.nome); setClientes([]); }} className="block w-full px-3 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-neutral-800">
                        {cliente.nome}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {linhas.map((linha, indice) => (
                <div key={indice} className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  <select value={linha.produto || ""} onChange={(e) => escolherProduto(indice, Number(e.target.value))} className="col-span-2 rounded-lg border px-2 py-2 text-sm dark:border-neutral-600 dark:bg-neutral-800">
                    <option value="">Produto</option>
                    {vendaveis.map((produto) => (
                      <option key={produto.id} value={produto.id}>{produto.nome}</option>
                    ))}
                  </select>
                  <input type="number" min="0.01" step="0.01" value={linha.quantidade} onChange={(e) => setLinhas((atual) => atual.map((item, i) => i === indice ? { ...item, quantidade: e.target.value } : item))} className="rounded-lg border px-2 py-2 text-sm dark:border-neutral-600 dark:bg-neutral-800" placeholder="Qtd" />
                  <input type="number" min="0" step="0.01" value={linha.preco} onChange={(e) => setLinhas((atual) => atual.map((item, i) => i === indice ? { ...item, preco: e.target.value } : item))} className="rounded-lg border px-2 py-2 text-sm dark:border-neutral-600 dark:bg-neutral-800" placeholder="Preço" />
                  <input type="number" min="0" step="0.01" value={linha.desconto} onChange={(e) => setLinhas((atual) => atual.map((item, i) => i === indice ? { ...item, desconto: e.target.value } : item))} className="rounded-lg border px-2 py-2 text-sm dark:border-neutral-600 dark:bg-neutral-800" placeholder="Desconto" />
                </div>
              ))}
              <button type="button" onClick={() => setLinhas((atual) => [...atual, { produto: 0, quantidade: "1", preco: "", desconto: "0" }])} className="text-sm text-[var(--cb-primary,#8B3D52)]">Adicionar produto</button>
              <div>
                <label className="mb-1 block text-sm font-medium">Forma de pagamento</label>
                <select value={forma} onChange={(e) => setForma(e.target.value)} className="w-full rounded-lg border px-3 py-2 text-sm dark:border-neutral-600 dark:bg-neutral-800">
                  {FORMAS.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
                </select>
              </div>
              <p className="text-sm font-medium">Total {total.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</p>
              {erro && <p className="text-sm text-red-600">{erro}</p>}
              <button type="button" disabled={salvando} onClick={() => void confirmar()} className="rounded-lg bg-[var(--cb-primary,#8B3D52)] px-4 py-2 text-sm text-white disabled:opacity-50">
                {salvando ? "Registrando..." : "Registrar venda"}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
