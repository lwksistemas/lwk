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
  cor: string;
  ordem: number;
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

interface Filtros {
  tipo?: string;
  categoria?: string;
}

/**
 * Hook para gerenciar produtos e serviços.
 * 
 * @returns Objeto com estados e funções para gerenciar produtos/serviços
 */
export function useProdutosServicos() {
  const [itens, setItens] = useState<ProdutoServico[]>([]);
  const [loading, setLoading] = useState(true);
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
      if (filtros?.categoria) params.categoria = filtros.categoria;
      
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
  const criarItem = useCallback(async (data: FormData) => {
    const payload = {
      ...data,
      preco: parseFloat(data.preco) || 0,
    };
    await apiClient.post('/crm-vendas/produtos-servicos/', payload);
    await loadItens();
  }, [loadItens]);

  /**
   * Atualiza um produto/serviço existente.
   */
  const atualizarItem = useCallback(async (id: number, data: FormData) => {
    const payload = {
      ...data,
      preco: parseFloat(data.preco) || 0,
    };
    await apiClient.put(`/crm-vendas/produtos-servicos/${id}/`, payload);
    await loadItens();
  }, [loadItens]);

  /**
   * Deleta um produto/serviço.
   */
  const deletarItem = useCallback(async (id: number) => {
    await apiClient.delete(`/crm-vendas/produtos-servicos/${id}/`);
    await loadItens();
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
      console.log('Categorias carregadas:', cats);
      setCategorias(cats);
    } catch (err) {
      console.error('Erro ao carregar categorias:', err);
      setError('Erro ao carregar categorias');
      setCategorias([]);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    categorias,
    loading,
    error,
    loadCategorias,
  };
}
