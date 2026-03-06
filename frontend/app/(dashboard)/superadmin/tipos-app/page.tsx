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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {tipos.map((tipo) => (
                <TipoAppCard
                  key={tipo.id}
                  tipo={tipo}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                />
              ))}
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
