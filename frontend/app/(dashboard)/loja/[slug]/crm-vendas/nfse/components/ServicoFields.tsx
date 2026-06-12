'use client';

/**
 * Campos de serviço: atividade rápida, códigos fiscais, descrição e valor.
 */

import { NFSE_EMISSAO_INPUT_CLASS } from '@/lib/nfse-emissao-form';

interface ServicoFieldsProps {
  servico_descricao: string;
  valor_servicos: string;
  enviar_email: boolean;
  codigo_cnae?: string;
  codigo_servico?: string;
  item_lista_servico?: string;
  onChange: (field: string, value: string | boolean) => void;
}

const ATIVIDADES_COMUNS = [
  { label: 'Usar configuração padrão da loja', cnae: '', servico: '', item_lista: '' },
  {
    label: '17.06 - Promoção de Vendas e Negócios (CNAE 7319002)',
    cnae: '7319002',
    servico: '170602',
    item_lista: '17.06',
  },
  {
    label: '14.01 - Manutenção de Computadores (CNAE 9511800)',
    cnae: '9511800',
    servico: '140118',
    item_lista: '14.01',
  },
  {
    label: '46.18 - Representação Comercial (CNAE 4618402)',
    cnae: '4618402',
    servico: '101002',
    item_lista: '46.18',
  },
  {
    label: '47.51 - Comércio de Informática (CNAE 4751201)',
    cnae: '4751201',
    servico: '140118',
    item_lista: '47.51',
  },
];

export function ServicoFields({
  servico_descricao,
  valor_servicos,
  enviar_email,
  codigo_cnae,
  codigo_servico,
  item_lista_servico,
  onChange,
}: ServicoFieldsProps) {
  const handleAtividadeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const idx = parseInt(e.target.value, 10);
    if (idx >= 0 && idx < ATIVIDADES_COMUNS.length) {
      const atividade = ATIVIDADES_COMUNS[idx];
      onChange('codigo_cnae', atividade.cnae);
      onChange('codigo_servico', atividade.servico);
      onChange('item_lista_servico', atividade.item_lista);
    }
  };

  const selectedIdx = ATIVIDADES_COMUNS.findIndex(
    (a) =>
      a.cnae === (codigo_cnae || '') &&
      a.servico === (codigo_servico || '') &&
      a.item_lista === (item_lista_servico || ''),
  );

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
      <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Dados do Serviço</h3>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Atividade / perfil do serviço
          </label>
          <select
            value={selectedIdx >= 0 ? selectedIdx : 0}
            onChange={handleAtividadeChange}
            className={NFSE_EMISSAO_INPUT_CLASS}
          >
            {ATIVIDADES_COMUNS.map((a, i) => (
              <option key={i} value={i}>
                {a.label}
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Atalho para preencher os códigos abaixo. Você pode ajustar manualmente.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Código do Serviço Municipal
            </label>
            <input
              type="text"
              value={codigo_servico || ''}
              onChange={(e) => onChange('codigo_servico', e.target.value)}
              className={NFSE_EMISSAO_INPUT_CLASS}
              placeholder="Ex: 1401 ou 170602"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Código CNAE
            </label>
            <input
              type="text"
              value={codigo_cnae || ''}
              onChange={(e) => onChange('codigo_cnae', e.target.value)}
              className={NFSE_EMISSAO_INPUT_CLASS}
              placeholder="Ex: 7319002"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Item da Lista de Serviços
            </label>
            <input
              type="text"
              value={item_lista_servico || ''}
              onChange={(e) => onChange('item_lista_servico', e.target.value)}
              className={NFSE_EMISSAO_INPUT_CLASS}
              placeholder="Ex: 17.06"
            />
          </div>
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
            className={NFSE_EMISSAO_INPUT_CLASS}
            placeholder="Ex: Serviços de representação comercial"
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
            className={NFSE_EMISSAO_INPUT_CLASS}
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
