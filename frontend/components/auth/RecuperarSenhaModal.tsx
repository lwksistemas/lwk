'use client';

import { useState, FormEvent } from 'react';
import apiClient from '@/lib/api-client';

interface RecuperarSenhaModalProps {
  isOpen: boolean;
  onClose: () => void;
  endpoint: string;
  extraData?: Record<string, any>;
  title?: string;
  description?: string;
  primaryColor?: string;
}

export default function RecuperarSenhaModal({
  isOpen,
  onClose,
  endpoint,
  extraData = {},
  title = 'Recuperar Senha',
  description = 'Digite o email cadastrado para receber uma nova senha provisória.',
  primaryColor = '#9333ea' // purple-600
}: RecuperarSenhaModalProps) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [mensagem, setMensagem] = useState('');
  const [tipoMensagem, setTipoMensagem] = useState<'success' | 'error'>('success');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setMensagem('');
    setLoading(true);

    try {
      await apiClient.post(endpoint, {
        email,
        ...extraData
      });
      
      setTipoMensagem('success');
      setMensagem('✅ Senha provisória enviada para o email cadastrado!');
      
      // Fechar modal após 3 segundos
      setTimeout(() => {
        handleClose();
      }, 3000);
    } catch (err: any) {
      setTipoMensagem('error');
      const errorMessage = err.response?.data?.detail 
        || err.response?.data?.error 
        || '❌ Erro ao recuperar senha. Verifique o email.';
      setMensagem(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setEmail('');
    setMensagem('');
    setLoading(false);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-3 sm:p-4"
      onClick={handleClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div 
        className="bg-white dark:bg-gray-800 rounded-lg p-6 sm:p-8 max-w-md w-full max-h-[95vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 
          id="modal-title"
          className="text-xl sm:text-2xl font-bold mb-3 sm:mb-4"
          style={{ color: primaryColor }}
        >
          {title}
        </h3>
        <p className="text-sm sm:text-base text-gray-600 dark:text-gray-300 mb-4 sm:mb-6">
          {description}
        </p>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {mensagem && (
            <div 
              className={`p-3 rounded text-sm ${
                tipoMensagem === 'success' 
                  ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-800' 
                  : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800'
              }`}
              role="alert"
            >
              {mensagem}
            </div>
          )}
          
          <div>
            <label htmlFor="email-recuperacao" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Email
            </label>
            <input
              id="email-recuperacao"
              type="email"
              required
              className="w-full px-3 py-3 sm:py-2.5 min-h-[44px] text-base sm:text-sm text-gray-900 dark:text-gray-100 placeholder:text-gray-500 dark:placeholder:text-gray-400 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-0 dark:focus:ring-offset-gray-800"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seu@email.com"
              disabled={loading}
              autoComplete="email"
            />
          </div>
          
          <div className="flex flex-col-reverse sm:flex-row justify-end gap-3 sm:space-x-4 pt-4">
            <button
              type="button"
              onClick={handleClose}
              disabled={loading}
              className="px-6 py-3 sm:py-2.5 min-h-[44px] border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 disabled:opacity-50 active:scale-95 transition-transform"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3 sm:py-2.5 min-h-[44px] text-white rounded-md hover:opacity-90 disabled:opacity-50 active:scale-95 transition-transform"
              style={{ backgroundColor: primaryColor }}
            >
              {loading ? 'Enviando...' : 'Enviar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
