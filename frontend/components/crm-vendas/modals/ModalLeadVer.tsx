'use client';

import Link from 'next/link';
import { X, DollarSign } from 'lucide-react';
import type { Lead } from '@/components/crm-vendas/LeadsTable';

interface ModalLeadVerProps {
  lead: Lead;
  slug: string;
  origemLabel: (value: string) => string;
  statusLabel: (value: string) => string;
  formatarData: (s: string) => string;
  onClose: () => void;
  onCriarOportunidade: (lead: Lead) => void;
}

export default function ModalLeadVer({
  lead,
  slug,
  origemLabel,
  statusLabel,
  formatarData,
  onClose,
  onCriarOportunidade,
}: ModalLeadVerProps) {
  return (
    <div
      className="fixed inset-0 z-[80] flex items-center justify-center p-4 bg-black/50"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Detalhes do lead</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>
        <div className="p-4 space-y-4">
          <div className="flex items-center gap-3 pb-3 border-b border-gray-100 dark:border-gray-700">
            <div className="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-500/20 flex items-center justify-center text-blue-600 dark:text-blue-300 font-semibold text-lg">
              {lead.nome.charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="font-semibold text-gray-900 dark:text-white">{lead.nome}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">{lead.empresa || 'Sem empresa'}</p>
            </div>
          </div>
          <div className="flex gap-2 pb-3 border-b border-gray-100 dark:border-gray-700">
            <button
              type="button"
              onClick={() => onCriarOportunidade(lead)}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700"
            >
              <DollarSign size={16} />
              Criar oportunidade (venda)
            </button>
            <Link
              href={`/loja/${slug}/crm-vendas/pipeline`}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              Ver pipeline
            </Link>
          </div>
          <dl className="space-y-3 text-sm">
            {lead.contato_info && (
              <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg border border-blue-200 dark:border-blue-800">
                <dt className="text-blue-700 dark:text-blue-300 font-semibold mb-2">Detalhes do Contato</dt>
                <dd className="space-y-2">
                  <div>
                    <span className="text-gray-600 dark:text-gray-400 text-xs">Nome:</span>
                    <p className="text-gray-900 dark:text-white font-medium">{lead.contato_info.nome}</p>
                  </div>
                  {lead.contato_info.cargo && (
                    <div>
                      <span className="text-gray-600 dark:text-gray-400 text-xs">Cargo:</span>
                      <p className="text-gray-900 dark:text-white">{lead.contato_info.cargo}</p>
                    </div>
                  )}
                  {lead.contato_info.email && (
                    <div>
                      <span className="text-gray-600 dark:text-gray-400 text-xs">Email:</span>
                      <p className="text-gray-900 dark:text-white">{lead.contato_info.email}</p>
                    </div>
                  )}
                  {lead.contato_info.telefone && (
                    <div>
                      <span className="text-gray-600 dark:text-gray-400 text-xs">Telefone:</span>
                      <p className="text-gray-900 dark:text-white">{lead.contato_info.telefone}</p>
                    </div>
                  )}
                </dd>
              </div>
            )}
            {lead.conta_info && (
              <div>
                <dt className="text-gray-500 dark:text-gray-400 font-medium">Conta</dt>
                <dd className="text-gray-900 dark:text-white mt-0.5">{lead.conta_info.nome}</dd>
              </div>
            )}
            <div>
              <dt className="text-gray-500 dark:text-gray-400 font-medium">Email</dt>
              <dd className="text-gray-900 dark:text-white mt-0.5">{lead.email || '–'}</dd>
            </div>
            <div>
              <dt className="text-gray-500 dark:text-gray-400 font-medium">Telefone</dt>
              <dd className="text-gray-900 dark:text-white mt-0.5">{lead.telefone || '–'}</dd>
            </div>
            {(lead.cep || lead.logradouro || lead.cidade) && (
              <div>
                <dt className="text-gray-500 dark:text-gray-400 font-medium">Endereço</dt>
                <dd className="text-gray-900 dark:text-white mt-0.5">
                  {[
                    lead.logradouro,
                    lead.numero && `nº ${lead.numero}`,
                    lead.complemento,
                    lead.bairro,
                    lead.cidade && lead.uf ? `${lead.cidade}/${lead.uf}` : lead.cidade || lead.uf,
                    lead.cep,
                  ]
                    .filter(Boolean)
                    .join(', ') || '–'}
                </dd>
              </div>
            )}
            <div>
              <dt className="text-gray-500 dark:text-gray-400 font-medium">Origem</dt>
              <dd className="mt-0.5">
                <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-300">
                  {origemLabel(lead.origem)}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-gray-500 dark:text-gray-400 font-medium">Status</dt>
              <dd className="mt-0.5">
                <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-300">
                  {statusLabel(lead.status)}
                </span>
              </dd>
            </div>
            {lead.valor_estimado != null && lead.valor_estimado !== '' && (
              <div>
                <dt className="text-gray-500 dark:text-gray-400 font-medium">Valor estimado</dt>
                <dd className="text-gray-900 dark:text-white mt-0.5">
                  {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(lead.valor_estimado))}
                </dd>
              </div>
            )}
            <div>
              <dt className="text-gray-500 dark:text-gray-400 font-medium">Cadastrado em</dt>
              <dd className="text-gray-900 dark:text-white mt-0.5">{formatarData(lead.created_at)}</dd>
            </div>
          </dl>
          <div className="pt-2">
            <button
              type="button"
              onClick={onClose}
              className="w-full px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 font-medium"
            >
              Fechar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
