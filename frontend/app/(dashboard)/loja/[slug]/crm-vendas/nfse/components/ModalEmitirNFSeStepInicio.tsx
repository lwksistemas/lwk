'use client';

import { Search } from 'lucide-react';
import { formatCpfCnpj } from '@/lib/format-br';
import { NFSE_EMISSAO_INPUT_CLASS } from '@/lib/nfse-emissao-form';
import BuscarContaInput from '@/components/crm-vendas/BuscarContaInput';

export function ModalEmitirNFSeStepInicio({
  documentoTomador,
  onDocumentoChange,
  contaBuscaId,
  onContaBuscaChange,
  erro,
  buscandoTomador,
  onContinuar,
  onClose,
  emitenteNome,
}: {
  documentoTomador: string;
  onDocumentoChange: (value: string) => void;
  contaBuscaId: string;
  onContaBuscaChange: (id: string) => void;
  erro: string;
  buscandoTomador: boolean;
  onContinuar: () => void | Promise<void>;
  onClose: () => void;
  /** Razão social / nome da loja logada (prestador da NFS-e). */
  emitenteNome: string;
}) {
  const nome = (emitenteNome || '').trim() || 'esta loja';
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20 p-3 text-sm text-blue-900 dark:text-blue-100">
        A nota será emitida pela <strong>{nome}</strong> (CNPJ cadastrado desta loja) para o
        cliente informado abaixo.
      </div>

      <div>
        <h3 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
          <Search size={18} className="text-[#0176d3]" />
          Buscar cliente pelo nome
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
          Digite o nome da empresa (ex.: ULTRASIS, ANADEM). O CNPJ será preenchido automaticamente.
        </p>
        <BuscarContaInput
          contaId={contaBuscaId}
          onContaChange={onContaBuscaChange}
          placeholder="Buscar conta pelo nome ou CNPJ..."
          disabled={buscandoTomador}
          inputClassName={NFSE_EMISSAO_INPUT_CLASS}
        />
      </div>

      <div className="relative">
        <div className="absolute inset-0 flex items-center" aria-hidden="true">
          <div className="w-full border-t border-gray-200 dark:border-gray-600" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-white dark:bg-[#16325c] text-gray-500 dark:text-gray-400">ou</span>
        </div>
      </div>

      <div>
        <h3 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
          <Search size={18} className="text-[#0176d3]" />
          CPF ou CNPJ do cliente (tomador)
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
          Informe o CPF/CNPJ do cliente que receberá a nota. Se estiver cadastrado no CRM, os dados
          serão preenchidos automaticamente.
        </p>
        <input
          type="text"
          value={documentoTomador}
          onChange={(e) => onDocumentoChange(formatCpfCnpj(e.target.value))}
          className={NFSE_EMISSAO_INPUT_CLASS}
          placeholder="00.000.000/0001-00"
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
