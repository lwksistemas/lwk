import type { CrmConfirmVariant } from '@/components/crm-vendas/CrmConfirmActionModal';
import type { FinanceiroConfirmAction } from '@/lib/crm-financeiro-types';

export function getFinanceiroConfirmCopy(action: FinanceiroConfirmAction) {
  if (!action) return null;
  if (action.type === 'excluir_lancamento') {
    return {
      title: 'Excluir lançamento',
      message: `Excluir o lançamento "${action.item.descricao}"?`,
      confirmLabel: 'Excluir',
      variant: 'danger' as CrmConfirmVariant,
    };
  }
  if (action.type === 'excluir_grupo') {
    return {
      title: 'Excluir grupo',
      message: `Excluir o grupo "${action.grupo.nome}"?`,
      confirmLabel: 'Excluir',
      variant: 'danger' as CrmConfirmVariant,
    };
  }
  return {
    title: 'Sincronizar comissões',
    message: 'Importar comissões das oportunidades já ganhas para o financeiro?',
    confirmLabel: 'Sincronizar',
    variant: 'primary' as CrmConfirmVariant,
  };
}
