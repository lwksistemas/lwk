/**
 * Página de Produtos e Serviços — grade de categorias e lista filtrada.
 */
'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import apiClient from '@/lib/api-client';
import SkeletonTable from '@/components/crm-vendas/SkeletonTable';
import {
  useProdutosServicos,
  useCategorias,
  ProdutoServico,
  FormData,
  Filtros,
} from '@/hooks/useProdutosServicos';
import { ProdutoServicoFilters } from './components/ProdutoServicoFilters';
import { ProdutoServicoTable } from './components/ProdutoServicoTable';
import { ProdutoServicoModal } from './components/ProdutoServicoModal';
import { CategoriasModal } from './components/CategoriasModal';
import { CategoriasProdutosGrid } from './components/CategoriasProdutosGrid';

type ModalType = 'create' | 'edit' | 'view' | 'delete' | null;

export default function CrmVendasProdutosServicosPage() {
  const {
    itens,
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
  const [modalType, setModalType] = useState<ModalType>(null);
  const [selected, setSelected] = useState<ProdutoServico | null>(null);
  const [filtroTipo, setFiltroTipo] = useState('');
  const [filtroCategoria, setFiltroCategoria] = useState('');
  const [modalCategoriasAberto, setModalCategoriasAberto] = useState(false);
  const [countSemCategoria, setCountSemCategoria] = useState<number | null>(null);
  const [formData, setFormData] = useState<FormData>({
    tipo: 'produto',
    codigo: '',
    nome: '',
    descricao: '',
    categoria: null,
    preco: '0',
    ativo: true,
  });
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
          typeof d.count === 'number' ? d.count : Array.isArray(d.results) ? d.results.length : 0
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

  const openModal = (type: ModalType, item?: ProdutoServico) => {
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
        ativo: item.ativo ?? true,
      });
    } else if (type === 'create') {
      let cid: number | null = null;
      if (filtroCategoria && filtroCategoria !== '__sem__') {
        const n = parseInt(filtroCategoria, 10);
        if (Number.isFinite(n)) cid = n;
      }
      setFormData({
        tipo: 'produto',
        codigo: '',
        nome: '',
        descricao: '',
        categoria: cid,
        preco: '0',
        ativo: true,
      });
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
      alert('Nome é obrigatório');
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
      alert(e.response?.data?.detail || 'Erro ao salvar.');
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
      alert(e.response?.data?.detail || 'Erro ao excluir.');
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

  if (viewMode === 'categorias' && loadingCategorias) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-48 animate-pulse" />
          <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-40 animate-pulse" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="h-32 rounded-xl bg-gray-100 dark:bg-gray-800 animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <ProdutoServicoFilters
        variant={viewMode === 'categorias' ? 'grid' : 'lista'}
        filtroCategoria={filtroCategoria}
        filtroTipo={filtroTipo}
        categorias={categorias}
        onCategoriaChange={setFiltroCategoria}
        onTipoChange={setFiltroTipo}
        onNovoClick={() => openModal('create')}
        onGerenciarCategoriasClick={() => setModalCategoriasAberto(true)}
        onVoltarCategorias={voltarCategorias}
        subtituloLista={subtituloLista}
      />

      {error && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">
          {error}
        </div>
      )}

      {viewMode === 'categorias' ? (
        <CategoriasProdutosGrid
          categorias={categorias}
          countSemCategoria={countSemCategoria}
          onSelectCategoria={irParaCategoria}
          onSelectSemCategoria={irSemCategoria}
          onVerTodos={irVerTodos}
        />
      ) : loadingItens ? (
        <SkeletonTable rows={5} columns={5} />
      ) : (
        <ProdutoServicoTable
          itens={itens}
          onView={(item) => openModal('view', item)}
          onEdit={(item) => openModal('edit', item)}
          onDelete={(item) => openModal('delete', item)}
        />
      )}

      <ProdutoServicoModal
        modalType={modalType}
        selected={selected}
        formData={formData}
        categorias={categorias}
        submitting={submitting}
        onClose={closeModal}
        onFormChange={handleFormChange}
        onSubmit={handleSubmit}
        onDelete={handleDelete}
      />

      <CategoriasModal
        isOpen={modalCategoriasAberto}
        categorias={categorias}
        onClose={() => setModalCategoriasAberto(false)}
        onCriar={criarCategoria}
        onEditar={atualizarCategoria}
        onExcluir={deletarCategoria}
      />
    </div>
  );
}
