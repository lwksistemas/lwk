'use client';

import { CRM_PROPOSTA_STATUS_LABEL as STATUS_LABEL } from '@/lib/crm-constants';
import CrmConfirmDeleteModal from '@/components/crm-vendas/CrmConfirmDeleteModal';
import CrmConfirmActionModal from '@/components/crm-vendas/CrmConfirmActionModal';
import CrmCancelarModal from '@/components/crm-vendas/CrmCancelarModal';
import CrmDocumentoDetalhesModal from '@/components/crm-vendas/CrmDocumentoDetalhesModal';
import {
  propostaConfirmCopy,
  type PropostasConfirmAction,
} from '@/app/(dashboard)/loja/[slug]/crm-vendas/propostas/components/PropostasTable';
import type { CrmProposta, CrmPropostaModalType } from '@/hooks/crm-vendas/useCrmPropostasPage';

export type PropostasPageModalsProps = {
  modalType: CrmPropostaModalType;
  selected: CrmProposta | null;
  submitting: boolean;
  confirmAction: PropostasConfirmAction;
  confirmando: boolean;
  onClose: () => void;
  onDelete: () => void;
  onCancelar: (motivo: string) => Promise<void>;
  onCloseConfirm: () => void;
  onExecuteConfirm: () => void;
};

export function PropostasPageModals({
  modalType,
  selected,
  submitting,
  confirmAction,
  confirmando,
  onClose,
  onDelete,
  onCancelar,
  onCloseConfirm,
  onExecuteConfirm,
}: PropostasPageModalsProps) {
  const confirmCopy = propostaConfirmCopy(confirmAction);

  return (
    <>
      {modalType === 'view' && selected && (
        <CrmDocumentoDetalhesModal
          aberto
          onClose={onClose}
          titulo={selected.titulo}
          oportunidadeTitulo={selected.oportunidade_titulo}
          leadNome={selected.lead_nome}
          statusExibicao={STATUS_LABEL[selected.status] || selected.status}
          valorTotal={selected.valor_total}
          descontoTipo={selected.desconto_tipo}
          descontoValor={selected.desconto_valor}
          valorComDesconto={selected.valor_com_desconto}
          conteudo={selected.conteudo}
        />
      )}

      {modalType === 'delete' && selected && (
        <CrmConfirmDeleteModal
          tituloItem={selected.titulo}
          enviando={submitting}
          onClose={onClose}
          onConfirm={onDelete}
        />
      )}

      {modalType === 'cancelar' && selected && (
        <CrmCancelarModal
          titulo={selected.titulo}
          tipo="proposta"
          onConfirm={onCancelar}
          onClose={onClose}
        />
      )}

      {confirmCopy && (
        <CrmConfirmActionModal
          open
          title={confirmCopy.title}
          message={confirmCopy.message}
          confirmLabel={confirmCopy.confirmLabel}
          variant={confirmCopy.variant}
          loading={confirmando}
          onClose={onCloseConfirm}
          onConfirm={onExecuteConfirm}
        />
      )}
    </>
  );
}
