'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

interface Product {
  id: number;
  name: string;
  price: string;
  stock: number;
  store_name: string;
}

function LojaDashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [lojaSlug, setLojaSlug] = useState('');
  const [lojaNome, setLojaNome] = useState('');

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const userType = authService.getUserType();
      if (userType !== 'loja') {
        router.push('/loja/login');
        return;
      }

      // Verificar se precisa trocar senha provisória
      verificarSenhaProvisoria();

      const slug = searchParams.get('slug') || authService.getLojaSlug() || '';
      setLojaSlug(slug);
      
      if (slug) {
        loadProducts(slug);
      }
    }
  }, [router, searchParams]);

  const verificarSenhaProvisoria = async () => {
    try {
      const response = await apiClient.get('/superadmin/lojas/verificar_senha_provisoria/');
      if (response.data.precisa_trocar_senha) {
        // Redirecionar para página de troca de senha
        router.push('/loja/trocar-senha');
      }
    } catch (error) {
      console.error('Erro ao verificar senha provisória:', error);
    }
  };

  const loadProducts = async (slug: string) => {
    try {
      setLoading(true);
      // Adicionar header com tenant slug
      const response = await apiClient.get('/products/', {
        headers: {
          'X-Tenant-Slug': slug
        }
      });
      setProducts(response.data.results || response.data);
    } catch (error) {
      console.error('Erro ao carregar produtos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    authService.logout();
    router.push('/loja/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-green-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div>
              <h1 className="text-2xl font-bold">{lojaNome || 'Minha Loja'}</h1>
              <p className="text-green-200 text-sm">{lojaSlug}</p>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-md transition-colors"
            >
              Sair
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Estatísticas */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Total de Produtos</h3>
              <p className="text-3xl font-bold text-green-600 mt-2">{products.length}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Estoque Total</h3>
              <p className="text-3xl font-bold text-blue-600 mt-2">
                {products.reduce((acc, p) => acc + p.stock, 0)}
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Valor Total</h3>
              <p className="text-3xl font-bold text-purple-600 mt-2">
                R$ {products.reduce((acc, p) => acc + (parseFloat(p.price) * p.stock), 0).toFixed(2)}
              </p>
            </div>
          </div>

          {/* Produtos */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <h3 className="text-lg font-semibold">Produtos</h3>
              <button className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
                + Novo Produto
              </button>
            </div>
            <div className="p-6">
              {loading ? (
                <p className="text-center text-gray-500">Carregando...</p>
              ) : products.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-500 mb-4">Nenhum produto cadastrado</p>
                  <button className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
                    Cadastrar Primeiro Produto
                  </button>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead>
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Nome
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Preço
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Estoque
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Ações
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {products.map((product) => (
                        <tr key={product.id}>
                          <td className="px-6 py-4 whitespace-nowrap">{product.name}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            R$ {parseFloat(product.price).toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">{product.stock}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <button className="text-blue-600 hover:text-blue-800 mr-3">
                              Editar
                            </button>
                            <button className="text-red-600 hover:text-red-800">
                              Excluir
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function LojaDashboardPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Carregando...</div>}>
      <LojaDashboardContent />
    </Suspense>
  );
}
