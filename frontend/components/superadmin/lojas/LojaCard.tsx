'use client';

import { Loja } from '@/hooks/useLojaList';

interface LojaCardProps {
  loja: Loja;
  onInfo: (loja: Loja) => void;
  onEdit: (loja: Loja) => void;
  onDelete: (loja: Loja) => void;
  onCriarBanco: (lojaId: number) => void;
  onReenviarSenha: (loja: Loja) => void;
  actionLoading: boolean;
}

export function LojaCard({
  loja,
  onInfo,
  onEdit,
  onDelete,
  onCriarBanco,
  onReenviarSenha,
  actionLoading,
}: LojaCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-bold text-gray-900">{loja.nome}</h3>
          <p className="text-sm text-gray-500">@{loja.owner_username}</p>
        </div>
        <span
          className={`px-3 py-1 text-xs rounded-full ${
            loja.is_active
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-800'
          }`}
        >
          {loja.is_active ? 'Ativa' : 'Inativa'}
        </span>
      </div>

      {/* Informações */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center text-sm text-gray-600">
          <span className="mr-2">📧</span>
          <span>{loja.owner_email}</span>
        </div>
        {loja.owner_telefone && (
          <div className="flex items-center text-sm text-gray-600">
            <span className="mr-2">📱</span>
            <span>{loja.owner_telefone}</span>
          </div>
        )}
        <div className="flex items-center text-sm text-gray-600">
          <span className="mr-2">🏪</span>
          <span>{loja.tipo_loja_nome}</span>
        </div>
        <div className="flex items-center text-sm text-gray-600">
          <span className="mr-2">💳</span>
          <span>{loja.plano_nome}</span>
        </div>
      </div>

      {/* Status do Banco */}
      <div className="mb-4 pb-4 border-b">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Banco de Dados:</span>
          {loja.database_created ? (
            <span className="text-green-600 text-sm font-medium">✓ Criado</span>
          ) : (
            <button
              onClick={() => onCriarBanco(loja.id)}
              className="text-xs px-3 py-1 bg-blue-100 text-blue-800 rounded hover:bg-blue-200 disabled:opacity-50"
              disabled={actionLoading}
            >
              Criar Banco
            </button>
          )}
        </div>
      </div>

      {/* Senha Provisória */}
      {loja.senha_provisoria && (
        <div className="mb-4 pb-4 border-b">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Senha Provisória:</span>
            <button
              onClick={() => onReenviarSenha(loja)}
              className="text-xs px-3 py-1 bg-purple-100 text-purple-800 rounded hover:bg-purple-200 disabled:opacity-50"
              title="Reenviar senha por email"
              disabled={actionLoading}
            >
              📧 Reenviar
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-1">Disponível em Informações da Loja</p>
        </div>
      )}

      {/* Ações */}
      <div className="flex items-center justify-between pt-4">
        <div className="text-xs text-gray-500">
          Criada em {new Date(loja.created_at).toLocaleDateString('pt-BR')}
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onInfo(loja)}
            className="px-3 py-1 text-xs bg-purple-100 text-purple-800 rounded hover:bg-purple-200"
            title="Ver informações da loja"
          >
            ℹ️ Info
          </button>
          <button
            onClick={() => onEdit(loja)}
            className="px-3 py-1 text-xs bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
          >
            ✏️ Editar
          </button>
          <button
            onClick={() => onDelete(loja)}
            className="px-3 py-1 text-xs bg-red-100 text-red-800 rounded hover:bg-red-200"
            title={loja.database_created ? 'Não é possível excluir - banco criado' : 'Excluir loja'}
          >
            🗑️ Excluir
          </button>
        </div>
      </div>
    </div>
  );
}
