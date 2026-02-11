interface Appointment {
  id: number;
  horario: string;
  cliente_nome: string;
  servico_nome: string;
  profissional_nome: string;
  status: string;
}

interface AppointmentsTableProps {
  appointments: Appointment[];
  onFilterChange?: (filter: string) => void;
}

const statusStyle = {
  Confirmado: "bg-green-100 text-green-700",
  "A Confirmar": "bg-yellow-100 text-yellow-700",
  Agendado: "bg-blue-100 text-blue-700",
  confirmado: "bg-green-100 text-green-700",
  agendado: "bg-blue-100 text-blue-700",
  em_atendimento: "bg-yellow-100 text-yellow-700",
};

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    'confirmado': 'Confirmado',
    'agendado': 'Agendado',
    'em_atendimento': 'A Confirmar',
    'Confirmado': 'Confirmado',
    'Agendado': 'Agendado',
    'A Confirmar': 'A Confirmar',
  };
  return labels[status] || 'Agendado';
};

const getAvatar = (nome: string, seed: number) => {
  const inicial = nome.charAt(0).toUpperCase();
  const colors = ['bg-purple-500', 'bg-pink-500', 'bg-blue-500', 'bg-indigo-500', 'bg-green-500'];
  const color = colors[seed % colors.length];
  return (
    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-semibold text-xs ${color}`}>
      {inicial}
    </div>
  );
};

export function AppointmentsTable({ appointments, onFilterChange }: AppointmentsTableProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-4 mb-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-3">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Próximos Agendamentos
        </h2>
        <div className="flex gap-2 w-full sm:w-auto">
          <select 
            className="flex-1 sm:flex-none border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            onChange={(e) => onFilterChange?.(e.target.value)}
          >
            <option value="hoje">Hoje</option>
            <option value="semana">Esta Semana</option>
          </select>
          <select className="flex-1 sm:flex-none border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
            <option>Todos</option>
          </select>
        </div>
      </div>
      
      {appointments.length === 0 ? (
        <div className="py-8 text-center text-gray-500 dark:text-gray-400">
          Nenhum agendamento encontrado
        </div>
      ) : (
        <>
          {/* Desktop: Tabela */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-gray-500 dark:text-gray-400">
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3">Horário</th>
                  <th className="text-left py-3">Cliente</th>
                  <th className="text-left py-3">Serviço</th>
                  <th className="text-left py-3">Profissional</th>
                  <th className="text-left py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {appointments.map((a, i) => (
                  <tr 
                    key={a.id} 
                    className="border-b border-gray-200 dark:border-gray-700 last:border-none hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                  >
                    <td className="py-4 font-medium text-gray-900 dark:text-white">
                      {a.horario}
                    </td>
                    <td className="py-4">
                      <div className="flex items-center gap-2">
                        {getAvatar(a.cliente_nome, i)}
                        <span className="text-gray-900 dark:text-white">{a.cliente_nome}</span>
                      </div>
                    </td>
                    <td className="py-4 text-gray-600 dark:text-gray-400">
                      {a.servico_nome}
                    </td>
                    <td className="py-4">
                      <div className="flex items-center gap-2">
                        {getAvatar(a.profissional_nome, i + 10)}
                        <span className="text-gray-900 dark:text-white">{a.profissional_nome}</span>
                      </div>
                    </td>
                    <td className="py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusStyle[a.status as keyof typeof statusStyle] || statusStyle.Agendado}`}>
                        {getStatusLabel(a.status)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile: Cards */}
          <div className="md:hidden space-y-3">
            {appointments.map((a, i) => (
              <div 
                key={a.id}
                className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-lg font-bold text-gray-900 dark:text-white">
                    {a.horario}
                  </span>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusStyle[a.status as keyof typeof statusStyle] || statusStyle.Agendado}`}>
                    {getStatusLabel(a.status)}
                  </span>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    {getAvatar(a.cliente_nome, i)}
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Cliente</p>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">{a.cliente_nome}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {getAvatar(a.profissional_nome, i + 10)}
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Profissional</p>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">{a.profissional_nome}</p>
                    </div>
                  </div>
                  
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Serviço</p>
                    <p className="text-sm text-gray-900 dark:text-white">{a.servico_nome}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
