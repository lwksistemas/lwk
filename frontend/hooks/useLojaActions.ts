/**
 * Hook customizado para ações de lojas (criar, editar, excluir)
 * Centraliza lógica de negócio e tratamento de erros
 */
import { useState } from 'react';
import apiClient from '@/lib/api-client';

interface Loja {
  id: number;
  nome: string;
  slug: string;
  owner_username: string;
  owner_email: string;
  database_created: boolean;
}

interface ExclusaoDetalhes {
  loja_nome: string;
  loja_removida: boolean;
  banco_dados?: {
    existia: boolean;
    nome?: string;
    arquivo_removido?: boolean;
  };
  dados_financeiros?: {
    financeiro_removido?: boolean;
    pagamentos_removidos?: number;
  };
  usuario_proprietario?: {
    username?: string;
    removido?: boolean;
    motivo_nao_removido?: string;
  };
  suporte?: {
    chamados_removidos?: number;
    respostas_removidas?: number;
  };
  logs_auditoria?: {
    logs_removidos?: number;
    alertas_removidos?: number;
  };
}

export function useLojaActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const excluirLoja = async (loja: Loja): Promise<{ success: boolean; message: string }> => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.delete(`/superadmin/lojas/${loja.id}/`);
      
      // Verificar se a resposta tem detalhes
      if (!response.data || !response.data.detalhes) {
        return {
          success: true,
          message: `✅ Loja "${loja.nome}" foi removida com sucesso!`
        };
      }
      
      // Construir mensagem detalhada
      const detalhes: ExclusaoDetalhes = response.data.detalhes;
      const mensagens: string[] = [
        `✅ Loja "${detalhes.loja_nome || loja.nome}" foi completamente removida!`,
        '',
        '📋 Detalhes da limpeza:'
      ];
      
      // Banco de dados
      if (detalhes.banco_dados?.existia) {
        mensagens.push(`• Banco de dados: ✅ Removido (${detalhes.banco_dados.nome})`);
      }
      
      // Dados financeiros
      if (detalhes.dados_financeiros?.financeiro_removido) {
        mensagens.push('• Dados financeiros: ✅ Removidos');
      }
      if (detalhes.dados_financeiros?.pagamentos_removidos) {
        mensagens.push(`• Pagamentos: ✅ ${detalhes.dados_financeiros.pagamentos_removidos} registro(s)`);
      }
      
      // Suporte
      if (detalhes.suporte?.chamados_removidos) {
        mensagens.push(`• Chamados de suporte: ✅ ${detalhes.suporte.chamados_removidos} removido(s)`);
      }
      
      // Logs e alertas
      if (detalhes.logs_auditoria?.logs_removidos) {
        mensagens.push(`• Logs de auditoria: ✅ ${detalhes.logs_auditoria.logs_removidos} removido(s)`);
      }
      if (detalhes.logs_auditoria?.alertas_removidos) {
        mensagens.push(`• Alertas de segurança: ✅ ${detalhes.logs_auditoria.alertas_removidos} removido(s)`);
      }
      
      // Usuário proprietário
      if (detalhes.usuario_proprietario?.removido) {
        mensagens.push(`• Usuário: ✅ Removido (${detalhes.usuario_proprietario.username})`);
      } else if (detalhes.usuario_proprietario?.motivo_nao_removido) {
        mensagens.push(`• Usuário: ℹ️ ${detalhes.usuario_proprietario.motivo_nao_removido}`);
      }
      
      mensagens.push('', '🎯 Limpeza 100% completa!');
      
      return {
        success: true,
        message: mensagens.join('\n')
      };
      
    } catch (err: any) {
      console.error('Erro ao excluir loja:', err);
      
      // 404 = loja já foi excluída
      if (err.response?.status === 404) {
        return {
          success: true,
          message: 'ℹ️ Esta loja já foi excluída ou não existe.'
        };
      }
      
      // Construir mensagem de erro
      let mensagemErro = '❌ Erro ao excluir loja:\n\n';
      
      if (err.response?.data?.error) {
        mensagemErro += err.response.data.error;
      } else if (err.message) {
        mensagemErro += err.message;
      } else {
        mensagemErro += 'Erro desconhecido';
      }
      
      if (err.response?.data?.detalhes) {
        mensagemErro += '\n\n' + err.response.data.detalhes;
      }
      
      setError(mensagemErro);
      return {
        success: false,
        message: mensagemErro
      };
      
    } finally {
      setLoading(false);
    }
  };

  const reenviarSenha = async (loja: Loja): Promise<{ success: boolean; message: string }> => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.post(`/superadmin/lojas/${loja.id}/reenviar_senha/`);
      return {
        success: true,
        message: `✅ ${response.data.message}`
      };
    } catch (err: any) {
      console.error('Erro ao reenviar senha:', err);
      const mensagemErro = `❌ Erro ao reenviar senha: ${err.response?.data?.error || 'Erro desconhecido'}`;
      setError(mensagemErro);
      return {
        success: false,
        message: mensagemErro
      };
    } finally {
      setLoading(false);
    }
  };

  const criarBanco = async (lojaId: number): Promise<{ success: boolean; message: string; data?: any }> => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.post(`/superadmin/lojas/${lojaId}/criar_banco/`);
      return {
        success: true,
        message: `✅ Banco criado com sucesso!\n\nUsuário: ${response.data.admin_username}\nSenha: ${response.data.admin_password}`,
        data: response.data
      };
    } catch (err: any) {
      console.error('Erro ao criar banco:', err);
      const mensagemErro = `❌ Erro: ${err.response?.data?.error || 'Erro ao criar banco'}`;
      setError(mensagemErro);
      return {
        success: false,
        message: mensagemErro
      };
    } finally {
      setLoading(false);
    }
  };

  return {
    excluirLoja,
    reenviarSenha,
    criarBanco,
    loading,
    error,
    clearError: () => setError(null)
  };
}
