/**
 * Página de Tipos de App
 * ✅ REFATORADO v770: Código reduzido de 600+ para ~100 linhas usando hooks e componentes
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';
import { useTipoAppList } from '@/hooks/useTipoAppList';
import { useTipoAppActions, TipoApp } from '@/hooks/useTipoAppActions';
import { TipoAppCard, TipoAppModal } from '@/components/superadmin/tipos-app';

export default function TiposAppPage() {
  const router = useRouter();
  const { tipos, loading, reload } = useTipoAppList();
  const { excluirTipoApp } = useTipoAppActions();
  
  const [showModal, setShowModal] = useState(false);
  const [editingTipo, setEditingTipo] = useState<TipoApp | null>(null);

  // Verificar autenticação
  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
    }
  }, [router]);

  const handleEdit = (tipo: TipoApp) => {
    setEditingTipo(tipo);
    setShowModal(true);
  };

  const handleDelete = async (tipo: TipoApp) => {
    const success = await excluirTipoApp(tipo);
    if (success) {
      alert('Tipo de app excluído com sucesso!');
      reload();
    }
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingTipo(null);
  };

  const handleSuccess = () => {
    reload();
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <nav className="bg-purple-900 dark:bg-purple-950 text-white shadow-lg">
        <div className="w-full max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <a href="/superadmin/dashboard" className="text-purple-200 hover:text-white">
                ← Voltar
              </a>
              <h1 className="text-2xl font-bold">Tipos de App</h1>
            </div>
            <button
              onClick={() => setShowModal(true)}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-md transition-colors"
            >
              + Novo Tipo de App
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="w-full max-w-full py-6 px-4 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {loading ? (
            <div className="text-center py-12">Carregando...</div>
          ) : tipos.length === 0 ? (
            <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow">
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                Nenhum tipo de app cadastrado ainda.
              </p>
              <button
                onClick={() => setShowModal(true)}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
              >
                Criar Primeiro Tipo de App
              </button>
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
                      <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Nome</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Slug</th>
                      <th className="text-center py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Lojas</th>
                      <th className="text-center py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Status</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Recursos</th>
                      <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tipos.map((tipo) => (
                      <tr key={tipo.id} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30">
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: tipo.cor_primaria || '#6b21a8' }} />
                            <span className="font-medium text-gray-900 dark:text-white">{tipo.nome}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-500 dark:text-gray-400 font-mono">{tipo.slug}</td>
                        <td className="py-3 px-4 text-center">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300">
                            {tipo.total_lojas}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${tipo.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'}`}>
                            {tipo.is_active ? 'Ativo' : 'Inativo'}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex gap-1 flex-wrap">
                            {tipo.tem_produtos && <span className="text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 px-1.5 py-0.5 rounded">Produtos</span>}
                            {tipo.tem_servicos && <span className="text-xs bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 px-1.5 py-0.5 rounded">Serviços</span>}
                            {tipo.tem_agendamento && <span className="text-xs bg-yellow-50 dark:bg-yellow-900/20 text-yellow-600 dark:text-yellow-400 px-1.5 py-0.5 rounded">Agenda</span>}
                            {tipo.tem_delivery && <span className="text-xs bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400 px-1.5 py-0.5 rounded">Delivery</span>}
                            {tipo.tem_estoque && <span className="text-xs bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 px-1.5 py-0.5 rounded">Estoque</span>}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex justify-end gap-1">
                            <button onClick={() => handleEdit(tipo)} className="px-3 py-1 text-sm bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded hover:bg-blue-200 dark:hover:bg-blue-900/50">Editar</button>
                            <button onClick={() => handleDelete(tipo)} className="px-3 py-1 text-sm bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded hover:bg-red-200 dark:hover:bg-red-900/50">Excluir</button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Modal */}
      {showModal && (
        <TipoAppModal 
          onClose={handleCloseModal} 
          onSuccess={handleSuccess}
          editingTipo={editingTipo}
        />
      )}
    </div>
  );
}
