"use client";

/**
 * Estoque da Clínica - Clínica da Beleza
 * Controle de produtos, movimentações (entrada/saída), alertas de estoque baixo
 */

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { Package, ArrowDown, ArrowUp, AlertTriangle, Search, X } from "lucide-react";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { ClinicaBelezaRelatedLinks } from "@/components/clinica-beleza/ClinicaBelezaRelatedLinks";

interface Produto {
  id: number;
  nome: string;
  categoria: string;
  quantidade_atual: number;
  quantidade_minima: number;
  preco_custo: number | string;
  validade: string | null;
  status?: string;
}

interface Resumo {
  total_produtos: number;
  estoque_baixo: number;
  valor_total: number;
}

const CATEGORIAS = [
  { value: "injetavel", label: "Injetável" },
  { value: "soroterapia", label: "Soroterapia" },
  { value: "cosmetico", label: "Cosmético" },
  { value: "descartavel", label: "Descartável" },
  { value: "equipamento", label: "Equipamento" },
  { value: "outro", label: "Outro" },
];

const categoriaLabel = (val: string) => CATEGORIAS.find((c) => c.value === val)?.label ?? val;

const formatBRL = (value: number | string) =>
  Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

export interface EstoquePageContentProps {
  title?: string;
  subtitle?: string;
  defaultCategoria?: string;
  backHref?: string;
  relatedLinks?: { label: string; href: string }[];
}

export function EstoquePageContent({
  title = 'Estoque',
  subtitle = 'Controle de produtos e movimentações',
  defaultCategoria = '',
  backHref,
  relatedLinks = [],
}: EstoquePageContentProps) {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;

  const [produtos, setProdutos] = useState<Produto[]>([]);
  const [resumo, setResumo] = useState<Resumo | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [categoriaFilter, setCategoriaFilter] = useState("");

  // Modal states
  const [showProdutoModal, setShowProdutoModal] = useState(false);
  const [editingProduto, setEditingProduto] = useState<Produto | null>(null);
  const [showMovModal, setShowMovModal] = useState(false);
  const [movProduto, setMovProduto] = useState<Produto | null>(null);
  const [movTipo, setMovTipo] = useState<"entrada" | "saida">("entrada");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const cat = searchParams.get("categoria") || defaultCategoria;
    if (cat) setCategoriaFilter(cat);
  }, [searchParams, defaultCategoria]);

  const loadProdutos = useCallback(async () => {
    try {
      const qp = new URLSearchParams();
      if (categoriaFilter) qp.set("categoria", categoriaFilter);
      if (searchTerm) qp.set("search", searchTerm);
      const qs = qp.toString();
      const res = await clinicaBelezaFetch(`/estoque/${qs ? `?${qs}` : ""}`);
      if (res.ok) {
        const data = await res.json();
        setProdutos(Array.isArray(data) ? data : data.results ?? []);
      }
    } catch {
      setProdutos([]);
    }
  }, [categoriaFilter, searchTerm]);

  const loadResumo = useCallback(async () => {
    try {
      const res = await clinicaBelezaFetch("/estoque/resumo/");
      if (res.ok) setResumo(await res.json());
    } catch {
      setResumo(null);
    }
  }, []);

  const loadAll = useCallback(async () => {
    setLoading(true);
    await Promise.all([loadProdutos(), loadResumo()]);
    setLoading(false);
  }, [loadProdutos, loadResumo]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  // --- Product Modal ---
  function ProdutoModal() {
    const [form, setForm] = useState({
      nome: editingProduto?.nome ?? "",
      categoria: editingProduto?.categoria ?? "outro",
      quantidade_atual: editingProduto?.quantidade_atual ?? 0,
      quantidade_minima: editingProduto?.quantidade_minima ?? 0,
      preco_custo: editingProduto ? Number(editingProduto.preco_custo) : 0,
      validade: editingProduto?.validade ?? "",
    });

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      setSaving(true);
      try {
        const payload = { ...form, preco_custo: Number(form.preco_custo) };
        const url = editingProduto ? `/estoque/${editingProduto.id}/` : "/estoque/";
        const method = editingProduto ? "PUT" : "POST";
        const res = await clinicaBelezaFetch(url, { method, body: JSON.stringify(payload) });
        if (res.ok) {
          setShowProdutoModal(false);
          setEditingProduto(null);
          loadAll();
        }
      } finally {
        setSaving(false);
      }
    };

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
        <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-neutral-700">
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              {editingProduto ? "Editar Produto" : "Novo Produto"}
            </h2>
            <button onClick={() => { setShowProdutoModal(false); setEditingProduto(null); }} className="p-1 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded">
              <X size={20} className="text-gray-500 dark:text-gray-400" />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="p-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome</label>
              <input type="text" required value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Categoria</label>
              <select value={form.categoria} onChange={(e) => setForm({ ...form, categoria: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100">
                {CATEGORIAS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Quantidade</label>
                <input type="number" min={0} value={form.quantidade_atual} onChange={(e) => setForm({ ...form, quantidade_atual: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Mínimo</label>
                <input type="number" min={0} value={form.quantidade_minima} onChange={(e) => setForm({ ...form, quantidade_minima: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Preço Custo (R$)</label>
                <input type="number" step="0.01" min={0} value={form.preco_custo} onChange={(e) => setForm({ ...form, preco_custo: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Validade</label>
                <input type="date" value={form.validade} onChange={(e) => setForm({ ...form, validade: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100" />
              </div>
            </div>
            <button type="submit" disabled={saving}
              className="w-full py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 font-medium">
              {saving ? "Salvando..." : editingProduto ? "Salvar Alterações" : "Criar Produto"}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // --- Movimentação Modal ---
  function MovimentacaoModal() {
    const [quantidade, setQuantidade] = useState(1);
    const [motivo, setMotivo] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      if (!movProduto) return;
      setSaving(true);
      try {
        const res = await clinicaBelezaFetch(`/estoque/${movProduto.id}/movimentar/`, {
          method: "POST",
          body: JSON.stringify({ tipo: movTipo, quantidade, motivo }),
        });
        if (res.ok) {
          setShowMovModal(false);
          setMovProduto(null);
          loadAll();
        }
      } finally {
        setSaving(false);
      }
    };

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
        <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-xl w-full max-w-sm">
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-neutral-700">
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              {movTipo === "entrada" ? "Entrada de Estoque" : "Saída de Estoque"}
            </h2>
            <button onClick={() => { setShowMovModal(false); setMovProduto(null); }} className="p-1 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded">
              <X size={20} className="text-gray-500 dark:text-gray-400" />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="p-4 space-y-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Produto: <span className="font-medium text-gray-900 dark:text-gray-100">{movProduto?.nome}</span>
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Estoque atual: <span className="font-medium">{movProduto?.quantidade_atual}</span>
            </p>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Quantidade</label>
              <input type="number" min={1} required value={quantidade} onChange={(e) => setQuantidade(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Motivo</label>
              <input type="text" value={motivo} onChange={(e) => setMotivo(e.target.value)}
                placeholder="Ex: Compra fornecedor, Uso em procedimento..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100" />
            </div>
            <button type="submit" disabled={saving}
              className={`w-full py-2 text-white rounded-lg font-medium disabled:opacity-50 ${
                movTipo === "entrada" ? "bg-green-600 hover:bg-green-700" : "bg-red-600 hover:bg-red-700"
              }`}>
              {saving ? "Registrando..." : movTipo === "entrada" ? "Registrar Entrada" : "Registrar Saída"}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // --- Status badge ---
  const StatusBadge = ({ produto }: { produto: Produto }) => {
    const baixo = produto.quantidade_atual <= produto.quantidade_minima;
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
        baixo
          ? "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300"
          : "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300"
      }`}>
        {baixo && <AlertTriangle size={12} />}
        {baixo ? "Estoque baixo" : "OK"}
      </span>
    );
  };

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={title}
        subtitle={subtitle}
        backHref={backHref}
        icon={Package}
        newLabel="Novo Produto"
        onNew={() => { setEditingProduto(null); setShowProdutoModal(true); }}
      />
      <ClinicaBelezaPageContent>

        {loading && !resumo ? (
          <div className="flex justify-center py-12">
            <div className="w-10 h-10 border-4 border-purple-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <>
            {/* Summary Cards */}
            <section className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
              <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-purple-100 dark:border-purple-900/50">
                <div className="flex items-center gap-2 text-purple-700 dark:text-purple-400 mb-1">
                  <Package size={20} />
                  <span className="text-sm font-medium">Total Produtos</span>
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {resumo?.total_produtos ?? 0}
                </p>
              </div>
              <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-red-100 dark:border-red-900/50">
                <div className="flex items-center gap-2 text-red-700 dark:text-red-400 mb-1">
                  <AlertTriangle size={20} />
                  <span className="text-sm font-medium">Estoque Baixo</span>
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {resumo?.estoque_baixo ?? 0}
                </p>
              </div>
              <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-green-100 dark:border-green-900/50">
                <div className="flex items-center gap-2 text-green-700 dark:text-green-400 mb-1">
                  <Package size={20} />
                  <span className="text-sm font-medium">Valor Total Estoque</span>
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {formatBRL(resumo?.valor_total ?? 0)}
                </p>
              </div>
            </section>

            {/* Filters */}
            <div className="flex flex-wrap gap-3 mb-4">
              <div className="relative flex-1 min-w-[200px] max-w-sm">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Buscar por nome..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm"
                />
              </div>
              <select
                value={categoriaFilter}
                onChange={(e) => setCategoriaFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm"
              >
                <option value="">Todas as categorias</option>
                {CATEGORIAS.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>

            {/* Table */}
            <section className="bg-white dark:bg-neutral-800 rounded-xl shadow-md overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-neutral-700 border-b border-gray-200 dark:border-neutral-600">
                    <tr>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Nome</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Categoria</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Qtd</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Mínimo</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Preço Custo</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Validade</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Status</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {produtos.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="py-8 text-center text-gray-500 dark:text-gray-400">
                          Nenhum produto encontrado
                        </td>
                      </tr>
                    ) : (
                      produtos.map((p) => (
                        <tr key={p.id} className="border-b border-gray-100 dark:border-neutral-700 hover:bg-gray-50/50 dark:hover:bg-neutral-700/50">
                          <td className="py-3 px-4 font-medium text-gray-900 dark:text-gray-100">{p.nome}</td>
                          <td className="py-3 px-4 text-gray-600 dark:text-gray-300">{categoriaLabel(p.categoria)}</td>
                          <td className="py-3 px-4 text-right font-medium text-gray-900 dark:text-gray-100">{p.quantidade_atual}</td>
                          <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-300">{p.quantidade_minima}</td>
                          <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-300">{formatBRL(p.preco_custo)}</td>
                          <td className="py-3 px-4 text-gray-600 dark:text-gray-300">
                            {p.validade ? new Date(p.validade + "T00:00:00").toLocaleDateString("pt-BR") : "—"}
                          </td>
                          <td className="py-3 px-4"><StatusBadge produto={p} /></td>
                          <td className="py-3 px-4 text-right">
                            <div className="flex items-center justify-end gap-1">
                              <button
                                onClick={() => { setEditingProduto(p); setShowProdutoModal(true); }}
                                className="px-2 py-1 text-xs font-medium text-purple-700 dark:text-purple-300 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded"
                                title="Editar produto"
                              >
                                Editar
                              </button>
                              <button
                                onClick={() => { setMovProduto(p); setMovTipo("entrada"); setShowMovModal(true); }}
                                className="p-1 text-green-700 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 rounded"
                                title="Entrada de estoque"
                              >
                                <ArrowDown size={16} />
                              </button>
                              <button
                                onClick={() => { setMovProduto(p); setMovTipo("saida"); setShowMovModal(true); }}
                                className="p-1 text-red-700 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                                title="Saída de estoque"
                              >
                                <ArrowUp size={16} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}
        <ClinicaBelezaRelatedLinks slug={slug} items={relatedLinks} />
      </ClinicaBelezaPageContent>

      {/* Modals */}
      {showProdutoModal && <ProdutoModal />}
      {showMovModal && movProduto && <MovimentacaoModal />}

    </>
  );
}
