import { describe, expect, it } from 'vitest';
import {
  buildCrmSidebarNavItems,
  filterCrmSidebarNavItems,
  isCrmSidebarNavActive,
} from './crm-sidebar-nav';

const base = '/loja/felix/crm-vendas';

describe('crm-sidebar-nav', () => {
  it('buildCrmSidebarNavItems inclui rotas principais com permissão', () => {
    const items = buildCrmSidebarNavItems(base);
    const leads = items.find((i) => i.label === 'Leads');
    expect(leads?.permission).toBe('view_lead');
    expect(items.some((i) => i.requiresAcessoTotal && i.label === 'Financeiro')).toBe(true);
  });

  it('isCrmSidebarNavActive respeita exact no Home', () => {
    const home = buildCrmSidebarNavItems(base)[0];
    expect(isCrmSidebarNavActive(`${base}/`, home)).toBe(true);
    expect(isCrmSidebarNavActive(`${base}/leads`, home)).toBe(false);
    expect(isCrmSidebarNavActive(`${base}/leads`, { href: `${base}/leads`, label: 'Leads' })).toBe(
      true,
    );
  });

  it('filterCrmSidebarNavItems oculta itens sem permissão', () => {
    const items = buildCrmSidebarNavItems(base);
    const filtered = filterCrmSidebarNavItems(items, {
      moduloAtivo: () => true,
      hasAcessoTotal: () => false,
      temPermissao: (codename) => codename === 'view_lead',
    });
    expect(filtered.map((i) => i.label)).toEqual(['Home', 'Leads']);
  });

  it('filterCrmSidebarNavItems oculta módulos inativos', () => {
    const items = buildCrmSidebarNavItems(base);
    const filtered = filterCrmSidebarNavItems(items, {
      moduloAtivo: (modulo) => modulo !== 'contatos',
      hasAcessoTotal: () => true,
      temPermissao: () => true,
    });
    expect(filtered.some((i) => i.label === 'Contatos')).toBe(false);
    expect(filtered.some((i) => i.label === 'Contas')).toBe(true);
  });
});
