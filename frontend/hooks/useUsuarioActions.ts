'use client';

import { useState } from 'react';
import apiClient from '@/lib/api-client';

export interface UsuarioFormData {
  username: string;
  email: string;
  password?: string;
  first_name: string;
  last_name: string;
  tipo: string;
  cpf: string;
  telefone: string;
  pode_criar_lojas: boolean;
  pode_gerenciar_financeiro: boolean;
  pode_acessar_todas_lojas: boolean;
}

export interface UsuarioPayload {
  tipo: string;
  cpf: string;
  telefone: string;
  pode_criar_lojas: boolean;
  pode_gerenciar_financeiro: boolean;
  pode_acessar_todas_lojas: boolean;
  user: {
    username?: string;
    email: string;
    first_name: string;
    last_name: string;
    password?: string;
  };
}

export interface Usuario {
  id: number;
  user: {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    is_active: boolean;
  };
  tipo: string;
  tipo_display: string;
  cpf: string;
  telefone: string;
  foto: string;
  pode_criar_lojas: boolean;
  pode_gerenciar_financeiro: boolean;
  pode_acessar_todas_lojas: boolean;
  is_active: boolean;
  created_at: string;
}

export function useUsuarioActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const criarUsuario = async (data: UsuarioFormData) => {
    setLoading(true);
    setError(null);
    try {
      const payload: UsuarioPayload = {
        tipo: data.tipo,
        cpf: data.cpf,
        telefone: data.telefone,
        pode_criar_lojas: data.pode_criar_lojas,
        pode_gerenciar_financeiro: data.pode_gerenciar_financeiro,
        pode_acessar_todas_lojas: data.pode_acessar_todas_lojas,
        user: {
          username: data.username,
          email: data.email,
          first_name: data.first_name,
          last_name: data.last_name,
        }
      };

      const response = await apiClient.post('/superadmin/usuarios/', payload);
      return response.data as { senha_provisoria?: string };
    } catch (err) {
      const errorObj = err && typeof err === 'object' ? (err as Record<string, unknown>) : null;
      const response = errorObj?.response as Record<string, unknown> | undefined;
      const errData = response?.data;
      const errorMsg =
        (typeof errData === 'object' && errData !== null ? (errData as { error?: string }).error : null) ||
        (typeof errData === 'string' ? errData : null) ||
        'Erro ao criar usuário';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const atualizarUsuario = async (id: number, data: UsuarioFormData) => {
    setLoading(true);
    setError(null);
    try {
      const payload: UsuarioPayload = {
        tipo: data.tipo,
        cpf: data.cpf,
        telefone: data.telefone,
        pode_criar_lojas: data.pode_criar_lojas,
        pode_gerenciar_financeiro: data.pode_gerenciar_financeiro,
        pode_acessar_todas_lojas: data.pode_acessar_todas_lojas,
        user: {
          email: data.email,
          first_name: data.first_name,
          last_name: data.last_name,
        }
      };

      // Só incluir senha se foi preenchida
      if (data.password) {
        payload.user.password = data.password;
      }

      await apiClient.put(`/superadmin/usuarios/${id}/`, payload);
      return true;
    } catch (err) {
      const errorObj = err && typeof err === 'object' ? (err as Record<string, unknown>) : null;
      const response = errorObj?.response as Record<string, unknown> | undefined;
      const errData = response?.data;
      const errorMsg =
        (typeof errData === 'object' && errData !== null ? (errData as { error?: string }).error : null) ||
        (typeof errData === 'string' ? errData : null) ||
        'Erro ao atualizar usuário';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const excluirUsuario = async (usuario: Usuario) => {
    setLoading(true);
    setError(null);
    try {
      await apiClient.delete(`/superadmin/usuarios/${usuario.id}/`);
      return true;
    } catch (err) {
      const errorObj = err && typeof err === 'object' ? (err as Record<string, unknown>) : null;
      const response = errorObj?.response as Record<string, unknown> | undefined;
      const errData = response?.data;
      const errorMsg =
        (typeof errData === 'object' && errData !== null ? (errData as { error?: string }).error : null) ||
        (typeof errData === 'string' ? errData : null) ||
        'Erro ao excluir usuário';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const toggleStatus = async (usuario: Usuario) => {
    setLoading(true);
    setError(null);
    try {
      const novoStatus = !usuario.is_active;
      await apiClient.patch(`/superadmin/usuarios/${usuario.id}/`, {
        is_active: novoStatus
      });
      return novoStatus;
    } catch (err) {
      const errorObj = err && typeof err === 'object' ? (err as Record<string, unknown>) : null;
      const response = errorObj?.response as Record<string, unknown> | undefined;
      const errData = response?.data;
      const errorMsg =
        (typeof errData === 'object' && errData !== null ? (errData as { error?: string }).error : null) ||
        (typeof errData === 'string' ? errData : null) ||
        'Erro ao alterar status';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return {
    criarUsuario,
    atualizarUsuario,
    excluirUsuario,
    toggleStatus,
    loading,
    error,
  };
}
