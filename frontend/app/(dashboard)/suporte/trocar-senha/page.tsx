'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';

export default function TrocarSenhaSuportePage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    nova_senha: '',
    confirmar_senha: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.nova_senha !== formData.confirmar_senha) {
      setError('As senhas não coincidem');
      return;
    }

    if (formData.nova_senha.length < 6) {
      setError('A senha deve ter no mínimo 6 caracteres');
      return;
    }

    setLoading(true);

    try {
      await apiClient.post('/superadmin/usuarios/alterar_senha_primeiro_acesso/', {
        nova_senha: formData.nova_senha,
        confirmar_senha: formData.confirmar_senha
      });

      alert('✅ Senha alterada com sucesso!');
      router.push('/suporte/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao alterar senha');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 to-cyan-900 p-4">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-2xl">
        <div>
          <div className="mx-auto h-16 w-16 bg-blue-600 rounded-full flex items-center justify-center">
            <svg className="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
            </svg>
          </div>
          <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
            Trocar Senha
          </h2>
          <p className="mt-2 text-center text-gray-600">
            Por segurança, altere sua senha provisória
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="nova_senha" className="block text-sm font-medium text-gray-700">
                Nova Senha *
              </label>
              <input
                id="nova_senha"
                type="password"
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={formData.nova_senha}
                onChange={(e) => setFormData({ ...formData, nova_senha: e.target.value })}
                placeholder="Mínimo 6 caracteres"
              />
            </div>

            <div>
              <label htmlFor="confirmar_senha" className="block text-sm font-medium text-gray-700">
                Confirmar Nova Senha *
              </label>
              <input
                id="confirmar_senha"
                type="password"
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={formData.confirmar_senha}
                onChange={(e) => setFormData({ ...formData, confirmar_senha: e.target.value })}
                placeholder="Digite a senha novamente"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-md disabled:opacity-50 transition-colors"
          >
            {loading ? 'Alterando...' : 'Alterar Senha'}
          </button>
        </form>

        <div className="text-center text-sm text-gray-500">
          <p>⚠️ Esta alteração é obrigatória para continuar</p>
        </div>
      </div>
    </div>
  );
}
