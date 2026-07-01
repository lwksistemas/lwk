'use client';

import { Download, FileText, Mail, MessageCircle, RefreshCw, Trash2, X } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { useToast } from '@/components/ui/Toast';
import { formatDateTime } from '@/lib/financeiro-helpers';
import { NfseStatusPill } from '@/components/nfse/NfseStatusPill';
import {
  downloadNfseXmlBlob,
  nfsePodeBaixar,
  nfsePodeCancelar,
  nfsePodeEnviarWhatsapp,
  nfsePodeExcluirLoja,
  nfsePodeSincronizar,
  nfseSyncEndpoint,
  nfUsaIssnet,
} from '@/lib/nfse-helpers';
import type { NFSe, NfseLojaRowHandlers } from '../types';

type NfseLojaTableProps = {
  nfses: NFSe[];
  lojaProvedor?: string;
  syncingId: number | null;
  deletingId: number | null;
} & NfseLojaRowHandlers;

export function NfseLojaTable({
  nfses,
  lojaProvedor,
  syncingId,
  deletingId,
  onSync,
  onDelete,
  onDownloadPdf,
  onReenviarEmail,
  onEnviarWhatsapp,
  onCancelar,
  whatsappHabilitado = false,
}: NfseLojaTableProps) {
  return (
    <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <FileText size={20} /> Notas Fiscais
        </h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-[#0d1f3c]">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">NF</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Data</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Tomador</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Valor</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">ISS</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {nfses.map((nf) => (
              <NfseLojaRow
                key={nf.id}
                nf={nf}
                lojaProvedor={lojaProvedor}
                syncingId={syncingId}
                deletingId={deletingId}
                onSync={onSync}
                onDelete={onDelete}
                onDownloadPdf={onDownloadPdf}
                onReenviarEmail={onReenviarEmail}
                onEnviarWhatsapp={onEnviarWhatsapp}
                onCancelar={onCancelar}
                whatsappHabilitado={whatsappHabilitado}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function NfseLojaRow({
  nf,
  lojaProvedor,
  syncingId,
  deletingId,
  onSync,
  onDelete,
  onDownloadPdf,
  onReenviarEmail,
  onEnviarWhatsapp,
  onCancelar,
  whatsappHabilitado = false,
}: {
  nf: NFSe;
  lojaProvedor?: string;
  syncingId: number | null;
  deletingId: number | null;
} & NfseLojaRowHandlers) {
  const toast = useToast();
  const aliquota = Number(nf.aliquota_iss ?? 0).toFixed(2);
  const podeBaixar = nfsePodeBaixar(nf.status);
  const podeSincronizar = nfsePodeSincronizar(nf.status);

  return (
    <tr className="hover:bg-gray-50 dark:hover:bg-[#0d1f3c]/50">
      <td className="px-4 py-3 text-sm">
        <div className="font-bold text-gray-900 dark:text-white">{nf.numero_nf || '—'}</div>
        <div className="text-xs text-gray-500 dark:text-gray-400">RPS {nf.numero_rps}</div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap">
        {formatDateTime(nf.data_emissao)}
      </td>
      <td className="px-4 py-3 text-sm">
        <div className="font-medium text-gray-900 dark:text-white">{nf.tomador_nome}</div>
        <div className="text-xs text-gray-500 dark:text-gray-400">{nf.tomador_cpf_cnpj}</div>
      </td>
      <td className="px-4 py-3 text-sm text-right font-medium text-gray-900 dark:text-white">
        R$ {Number(nf.valor ?? 0).toFixed(2)}
      </td>
      <td className="px-4 py-3 text-sm text-right">
        <div className="text-gray-700 dark:text-gray-300">R$ {Number(nf.valor_iss ?? 0).toFixed(2)}</div>
        <div className="text-xs text-gray-500 dark:text-gray-400">{aliquota}%</div>
      </td>
      <td className="px-4 py-3 text-center">
        <NfseStatusPill status={nf.status} label={nf.status_display ?? nf.status} erro={nf.erro} />
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center justify-center gap-1">
          {podeBaixar && (
            <>
              <button
                type="button"
                title="Baixar PDF"
                onClick={(e) => onDownloadPdf(e, nf)}
                className="p-1.5 text-gray-600 hover:text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded"
              >
                <FileText size={16} />
              </button>
              <button
                type="button"
                title="Baixar XML"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  downloadNfseXmlBlob(
                    () => apiClient.get(`/nfse/${nf.id}/download_xml/`, { responseType: 'blob' }),
                    `nfse_${nf.numero_nf || nf.id}.xml`,
                  ).catch(() => toast.error('XML não disponível'));
                }}
                className="p-1.5 text-gray-600 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded"
              >
                <Download size={16} />
              </button>
              <button
                type="button"
                title="Reenviar por email"
                onClick={(e) => onReenviarEmail(e, nf)}
                className="p-1.5 text-gray-600 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded"
              >
                <Mail size={16} />
              </button>
              {whatsappHabilitado && nfsePodeEnviarWhatsapp(nf.status) && (
                <button
                  type="button"
                  title="Enviar PDF por WhatsApp"
                  onClick={(e) => onEnviarWhatsapp(e, nf)}
                  className="p-1.5 text-gray-600 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded"
                >
                  <MessageCircle size={16} />
                </button>
              )}
            </>
          )}
          {nfsePodeCancelar(nf.status) && (
            <button
              type="button"
              title="Cancelar NFS-e"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onCancelar(nf);
              }}
              className="p-1.5 text-gray-600 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
            >
              <X size={16} />
            </button>
          )}
          {podeSincronizar && nfseSyncEndpoint(nf, lojaProvedor) && (
            <button
              type="button"
              title={
                nfUsaIssnet(nf, lojaProvedor)
                  ? 'Sincronizar status com ISSNet (portal da prefeitura)'
                  : 'Sincronizar com Asaas'
              }
              onClick={(e) => onSync(e, nf)}
              disabled={syncingId === nf.id}
              className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-[#0176d3] hover:bg-[#0176d3]/10 border border-[#0176d3]/30 rounded disabled:opacity-50 whitespace-nowrap"
            >
              <RefreshCw size={14} className={syncingId === nf.id ? 'animate-spin shrink-0' : 'shrink-0'} />
              Sincronizar
            </button>
          )}
          {nfsePodeExcluirLoja(nf.status) && (
            <button
              type="button"
              title="Excluir"
              onClick={(e) => onDelete(e, nf)}
              disabled={deletingId === nf.id}
              className="p-1.5 text-gray-600 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded disabled:opacity-50"
            >
              <Trash2 size={16} />
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}
