"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, usePathname, useRouter, useSearchParams } from "next/navigation";
import type {
  EstoqueMovimentacaoHistorico,
  EstoqueProduto,
  EstoqueResumo,
} from "@/components/clinica-beleza/estoque/estoque-types";
import { extractEstoqueApiError } from "@/components/clinica-beleza/estoque/estoque-types";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";

export interface UseEstoquePageOptions {
  defaultCategoria?: string;
}

export function useEstoquePage({ defaultCategoria = "" }: UseEstoquePageOptions = {}) {
  const params = useParams();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const slug = params.slug as string;

  const [resumo, setResumo] = useState<EstoqueResumo | null>(null);
  const [loadingResumo, setLoadingResumo] = useState(true);
  const [produtos, setProdutos] = useState<EstoqueProduto[]>([]);
  const [loadingProdutos, setLoadingProdutos] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [categoriaFilter, setCategoriaFilter] = useState("");

  const [showProdutoModal, setShowProdutoModal] = useState(false);
  const [showImportXmlModal, setShowImportXmlModal] = useState(false);
  const [showHistoricoModal, setShowHistoricoModal] = useState(false);
  const [historicoProduto, setHistoricoProduto] = useState<EstoqueProduto | null>(null);
  const [historicoData, setHistoricoData] = useState<EstoqueMovimentacaoHistorico[]>([]);
  const [editingProduto, setEditingProduto] = useState<EstoqueProduto | null>(null);
  const [showMovModal, setShowMovModal] = useState(false);
  const [movProduto, setMovProduto] = useState<EstoqueProduto | null>(null);
  const [movTipo, setMovTipo] = useState<"entrada" | "saida">("entrada");
  const [saving, setSaving] = useState(false);

  const lojaCtx = useMemo(() => ({ slug }), [slug]);
  const loading = loadingResumo || loadingProdutos;

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

  const handleExcluirProduto = async (id: number, nome: string) => {
    if (!confirm(`Excluir "${nome}" do estoque? Esta ação não pode ser desfeita.`)) return;
    try {
      await ClinicaBelezaAPI.estoque.delete(id);
      await loadAll();
    } catch {
      alert("Erro ao excluir produto.");
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

  return {
    slug,
    resumo,
    produtos,
    loading,
    listError,
    saveError,
    searchTerm,
    setSearchTerm,
    categoriaFilter,
    setCategoriaFilterAndUrl,
    showProdutoModal,
    showImportXmlModal,
    setShowImportXmlModal,
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
    handleExcluirProduto,
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

export type UseEstoquePageReturn = ReturnType<typeof useEstoquePage>;
