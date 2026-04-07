/**
 * Custom Hook para gerenciar Produtos e Serviços.
 * 
 * Segue React Best Practices:
 * - Encapsula lógica de API
 * - Promove reutilização
 * - Facilita testes
 */
import { useState, useCallback } from 'react';
import apiClient from '@/lib/api-client';
import { normalizeListResponse } from '@/lib/crm-utils';

export interface ProdutoServico {
  id: number;
  tipo: 'produto' | 'servico';
  codigo: string;
  nome: string;
  descricao: string;
  categoria: number | null;
  categoria_nome?: string;
  categoria_cor?: string;
  preco: string;
  ativo: boolean;
  created_at: string;
}

export interface Categoria {
  id: number;
  nome: string;
  descricao?: string;
  cor: string;
  ordem: number;
  /** Quantidade de produtos/serviços ativos (API) */
  produtos_count?: number;
}

export interface FormData {
  tipo: 'produto' | 'servico';
  codigo: string;
  nome: string;
  descricao: string;
  categoria: number | null;
  preco: string;
  ativo: boolean;
}

export interface Filtros {
  tipo?: string;
  /** ID da categoria ou vazio para todos (exceto quando semCategoria) */
  categoria?: string;
  /** Itens sem categoria (mutuamente exclusivo com categoria numérica) */
  semCategoria?: boolean;
}

/**
 * Hook para gerenciar produtos e serviços.
 * 
 * @returns Objeto com estados e funções para gerenciar produtos/serviços
 */
export function useProdutosServicos() {
  const [itens, setItens] = useState<ProdutoServico[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Carrega lista de produtos/serviços com filtros opcionais.
   */
  const loadItens = useCallback(async (filtros?: Filtros) => {
    try {
      setLoading(true);
      setError(null);
      
      const params: Record<string, string> = {};
      if (filtros?.tipo) params.tipo = filtros.tipo;
      if (filtros?.semCategoria) params.sem_categoria = 'true';
      else if (filtros?.categoria) params.categoria = filtros.categoria;

      const query = new URLSearchParams(params).toString();
      const url = query 
        ? `/crm-vendas/produtos-servicos/?${query}` 
        : '/crm-vendas/produtos-servicos/';
      
      const res = await apiClient.get<ProdutoServico[] | { results: ProdutoServico[] }>(url);
      setItens(normalizeListResponse(res.data));
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || 'Erro ao carregar produtos e serviços.');
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Cria um novo produto/serviço.
   */
  const criarItem = useCallback(async (data: FormData, filtros?: Filtros) => {
    const payload = {
      ...data,
      preco: parseFloat(data.preco) || 0,
    };
    await apiClient.post('/crm-vendas/produtos-servicos/', payload);
    if (filtros !== undefined) await loadItens(filtros);
  }, [loadItens]);

  /**
   * Atualiza um produto/serviço existente.
   */
  const atualizarItem = useCallback(async (id: number, data: FormData, filtros?: Filtros) => {
    const payload = {
      ...data,
      preco: parseFloat(data.preco) || 0,
    };
    await apiClient.put(`/crm-vendas/produtos-servicos/${id}/`, payload);
    if (filtros !== undefined) await loadItens(filtros);
  }, [loadItens]);

  /**
   * Deleta um produto/serviço.
   */
  const deletarItem = useCallback(async (id: number, filtros?: Filtros) => {
    await apiClient.delete(`/crm-vendas/produtos-servicos/${id}/`);
    if (filtros !== undefined) await loadItens(filtros);
  }, [loadItens]);

  return {
    itens,
    loading,
    error,
    loadItens,
    criarItem,
    atualizarItem,
    deletarItem,
  };
}

/**
 * Hook para gerenciar categorias de produtos/serviços.
 */
export function useCategorias() {
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Carrega lista de categorias ativas.
   */
  const loadCategorias = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const res = await apiClient.get<Categoria[] | { results: Categoria[] }>(
        '/crm-vendas/categorias-produtos-servicos/?ativo=true'
      );
      const cats = normalizeListResponse(res.data);
      setCategorias(cats);
    } catch (err) {
      console.error('Erro ao carregar categorias:', err);
      setError('Erro ao carregar categorias');
      setCategorias([]);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Cria uma nova categoria.
   */
  const criarCategoria = useCallback(async (data: { nome: string; descricao: string; cor: string }) => {
    await apiClient.post('/crm-vendas/categorias-produtos-servicos/', {
      ...data,
      ativo: true,
      ordem: 0,
    });
    await loadCategorias();
  }, [loadCategorias]);

  /**
   * Atualiza uma categoria existente.
   */
  const atualizarCategoria = useCallback(async (id: number, data: { nome: string; descricao: string; cor: string }) => {
    await apiClient.put(`/crm-vendas/categorias-produtos-servicos/${id}/`, {
      ...data,
      ativo: true,
    });
    await loadCategorias();
  }, [loadCategorias]);

  /**
   * Deleta uma categoria.
   */
  const deletarCategoria = useCallback(async (id: number) => {
    await apiClient.delete(`/crm-vendas/categorias-produtos-servicos/${id}/`);
    await loadCategorias();
  }, [loadCategorias]);

  return {
    categorias,
    loading,
    error,
    loadCategorias,
    criarCategoria,
    atualizarCategoria,
    deletarCategoria,
  };
}
