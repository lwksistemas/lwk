'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { logger } from '@/lib/logger';
import PasswordInput from '@/components/auth/PasswordInput';
import { AuthScreenShell } from '@/components/auth/AuthScreenShell';
import { getLoginSistemaDefaults, type LoginSistemaTipo } from '@/lib/login-sistema-defaults';
import { validatePasswordPolicy, checkPasswordRules } from '@/lib/password-policy';

interface TrocarSenhaFormProps {
  /** Tipo de usuário: 'loja', 'suporte' ou 'superadmin' */
  userType: 'loja' | 'suporte' | 'superadmin';
  /** Endpoint da API para alterar senha */
  endpoint: string;
  /** Rota de redirecionamento após sucesso */
  redirectTo: string;
  /** Cor primária do tema (ex: 'green', 'blue', 'purple') */
  themeColor: 'green' | 'blue' | 'purple';
}

const buttonClasses = {
  green: 'bg-green-600 hover:bg-green-700 focus:ring-green-500',
  blue: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500',
  purple: 'bg-purple-600 hover:bg-purple-700 focus:ring-purple-500',
};

export default function TrocarSenhaForm({
  userType,
  endpoint,
  redirectTo,
  themeColor,
}: TrocarSenhaFormProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    nova_senha: '',
    confirmar_senha: '',
  });
  const [erro, setErro] = useState('');

  const isLoja = userType === 'loja';
  const sistemaTipo: LoginSistemaTipo | null =
    userType === 'superadmin' ? 'superadmin' : userType === 'suporte' ? 'suporte' : null;
  const sistemaDefaults = sistemaTipo ? getLoginSistemaDefaults(sistemaTipo) : null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro('');

    const policyError = validatePasswordPolicy(formData.nova_senha);
    if (policyError) {
      setErro(policyError);
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
      logger.warn('Erro ao alterar senha:', error);
      setErro(error.response?.data?.error || error.response?.data?.detail || 'Erro ao alterar senha');
    } finally {
      setLoading(false);
    }
  };

  const formContent = (
    <>
      <div className="text-center mb-8">
        <div className={`mx-auto h-16 w-16 rounded-full flex items-center justify-center mb-4 ${
          isLoja ? 'bg-yellow-100 dark:bg-yellow-900/30' : 'bg-white/20'
        }`}>
          <svg
            className={`h-8 w-8 ${isLoja ? 'text-yellow-600 dark:text-yellow-400' : 'text-white'}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          {isLoja ? 'Alterar Senha Provisória' : 'Trocar Senha'}
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          Por segurança, {isLoja ? 'você precisa alterar sua senha provisória antes de continuar.' : 'altere sua senha provisória'}
        </p>
      </div>

      {isLoja && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">Primeiro Acesso</h3>
              <p className="mt-1 text-sm text-yellow-700 dark:text-yellow-300">
                Esta é sua senha provisória. Por favor, escolha uma senha forte e única.
              </p>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {erro && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-3">
            <p className="text-sm text-red-800 dark:text-red-300">{erro}</p>
          </div>
        )}

        <div className="space-y-4">
          <PasswordInput
            id="nova_senha"
            value={formData.nova_senha}
            onChange={(v) => { setFormData(prev => ({ ...prev, nova_senha: v })); setErro(''); }}
            label="Nova Senha *"
            placeholder="Mínimo 6 caracteres"
            autoComplete="new-password"
            required
          />
          <PasswordInput
            id="confirmar_senha"
            value={formData.confirmar_senha}
            onChange={(v) => { setFormData(prev => ({ ...prev, confirmar_senha: v })); setErro(''); }}
            label="Confirmar Nova Senha *"
            placeholder="Digite a senha novamente"
            autoComplete="new-password"
            required
          />
        </div>

        {/* Requisitos de senha — feedback em tempo real */}
        <div className="bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-md p-4">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
            Requisitos da senha:
          </h4>
          <ul className="text-xs space-y-1.5">
            {checkPasswordRules(formData.nova_senha).map(({ rule, passed }) => (
              <li key={rule.id} className="flex items-center gap-2">
                <span className={`flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
                  formData.nova_senha
                    ? passed
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                      : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                    : 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
                }`}>
                  {formData.nova_senha ? (passed ? '✓' : '✗') : '•'}
                </span>
                <span className={`${
                  formData.nova_senha
                    ? passed
                      ? 'text-green-700 dark:text-green-400'
                      : 'text-red-700 dark:text-red-400'
                    : 'text-gray-600 dark:text-gray-400'
                }`}>
                  {rule.texto}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <button
          type="submit"
          disabled={loading}
          className={`w-full py-3 px-4 text-white font-semibold rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${buttonClasses[themeColor]}`}
        >
          {loading ? 'Alterando...' : 'Alterar Senha'}
        </button>
      </form>

      <div className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
        <p>Esta alteração é obrigatória para continuar</p>
      </div>
    </>
  );

  if (sistemaDefaults) {
    return (
      <AuthScreenShell backgroundUrl={sistemaDefaults.login_background}>
        {formContent}
      </AuthScreenShell>
    );
  }

  return (
    <AuthScreenShell>
      {formContent}
    </AuthScreenShell>
  );
}
