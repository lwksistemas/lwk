'use client';

import { NFSE_EMISSAO_INPUT_CLASS } from '@/lib/nfse-emissao-form';

type EnderecoForm = {
  tomador_cep: string;
  tomador_logradouro: string;
  tomador_numero: string;
  tomador_complemento: string;
  tomador_bairro: string;
  tomador_cidade: string;
  tomador_uf: string;
};

export function ModalEmitirNFSeEnderecoFields({
  formData,
  onChange,
}: {
  formData: EnderecoForm;
  onChange: (field: string, value: string) => void;
}) {
  return (
    <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
      <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Endereço</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">CEP</label>
          <input
            type="text"
            value={formData.tomador_cep}
            onChange={(e) => onChange('tomador_cep', e.target.value)}
            className={NFSE_EMISSAO_INPUT_CLASS}
            placeholder="00000-000"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Logradouro</label>
          <input
            type="text"
            value={formData.tomador_logradouro}
            onChange={(e) => onChange('tomador_logradouro', e.target.value)}
            className={NFSE_EMISSAO_INPUT_CLASS}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Número</label>
          <input
            type="text"
            value={formData.tomador_numero}
            onChange={(e) => onChange('tomador_numero', e.target.value)}
            className={NFSE_EMISSAO_INPUT_CLASS}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Complemento</label>
          <input
            type="text"
            value={formData.tomador_complemento}
            onChange={(e) => onChange('tomador_complemento', e.target.value)}
            className={NFSE_EMISSAO_INPUT_CLASS}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Bairro</label>
          <input
            type="text"
            value={formData.tomador_bairro}
            onChange={(e) => onChange('tomador_bairro', e.target.value)}
            className={NFSE_EMISSAO_INPUT_CLASS}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Cidade *</label>
          <input
            type="text"
            value={formData.tomador_cidade}
            onChange={(e) => onChange('tomador_cidade', e.target.value)}
            required
            className={NFSE_EMISSAO_INPUT_CLASS}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">UF *</label>
          <input
            type="text"
            maxLength={2}
            value={formData.tomador_uf}
            onChange={(e) => onChange('tomador_uf', e.target.value.toUpperCase())}
            required
            className={NFSE_EMISSAO_INPUT_CLASS}
            placeholder="SP"
          />
        </div>
      </div>
    </div>
  );
}
