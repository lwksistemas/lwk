'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

export default function TrocarSenhaLojaPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [loadingInfo, setLoadingInfo] = useState(true);
  const [lojaId, setLojaId] = useState<number | null>(null);
  const [lojaSlug, setLojaSlug] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    nova_senha: '',
    confirmar_senha: '',
  });
  const [erro, setErro] = useState('');

  const loadLojaInfo = useCallback(async () => {
    try {
      const slug = authService.getLojaSlug();
      if (!slug) {
        setErro('Informações da loja não encontradas. Faça login novamente.');
        setTimeout(() => router.push('/'), 2000);
        return;
      }
      setLojaSlug(slug);
      const response = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
      setLojaId(response.data.id);
    } catch (error) {
      console.error('Erro ao carregar informações da loja:', error);
      setErro('Erro ao carregar informações. Faça login novamente.');
      setTimeout(() => router.push('/'), 2000);
    } finally {
      setLoadingInfo(false);
    }
  }, [router]);

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
      router.push(`/loja/${lojaSlug}/dashboard`);
    } catch (error: any) {
      console.error('Erro ao alterar senha:', error);
      setErro(error.response?.data?.error || 'Erro ao alterar senha');
    } finally {
      setLoading(false);
    }
  };

  if (loadingInfo) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-green-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
        <div className="text-gray-600 dark:text-gray-400">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-green-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8 max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-yellow-100 dark:bg-yellow-900/30 mb-4">
            <svg className="h-8 w-8 text-yellow-600 dark:text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Alterar Senha Provisória
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            Por segurança, você precisa alterar sua senha provisória antes de continuar.
          </p>
        </div>

        {/* Alerta */}
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400 dark:text-yellow-500" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">Primeiro Acesso</h3>
              <p className="mt-1 text-sm text-yellow-700 dark:text-yellow-300">
                Esta é sua senha provisória. Escolha uma senha forte e única.
              </p>
            </div>
          </div>
        </div>

        {/* Formulário */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {erro && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-3">
              <p className="text-sm text-red-800 dark:text-red-300">{erro}</p>
            </div>
          )}

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

          {/* Dicas de senha */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-4">
            <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">
              Dicas para uma senha forte:
            </h4>
            <ul className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
              <li>• Use no mínimo 6 caracteres (recomendado: 8+)</li>
              <li>• Combine letras maiúsculas e minúsculas</li>
              <li>• Inclua números e símbolos</li>
              <li>• Não use informações pessoais</li>
            </ul>
          </div>

          {/* Botão */}
          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
          >
            {loading ? 'Alterando...' : 'Alterar Senha e Continuar'}
          </button>
        </form>

        {/* Footer */}
        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Após alterar a senha, você será redirecionado para o dashboard.
          </p>
        </div>
      </div>
    </div>
  );
}
