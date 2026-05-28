'use client';

import { Download, FileText, Mail, Trash2, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { NfseProvedorBadge } from '@/components/nfse/NfseProvedorBadge';
import { NfseStatusBadge } from '@/components/nfse/NfseStatusBadge';
import { formatDateTime } from '@/lib/financeiro-helpers';
import {
  nfsePodeBaixar,
  nfsePodeCancelar,
  nfsePodeExcluirSuperadmin,
} from '@/lib/nfse-helpers';
import type { NFSeEmitida, NfseSuperadminHandlers } from '../types';

const TABLE_HEADERS = ['NF', 'Data', 'Tomador', 'Valor', 'ISS', 'Status', 'Provedor', 'Ações'];

type NfseSuperadminTableProps = {
  notas: NFSeEmitida[];
  loading: boolean;
} & NfseSuperadminHandlers;

export function NfseSuperadminTable({
  notas,
  loading,
  onBaixarPdf,
  onBaixarXml,
  onReenviar,
  onCancelar,
  onExcluir,
}: NfseSuperadminTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="w-5 h-5" />
          Notas Fiscais
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-muted-foreground">Carregando...</div>
        ) : notas.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            Nenhuma NFS-e encontrada. As notas aparecerão aqui quando forem emitidas automaticamente após
            pagamentos.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  {TABLE_HEADERS.map((h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {notas.map((nf) => (
                  <NfseSuperadminRow
                    key={nf.id}
                    nf={nf}
                    onBaixarPdf={onBaixarPdf}
                    onBaixarXml={onBaixarXml}
                    onReenviar={onReenviar}
                    onCancelar={onCancelar}
                    onExcluir={onExcluir}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function NfseSuperadminRow({
  nf,
  onBaixarPdf,
  onBaixarXml,
  onReenviar,
  onCancelar,
  onExcluir,
}: { nf: NFSeEmitida } & NfseSuperadminHandlers) {
  return (
    <tr className="hover:bg-gray-50 dark:hover:bg-gray-800">
      <td className="px-4 py-3">
        <div className="font-medium">{nf.numero_nf || '-'}</div>
        <div className="text-xs text-muted-foreground">RPS {nf.numero_rps}</div>
      </td>
      <td className="px-4 py-3 text-sm">{formatDateTime(nf.data_emissao)}</td>
      <td className="px-4 py-3">
        <div className="font-medium text-sm">{nf.tomador_nome}</div>
        <div className="text-xs text-muted-foreground">{nf.tomador_cpf_cnpj}</div>
        <div className="text-xs text-muted-foreground">{nf.loja_nome}</div>
      </td>
      <td className="px-4 py-3 text-sm font-medium">R$ {parseFloat(nf.valor).toFixed(2)}</td>
      <td className="px-4 py-3 text-sm text-muted-foreground">
        R$ {parseFloat(nf.valor_iss).toFixed(2)}
        <div className="text-xs">{nf.aliquota_iss}%</div>
      </td>
      <td className="px-4 py-3">
        <NfseStatusBadge status={nf.status} />
        {nf.erro_mensagem && (
          <div className="text-xs text-red-500 mt-1 max-w-[200px] truncate" title={nf.erro_mensagem}>
            {nf.erro_mensagem}
          </div>
        )}
      </td>
      <td className="px-4 py-3">
        <NfseProvedorBadge provedor={nf.provedor} />
      </td>
      <td className="px-4 py-3 space-x-1">
        {nfsePodeBaixar(nf.status) && (
          <Button size="sm" variant="ghost" onClick={() => onBaixarPdf(nf)} title="Baixar/Consultar PDF">
            <FileText className="w-4 h-4" />
          </Button>
        )}
        {nf.tem_xml && (
          <Button size="sm" variant="ghost" onClick={() => onBaixarXml(nf)} title="Baixar XML">
            <Download className="w-4 h-4" />
          </Button>
        )}
        {nfsePodeBaixar(nf.status) && nf.tomador_email && (
          <Button size="sm" variant="ghost" onClick={() => onReenviar(nf)} title="Reenviar email">
            <Mail className="w-4 h-4" />
          </Button>
        )}
        {nfsePodeCancelar(nf.status) && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onCancelar(nf)}
            title="Cancelar NF"
            className="text-red-500 hover:text-red-700"
          >
            <XCircle className="w-4 h-4" />
          </Button>
        )}
        {nfsePodeExcluirSuperadmin(nf.status) && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onExcluir(nf)}
            title="Excluir registro"
            className="text-red-500 hover:text-red-700"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        )}
      </td>
    </tr>
  );
}
