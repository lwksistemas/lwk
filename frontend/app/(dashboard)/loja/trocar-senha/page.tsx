'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

export default function TrocarSenhaPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    nova_senha: '',
    confirmar_senha: '',
  });
  const [erro, setErro] = useState('');

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

    // Validações
    if (formData.nova_senha.length < 6) {
      setErro('A senha deve ter no mínimo 6 caracteres');
      return;
    }

    if (formData.nova_senha !== formData.confirmar_senha) {
      setErro('As senhas não coincidem');
      return;
    }

    setLoading(true);

    try {
      // Buscar informações da loja do localStorage (salvas no login)
      const lojaSlug = authService.getLojaSlug();
      
      if (!lojaSlug) {
        setErro('Informações da loja não encontradas. Faça login novamente.');
        router.push('/');
        return;
      }

      // Buscar ID da loja
      const lojaResponse = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${lojaSlug}`);
      const lojaId = lojaResponse.data.id;

      // Alterar senha
      await apiClient.post(`/superadmin/lojas/${lojaId}/alterar_senha_primeiro_acesso/`, {
        nova_senha: formData.nova_senha,
        confirmar_senha: formData.confirmar_senha,
      });

      alert('✅ Senha alterada com sucesso! Você será redirecionado para o dashboard.');
      
      // Redirecionar para o dashboard da loja específica
      router.push(`/loja/${lojaSlug}/dashboard`);
    } catch (error: any) {
      console.error('Erro ao alterar senha:', error);
      setErro(error.response?.data?.error || 'Erro ao alterar senha');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-green-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-yellow-100 mb-4">
            <svg className="h-8 w-8 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Alterar Senha Provisória
          </h1>
          <p className="text-sm text-gray-600">
            Por segurança, você precisa alterar sua senha provisória antes de continuar.
          </p>
        </div>

        {/* Alerta */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                Primeiro Acesso
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>
                  Esta é sua senha provisória. Por favor, escolha uma senha forte e única para proteger sua conta.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Formulário */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nova Senha *
            </label>
            <input
              type="password"
              name="nova_senha"
              value={formData.nova_senha}
              onChange={handleChange}
              required
              minLength={6}
              className="w-full px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
              placeholder="Mínimo 6 caracteres"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Confirmar Nova Senha *
            </label>
            <input
              type="password"
              name="confirmar_senha"
              value={formData.confirmar_senha}
              onChange={handleChange}
              required
              minLength={6}
              className="w-full px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
              placeholder="Digite a senha novamente"
            />
          </div>

          {/* Erro */}
          {erro && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-800">{erro}</p>
            </div>
          )}

          {/* Dicas de senha */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h4 className="text-sm font-medium text-blue-800 mb-2">
              💡 Dicas para uma senha forte:
            </h4>
            <ul className="text-xs text-blue-700 space-y-1">
              <li>• Use no mínimo 6 caracteres (recomendado: 8+)</li>
              <li>• Combine letras maiúsculas e minúsculas</li>
              <li>• Inclua números e símbolos</li>
              <li>• Não use informações pessoais óbvias</li>
              <li>• Não reutilize senhas de outros sites</li>
            </ul>
          </div>

          {/* Botão */}
          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {loading ? 'Alterando...' : 'Alterar Senha e Continuar'}
          </button>
        </form>

        {/* Footer */}
        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500">
            Após alterar a senha, você será redirecionado para o dashboard da sua loja.
          </p>
        </div>
      </div>
    </div>
  );
}
