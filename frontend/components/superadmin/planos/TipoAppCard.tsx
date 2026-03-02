'use client';

import { TipoApp } from '@/hooks/useTipoAppList';

interface TipoAppCardProps {
  tipo: TipoApp;
  onClick: () => void;
}

const getIconForType = (nome: string) => {
  switch (nome.toLowerCase()) {
    case 'e-commerce': return '🛒';
    case 'serviços': return '🔧';
    case 'restaurante': return '🍕';
    case 'clínica de estética': return '💅';
    case 'crm vendas': return '📊';
    default: return '🏪';
  }
};

export function TipoAppCard({ tipo, onClick }: TipoAppCardProps) {
  return (
    <button
      onClick={onClick}
      className="bg-white rounded-lg shadow-md hover:shadow-xl transition-all p-8 text-left border-2 border-transparent hover:border-purple-300"
    >
      <div className="flex items-center space-x-4 mb-4">
        <div
          className="w-16 h-16 rounded-full flex items-center justify-center text-3xl"
          style={{ backgroundColor: tipo.cor_primaria + '20' }}
        >
          {getIconForType(tipo.nome)}
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-bold text-gray-900">{tipo.nome}</h3>
          <div
            className="w-12 h-1 rounded-full mt-2"
            style={{ backgroundColor: tipo.cor_primaria }}
          />
        </div>
      </div>
      <div className="flex items-center justify-between text-sm text-gray-600">
        <span>Ver planos disponíveis</span>
        <span className="text-2xl">→</span>
      </div>
    </button>
  );
}
