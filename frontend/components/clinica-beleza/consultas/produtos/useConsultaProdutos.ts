import { useCallback, useEffect, useMemo, useState } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { useToast } from "@/components/ui/Toast";
import type { CategoriaEstoque, ConsultaProdutoItem, ProdutoEstoque } from "./produtos-types";
import {
  avisoFormularioEstoque,
  extractProdutosError,
  listarAvisosEstoqueInsuficiente,
  totalPorProduto,
} from "./produtos-utils";

export function useConsultaProdutos(consultaId: number, onItensChanged?: () => void) {
  const toast = useToast();
  const [itens, setItens] = useState<ConsultaProdutoItem[]>([]);
  const [produtos, setProdutos] = useState<ProdutoEstoque[]>([]);
  const [categorias, setCategorias] = useState<CategoriaEstoque[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [produtoId, setProdutoId] = useState<number | "">("");
  const [quantidade, setQuantidade] = useState("1");
  const [lote, setLote] = useState("");
  const [validade, setValidade] = useState("");
  const [erro, setErro] = useState("");
  const [erroEstoque, setErroEstoque] = useState("");

  const carregar = useCallback(async () => {
    setLoading(true);
    setErroEstoque("");

    const listaPromise = ClinicaBelezaAPI.consultas.produtos
      .list(consultaId)
      .then((lista) => {
        setItens(Array.isArray(lista) ? lista : []);
      })
      .catch(() => {
        setItens([]);
      });

    const estoquePromise = ClinicaBelezaAPI.estoque
      .list()
      .then((estoque) => {
        setProdutos(Array.isArray(estoque) ? (estoque as ProdutoEstoque[]) : []);
      })
      .catch((err: unknown) => {
        setProdutos([]);
        setErroEstoque(extractProdutosError(err, "Não foi possível carregar os produtos do estoque."));
      });

    const categoriasPromise = ClinicaBelezaAPI.estoque.categorias
      .list()
      .then((cats) => {
        setCategorias(Array.isArray(cats) ? cats : []);
      })
      .catch(() => {
        setCategorias([]);
      });

    await Promise.all([listaPromise, estoquePromise, categoriasPromise]);
    setLoading(false);
  }, [consultaId]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const totaisConsulta = useMemo(() => totalPorProduto(itens), [itens]);

  const produtoSelecionado = produtoId ? produtos.find((x) => x.id === produtoId) : undefined;
  const qtdInformada = Number(quantidade) || 0;
  const qtdJaRegistrada = produtoId ? totaisConsulta.get(Number(produtoId)) || 0 : 0;
  const avisoFormulario = avisoFormularioEstoque(produtoSelecionado, qtdInformada, qtdJaRegistrada);

  const produtosComEstoqueInsuficiente = useMemo(
    () => listarAvisosEstoqueInsuficiente(itens, produtos, totaisConsulta),
    [itens, produtos, totaisConsulta],
  );

  const produtosPorCategoria = useMemo(() => {
    const map = new Map<number, { categoria: CategoriaEstoque; produtos: ProdutoEstoque[] }>();
    const semCategoria: ProdutoEstoque[] = [];

    for (const p of produtos) {
      const catId = p.categoria ?? 0;
      if (catId === 0) {
        semCategoria.push(p);
        continue;
      }
      const cat = categorias.find((c) => c.id === catId);
      if (!cat) {
        semCategoria.push(p);
        continue;
      }
      const entry = map.get(catId);
      if (entry) {
        entry.produtos.push(p);
      } else {
        map.set(catId, { categoria: cat, produtos: [p] });
      }
    }

    const sorted = Array.from(map.values()).sort((a, b) => {
      const ordemA = a.categoria.ordem ?? Number.MAX_SAFE_INTEGER;
      const ordemB = b.categoria.ordem ?? Number.MAX_SAFE_INTEGER;
      return ordemA - ordemB || a.categoria.nome.localeCompare(b.categoria.nome);
    });

    return { comCategoria: sorted, semCategoria };
  }, [produtos, categorias]);

  const onProdutoChange = (id: number | "") => {
    setProdutoId(id);
    if (!id) {
      setLote("");
      setValidade("");
      return;
    }
    const p = produtos.find((x) => x.id === id);
    if (p) {
      setLote(p.lote || "");
      setValidade(p.validade ? String(p.validade).slice(0, 10) : "");
    }
  };

  const resetFormulario = () => {
    setProdutoId("");
    setQuantidade("1");
    setLote("");
    setValidade("");
  };

  const adicionar = async () => {
    if (!produtoId) {
      setErro("Selecione um produto.");
      return;
    }
    const qtd = Number(quantidade);
    if (!qtd || qtd <= 0) {
      setErro("Informe a quantidade utilizada.");
      return;
    }
    if (avisoFormulario) {
      const continuar = confirm(
        `Estoque insuficiente:\n${avisoFormulario}\n\nDeseja registrar mesmo assim? A finalização da consulta ficará bloqueada até regularizar o estoque.`,
      );
      if (!continuar) return;
    }
    setSaving(true);
    setErro("");
    try {
      const res = (await ClinicaBelezaAPI.consultas.produtos.add(consultaId, {
        produto: Number(produtoId),
        quantidade: qtd,
        lote: lote.trim() || undefined,
        validade: validade || undefined,
      })) as { error?: string };
      if (res?.error) throw res;
      resetFormulario();
      await carregar();
      onItensChanged?.();
    } catch (e: unknown) {
      setErro(extractProdutosError(e, "Erro ao registrar produto."));
    } finally {
      setSaving(false);
    }
  };

  const remover = async (item: ConsultaProdutoItem) => {
    if (!confirm(`Remover ${item.produto_nome} da consulta?`)) return;
    setSaving(true);
    try {
      await ClinicaBelezaAPI.consultas.produtos.remove(consultaId, item.id);
      await carregar();
      onItensChanged?.();
    } catch {
      toast.error("Não foi possível remover o produto.");
    } finally {
      setSaving(false);
    }
  };

  return {
    itens,
    produtos,
    categorias,
    produtosPorCategoria,
    loading,
    saving,
    showAddForm,
    produtoId,
    quantidade,
    lote,
    validade,
    erro,
    erroEstoque,
    totaisConsulta,
    avisoFormulario,
    produtosComEstoqueInsuficiente,
    setShowAddForm,
    setQuantidade,
    setLote,
    setValidade,
    onProdutoChange,
    adicionar,
    remover,
  };
}
