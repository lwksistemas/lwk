'use client';

import { useState } from 'react';

interface ModalRecuperarSenhaProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ModalRecuperarSenha({ isOpen, onClose }: ModalRecuperarSenhaProps) {
  const [emailRecuperacao, setEmailRecuperacao] = useState('');
  const [loadingRecuperacao, setLoadingRecuperacao] = useState(false);
  const [mensagemRecuperacao, setMensagemRecuperacao] = useState('');

  if (!isOpen) return null;

  const handleRecuperarSenha = async (e: React.FormEvent) => {
    e.preventDefault();
    setMensagemRecuperacao('');
    setLoadingRecuperacao(true);

    try {
      const apiClient = (await import('@/lib/api-client')).default;
      await apiClient.post('/superadmin/usuarios/recuperar_senha/', {
        email: emailRecuperacao,
        tipo: 'suporte'
      });
      setMensagemRecuperacao('✅ Senha provisória enviada para o email cadastrado!');
      setTimeout(() => {
        handleClose();
      }, 3000);
    } catch (err: any) {
      setMensagemRecuperacao(err.response?.data?.detail || '❌ Erro ao recuperar senha. Verifique o email.');
    } finally {
      setLoadingRecuperacao(false);
    }
  };

  const handleClose = () => {
    setEmailRecuperacao('');
    setMensagemRecuperacao('');
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-md w-full">
        <h3 className="text-2xl font-bold mb-4 text-blue-600">
          Recuperar Senha
        </h3>
        <p className="text-gray-600 mb-6">
          Digite o email cadastrado para receber uma nova senha provisória.
        </p>
        
        <form onSubmit={handleRecuperarSenha} className="space-y-4">
          {mensagemRecuperacao && (
            <div className={`p-3 rounded ${mensagemRecuperacao.includes('✅') ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
              {mensagemRecuperacao}
            </div>
          )}
          
          <div>
            <label htmlFor="email-recuperacao" className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              id="email-recuperacao"
              type="email"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={emailRecuperacao}
              onChange={(e) => setEmailRecuperacao(e.target.value)}
              placeholder="seu@email.com"
            />
          </div>
          
          <div className="flex justify-end space-x-4 pt-4">
            <button
              type="button"
              onClick={handleClose}
              disabled={loadingRecuperacao}
              className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loadingRecuperacao}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md disabled:opacity-50"
            >
              {loadingRecuperacao ? 'Enviando...' : 'Enviar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
