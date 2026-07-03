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
  if (action.type === 'receber_comissoes') {
    return {
      title: 'Receber comissões',
      message: `Marcar como recebidas ${action.ids.length} comissão(ões) de vendas (${action.item.descricao})?`,
      confirmLabel: 'Receber',
      variant: 'primary' as CrmConfirmVariant,
    };
  }
  if (action.type === 'cancelar_comissoes') {
    return {
      title: 'Cancelar comissões',
      message: `Cancelar ${action.ids.length} comissão(ões) de vendas no período? Elas deixam de aparecer nos totais.`,
      confirmLabel: 'Cancelar comissões',
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
