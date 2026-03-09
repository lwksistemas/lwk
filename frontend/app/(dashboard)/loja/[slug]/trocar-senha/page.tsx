'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { isTipoCRMVendas } from '@/lib/loja-tipo';

export default function TrocarSenhaLojaComSlugPage() {
  const router = useRouter();
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const [loading, setLoading] = useState(false);
  const [loadingInfo, setLoadingInfo] = useState(true);
  const [lojaId, setLojaId] = useState<number | null>(null);
  const [tipoLojaNome, setTipoLojaNome] = useState<string>('');
  const [formData, setFormData] = useState({
    nova_senha: '',
    confirmar_senha: '',
  });
  const [erro, setErro] = useState('');

  const loadLojaInfo = useCallback(async () => {
    if (!slug) {
      setErro('Informações da loja não encontradas. Faça login novamente.');
      setTimeout(() => router.push('/'), 2000);
      setLoadingInfo(false);
      return;
    }
    try {
      setLoadingInfo(true);
      const response = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
      setLojaId(response.data.id);
      setTipoLojaNome(response.data.tipo_loja_nome || '');
    } catch (error) {
      console.error('Erro ao carregar informações da loja:', error);
      setErro('Erro ao carregar informações. Faça login novamente.');
      setTimeout(() => router.push('/'), 2000);
    } finally {
      setLoadingInfo(false);
    }
  }, [slug, router]);

  useEffect(() => {
    loadLojaInfo();
  }, [loadLojaInfo]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
    setErro('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro('');

    if (formData.nova_senha.length < 6) {
      setErro('A senha deve ter no mínimo 6 caracteres');
      return;
    }

    if (formData.nova_senha !== formData.confirmar_senha) {
      setErro('As senhas não coincidem');
      return;
    }

    if (!lojaId) {
      setErro('ID da loja não encontrado');
      return;
    }

    setLoading(true);

    try {
      await apiClient.post(`/superadmin/lojas/${lojaId}/alterar_senha_primeiro_acesso/`, {
        nova_senha: formData.nova_senha,
        confirmar_senha: formData.confirmar_senha,
      });

      alert('✅ Senha alterada com sucesso!');
      const destino = tipoLojaNome && isTipoCRMVendas(tipoLojaNome)
        ? `/loja/${slug}/crm-vendas`
        : `/loja/${slug}/dashboard`;
      router.push(destino);
    } catch (error: any) {
      console.error('Erro ao alterar senha:', error);
      setErro(error.response?.data?.error || 'Erro ao alterar senha');
    } finally {
      setLoading(false);
    }
  };

  if (loadingInfo) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <div className="text-gray-500 dark:text-gray-400">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto py-8 px-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8 max-w-md w-full">
        <div className="text-center mb-8">
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-yellow-100 dark:bg-yellow-900/30 mb-4">
            <svg className="h-8 w-8 text-yellow-600 dark:text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Alterar Senha
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            Por segurança, altere sua senha periodicamente.
          </p>
        </div>

        {erro && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-3 mb-6">
            <p className="text-sm text-red-800 dark:text-red-300">{erro}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="nova_senha" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Nova Senha *
            </label>
            <input
              id="nova_senha"
              name="nova_senha"
              type="password"
              autoComplete="new-password"
              required
              minLength={6}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder:text-gray-500 dark:placeholder:text-gray-400 focus:ring-2 focus:ring-green-500 focus:border-green-500 dark:focus:ring-offset-gray-800"
              value={formData.nova_senha}
              onChange={handleChange}
              placeholder="Mínimo 6 caracteres"
            />
          </div>

          <div>
            <label htmlFor="confirmar_senha" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Confirmar Nova Senha *
            </label>
            <input
              id="confirmar_senha"
              name="confirmar_senha"
              type="password"
              autoComplete="new-password"
              required
              minLength={6}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder:text-gray-500 dark:placeholder:text-gray-400 focus:ring-2 focus:ring-green-500 focus:border-green-500 dark:focus:ring-offset-gray-800"
              value={formData.confirmar_senha}
              onChange={handleChange}
              placeholder="Digite a senha novamente"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
          >
            {loading ? 'Alterando...' : 'Alterar Senha'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Após alterar a senha, você será redirecionado para o CRM.
          </p>
        </div>
      </div>
    </div>
  );
}
