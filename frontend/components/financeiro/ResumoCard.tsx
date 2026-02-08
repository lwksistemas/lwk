/**
 * Card de Resumo Financeiro
 * Componente reutilizável (SOLID - Single Responsibility)
 */

import { formatCurrency } from '@/lib/financeiro-helpers';

interface ResumoCardProps {
  titulo: string;
  valor: number;
  valorSecundario?: number;
  labelSecundario?: string;
  cor: string;
  icone: string;
}

export function ResumoCard({
  titulo,
  valor,
  valorSecundario,
  labelSecundario,
  cor,
  icone
}: ResumoCardProps) {
  return (
    <div className="p-6 rounded-xl" style={{ backgroundColor: `${cor}10` }}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-2xl">{icone}</span>
        <p className="text-sm text-gray-600 dark:text-gray-400">{titulo}</p>
      </div>
      <p className="text-2xl font-bold" style={{ color: cor }}>
        {formatCurrency(valor)}
      </p>
      {valorSecundario !== undefined && labelSecundario && (
        <p className="text-xs text-gray-500 mt-1">
          {labelSecundario}: {formatCurrency(valorSecundario)}
        </p>
      )}
    </div>
  );
}
