'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';

interface TrocarSenhaFormProps {
  /** Tipo de usuário: 'loja', 'suporte' ou 'superadmin' */
  userType: 'loja' | 'suporte' | 'superadmin';
  /** Endpoint da API para alterar senha */
  endpoint: string;
  /** Rota de redirecionamento após sucesso */
  redirectTo: string;
  /** Cor primária do tema (ex: 'green', 'blue', 'purple') */
  themeColor: 'green' | 'blue' | 'purple';
  /** Mostrar dicas de senha (opcional) */
  showPasswordTips?: boolean;
}

const colorClasses = {
  green: {
    gradient: 'from-green-50 to-green-100',
    icon: 'bg-yellow-100',
    iconText: 'text-yellow-600',
    ring: 'focus:ring-green-500 focus:border-green-500',
    button: 'bg-green-600 hover:bg-green-700 focus:ring-green-500',
  },
  blue: {
    gradient: 'from-blue-900 to-cyan-900',
    icon: 'bg-blue-600',
    iconText: 'text-white',
    ring: 'focus:ring-blue-500',
    button: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500',
  },
  purple: {
    gradient: 'from-purple-900 to-indigo-900',
    icon: 'bg-purple-600',
    iconText: 'text-white',
    ring: 'focus:ring-purple-500',
    button: 'bg-purple-600 hover:bg-purple-700 focus:ring-purple-500',
  },
};

export default function TrocarSenhaForm({
  userType,
  endpoint,
  redirectTo,
  themeColor,
  showPasswordTips = false,
}: TrocarSenhaFormProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    nova_senha: '',
    confirmar_senha: '',
  });
  const [erro, setErro] = useState('');

  const colors = colorClasses[themeColor];
  const isLightBg = themeColor === 'green';

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
      await apiClient.post(endpoint, {
        nova_senha: formData.nova_senha,
        confirmar_senha: formData.confirmar_senha,
      });

      alert('✅ Senha alterada com sucesso!');
      router.push(redirectTo);
    } catch (error: any) {
      console.error('Erro ao alterar senha:', error);
      setErro(error.response?.data?.error || error.response?.data?.detail || 'Erro ao alterar senha');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`min-h-screen flex items-center justify-center p-4 ${isLightBg ? `bg-gradient-to-br ${colors.gradient}` : `bg-gradient-to-br ${colors.gradient}`}`}>
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-2xl">
        {/* Header */}
        <div className="text-center">
          <div className={`mx-auto h-16 w-16 ${colors.icon} rounded-full flex items-center justify-center mb-4`}>
            <svg className={`h-8 w-8 ${colors.iconText}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {isLightBg ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
              )}
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            {isLightBg ? 'Alterar Senha Provisória' : 'Trocar Senha'}
          </h1>
          <p className="text-sm text-gray-600">
            Por segurança, {isLightBg ? 'você precisa alterar sua senha provisória antes de continuar.' : 'altere sua senha provisória'}
          </p>
        </div>

        {/* Alerta de primeiro acesso (apenas para loja) */}
        {isLightBg && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">Primeiro Acesso</h3>
                <p className="mt-1 text-sm text-yellow-700">
                  Esta é sua senha provisória. Por favor, escolha uma senha forte e única.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Formulário */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {erro && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-800">{erro}</p>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="nova_senha" className="block text-sm font-medium text-gray-700 mb-2">
                Nova Senha *
              </label>
              <input
                id="nova_senha"
                name="nova_senha"
                type="password"
                autoComplete="new-password"
                required
                minLength={6}
                className={`w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 ${colors.ring}`}
                value={formData.nova_senha}
                onChange={handleChange}
                placeholder="Mínimo 6 caracteres"
              />
            </div>

            <div>
              <label htmlFor="confirmar_senha" className="block text-sm font-medium text-gray-700 mb-2">
                Confirmar Nova Senha *
              </label>
              <input
                id="confirmar_senha"
                name="confirmar_senha"
                type="password"
                autoComplete="new-password"
                required
                minLength={6}
                className={`w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 ${colors.ring}`}
                value={formData.confirmar_senha}
                onChange={handleChange}
                placeholder="Digite a senha novamente"
              />
            </div>
          </div>

          {/* Dicas de senha (opcional) */}
          {showPasswordTips && (
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <h4 className="text-sm font-medium text-blue-800 mb-2">
                Dicas para uma senha forte:
              </h4>
              <ul className="text-xs text-blue-700 space-y-1">
                <li>• Use no mínimo 6 caracteres (recomendado: 8+)</li>
                <li>• Combine letras maiúsculas e minúsculas</li>
                <li>• Inclua números e símbolos</li>
                <li>• Não use informações pessoais</li>
              </ul>
            </div>
          )}

          {/* Botão */}
          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 px-4 text-white font-semibold rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${colors.button}`}
          >
            {loading ? 'Alterando...' : 'Alterar Senha'}
          </button>
        </form>

        {/* Footer */}
        <div className="text-center text-sm text-gray-500">
          <p>Esta alteração é obrigatória para continuar</p>
        </div>
      </div>
    </div>
  );
}
