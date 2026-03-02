'use client';

import { Plano } from '@/hooks/usePlanoActions';

interface PlanoCardProps {
  plano: Plano;
  onEdit: (plano: Plano) => void;
  onDelete: (plano: Plano) => void;
}

const getPlanoColor = (ordem: number) => {
  const colors = [
    'border-green-200 bg-green-50',
    'border-blue-200 bg-blue-50',
    'border-purple-200 bg-purple-50',
  ];
  return colors[ordem - 1] || colors[0];
};

const getPlanoBadgeColor = (ordem: number) => {
  const colors = [
    'bg-green-100 text-green-800',
    'bg-blue-100 text-blue-800',
    'bg-purple-100 text-purple-800',
  ];
  return colors[ordem - 1] || colors[0];
};

const formatPrice = (price: string) => {
  return parseFloat(price).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  });
};

export function PlanoCard({ plano, onEdit, onDelete }: PlanoCardProps) {
  return (
    <div
      className={`bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow border-2 ${getPlanoColor(plano.ordem)}`}
    >
      {/* Header do Card */}
      <div className="p-6 text-center">
        <div className="flex justify-between items-start mb-2">
          <span className={`px-2 py-1 text-xs rounded-full ${getPlanoBadgeColor(plano.ordem)}`}>
            {plano.ordem === 1 ? 'Básico' : plano.ordem === 2 ? 'Intermediário' : 'Avançado'}
          </span>
          {!plano.is_active && (
            <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">
              Inativo
            </span>
          )}
        </div>
        
        <h3 className="text-xl font-bold text-gray-900 mb-2">{plano.nome}</h3>
        <p className="text-gray-600 text-sm mb-4">{plano.descricao}</p>
        
        {/* Preços */}
        <div className="mb-4">
          <div className="text-3xl font-bold text-purple-600">
            {formatPrice(plano.preco_mensal)}
          </div>
          <div className="text-sm text-gray-500">por mês</div>
          {plano.preco_anual && parseFloat(plano.preco_anual) > 0 && (
            <div className="text-sm text-green-600 mt-1">
              ou {formatPrice(plano.preco_anual)}/ano
            </div>
          )}
        </div>
      </div>

      {/* Limites */}
      <div className="px-6 pb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Limites:</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Produtos:</span>
            <span className="font-medium">
              {plano.max_produtos === 999999 ? 'Ilimitado' : plano.max_produtos}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Usuários:</span>
            <span className="font-medium">{plano.max_usuarios}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Pedidos/mês:</span>
            <span className="font-medium">
              {plano.max_pedidos_mes === 999999 ? 'Ilimitado' : plano.max_pedidos_mes}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Storage:</span>
            <span className="font-medium">{plano.espaco_storage_gb}GB</span>
          </div>
        </div>
      </div>

      {/* Funcionalidades */}
      <div className="px-6 pb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Funcionalidades:</h4>
        <div className="flex flex-wrap gap-1">
          {plano.tem_relatorios_avancados && (
            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
              📊 Relatórios
            </span>
          )}
          {plano.tem_api_acesso && (
            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
              🔌 API
            </span>
          )}
          {plano.tem_suporte_prioritario && (
            <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
              ⭐ Suporte VIP
            </span>
          )}
          {plano.tem_dominio_customizado && (
            <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded">
              🌐 Domínio
            </span>
          )}
          {plano.tem_whatsapp_integration && (
            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
              💬 WhatsApp
            </span>
          )}
        </div>
      </div>

      {/* Estatísticas e Ações */}
      <div className="px-6 pb-6">
        <div className="flex justify-between items-center pt-4 border-t">
          <div className="text-sm">
            <div className="font-medium text-purple-600">{plano.total_lojas} lojas</div>
            <div className="text-xs text-gray-500">
              {new Date(plano.created_at).toLocaleDateString('pt-BR')}
            </div>
          </div>
          <div className="space-x-2">
            <button 
              onClick={() => onEdit(plano)}
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              Editar
            </button>
            {plano.total_lojas === 0 && (
              <button 
                onClick={() => onDelete(plano)}
                className="text-red-600 hover:text-red-800 text-sm font-medium"
              >
                Excluir
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
