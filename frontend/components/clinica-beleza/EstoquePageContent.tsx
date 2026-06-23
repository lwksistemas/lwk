"use client";

/**
 * Estoque da Clínica - Clínica da Beleza
 * Controle de produtos, movimentações (entrada/saída), alertas de estoque baixo
 */

import { useEffect, useMemo, useState, useCallback } from "react";
import { useParams, usePathname, useRouter, useSearchParams } from "next/navigation";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { Package, ArrowDown, ArrowUp, AlertTriangle, Search, X, FileUp } from "lucide-react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { formatClinicaDataCurta } from "@/lib/clinica-beleza-datetime";
import { ClinicaBelezaRelatedLinks } from "@/components/clinica-beleza/ClinicaBelezaRelatedLinks";
import { EstoqueImportarXmlModal } from "@/components/clinica-beleza/EstoqueImportarXmlModal";
import { toUpperCase } from "@/lib/format-br";

interface Produto {
  id: number;
  nome: string;
  categoria: string;
  marca?: string;
  quantidade_atual: number;
  quantidade_minima: number;
  preco_custo: number | string;
  validade: string | null;
  lote?: string;
  numero_nota?: string;
  status?: string;
}

interface Resumo {
  total_produtos: number;
  estoque_baixo: number;
  valor_total_estoque: number;
}

const CATEGORIAS = [
  { value: "injetavel", label: "Injetável" },
  { value: "soroterapia", label: "Soroterapia" },
  { value: "cosmético", label: "Cosmético" },
  { value: "medicamentos", label: "Medicamentos" },
  { value: "descartavel", label: "Descartável" },
  { value: "equipamento", label: "Equipamento" },
  { value: "outro", label: "Outro" },
];

const CATEGORIA_VALUES = new Set(CATEGORIAS.map((c) => c.value));

const normalizeCategoria = (val?: string | null): string => {
  if (!val) return "outro";
  if (val === "cosmetico") return "cosmético";
  if (val === "Medicamentos" || val === "medicamento") return "medicamentos";
  if (CATEGORIA_VALUES.has(val)) return val;
  return "outro";
};

const categoriaLabel = (val: string) => {
  const norm = normalizeCategoria(val);
  return CATEGORIAS.find((c) => c.value === norm)?.label ?? val;
};

export interface EstoquePageContentProps {
  title?: string;
  subtitle?: string;
  defaultCategoria?: string;
  backHref?: string;
  relatedLinks?: { label: string; href: string }[];
}

export function EstoquePageContent({
  title = 'Estoque',
  subtitle = 'Produtos, insumos e movimentações da clínica',
  defaultCategoria = '',
  backHref,
  relatedLinks = [],
}: EstoquePageContentProps) {
  const params = useParams();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const slug = params.slug as string;

  const [resumo, setResumo] = useState<Resumo | null>(null);
  const [loadingResumo, setLoadingResumo] = useState(true);
  const [produtos, setProdutos] = useState<Produto[]>([]);
  const [loadingProdutos, setLoadingProdutos] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [categoriaFilter, setCategoriaFilter] = useState("");

  const lojaCtx = useMemo(() => ({ slug }), [slug]);

  const loading = loadingResumo || loadingProdutos;

  // Modal states
  const [showProdutoModal, setShowProdutoModal] = useState(false);
  const [showImportXmlModal, setShowImportXmlModal] = useState(false);
  const [editingProduto, setEditingProduto] = useState<Produto | null>(null);
  const [showMovModal, setShowMovModal] = useState(false);
  const [movProduto, setMovProduto] = useState<Produto | null>(null);
  const [movTipo, setMovTipo] = useState<"entrada" | "saida">("entrada");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const cat = searchParams.get("categoria") || defaultCategoria;
    setCategoriaFilter(cat);
  }, [searchParams, defaultCategoria]);

  const setCategoriaFilterAndUrl = (value: string) => {
    setCategoriaFilter(value);
    const qp = new URLSearchParams(searchParams.toString());
    if (value) qp.set("categoria", value);
    else qp.delete("categoria");
    const qs = qp.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
  };

  const extractApiError = (err: unknown, fallback: string): string => {
    if (err && typeof err === "object" && "error" in err) {
      return String((err as { error: string }).error);
    }
    if (err && typeof err === "object" && "detail" in err) {
      return String((err as { detail: string }).detail);
    }
    if (err && typeof err === "object") {
      const parts = Object.entries(err as Record<string, unknown>).flatMap(([key, val]) => {
        if (Array.isArray(val)) return val.map((v) => `${key}: ${v}`);
        if (typeof val === "string") return [`${key}: ${val}`];
        return [];
      });
      if (parts.length) return parts.join("; ");
    }
    return fallback;
  };

  const loadProdutos = useCallback(async () => {
    setLoadingProdutos(true);
    setListError(null);
    try {
      const params: { categoria?: string; search?: string } = {};
      if (categoriaFilter) params.categoria = categoriaFilter;
      if (searchTerm.trim()) params.search = searchTerm.trim();
      const items = await ClinicaBelezaAPI.estoque.list(params, lojaCtx);
      setProdutos(Array.isArray(items) ? items : []);
    } catch (err) {
      setProdutos([]);
      setListError(extractApiError(err, "Não foi possível carregar a lista."));
    } finally {
      setLoadingProdutos(false);
    }
  }, [categoriaFilter, searchTerm, lojaCtx]);

  const loadResumo = useCallback(async () => {
    try {
      const data = await ClinicaBelezaAPI.estoque.resumo(lojaCtx);
      setResumo(data);
    } catch {
      setResumo(null);
    }
  }, [lojaCtx]);

  const loadAll = useCallback(async () => {
    setLoadingResumo(true);
    await Promise.all([loadProdutos(), loadResumo()]);
    setLoadingResumo(false);
  }, [loadProdutos, loadResumo]);

  useEffect(() => {
    loadResumo();
  }, [loadResumo]);

  useEffect(() => {
    const timer = setTimeout(() => {
      loadProdutos();
    }, searchTerm ? 300 : 0);
    return () => clearTimeout(timer);
  }, [loadProdutos, searchTerm]);

  // --- Delete Product ---
  const handleExcluirProduto = async (id: number, nome: string) => {
    if (!confirm(`Excluir "${nome}" do estoque? Esta ação não pode ser desfeita.`)) return;
    try {
      await ClinicaBelezaAPI.estoque.delete(id);
      await loadAll();
    } catch {
      alert("Erro ao excluir produto.");
    }
  };

  // --- Product Modal ---
  function ProdutoModal() {
    const [form, setForm] = useState({
      nome: editingProduto?.nome ?? "",
      categoria: normalizeCategoria(editingProduto?.categoria),
      quantidade_atual: editingProduto?.quantidade_atual ?? 0,
      quantidade_minima: editingProduto?.quantidade_minima ?? 0,
      preco_custo: editingProduto ? Number(editingProduto.preco_custo) : 0,
      validade: editingProduto?.validade ? String(editingProduto.validade).slice(0, 10) : "",
      lote: editingProduto?.lote ?? "",
      numero_nota: editingProduto?.numero_nota ?? "",
    });

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      setSaving(true);
      setSaveError(null);
      try {
        const payload = {
          ...form,
          preco_custo: Number(form.preco_custo),
          validade: form.validade || null,
        };
        if (editingProduto) {
          await ClinicaBelezaAPI.estoque.update(editingProduto.id, payload, lojaCtx);
        } else {
          await ClinicaBelezaAPI.estoque.create(payload, lojaCtx);
        }
        setShowProdutoModal(false);
        setEditingProduto(null);
        loadAll();
      } catch (err) {
        setSaveError(extractApiError(err, "Não foi possível salvar o produto."));
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
              <input type="text" required value={form.nome} onChange={(e) => setForm({ ...form, nome: toUpperCase(e.target.value) })}
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
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nº da nota fiscal</label>
                <input type="text" value={form.numero_nota} onChange={(e) => setForm({ ...form, numero_nota: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                  placeholder="Ex: 12345" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nº do lote</label>
                <input type="text" value={form.lote} onChange={(e) => setForm({ ...form, lote: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                  placeholder="Lote do produto" />
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
            {saveError && (
              <div className="px-3 py-2 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300">
                {saveError}
              </div>
            )}
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
        await ClinicaBelezaAPI.estoque.movimentar(movProduto.id, {
          tipo: movTipo,
          quantidade,
          motivo,
        });
        setShowMovModal(false);
        setMovProduto(null);
        loadAll();
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
        extraActions={
          <button
            type="button"
            onClick={() => setShowImportXmlModal(true)}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs sm:text-sm font-medium rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700"
          >
            <FileUp size={16} />
            <span className="hidden sm:inline">Importar XML</span>
          </button>
        }
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
                  {formatCurrency(resumo?.valor_total_estoque ?? 0)}
                </p>
              </div>
            </section>

            {/* Filters */}
            <div className="flex flex-wrap items-center gap-3 mb-4">
              {categoriaFilter && (
                <span className="px-2 py-1 rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200 text-sm">
                  Filtro: {categoriaLabel(categoriaFilter)}
                </span>
              )}
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
                onChange={(e) => setCategoriaFilterAndUrl(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm"
              >
                <option value="">Todas as categorias</option>
                {CATEGORIAS.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>

            {listError && (
              <div className="mb-4 px-4 py-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300">
                Erro ao carregar produtos: {listError}
              </div>
            )}

            {/* Table */}
            <section className="bg-white dark:bg-neutral-800 rounded-xl shadow-md overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-neutral-700 border-b border-gray-200 dark:border-neutral-600">
                    <tr>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Nome</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300 hidden md:table-cell">Fornecedor</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Categoria</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Qtd</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700 dark:text-gray-300 hidden sm:table-cell">Mínimo</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Preço Custo</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300 hidden lg:table-cell">Lote</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300 hidden xl:table-cell">Nota</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300 hidden lg:table-cell">Validade</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Status</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {produtos.length === 0 ? (
                      <tr>
                        <td colSpan={10} className="py-8 text-center text-gray-500 dark:text-gray-400">
                          Nenhum produto encontrado
                        </td>
                      </tr>
                    ) : (
                      produtos.map((p) => (
                        <tr key={p.id} className="border-b border-gray-100 dark:border-neutral-700 hover:bg-gray-50/50 dark:hover:bg-neutral-700/50">
                          <td className="py-3 px-4 font-medium text-gray-900 dark:text-gray-100">{p.nome}</td>
                          <td className="py-3 px-4 text-gray-600 dark:text-gray-300 hidden md:table-cell">{p.marca || "—"}</td>
                          <td className="py-3 px-4 text-gray-600 dark:text-gray-300">{categoriaLabel(p.categoria)}</td>
                          <td className="py-3 px-4 text-right font-medium text-gray-900 dark:text-gray-100">{p.quantidade_atual}</td>
                          <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-300 hidden sm:table-cell">{p.quantidade_minima}</td>
                          <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-300">{formatCurrency(p.preco_custo)}</td>
                          <td className="py-3 px-4 text-gray-600 dark:text-gray-300 hidden lg:table-cell">{p.lote || "—"}</td>
                          <td className="py-3 px-4 text-gray-600 dark:text-gray-300 hidden xl:table-cell">{p.numero_nota || "—"}</td>
                          <td className="py-3 px-4 text-gray-600 dark:text-gray-300 hidden lg:table-cell">
                            {p.validade ? formatClinicaDataCurta(new Date(p.validade + "T00:00:00")) : "—"}
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
                              <button
                                onClick={() => handleExcluirProduto(p.id, p.nome)}
                                className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                                title="Excluir produto"
                              >
                                <X size={16} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
              {produtos.length > 0 && (
                <div className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 border-t border-gray-100 dark:border-neutral-700">
                  {produtos.length} produto{produtos.length !== 1 ? "s" : ""} exibido
                  {produtos.length !== 1 ? "s" : ""}
                  {resumo?.total_produtos != null && resumo.total_produtos !== produtos.length
                    ? ` de ${resumo.total_produtos}`
                    : ""}
                </div>
              )}
            </section>
          </>
        )}
        <ClinicaBelezaRelatedLinks slug={slug} items={relatedLinks} />
      </ClinicaBelezaPageContent>

      {/* Modals */}
      {showProdutoModal && <ProdutoModal />}
      {showMovModal && movProduto && <MovimentacaoModal />}
      <EstoqueImportarXmlModal
        open={showImportXmlModal}
        onClose={() => setShowImportXmlModal(false)}
        onSuccess={loadAll}
      />

    </>
  );
}
