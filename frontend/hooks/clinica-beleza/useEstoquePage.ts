"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, usePathname, useRouter, useSearchParams } from "next/navigation";
import type {
  EstoqueCategoria,
  EstoqueMovimentacaoHistorico,
  EstoqueProduto,
  EstoqueResumo,
} from "@/components/clinica-beleza/estoque/estoque-types";
import { extractEstoqueApiError } from "@/components/clinica-beleza/estoque/estoque-types";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { useToast } from "@/components/ui/Toast";

export interface UseEstoquePageOptions {
  defaultCategoria?: string;
}

export type EstoqueViewMode = "categorias" | "lista";

export function useEstoquePage({ defaultCategoria = "" }: UseEstoquePageOptions = {}) {
  const toast = useToast();
  const params = useParams();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const slug = params.slug as string;

  const [resumo, setResumo] = useState<EstoqueResumo | null>(null);
  const [loadingResumo, setLoadingResumo] = useState(true);
  const [produtos, setProdutos] = useState<EstoqueProduto[]>([]);
  const [loadingProdutos, setLoadingProdutos] = useState(true);
  const [categorias, setCategorias] = useState<EstoqueCategoria[]>([]);
  const [loadingCategorias, setLoadingCategorias] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [categoriaFilter, setCategoriaFilter] = useState("");
  const [viewMode, setViewMode] = useState<EstoqueViewMode>("categorias");

  const [showProdutoModal, setShowProdutoModal] = useState(false);
  const [showImportXmlModal, setShowImportXmlModal] = useState(false);
  const [showCategoriasModal, setShowCategoriasModal] = useState(false);
  const [showHistoricoModal, setShowHistoricoModal] = useState(false);
  const [historicoProduto, setHistoricoProduto] = useState<EstoqueProduto | null>(null);
  const [historicoData, setHistoricoData] = useState<EstoqueMovimentacaoHistorico[]>([]);
  const [editingProduto, setEditingProduto] = useState<EstoqueProduto | null>(null);
  const [showMovModal, setShowMovModal] = useState(false);
  const [movProduto, setMovProduto] = useState<EstoqueProduto | null>(null);
  const [movTipo, setMovTipo] = useState<"entrada" | "saida">("entrada");
  const [saving, setSaving] = useState(false);

  const lojaCtx = useMemo(() => ({ slug }), [slug]);
  const loading = loadingResumo || loadingCategorias || (viewMode === "lista" && loadingProdutos);

  useEffect(() => {
    const cat = searchParams.get("categoria") || defaultCategoria;
    setCategoriaFilter(cat);
    if (cat) setViewMode("lista");
  }, [searchParams, defaultCategoria]);

  const setCategoriaFilterAndUrl = (value: string) => {
    setCategoriaFilter(value);
    if (value) setViewMode("lista");
    const qp = new URLSearchParams(searchParams.toString());
    if (value) qp.set("categoria", value);
    else qp.delete("categoria");
    const qs = qp.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
  };

  const selecionarCategoria = (cat: EstoqueCategoria) => {
    setViewMode("lista");
    setCategoriaFilterAndUrl(cat.slug);
  };

  const verTodos = () => {
    setViewMode("lista");
    setCategoriaFilterAndUrl("");
  };

  const voltarCategorias = () => {
    setViewMode("categorias");
    setCategoriaFilterAndUrl("");
  };

  const loadCategorias = useCallback(async () => {
    setLoadingCategorias(true);
    try {
      const data = await ClinicaBelezaAPI.estoque.categorias.list(lojaCtx);
      setCategorias(Array.isArray(data) ? (data as EstoqueCategoria[]) : []);
    } catch {
      setCategorias([]);
    } finally {
      setLoadingCategorias(false);
    }
  }, [lojaCtx]);

  const loadProdutos = useCallback(async () => {
    setLoadingProdutos(true);
    setListError(null);
    try {
      const apiParams: { categoria?: string; search?: string } = {};
      if (categoriaFilter) apiParams.categoria = categoriaFilter;
      if (searchTerm.trim()) apiParams.search = searchTerm.trim();
      const items = await ClinicaBelezaAPI.estoque.list(apiParams, lojaCtx);
      setProdutos(Array.isArray(items) ? (items as EstoqueProduto[]) : []);
    } catch (err) {
      setProdutos([]);
      setListError(extractEstoqueApiError(err, "Não foi possível carregar a lista."));
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
    await Promise.all([loadProdutos(), loadResumo(), loadCategorias()]);
    setLoadingResumo(false);
  }, [loadProdutos, loadResumo, loadCategorias]);

  useEffect(() => {
    void loadResumo();
    void loadCategorias();
  }, [loadResumo, loadCategorias]);

  useEffect(() => {
    if (viewMode !== "lista") return;
    const timer = setTimeout(() => {
      void loadProdutos();
    }, searchTerm ? 300 : 0);
    return () => clearTimeout(timer);
  }, [loadProdutos, searchTerm, viewMode]);

  const handleExcluirProduto = async (id: number, nome: string) => {
    if (!confirm(`Excluir "${nome}" do estoque?\n\nProdutos já usados em consultas finalizadas não podem ser excluídos.`)) {
      return;
    }
    try {
      await ClinicaBelezaAPI.estoque.delete(id);
      toast.success("Produto excluído.");
      await loadAll();
    } catch (err) {
      toast.error(extractEstoqueApiError(err, "Não foi possível excluir o produto."));
    }
  };

  const moverProduto = async (produtoId: number, categoriaId: number) => {
    try {
      await ClinicaBelezaAPI.estoque.mover({ produto_ids: [produtoId], categoria_id: categoriaId });
      toast.success("Produto movido.");
      await loadAll();
    } catch (err) {
      toast.error(extractEstoqueApiError(err, "Não foi possível mover o produto."));
    }
  };

  const abrirHistorico = async (produto: EstoqueProduto) => {
    setHistoricoProduto(produto);
    setHistoricoData([]);
    setShowHistoricoModal(true);
    try {
      const { clinicaBelezaFetch } = await import("@/lib/clinica-beleza-api");
      const res = await clinicaBelezaFetch(`/estoque/${produto.id}/movimentar/`);
      if (res.ok) {
        const data = await res.json();
        setHistoricoData(Array.isArray(data) ? data : []);
      }
    } catch {
      setHistoricoData([]);
    }
  };

  const abrirNovoProduto = () => {
    setEditingProduto(null);
    setSaveError(null);
    setShowProdutoModal(true);
  };

  const abrirEditarProduto = (produto: EstoqueProduto) => {
    setEditingProduto(produto);
    setSaveError(null);
    setShowProdutoModal(true);
  };

  const fecharProdutoModal = () => {
    setShowProdutoModal(false);
    setEditingProduto(null);
    setSaveError(null);
  };

  const abrirMovimentacao = (produto: EstoqueProduto, tipo: "entrada" | "saida") => {
    setMovProduto(produto);
    setMovTipo(tipo);
    setShowMovModal(true);
  };

  const fecharMovModal = () => {
    setShowMovModal(false);
    setMovProduto(null);
  };

  const salvarProduto = async (payload: Record<string, unknown>) => {
    setSaving(true);
    setSaveError(null);
    try {
      if (editingProduto) {
        await ClinicaBelezaAPI.estoque.update(editingProduto.id, payload, lojaCtx);
      } else {
        await ClinicaBelezaAPI.estoque.create(payload, lojaCtx);
      }
      fecharProdutoModal();
      await loadAll();
    } catch (err) {
      setSaveError(extractEstoqueApiError(err, "Não foi possível salvar o produto."));
    } finally {
      setSaving(false);
    }
  };

  const registrarMovimentacao = async (quantidade: number, motivo: string) => {
    if (!movProduto) return;
    setSaving(true);
    try {
      await ClinicaBelezaAPI.estoque.movimentar(movProduto.id, {
        tipo: movTipo,
        quantidade,
        motivo,
      });
      fecharMovModal();
      await loadAll();
    } finally {
      setSaving(false);
    }
  };

  const categoriaAtual = categorias.find((c) => c.slug === categoriaFilter) ?? null;

  return {
    slug,
    lojaCtx,
    resumo,
    produtos,
    categorias,
    loading,
    loadingCategorias,
    listError,
    saveError,
    searchTerm,
    setSearchTerm,
    categoriaFilter,
    setCategoriaFilterAndUrl,
    viewMode,
    selecionarCategoria,
    verTodos,
    voltarCategorias,
    categoriaAtual,
    showProdutoModal,
    showImportXmlModal,
    setShowImportXmlModal,
    showCategoriasModal,
    setShowCategoriasModal,
    showHistoricoModal,
    setShowHistoricoModal,
    historicoProduto,
    historicoData,
    editingProduto,
    showMovModal,
    movProduto,
    movTipo,
    saving,
    loadAll,
    loadCategorias,
    handleExcluirProduto,
    moverProduto,
    abrirHistorico,
    abrirNovoProduto,
    abrirEditarProduto,
    fecharProdutoModal,
    abrirMovimentacao,
    fecharMovModal,
    salvarProduto,
    registrarMovimentacao,
  };
}
