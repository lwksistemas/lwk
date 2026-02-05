interface CardEstatisticasProps {
  titulo: string;
  valor: number;
  cor: 'blue' | 'yellow' | 'green' | 'gray';
}

const coresMap = {
  blue: 'text-blue-600',
  yellow: 'text-yellow-600',
  green: 'text-green-600',
  gray: 'text-gray-600',
};

export function CardEstatisticas({ titulo, valor, cor }: CardEstatisticasProps) {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-gray-500 text-sm font-medium">{titulo}</h3>
      <p className={`text-3xl font-bold ${coresMap[cor]} mt-2`}>{valor}</p>
    </div>
  );
}
