'use client';

import { Search } from 'lucide-react';
import { formatCpfCnpj } from '@/lib/format-br';
import { NFSE_EMISSAO_INPUT_CLASS } from '@/lib/nfse-emissao-form';

export function ModalEmitirNFSeStepInicioClinica({
  documentoTomador,
  onDocumentoChange,
  pacienteBusca,
  onPacienteBuscaChange,
  pacienteOpcoes,
  pacienteSelecionadoId,
  onPacienteSelecionado,
  erro,
  buscandoTomador,
  onContinuar,
  onClose,
  emitenteNome,
}: {
  documentoTomador: string;
  onDocumentoChange: (value: string) => void;
  pacienteBusca: string;
  onPacienteBuscaChange: (value: string) => void;
  pacienteOpcoes: { id: number; nome: string; cpf: string }[];
  pacienteSelecionadoId: string;
  onPacienteSelecionado: (id: string) => void;
  erro: string;
  buscandoTomador: boolean;
  onContinuar: () => void | Promise<void>;
  onClose: () => void;
  emitenteNome: string;
}) {
  const nome = (emitenteNome || '').trim() || 'esta clínica';
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-[#8B3D52]/30 bg-[#F5E6EA] dark:bg-[#8B3D52]/20 p-3 text-sm text-gray-900 dark:text-gray-100">
        A nota será emitida pela <strong>{nome}</strong> (CNPJ cadastrado desta loja) para o
        cliente informado abaixo.
      </div>

      <div>
        <h3 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
          <Search size={18} style={{ color: 'var(--cb-primary, #8B3D52)' }} />
          Buscar cliente pelo nome
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
          Digite o nome do paciente. O CPF será preenchido automaticamente.
        </p>
        <input
          type="text"
          value={pacienteBusca}
          onChange={(e) => onPacienteBuscaChange(e.target.value)}
          className={NFSE_EMISSAO_INPUT_CLASS}
          placeholder="Nome do paciente..."
          disabled={buscandoTomador}
        />
        {pacienteOpcoes.length > 0 && (
          <select
            value={pacienteSelecionadoId}
            onChange={(e) => onPacienteSelecionado(e.target.value)}
            className={`${NFSE_EMISSAO_INPUT_CLASS} mt-2`}
            disabled={buscandoTomador}
          >
            <option value="">Selecione o paciente…</option>
            {pacienteOpcoes.map((p) => (
              <option key={p.id} value={String(p.id)}>
                {p.nome}
                {p.cpf ? ` — ${formatCpfCnpj(p.cpf)}` : ' (sem CPF)'}
              </option>
            ))}
          </select>
        )}
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
          <Search size={18} style={{ color: 'var(--cb-primary, #8B3D52)' }} />
          CPF ou CNPJ do cliente (tomador)
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
          Informe o CPF/CNPJ. Se o paciente estiver cadastrado, os dados serão preenchidos.
        </p>
        <input
          type="text"
          value={documentoTomador}
          onChange={(e) => onDocumentoChange(formatCpfCnpj(e.target.value))}
          className={NFSE_EMISSAO_INPUT_CLASS}
          placeholder="000.000.000-00"
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
          className="px-4 py-2 text-white rounded-lg font-medium inline-flex items-center gap-2 disabled:opacity-50"
          style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
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
