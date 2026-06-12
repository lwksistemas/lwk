import { useState } from 'react';
import {
  getCrmApiErrorDetail,
  crmMensagemEnvioCanalSucesso,
  downloadCrmDocumento,
  type CrmDocumentoTipo,
} from '@/lib/crm-utils';
import { crmEnviarCliente } from '@/lib/crm-enviar-cliente';

export interface CrmDocumentoEnvioFields {
  id: number;
  titulo: string;
  status_assinatura?: string;
  lead_telefone?: string;
  vendedor_email?: string;
  vendedor_telefone?: string;
}

/** Ações compartilhadas de envio e download para propostas/contratos CRM. */
export function useCrmDocumentoActions(
  tipo: CrmDocumentoTipo,
  reload: (silent?: boolean) => void | Promise<void>,
) {
  const [enviandoId, setEnviandoId] = useState<number | null>(null);

  const handleEnviarCliente = async (doc: CrmDocumentoEnvioFields, canal: 'email' | 'whatsapp') => {
    setEnviandoId(doc.id);
    try {
      const msg = await crmEnviarCliente(tipo, doc.id, canal, {
        statusAssinatura: doc.status_assinatura,
        leadTelefone: doc.lead_telefone,
        vendedorEmail: doc.vendedor_email,
        vendedorTelefone: doc.vendedor_telefone,
      });
      alert(msg || crmMensagemEnvioCanalSucesso(canal));
      await reload(true);
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao enviar.'));
    } finally {
      setEnviandoId(null);
    }
  };

  const handleDownloadPdf = async (id: number, titulo: string) => {
    try {
      await downloadCrmDocumento(tipo, id, titulo, 'pdf');
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao baixar PDF.'));
    }
  };

  const handleDownloadDocx = async (id: number, titulo: string) => {
    try {
      await downloadCrmDocumento(tipo, id, titulo, 'docx');
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao baixar Word.'));
    }
  };

  return { enviandoId, handleEnviarCliente, handleDownloadPdf, handleDownloadDocx };
}
