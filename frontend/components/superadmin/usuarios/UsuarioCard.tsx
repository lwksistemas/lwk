'use client';

import { Usuario } from '@/hooks/useUsuarioActions';
import { formatDate } from '@/lib/financeiro-helpers';

interface UsuarioCardProps {
  usuario: Usuario;
  onEdit: (usuario: Usuario) => void;
  onDelete: (usuario: Usuario) => void;
  onToggleStatus: (usuario: Usuario) => void;
}

const getTipoColor = (tipo: string) => {
  return tipo === 'superadmin' 
    ? 'bg-purple-100 text-purple-800' 
    : 'bg-blue-100 text-blue-800';
};

const getTipoIcon = (tipo: string) => {
  return tipo === 'superadmin' ? '👑' : '🛠️';
};

export function UsuarioCard({ usuario, onEdit, onDelete, onToggleStatus }: UsuarioCardProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center text-2xl">
            {getTipoIcon(usuario.tipo)}
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              {usuario.user.first_name} {usuario.user.last_name}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">@{usuario.user.username}</p>
          </div>
        </div>
        <span className={`px-3 py-1 text-xs rounded-full ${getTipoColor(usuario.tipo)}`}>
          {usuario.tipo_display}
        </span>
      </div>

      {/* Informações */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
          <span className="mr-2">📧</span>
          <span>{usuario.user.email}</span>
        </div>
        {usuario.telefone && (
          <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
            <span className="mr-2">📱</span>
            <span>{usuario.telefone}</span>
          </div>
        )}
        {usuario.cpf && (
          <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
            <span className="mr-2">🆔</span>
            <span>{usuario.cpf}</span>
          </div>
        )}
      </div>

      {/* Permissões */}
      <div className="mb-4">
        <h4 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">Permissões:</h4>
        <div className="flex flex-wrap gap-1">
          {usuario.pode_criar_lojas && (
            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
              🏪 Criar Lojas
            </span>
          )}
          {usuario.pode_gerenciar_financeiro && (
            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
              💰 Financeiro
            </span>
          )}
          {usuario.pode_acessar_todas_lojas && (
            <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
              🌐 Todas Lojas
            </span>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="text-xs text-gray-500 dark:text-gray-400">
          Criado em {formatDate(usuario.created_at)}
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onToggleStatus(usuario)}
            className={`px-3 py-1 text-xs rounded ${
              usuario.is_active
                ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                : 'bg-green-100 text-green-800 hover:bg-green-200'
            }`}
          >
            {usuario.is_active ? '🔒 Desativar' : '✅ Ativar'}
          </button>
          <button
            onClick={() => onEdit(usuario)}
            className="px-3 py-1 text-xs bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
          >
            ✏️ Editar
          </button>
          <button
            onClick={() => onDelete(usuario)}
            className="px-3 py-1 text-xs bg-red-100 text-red-800 rounded hover:bg-red-200"
          >
            🗑️ Excluir
          </button>
        </div>
      </div>
    </div>
  );
}
