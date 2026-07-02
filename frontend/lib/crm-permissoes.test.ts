import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  getCrmPermissoes,
  hasCrmAcessoTotal,
  syncCrmPermissoesSession,
  temPermissaoCrm,
} from './crm-permissoes';

function mockBrowserSession() {
  const storage: Record<string, string> = {};
  const session = {
    getItem: (key: string) => (key in storage ? storage[key] : null),
    setItem: (key: string, value: string) => {
      storage[key] = value;
    },
    removeItem: (key: string) => {
      delete storage[key];
    },
    clear: () => {
      for (const key of Object.keys(storage)) delete storage[key];
    },
    key: (index: number) => Object.keys(storage)[index] ?? null,
    get length() {
      return Object.keys(storage).length;
    },
  };
  vi.stubGlobal('window', { sessionStorage: session });
  vi.stubGlobal('sessionStorage', session);
  return storage;
}

describe('crm-permissoes', () => {
  let store: Record<string, string>;

  beforeEach(() => {
    store = mockBrowserSession();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('syncCrmPermissoesSession persiste acesso_total e permissoes', () => {
    syncCrmPermissoesSession({
      acesso_total: true,
      permissoes: ['view_lead', 'view_proposta'],
    });
    expect(sessionStorage.getItem('crm_acesso_total')).toBe('1');
    expect(JSON.parse(sessionStorage.getItem('crm_permissoes') || '[]')).toEqual([
      'view_lead',
      'view_proposta',
    ]);
  });

  it('hasCrmAcessoTotal retorna true para owner (não vendedor)', () => {
    expect(hasCrmAcessoTotal()).toBe(true);
  });

  it('hasCrmAcessoTotal retorna false para vendedor sem flag admin', () => {
    sessionStorage.setItem('is_vendedor', '1');
    expect(hasCrmAcessoTotal()).toBe(false);
  });

  it('temPermissaoCrm libera quando não há lista (legado)', () => {
    sessionStorage.setItem('is_vendedor', '1');
    expect(temPermissaoCrm('view_lead')).toBe(true);
  });

  it('temPermissaoCrm bloqueia codename ausente na lista', () => {
    sessionStorage.setItem('is_vendedor', '1');
    syncCrmPermissoesSession({ acesso_total: false, permissoes: ['view_lead'] });
    expect(temPermissaoCrm('view_proposta')).toBe(false);
    expect(temPermissaoCrm('view_lead')).toBe(true);
  });

  it('getCrmPermissoes ignora JSON inválido', () => {
    sessionStorage.setItem('crm_permissoes', '{invalid');
    expect(getCrmPermissoes()).toEqual([]);
  });
});
