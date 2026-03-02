/**
 * Card de Tipo de App
 * ✅ REFATORADO v770: Componente extraído para reutilização
 */
import { TipoApp } from '@/hooks/useTipoAppActions';

interface TipoAppCardProps {
  tipo: TipoApp;
  onEdit: (tipo: TipoApp) => void;
  onDelete: (tipo: TipoApp) => void;
}

export function TipoAppCard({ tipo, onEdit, onDelete }: TipoAppCardProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
      {/* Header do Card */}
      <div 
        className="h-20 flex items-center justify-center"
        style={{ backgroundColor: tipo.cor_primaria }}
      >
        <h3 className="text-xl font-bold text-white">{tipo.nome}</h3>
      </div>

      {/* Conteúdo do Card */}
      <div className="p-6">
        {/* Estatísticas */}
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-500">Lojas usando:</span>
            <span className="font-semibold text-purple-600">{tipo.total_lojas}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Template:</span>
            <span className="text-sm font-medium">{tipo.dashboard_template}</span>
          </div>
        </div>

        {/* Funcionalidades */}
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Funcionalidades:</h4>
          <div className="flex flex-wrap gap-1">
            {tipo.tem_produtos && (
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                Produtos
              </span>
            )}
            {tipo.tem_servicos && (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                Serviços
              </span>
            )}
            {tipo.tem_agendamento && (
              <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
                Agendamento
              </span>
            )}
            {tipo.tem_delivery && (
              <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded">
                Delivery
              </span>
            )}
            {tipo.tem_estoque && (
              <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
                Estoque
              </span>
            )}
          </div>
        </div>

        {/* Cores */}
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Cores:</h4>
          <div className="flex space-x-2">
            <div className="flex items-center space-x-1">
              <div
                className="w-4 h-4 rounded-full border"
                style={{ backgroundColor: tipo.cor_primaria }}
              />
              <span className="text-xs text-gray-500">Primária</span>
            </div>
            <div className="flex items-center space-x-1">
              <div
                className="w-4 h-4 rounded-full border"
                style={{ backgroundColor: tipo.cor_secundaria }}
              />
              <span className="text-xs text-gray-500">Secundária</span>
            </div>
          </div>
        </div>

        {/* Ações */}
        <div className="flex justify-between items-center pt-4 border-t">
          <span className="text-xs text-gray-400">
            {new Date(tipo.created_at).toLocaleDateString('pt-BR')}
          </span>
          <div className="space-x-2">
            <button 
              onClick={() => onEdit(tipo)}
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              Editar
            </button>
            {tipo.total_lojas === 0 && (
              <button 
                onClick={() => onDelete(tipo)}
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
