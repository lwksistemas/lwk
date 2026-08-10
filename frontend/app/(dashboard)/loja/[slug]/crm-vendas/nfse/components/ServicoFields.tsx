'use client';

/**
 * Campos de serviço: Atividade Municipal preenche os códigos fiscais;
 * usuário informa só descrição e valor.
 */

import { NFSE_EMISSAO_INPUT_CLASS } from '@/lib/nfse-emissao-form';
import {
  NFSE_ATIVIDADES_MUNICIPAIS,
  encontrarAtividadeMunicipal,
} from '@/lib/nfse-atividades-municipais';

interface ServicoFieldsProps {
  servico_descricao: string;
  valor_servicos: string;
  enviar_email: boolean;
  codigo_cnae?: string;
  codigo_servico?: string;
  item_lista_servico?: string;
  codigo_tributacao_nacional?: string;
  onChange: (field: string, value: string | boolean) => void;
}

export function ServicoFields({
  servico_descricao,
  valor_servicos,
  enviar_email,
  codigo_cnae,
  codigo_servico,
  item_lista_servico,
  codigo_tributacao_nacional,
  onChange,
}: ServicoFieldsProps) {
  const handleAtividadeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const idx = parseInt(e.target.value, 10);
    if (idx < 0 || idx >= NFSE_ATIVIDADES_MUNICIPAIS.length) return;
    const atividade = NFSE_ATIVIDADES_MUNICIPAIS[idx];
    onChange('codigo_cnae', atividade.cnae);
    onChange('codigo_servico', atividade.trib_mun);
    onChange('item_lista_servico', atividade.item_lista);
    onChange('codigo_tributacao_nacional', atividade.trib_nac);
  };

  const selectedIdx = encontrarAtividadeMunicipal({
    cnae: codigo_cnae,
    codigo_servico,
    item_lista_servico,
    codigo_tributacao_nacional,
  });

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
      <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Dados do Serviço</h3>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Atividade Municipal *
          </label>
          <select
            value={selectedIdx}
            onChange={handleAtividadeChange}
            required
            className={NFSE_EMISSAO_INPUT_CLASS}
          >
            {NFSE_ATIVIDADES_MUNICIPAIS.map((a, i) => (
              <option key={a.id} value={i}>
                {a.label}
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Preenche automaticamente CNAE, tributação nacional e municipal.
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
