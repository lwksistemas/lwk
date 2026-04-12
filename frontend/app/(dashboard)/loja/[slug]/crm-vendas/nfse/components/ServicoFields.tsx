'use client';

/**
 * Campos de serviço reutilizáveis (Descrição, Valor, Enviar email).
 * Usado tanto no formulário manual quanto no formulário por conta cadastrada.
 */

interface ServicoFieldsProps {
  servico_descricao: string;
  valor_servicos: string;
  enviar_email: boolean;
  onChange: (field: string, value: string | boolean) => void;
}

export function ServicoFields({ servico_descricao, valor_servicos, enviar_email, onChange }: ServicoFieldsProps) {
  return (
    <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
      <h3 className="font-semibold text-gray-900 dark:text-white mb-4">
        Dados do Serviço
      </h3>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Descrição do Serviço *
          </label>
          <textarea
            value={servico_descricao}
            onChange={(e) => onChange('servico_descricao', e.target.value)}
            required
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
            placeholder="Ex: Desenvolvimento de sistema web personalizado"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Valor dos Serviços (R$) *
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={valor_servicos}
            onChange={(e) => onChange('valor_servicos', e.target.value)}
            required
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
            placeholder="0.00"
          />
        </div>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={enviar_email}
            onChange={(e) => onChange('enviar_email', e.target.checked)}
            className="w-4 h-4"
          />
          <span className="text-sm text-gray-700 dark:text-gray-300">
            Enviar NFS-e por email para o cliente
          </span>
        </label>
      </div>
    </div>
  );
}
