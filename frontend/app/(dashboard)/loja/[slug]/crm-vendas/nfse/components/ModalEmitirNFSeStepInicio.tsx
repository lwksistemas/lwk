'use client';

import { Search } from 'lucide-react';
import { formatCpfCnpj } from '@/lib/format-br';
import { NFSE_EMISSAO_INPUT_CLASS } from '@/lib/nfse-emissao-form';

export function ModalEmitirNFSeStepInicio({
  documentoTomador,
  onDocumentoChange,
  erro,
  buscandoTomador,
  onContinuar,
  onClose,
}: {
  documentoTomador: string;
  onDocumentoChange: (value: string) => void;
  erro: string;
  buscandoTomador: boolean;
  onContinuar: () => void | Promise<void>;
  onClose: () => void;
}) {
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20 p-3 text-sm text-blue-900 dark:text-blue-100">
        A nota será emitida pela <strong>Felix Representações</strong> (CNPJ da loja) para o
        cliente informado abaixo.
      </div>

      <div>
        <h3 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
          <Search size={18} className="text-[#0176d3]" />
          CPF ou CNPJ do cliente (tomador)
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
          Ex.: ULTRASIS INFORMATICA, ANADEM SA — informe o CNPJ do cliente que receberá a nota.
          Se estiver cadastrado no CRM, os dados serão preenchidos automaticamente.
        </p>
        <input
          type="text"
          value={documentoTomador}
          onChange={(e) => onDocumentoChange(formatCpfCnpj(e.target.value))}
          className={NFSE_EMISSAO_INPUT_CLASS}
          placeholder="00.000.000/0001-00"
          maxLength={18}
          autoFocus
          disabled={buscandoTomador}
        />
      </div>

      {erro && (
        <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
          {erro}
        </p>
      )}

      <div className="flex justify-end gap-2 pt-2">
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg"
        >
          Cancelar
        </button>
        <button
          type="button"
          onClick={onContinuar}
          disabled={buscandoTomador}
          className="px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] disabled:opacity-50 text-white rounded-lg font-medium inline-flex items-center gap-2"
        >
          {buscandoTomador && (
            <span className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
          )}
          {buscandoTomador ? 'Buscando...' : 'Continuar'}
        </button>
      </div>
    </div>
  );
}
