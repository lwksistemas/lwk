'use client';

import { useState } from 'react';
import { X, LogIn } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface AcessoRapidoModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AcessoRapidoModal({ isOpen, onClose }: AcessoRapidoModalProps) {
  const [documento, setDocumento] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  if (!isOpen) return null;

  const formatarDocumento = (valor: string) => {
    // Remove tudo que não é número
    const numeros = valor.replace(/\D/g, '');
    
    // Limita a 14 dígitos (CNPJ)
    const limitado = numeros.slice(0, 14);
    
    // Formata CPF (11 dígitos) ou CNPJ (14 dígitos)
    if (limitado.length <= 11) {
      // CPF: 000.000.000-00
      return limitado
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
    } else {
      // CNPJ: 00.000.000/0000-00
      return limitado
        .replace(/(\d{2})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1/$2')
        .replace(/(\d{4})(\d{1,2})$/, '$1-$2');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const valorFormatado = formatarDocumento(e.target.value);
    setDocumento(valorFormatado);
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Remove formatação
    const documentoLimpo = documento.replace(/\D/g, '');
    
    // Valida tamanho
    if (documentoLimpo.length !== 11 && documentoLimpo.length !== 14) {
      setError('Digite um CPF (11 dígitos) ou CNPJ (14 dígitos) válido');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Buscar loja pelo CPF/CNPJ
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}superadmin/lojas/buscar-por-documento/?documento=${documentoLimpo}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          setError('Nenhuma loja encontrada com este CPF/CNPJ');
        } else {
          setError('Erro ao buscar loja. Tente novamente.');
        }
        setLoading(false);
        return;
      }

      const data = await response.json();
      
      // Redirecionar para página de login da loja
      router.push(`/loja/${data.slug}/login`);
      
    } catch (err) {
      console.error('Erro ao buscar loja:', err);
      setError('Erro ao conectar com o servidor. Tente novamente.');
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 relative animate-in fade-in zoom-in duration-200">
        {/* Botão Fechar */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 transition-colors rounded-lg hover:bg-gray-100"
          aria-label="Fechar"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Ícone */}
        <div className="flex justify-center mb-4">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
            <LogIn className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        {/* Título */}
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
          Acesso Rápido
        </h2>
        <p className="text-gray-600 text-center mb-6">
          Digite seu CPF ou CNPJ para acessar sua loja
        </p>

        {/* Formulário */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="documento" className="block text-sm font-medium text-gray-700 mb-2">
              CPF ou CNPJ
            </label>
            <input
              id="documento"
              type="text"
              value={documento}
              onChange={handleChange}
              placeholder="000.000.000-00 ou 00.000.000/0000-00"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-lg"
              disabled={loading}
              autoFocus
            />
            {error && (
              <p className="mt-2 text-sm text-red-600 flex items-center gap-1">
                <span>⚠️</span>
                {error}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading || !documento}
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Buscando...
              </>
            ) : (
              <>
                <LogIn className="w-5 h-5" />
                Acessar Minha Loja
              </>
            )}
          </button>
        </form>

        {/* Informação adicional */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-sm text-gray-500 text-center">
            Não tem cadastro?{' '}
            <a href="/cadastro" className="text-blue-600 hover:text-blue-700 font-medium">
              Cadastre sua loja
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
