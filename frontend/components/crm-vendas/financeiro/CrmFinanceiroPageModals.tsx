'use client';

import CrmConfirmActionModal from '@/components/crm-vendas/CrmConfirmActionModal';
import { CrmGrupoModal, CrmLancamentoModal } from '@/components/crm-vendas/financeiro/CrmFinanceiroModals';
import { getFinanceiroConfirmCopy } from '@/lib/crm-financeiro-confirm';
import type { useCrmFinanceiroPage } from '@/hooks/crm-vendas/useCrmFinanceiroPage';
import type { TipoFinanceiro } from '@/lib/crm-financeiro-types';

interface Props {
  f: ReturnType<typeof useCrmFinanceiroPage>;
  tipoAtivo: TipoFinanceiro;
  gruposModal: ReturnType<typeof useCrmFinanceiroPage>['grupos'];
}

export function CrmFinanceiroPageModals({ f, tipoAtivo, gruposModal }: Props) {
  const confirmCopy = getFinanceiroConfirmCopy(f.confirmAction);

  return (
    <>
      <CrmLancamentoModal
        open={f.showModal}
        tipo={f.modalTipo}
        editing={f.editing}
        grupos={gruposModal}
        vendedores={f.vendedores}
        isAdmin={f.isAdmin}
        saving={f.saving}
        onClose={() => f.setShowModal(false)}
        onSave={f.salvarLancamento}
      />

      <CrmGrupoModal
        open={f.showGrupoModal}
        editing={f.editingGrupo}
        tipoInicial={tipoAtivo}
        saving={f.saving}
        onClose={() => f.setShowGrupoModal(false)}
        onSave={f.salvarGrupo}
      />

      {confirmCopy && (
        <CrmConfirmActionModal
          open
          title={confirmCopy.title}
          message={confirmCopy.message}
          confirmLabel={confirmCopy.confirmLabel}
          variant={confirmCopy.variant}
          loading={f.confirmando || f.sincronizando}
          onClose={f.closeConfirm}
          onConfirm={f.executeConfirm}
        />
      )}
    </>
  );
}
