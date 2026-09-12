"use client";

import { useEffect, useState } from "react";
import { AlertCircle, Loader2, Plus, Trash2, X } from "lucide-react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api/client";
import type {
  FornecedorItem,
  FornecedorProdutoItem,
  PedidoCompraItem,
} from "@/lib/clinica-beleza-api/client-ops";
import { ESTOQUE_INPUT_CLASS, extractEstoqueApiError } from "./estoque-types";
import { abrirPdfPedido, canalResultado } from "./pedido-compra-utils";

type Linha = {
  catalogo_id?: number;
  codigo: string;
  nome: string;
  unidade: string;
  quantidade: string;
  preco: string;
};

const linhaVazia = (): Linha => ({ codigo: "", nome: "", unidade: "un", quantidade: "1", preco: "0" });

function numeroPedido(raw: string): number {
  const s = String(raw || "").replace("R$", "").trim();
  if (!s) return 0;
  const n = s.includes(",")
    ? Number(s.replace(/\./g, "").replace(",", "."))
    : Number(s);
  return Number.isFinite(n) ? n : 0;
}

function brlPedido(valor: number): string {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function EstoquePedidoModal({
  open,
  pedidoId,
  onClose,
  onDeleted,
}: {
  open: boolean;
  pedidoId: number | null;
  onClose: () => void;
  onDeleted?: () => void;
}) {
  const [fornecedores, setFornecedores] = useState<FornecedorItem[]>([]);
  const [fornecedorId, setFornecedorId] = useState<number | "">("");
  const [sugestoes, setSugestoes] = useState<FornecedorProdutoItem[]>([]);
  const [busca, setBusca] = useState("");
  const [itens, setItens] = useState<Linha[]>([linhaVazia()]);
  const [obs, setObs] = useState("");
  const [pedido, setPedido] = useState<PedidoCompraItem | null>(null);
  const [profissionais, setProfissionais] = useState<{ id: number; nome: string; conselho?: string }[]>([]);
  const [profissionalId, setProfissionalId] = useState<number | "">("");
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    setError("");
    setOk("");
    setProfissionalId("");
    void ClinicaBelezaAPI.estoque.fornecedores.list().then(setFornecedores).catch(() => setFornecedores([]));
    void Promise.all([
      ClinicaBelezaAPI.estoque.pedidos.assinantes(),
      ClinicaBelezaAPI.me.get().catch(() => null),
    ]).then(([rows, me]) => {
      const lista = (rows || []).filter((p) => p.nome);
      setProfissionais(lista);
      const meuId = me?.professional_id;
      if (meuId && lista.some((p) => p.id === meuId)) {
        setProfissionalId(meuId);
      } else if (lista.length === 1) {
        setProfissionalId(lista[0].id);
      }
    }).catch(() => setProfissionais([]));
    if (pedidoId) {
      void ClinicaBelezaAPI.estoque.pedidos.get(pedidoId).then((p) => {
        setPedido(p);
        setFornecedorId(p.fornecedor.id);
        setObs(p.observacoes);
        setItens(
          p.itens.map((i) => ({
            catalogo_id: i.catalogo_id ?? undefined,
            codigo: i.codigo,
            nome: i.nome,
            unidade: i.unidade,
            quantidade: i.quantidade,
            preco: i.preco,
          })),
        );
      }).catch((err) => setError(extractEstoqueApiError(err, "Erro ao carregar pedido.")));
    } else {
      setPedido(null);
      setFornecedorId("");
      setObs("");
      setItens([linhaVazia()]);
    }
  }, [open, pedidoId]);

  useEffect(() => {
    if (!fornecedorId || busca.trim().length < 1) {
      setSugestoes([]);
      return;
    }
    const t = setTimeout(() => {
      void ClinicaBelezaAPI.estoque.fornecedores.produtos(Number(fornecedorId), busca)
        .then(setSugestoes)
        .catch(() => setSugestoes([]));
    }, 250);
    return () => clearTimeout(t);
  }, [fornecedorId, busca]);

  const rascunho = !pedido || pedido.status === "rascunho";
  const totalPedido = itens.reduce(
    (acc, item) => acc + numeroPedido(item.quantidade) * numeroPedido(item.preco),
    0,
  );

  const payload = () => ({
    fornecedor_id: Number(fornecedorId),
    observacoes: obs,
    itens: itens.filter((i) => i.codigo && i.nome).map((i) => ({
      catalogo_id: i.catalogo_id,
      codigo: i.codigo,
      nome: i.nome,
      unidade: i.unidade,
      quantidade: i.quantidade,
      preco: i.preco,
    })),
  });

  const salvar = async () => {
    setSaving(true);
    setError("");
    try {
      const p = pedido
        ? await ClinicaBelezaAPI.estoque.pedidos.update(pedido.id, payload())
        : await ClinicaBelezaAPI.estoque.pedidos.create(payload());
      setPedido(p);
      setOk(`Pedido nº ${p.numero} salvo.`);
    } catch (err) {
      setError(extractEstoqueApiError(err, "Erro ao salvar pedido."));
    } finally {
      setSaving(false);
    }
  };

  const assinar = async () => {
    if (!pedido) return;
    if (!profissionalId) {
      setError("Selecione o profissional que assina pela clínica.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      setPedido(await ClinicaBelezaAPI.estoque.pedidos.assinarClinica(pedido.id, Number(profissionalId)));
      setOk("Profissional assinou. Envie o PDF ao fornecedor.");
    } catch (err) {
      setError(extractEstoqueApiError(err, "Erro ao assinar."));
    } finally {
      setSaving(false);
    }
  };

  const excluirPedido = async () => {
    if (!pedido) return;
    if (!confirm(`Excluir o pedido nº ${pedido.numero}? Esta ação não pode ser desfeita.`)) return;
    setSaving(true);
    setError("");
    try {
      await ClinicaBelezaAPI.estoque.pedidos.delete(pedido.id);
      onDeleted?.();
      onClose();
    } catch (err) {
      setError(extractEstoqueApiError(err, "Erro ao excluir pedido."));
    } finally {
      setSaving(false);
    }
  };

  const enviarPdf = async (canal: "email" | "whatsapp") => {
    if (!pedido) return;
    setSaving(true);
    setError("");
    try {
      const res = await ClinicaBelezaAPI.estoque.pedidos.enviar(pedido.id, canal);
      setPedido(res.pedido);
      setOk(canalResultado(res, canal));
    } catch (err) {
      setError(extractEstoqueApiError(err, "Erro ao enviar pedido."));
    } finally {
      setSaving(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-3xl max-h-[92vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-neutral-700">
          <div>
            <h2 className="text-lg font-semibold">
              {pedido ? `Pedido nº ${pedido.numero}` : "Criar pedido"}
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              {pedido ? pedido.status_display : "Rascunho — não dá entrada no estoque."}
            </p>
          </div>
          <button type="button" onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800">
            <X size={20} className="text-gray-500" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 text-red-600 text-sm flex gap-2">
              <AlertCircle size={16} className="shrink-0 mt-0.5" />
              {error}
            </div>
          )}
          {ok && <div className="p-3 rounded-lg bg-green-50 text-green-700 text-sm">{ok}</div>}

          <select
            className={ESTOQUE_INPUT_CLASS}
            value={fornecedorId}
            disabled={!rascunho}
            onChange={(e) => setFornecedorId(e.target.value ? Number(e.target.value) : "")}
          >
            <option value="">Selecione o fornecedor</option>
            {fornecedores.map((f) => (
              <option key={f.id} value={f.id}>
                {f.nome_fantasia || f.razao_social} — {f.cnpj}
              </option>
            ))}
          </select>

          {rascunho && fornecedorId && (
            <div className="relative">
              <input
                className={ESTOQUE_INPUT_CLASS}
                placeholder="Buscar código ou nome no catálogo"
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
              />
              {sugestoes.length > 0 && (
                <div className="absolute z-10 mt-1 w-full bg-white dark:bg-neutral-800 border rounded-lg shadow max-h-40 overflow-y-auto">
                  {sugestoes.map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-neutral-700"
                      onClick={() => {
                        setItens((prev) => [
                          ...prev.filter((i) => i.codigo || i.nome),
                          {
                            catalogo_id: s.id,
                            codigo: s.codigo,
                            nome: s.nome,
                            unidade: s.unidade,
                            quantidade: "1",
                            preco: s.preco_ref,
                          },
                        ]);
                        setBusca("");
                        setSugestoes([]);
                      }}
                    >
                      {s.codigo} — {s.nome}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="space-y-2">
            <div className="grid grid-cols-12 gap-2 text-[11px] text-gray-500 px-0.5">
              <span className="col-span-2">Código</span>
              <span className="col-span-3">Produto</span>
              <span className="col-span-2">Qtd</span>
              <span className="col-span-2">Preço</span>
              <span className="col-span-2 text-right">Subtotal</span>
            </div>
            {itens.map((item, idx) => {
              const subtotal = numeroPedido(item.quantidade) * numeroPedido(item.preco);
              return (
              <div key={idx} className="grid grid-cols-12 gap-2 items-center">
                <input className={`${ESTOQUE_INPUT_CLASS} col-span-2`} placeholder="Código" disabled={!rascunho} value={item.codigo} onChange={(e) => setItens((p) => p.map((x, i) => i === idx ? { ...x, codigo: e.target.value } : x))} />
                <input className={`${ESTOQUE_INPUT_CLASS} col-span-3`} placeholder="Nome" disabled={!rascunho} value={item.nome} onChange={(e) => setItens((p) => p.map((x, i) => i === idx ? { ...x, nome: e.target.value } : x))} />
                <input className={`${ESTOQUE_INPUT_CLASS} col-span-2`} placeholder="Qtd" disabled={!rascunho} value={item.quantidade} onChange={(e) => setItens((p) => p.map((x, i) => i === idx ? { ...x, quantidade: e.target.value } : x))} />
                <input className={`${ESTOQUE_INPUT_CLASS} col-span-2`} placeholder="Preço" disabled={!rascunho} value={item.preco} onChange={(e) => setItens((p) => p.map((x, i) => i === idx ? { ...x, preco: e.target.value } : x))} />
                <div className="col-span-2 text-right text-sm font-medium whitespace-nowrap">{brlPedido(subtotal)}</div>
                {rascunho && (
                  <button type="button" onClick={() => setItens((p) => p.filter((_, i) => i !== idx))} className="col-span-1 text-gray-400 hover:text-red-500">
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
              );
            })}
            {rascunho && (
              <button type="button" onClick={() => setItens((p) => [...p, linhaVazia()])} className="text-sm inline-flex items-center gap-1 text-gray-600">
                <Plus size={14} /> Item
              </button>
            )}
            <div className="flex justify-end pt-1 text-sm font-semibold" style={{ color: "var(--cb-primary, #8B3D52)" }}>
              Total {brlPedido(totalPedido)}
            </div>
          </div>

          <textarea
            className={ESTOQUE_INPUT_CLASS}
            rows={2}
            placeholder="Observações"
            disabled={!rascunho}
            value={obs}
            onChange={(e) => setObs(e.target.value)}
          />

          {pedido && (
            <div className="text-xs text-gray-600 space-y-1">
              <p>
                Profissional:{" "}
                {pedido.assinaturas.clinica.assinado
                  ? `assinado por ${pedido.assinaturas.clinica.nome}${pedido.assinaturas.clinica.cpf ? ` · CPF ${pedido.assinaturas.clinica.cpf}` : ""}${pedido.assinaturas.clinica.conselho ? ` · ${pedido.assinaturas.clinica.conselho}` : ""}`
                  : "pendente"}
              </p>
              <p>Fornecedor: recebe o PDF assinado para processar o pedido.</p>
            </div>
          )}

          {pedido && !pedido.assinaturas.clinica.assinado && pedido.status !== "cancelado" && (
            <div className="space-y-1">
              <label className="text-xs text-gray-500">Quem assina pela clínica</label>
              <div className="flex gap-2">
                <select
                  className={ESTOQUE_INPUT_CLASS}
                  value={profissionalId}
                  onChange={(e) => setProfissionalId(e.target.value ? Number(e.target.value) : "")}
                >
                  <option value="">Selecione o profissional</option>
                  {profissionais.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.conselho ? `${p.nome} — ${p.conselho}` : p.nome}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  disabled={saving || !profissionalId}
                  onClick={() => void assinar()}
                  className="px-3 py-2 text-sm rounded-lg text-white whitespace-nowrap disabled:opacity-50"
                  style={{ background: "var(--cb-primary, #8B3D52)" }}
                >
                  Assinar
                </button>
              </div>
              {profissionais.length === 0 && (
                <p className="text-xs text-gray-500">Nenhum profissional ativo. Cadastre em Profissionais.</p>
              )}
            </div>
          )}

          {pedido?.pode_enviar_pdf && (
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={() => void abrirPdfPedido(pedido.id).catch((e) => setError(String(e.message || e)))} className="px-3 py-2 text-sm rounded-lg border">
                Visualizar / imprimir
              </button>
              <button type="button" disabled={saving} onClick={() => void enviarPdf("email")} className="px-3 py-2 text-sm rounded-lg border">
                E-mail
              </button>
              <button type="button" disabled={saving} onClick={() => void enviarPdf("whatsapp")} className="px-3 py-2 text-sm rounded-lg border">
                WhatsApp
              </button>
            </div>
          )}
        </div>
        <div className="px-6 py-3 border-t flex justify-between gap-2">
          <div className="flex gap-2">
            <button type="button" onClick={onClose} className="px-3 py-2 text-sm rounded-lg border">Fechar</button>
            {pedido && (
              <button
                type="button"
                disabled={saving}
                onClick={() => void excluirPedido()}
                className="inline-flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border border-red-200 text-red-600 hover:bg-red-50 disabled:opacity-50"
              >
                <Trash2 size={14} />
                Excluir
              </button>
            )}
          </div>
          {rascunho && (
            <button
              type="button"
              disabled={saving || !fornecedorId}
              onClick={() => void salvar()}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg text-white disabled:opacity-50"
              style={{ background: "var(--cb-primary, #8B3D52)" }}
            >
              {saving && <Loader2 size={16} className="animate-spin" />}
              Salvar rascunho
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
