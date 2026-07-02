'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import apiClient from '@/lib/api-client';
import { useToast } from '@/components/ui/Toast';
import {
  useProdutosServicos,
  useCategorias,
  type ProdutoServico,
  type FormData,
  type Filtros,
} from '@/hooks/useProdutosServicos';

export type ProdutoServicoModalType = 'create' | 'edit' | 'view' | 'delete' | null;

const EMPTY_FORM: FormData = {
  tipo: 'produto',
  codigo: '',
  nome: '',
  descricao: '',
  categoria: null,
  preco: '0',
  recorrencia: 'unico',
  ativo: true,
};

export function useCrmProdutosServicosPage() {
  const toast = useToast();
  const {
    itens,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading: loadingItens,
    error,
    loadItens,
    criarItem,
    atualizarItem,
    deletarItem,
  } = useProdutosServicos();

  const {
    categorias,
    loading: loadingCategorias,
    loadCategorias,
    criarCategoria,
    atualizarCategoria,
    deletarCategoria,
  } = useCategorias();

  const [viewMode, setViewMode] = useState<'categorias' | 'lista'>('categorias');
  const [modalType, setModalType] = useState<ProdutoServicoModalType>(null);
  const [selected, setSelected] = useState<ProdutoServico | null>(null);
  const [filtroTipo, setFiltroTipo] = useState('');
  const [filtroCategoria, setFiltroCategoria] = useState('');
  const [modalCategoriasAberto, setModalCategoriasAberto] = useState(false);
  const [countSemCategoria, setCountSemCategoria] = useState<number | null>(null);
  const [formData, setFormData] = useState<FormData>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);

  const buildFiltrosLista = useCallback((): Filtros => {
    const f: Filtros = {};
    if (filtroTipo) f.tipo = filtroTipo;
    if (filtroCategoria === '__sem__') f.semCategoria = true;
    else if (filtroCategoria) f.categoria = filtroCategoria;
    return f;
  }, [filtroTipo, filtroCategoria]);

  useEffect(() => {
    loadCategorias();
  }, [loadCategorias]);

  useEffect(() => {
    if (viewMode !== 'categorias') return;
    let cancelled = false;
    apiClient
      .get('/crm-vendas/produtos-servicos/?sem_categoria=true&page_size=1')
      .then((res) => {
        const d = res.data as { count?: number; results?: unknown[] };
        if (cancelled) return;
        setCountSemCategoria(
          typeof d.count === 'number' ? d.count : Array.isArray(d.results) ? d.results.length : 0,
        );
      })
      .catch(() => {
        if (!cancelled) setCountSemCategoria(0);
      });
    return () => {
      cancelled = true;
    };
  }, [viewMode, categorias]);

  useEffect(() => {
    if (viewMode !== 'lista') return;
    if (filtroCategoria === '__sem__') {
      loadItens({ tipo: filtroTipo, semCategoria: true });
    } else {
      loadItens({ tipo: filtroTipo, categoria: filtroCategoria });
    }
  }, [viewMode, filtroTipo, filtroCategoria, loadItens]);

  const subtituloLista = useMemo(() => {
    if (filtroCategoria === '__sem__') return 'Itens sem categoria';
    if (filtroCategoria) {
      const c = categorias.find((x) => String(x.id) === filtroCategoria);
      return c ? `Categoria: ${c.nome}` : undefined;
    }
    return 'Todos os produtos e serviços';
  }, [filtroCategoria, categorias]);

  const openModal = (type: ProdutoServicoModalType, item?: ProdutoServico) => {
    setModalType(type);
    setSelected(item || null);

    if (type === 'edit' && item) {
      setFormData({
        tipo: item.tipo,
        codigo: item.codigo || '',
        nome: item.nome || '',
        descricao: item.descricao || '',
        categoria: item.categoria || null,
        preco: item.preco || '0',
        recorrencia: item.recorrencia || 'unico',
        ativo: item.ativo ?? true,
      });
    } else if (type === 'create') {
      let cid: number | null = null;
      if (filtroCategoria && filtroCategoria !== '__sem__') {
        const n = parseInt(filtroCategoria, 10);
        if (Number.isFinite(n)) cid = n;
      }
      setFormData({ ...EMPTY_FORM, categoria: cid });
    }
  };

  const closeModal = () => {
    setModalType(null);
    setSelected(null);
  };

  const handleFormChange = (data: Partial<FormData>) => {
    setFormData((prev) => ({ ...prev, ...data }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.nome.trim()) {
      toast.warning('Nome é obrigatório');
      return;
    }

    try {
      setSubmitting(true);
      const filtrosReload = viewMode === 'lista' ? buildFiltrosLista() : undefined;

      if (modalType === 'create') {
        await criarItem(formData, filtrosReload);
      } else if (modalType === 'edit' && selected) {
        await atualizarItem(selected.id, formData, filtrosReload);
      }

      await loadCategorias();
      closeModal();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || 'Erro ao salvar.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selected) return;

    try {
      setSubmitting(true);
      const filtrosReload = viewMode === 'lista' ? buildFiltrosLista() : undefined;
      await deletarItem(selected.id, filtrosReload);
      await loadCategorias();
      closeModal();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || 'Erro ao excluir.');
    } finally {
      setSubmitting(false);
    }
  };

  const irParaCategoria = (id: number) => {
    setFiltroCategoria(String(id));
    setFiltroTipo('');
    setViewMode('lista');
  };

  const irSemCategoria = () => {
    setFiltroCategoria('__sem__');
    setFiltroTipo('');
    setViewMode('lista');
  };

  const irVerTodos = () => {
    setFiltroCategoria('');
    setFiltroTipo('');
    setViewMode('lista');
  };

  const voltarCategorias = () => {
    setViewMode('categorias');
    setFiltroCategoria('');
    setFiltroTipo('');
  };

  return {
    viewMode,
    loadingCategorias,
    loadingItens,
    error,
    categorias,
    itens,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    filtroTipo,
    setFiltroTipo,
    filtroCategoria,
    setFiltroCategoria,
    countSemCategoria,
    subtituloLista,
    modalType,
    selected,
    formData,
    submitting,
    modalCategoriasAberto,
    setModalCategoriasAberto,
    openModal,
    closeModal,
    handleFormChange,
    handleSubmit,
    handleDelete,
    irParaCategoria,
    irSemCategoria,
    irVerTodos,
    voltarCategorias,
    criarCategoria,
    atualizarCategoria,
    deletarCategoria,
  };
}
