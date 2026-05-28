'use client';

import { NFSE_EMISSAO_INPUT_CLASS } from '@/lib/nfse-emissao-form';

export function ModalEmitirNFSeTomadorFields({
  formData,
  onChange,
}: {
  formData: { tomador_cpf_cnpj: string; tomador_nome: string; tomador_email: string };
  onChange: (field: string, value: string) => void;
}) {
  return (
    <div>
      <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Dados do Cliente</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">CPF/CNPJ *</label>
          <input
            type="text"
            value={formData.tomador_cpf_cnpj}
            onChange={(e) => onChange('tomador_cpf_cnpj', e.target.value)}
            required
            className={NFSE_EMISSAO_INPUT_CLASS}
            placeholder="000.000.000-00"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Nome/Razão Social *</label>
          <input
            type="text"
            value={formData.tomador_nome}
            onChange={(e) => onChange('tomador_nome', e.target.value)}
            required
            className={NFSE_EMISSAO_INPUT_CLASS}
          />
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Email</label>
          <input
            type="email"
            value={formData.tomador_email}
            onChange={(e) => onChange('tomador_email', e.target.value)}
            className={NFSE_EMISSAO_INPUT_CLASS}
          />
        </div>
      </div>
    </div>
  );
}
