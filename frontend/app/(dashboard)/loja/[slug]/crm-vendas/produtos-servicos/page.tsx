/**
 * Página de Produtos e Serviços - Refatorada.
 * 
 * Segue Clean Code e React Best Practices:
 * - Componentes pequenos e focados
 * - Custom hooks para lógica de API
 * - Separação de responsabilidades
 * - Fácil de testar e manter
 */
'use client';

import { useEffect, useState } from 'react';
import SkeletonTable from '@/components/crm-vendas/SkeletonTable';
import { 
  useProdutosServicos, 
  useCategorias,
  ProdutoServico,
  FormData,
} from '@/hooks/useProdutosServicos';
import { ProdutoServicoFilters } from './components/ProdutoServicoFilters';
import { ProdutoServicoTable } from './components/ProdutoServicoTable';
import { ProdutoServicoModal } from './components/ProdutoServicoModal';
import { CategoriasModal } from './components/CategoriasModal';

type ModalType = 'create' | 'edit' | 'view' | 'delete' | null;

export default function CrmVendasProdutosServicosPage() {
  // Custom hooks para lógica de API
  const {
    itens,
    loading,
    error,
    loadItens,
    criarItem,
    atualizarItem,
    deletarItem,
  } = useProdutosServicos();

  const {
    categorias,
    loadCategorias,
    criarCategoria,
    atualizarCategoria,
    deletarCategoria,
  } = useCategorias();

  // Estados locais para UI
  const [modalType, setModalType] = useState<ModalType>(null);
  const [selected, setSelected] = useState<ProdutoServico | null>(null);
  const [filtroTipo, setFiltroTipo] = useState<string>('');
  const [filtroCategoria, setFiltroCategoria] = useState<string>('');
  const [modalCategoriasAberto, setModalCategoriasAberto] = useState(false);
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

  // Carregar dados iniciais
  useEffect(() => {
    loadCategorias();
    loadItens();
  }, [loadCategorias, loadItens]);

  // Recarregar quando filtros mudarem
  useEffect(() => {
    loadItens({ tipo: filtroTipo, categoria: filtroCategoria });
  }, [filtroTipo, filtroCategoria, loadItens]);

  /**
   * Abre modal com tipo e item específicos.
   */
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
      setFormData({
        tipo: 'produto',
        codigo: '',
        nome: '',
        descricao: '',
        categoria: null,
        preco: '0',
        ativo: true,
      });
    }
  };

  /**
   * Fecha modal e limpa estados.
   */
  const closeModal = () => {
    setModalType(null);
    setSelected(null);
  };

  /**
   * Atualiza dados do formulário.
   */
  const handleFormChange = (data: Partial<FormData>) => {
    setFormData((prev) => ({ ...prev, ...data }));
  };

  /**
   * Submete formulário (criar ou editar).
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.nome.trim()) {
      alert('Nome é obrigatório');
      return;
    }

    try {
      setSubmitting(true);

      if (modalType === 'create') {
        await criarItem(formData);
      } else if (modalType === 'edit' && selected) {
        await atualizarItem(selected.id, formData);
      }

      closeModal();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      alert(e.response?.data?.detail || 'Erro ao salvar.');
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Deleta item selecionado.
   */
  const handleDelete = async () => {
    if (!selected) return;

    try {
      setSubmitting(true);
      await deletarItem(selected.id);
      closeModal();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      alert(e.response?.data?.detail || 'Erro ao excluir.');
    } finally {
      setSubmitting(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-48 animate-pulse" />
          <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-40 animate-pulse" />
        </div>
        <SkeletonTable rows={5} columns={5} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filtros e botão Novo */}
      <ProdutoServicoFilters
        filtroCategoria={filtroCategoria}
        filtroTipo={filtroTipo}
        categorias={categorias}
        onCategoriaChange={setFiltroCategoria}
        onTipoChange={setFiltroTipo}
        onNovoClick={() => openModal('create')}
        onGerenciarCategoriasClick={() => setModalCategoriasAberto(true)}
      />

      {/* Mensagem de erro */}
      {error && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">
          {error}
        </div>
      )}

      {/* Tabela de produtos/serviços */}
      <ProdutoServicoTable
        itens={itens}
        onView={(item) => openModal('view', item)}
        onEdit={(item) => openModal('edit', item)}
        onDelete={(item) => openModal('delete', item)}
      />

      {/* Modal (criar/editar/visualizar/deletar) */}
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

      {/* Modal de Gerenciamento de Categorias */}
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
