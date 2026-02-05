interface Chamado {
  id: number;
  titulo: string;
  descricao: string;
  tipo: string;
  loja_nome: string;
  loja_slug: string;
  usuario_nome: string;
  usuario_email: string;
  status: string;
  prioridade: string;
  created_at: string;
  updated_at: string;
}

interface TabelaChamadosProps {
  chamados: Chamado[];
  loading: boolean;
  onAtender: (chamado: Chamado) => void;
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'aberto': 'bg-yellow-100 text-yellow-800',
    'em_andamento': 'bg-blue-100 text-blue-800',
    'resolvido': 'bg-green-100 text-green-800',
    'fechado': 'bg-gray-100 text-gray-800',
  };
  return colors[status] || 'bg-gray-100 text-gray-800';
};

const getPrioridadeColor = (prioridade: string) => {
  const colors: Record<string, string> = {
    'baixa': 'text-gray-600',
    'media': 'text-yellow-600',
    'alta': 'text-orange-600',
    'urgente': 'text-red-600',
  };
  return colors[prioridade] || 'text-gray-600';
};

export function TabelaChamados({ chamados, loading, onAtender }: TabelaChamadosProps) {
  if (loading) {
    return (
      <div className="text-center text-gray-500 py-12">
        Carregando...
      </div>
    );
  }

  if (chamados.length === 0) {
    return (
      <div className="text-center text-gray-500 py-12">
        Nenhum chamado encontrado
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead>
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              ID
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Título
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Loja
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Prioridade
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Ações
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {chamados.map((chamado) => (
            <tr key={chamado.id}>
              <td className="px-6 py-4 whitespace-nowrap">#{chamado.id}</td>
              <td className="px-6 py-4">{chamado.titulo}</td>
              <td className="px-6 py-4 whitespace-nowrap">{chamado.loja_nome}</td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(chamado.status)}`}>
                  {chamado.status.replace('_', ' ')}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`font-semibold ${getPrioridadeColor(chamado.prioridade)}`}>
                  {chamado.prioridade}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <button 
                  onClick={() => onAtender(chamado)}
                  className="text-blue-600 hover:text-blue-800 font-medium"
                >
                  Atender
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
