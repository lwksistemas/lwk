'use client';

import { X } from 'lucide-react';
import { formatCrmBrl } from '@/lib/crm-utils';

interface CrmDocumentoDetalhesModalProps {
  aberto: boolean;
  onClose: () => void;
  titulo: string;
  oportunidadeTitulo: string;
  leadNome: string;
  statusExibicao: string;
  valorTotal?: string | null;
  conteudo?: string | null;
  /** ex.: número do contrato */
  numero?: string | null;
}

/**
 * Modal de visualização rápida (proposta/contrato) — layout unificado CRM.
 */
export default function CrmDocumentoDetalhesModal({
  aberto,
  onClose,
  titulo,
  oportunidadeTitulo,
  leadNome,
  statusExibicao,
  valorTotal,
  conteudo,
  numero,
}: CrmDocumentoDetalhesModalProps) {
  if (!aberto) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-[80]" onClick={onClose} />
      <div className="fixed inset-0 z-[81] flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Detalhes</h2>
            <button type="button" onClick={onClose} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
              <X size={20} />
            </button>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              <p>
                <span className="font-medium">Título:</span> {titulo}
              </p>
              {numero ? (
                <p>
                  <span className="font-medium">Número:</span> {numero}
                </p>
              ) : null}
              <p>
                <span className="font-medium">Oportunidade:</span> {oportunidadeTitulo}
              </p>
              <p>
                <span className="font-medium">Lead:</span> {leadNome}
              </p>
              <p>
                <span className="font-medium">Status:</span> {statusExibicao}
              </p>
              {valorTotal ? (
                <p>
                  <span className="font-medium">Valor:</span> {formatCrmBrl(valorTotal)}
                </p>
              ) : null}
              {conteudo ? (
                <p>
                  <span className="font-medium">Conteúdo:</span>
                  <br />
                  <pre className="whitespace-pre-wrap text-sm mt-1">{conteudo}</pre>
                </p>
              ) : null}
              <button type="button" onClick={onClose} className="w-full mt-4 py-2 border rounded-lg">
                Fechar
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
