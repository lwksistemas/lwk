import { useState } from 'react';
import apiClient from '@/lib/api-client';
import { extractArrayData, formatApiError } from '@/lib/api-helpers';

interface UseFuncionariosOptions {
  endpoint: string;
  onError?: (error: any) => void;
}

interface Funcionario {
  id: number;
  nome: string;
  telefone: string;
  email?: string;
  cargo: string;
  funcao: string;
  funcao_display?: string;
  especialidade?: string;
  is_active: boolean;
  is_admin?: boolean;
}

/**
 * Hook reutilizável para gerenciar funcionários
 * Segue boas práticas: DRY, Single Responsibility, Error Handling
 */
export function useFuncionarios({ endpoint, onError }: UseFuncionariosOptions) {
  const [funcionarios, setFuncionarios] = useState<Funcionario[]>([]);
  const [loading, setLoading] = useState(true);

  const carregar = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get(endpoint);
      const data = extractArrayData<Funcionario>(response);
      setFuncionarios(data);
      return data;
    } catch (error) {
      console.error('Erro ao carregar funcionários:', error);
      if (onError) {
        onError(error);
      } else {
        alert(formatApiError(error));
      }
      setFuncionarios([]);
      return [];
    } finally {
      setLoading(false);
    }
  };

  const criar = async (data: Partial<Funcionario>) => {
    try {
      await apiClient.post(endpoint, data);
      await carregar();
      return true;
    } catch (error) {
      console.error('Erro ao criar funcionário:', error);
      if (onError) {
        onError(error);
      } else {
        alert(formatApiError(error));
      }
      return false;
    }
  };

  const atualizar = async (id: number, data: Partial<Funcionario>) => {
    try {
      await apiClient.put(`${endpoint}${id}/`, data);
      await carregar();
      return true;
    } catch (error) {
      console.error('Erro ao atualizar funcionário:', error);
      if (onError) {
        onError(error);
      } else {
        alert(formatApiError(error));
      }
      return false;
    }
  };

  const excluir = async (id: number) => {
    try {
      await apiClient.delete(`${endpoint}${id}/`);
      await carregar();
      return true;
    } catch (error) {
      console.error('Erro ao excluir funcionário:', error);
      if (onError) {
        onError(error);
      } else {
        alert(formatApiError(error));
      }
      return false;
    }
  };

  return {
    funcionarios,
    loading,
    carregar,
    criar,
    atualizar,
    excluir,
  };
}
