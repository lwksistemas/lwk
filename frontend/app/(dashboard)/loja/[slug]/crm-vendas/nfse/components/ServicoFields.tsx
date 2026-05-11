'use client';

/**
 * Campos de serviço reutilizáveis (Atividade/CNAE, Descrição, Valor, Enviar email).
 * Usado tanto no formulário manual quanto no formulário por conta cadastrada.
 */

interface ServicoFieldsProps {
  servico_descricao: string;
  valor_servicos: string;
  enviar_email: boolean;
  codigo_cnae?: string;
  codigo_servico?: string;
  onChange: (field: string, value: string | boolean) => void;
}

// Atividades comuns para seleção rápida
const ATIVIDADES_COMUNS = [
  { label: 'Usar configuração padrão da loja', cnae: '', servico: '' },
  { label: '17.06 - Promoção de Vendas e Negócios (CNAE 7319002)', cnae: '7319002', servico: '170602' },
  { label: '14.01 - Manutenção de Computadores (CNAE 9511800)', cnae: '9511800', servico: '140118' },
  { label: '46.18 - Representação Comercial (CNAE 4618402)', cnae: '4618402', servico: '101002' },
  { label: '47.51 - Comércio de Informática (CNAE 4751201)', cnae: '4751201', servico: '140118' },
];

export function ServicoFields({ servico_descricao, valor_servicos, enviar_email, codigo_cnae, codigo_servico, onChange }: ServicoFieldsProps) {
  const handleAtividadeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const idx = parseInt(e.target.value);
    if (idx >= 0 && idx < ATIVIDADES_COMUNS.length) {
      const atividade = ATIVIDADES_COMUNS[idx];
      onChange('codigo_cnae', atividade.cnae);
      onChange('codigo_servico', atividade.servico);
    }
  };

  // Determinar qual opção está selecionada
  const selectedIdx = ATIVIDADES_COMUNS.findIndex(
    (a) => a.cnae === (codigo_cnae || '') && a.servico === (codigo_servico || '')
  );

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
      <h3 className="font-semibold text-gray-900 dark:text-white mb-4">
        Dados do Serviço
      </h3>
      <div className="space-y-4">
        {/* Seletor de Atividade/CNAE */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Atividade / CNAE
          </label>
          <select
            value={selectedIdx >= 0 ? selectedIdx : 0}
            onChange={handleAtividadeChange}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
          >
            {ATIVIDADES_COMUNS.map((a, i) => (
              <option key={i} value={i}>{a.label}</option>
            ))}
          </select>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Selecione a atividade compatível com o serviço prestado
          </p>
        </div>

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
