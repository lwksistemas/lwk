'use client';

import { useState } from 'react';
import { X } from 'lucide-react';
import {
  NFSE_CANCELAMENTO_OPCOES,
  NFSE_ISSNET_ERRO_EMISSAO_AVISO,
  isIssnetProvedor,
  montarMotivoCancelamento,
  type NfseCancelamentoEscolha,
} from '@/lib/nfse-helpers';

export interface NfseCancelamentoModalProps {
  identificador: string;
  provedor?: string | null;
  loading?: boolean;
  onClose: () => void;
  onConfirm: (escolha: NfseCancelamentoEscolha) => void;
}

type Step = 'form' | 'issnet_aviso';

export function NfseCancelamentoModal({
  identificador,
  provedor,
  loading = false,
  onClose,
  onConfirm,
}: NfseCancelamentoModalProps) {
  const [step, setStep] = useState<Step>('form');
  const [codigo, setCodigo] = useState('');
  const [motivoTexto, setMotivoTexto] = useState('');
  const [erro, setErro] = useState<string | null>(null);
  const [pendente, setPendente] = useState<NfseCancelamentoEscolha | null>(null);

  const fechar = () => {
    if (loading) return;
    onClose();
  };

  const enviarFormulario = () => {
    if (!codigo || !NFSE_CANCELAMENTO_OPCOES[codigo]) {
      setErro('Selecione um motivo de cancelamento.');
      return;
    }
    setErro(null);
    const escolha: NfseCancelamentoEscolha = {
      codigo,
      motivo: montarMotivoCancelamento(codigo, motivoTexto),
    };
    if (codigo === '1' && isIssnetProvedor(provedor)) {
      setPendente(escolha);
      setStep('issnet_aviso');
      return;
    }
    onConfirm(escolha);
  };

  const confirmarIssnet = () => {
    if (pendente) onConfirm(pendente);
  };

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-[80]" onClick={fechar} />
      <div className="fixed inset-0 z-[81] flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {step === 'form' ? `Cancelar NFS-e ${identificador}` : 'Atenção — ISSNet'}
            </h2>
            <button
              type="button"
              onClick={fechar}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <X size={20} />
            </button>
          </div>

          {step === 'form' ? (
            <div className="p-6 space-y-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Escolha o motivo do cancelamento na prefeitura:
              </p>
              <div className="space-y-2">
                {Object.entries(NFSE_CANCELAMENTO_OPCOES).map(([value, label]) => (
                  <label
                    key={value}
                    className="flex items-start gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-600 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50"
                  >
                    <input
                      type="radio"
                      name="nfse-motivo"
                      value={value}
                      checked={codigo === value}
                      onChange={() => setCodigo(value)}
                      className="mt-1"
                    />
                    <span className="text-sm text-gray-800 dark:text-gray-200">
                      <span className="font-medium">{value}</span> — {label}
                    </span>
                  </label>
                ))}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Descrição adicional (opcional)
                </label>
                <textarea
                  value={motivoTexto}
                  onChange={(e) => setMotivoTexto(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                  placeholder="Detalhe o motivo, se necessário"
                />
              </div>
              {erro && <p className="text-sm text-red-600 dark:text-red-400">{erro}</p>}
              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={fechar}
                  disabled={loading}
                  className="flex-1 px-4 py-2 border rounded-lg disabled:opacity-50"
                >
                  Voltar
                </button>
                <button
                  type="button"
                  onClick={enviarFormulario}
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-50"
                >
                  {loading ? 'Enviando...' : 'Solicitar cancelamento'}
                </button>
              </div>
            </div>
          ) : (
            <div className="p-6 space-y-4">
              <p className="text-sm text-amber-800 dark:text-amber-200 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 whitespace-pre-line">
                {NFSE_ISSNET_ERRO_EMISSAO_AVISO}
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setStep('form')}
                  disabled={loading}
                  className="flex-1 px-4 py-2 border rounded-lg disabled:opacity-50"
                >
                  Escolher outro motivo
                </button>
                <button
                  type="button"
                  onClick={confirmarIssnet}
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-50"
                >
                  {loading ? 'Enviando...' : 'Continuar mesmo assim'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
