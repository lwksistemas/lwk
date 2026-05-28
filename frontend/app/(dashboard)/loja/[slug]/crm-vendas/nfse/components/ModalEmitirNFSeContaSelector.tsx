'use client';

import type { NfseEmissaoContaOption } from '@/lib/nfse-emissao-form';

export function ModalEmitirNFSeContaSelector({
  contas,
  loading,
  value,
  onChange,
}: {
  contas: NfseEmissaoContaOption[];
  loading: boolean;
  value: string;
  onChange: (id: number | string) => void;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Empresa / Pessoa Física *
      </label>
      {loading ? (
        <div className="text-center py-4">
          <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-[#0176d3]" />
        </div>
      ) : (
        <select
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
        >
          <option value="">Selecione...</option>
          {contas.filter((c) => c._tipo === 'conta').length > 0 && (
            <optgroup label="Empresas (Contas)">
              {contas
                .filter((c) => c._tipo === 'conta')
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    {c._display || c.nome}
                  </option>
                ))}
            </optgroup>
          )}
          {contas.filter((c) => c._tipo === 'lead').length > 0 && (
            <optgroup label="Pessoa Física (Leads com CPF/CNPJ)">
              {contas
                .filter((c) => c._tipo === 'lead')
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    {c._display || c.nome}
                  </option>
                ))}
            </optgroup>
          )}
        </select>
      )}
    </div>
  );
}
