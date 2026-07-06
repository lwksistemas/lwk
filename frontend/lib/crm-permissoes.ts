/** Permissão Django necessária para exibir item do menu (codename, ex.: view_lead). */
export type CrmPermissaoCodename = string;

export interface CrmMePermissoes {
  acesso_total?: boolean;
  permissoes?: CrmPermissaoCodename[];
}

const STORAGE_ACESSO_TOTAL = 'crm_acesso_total';
const STORAGE_PERMISSOES = 'crm_permissoes';
const STORAGE_PERMISSOES_SYNCED = 'crm_permissoes_synced';

export function syncCrmPermissoesSession(d: CrmMePermissoes): void {
  if (typeof window === 'undefined') return;
  if (d.acesso_total) {
    sessionStorage.setItem(STORAGE_ACESSO_TOTAL, '1');
  } else {
    sessionStorage.removeItem(STORAGE_ACESSO_TOTAL);
  }
  if (Array.isArray(d.permissoes)) {
    sessionStorage.setItem(STORAGE_PERMISSOES, JSON.stringify(d.permissoes));
  } else {
    sessionStorage.removeItem(STORAGE_PERMISSOES);
  }
  sessionStorage.setItem(STORAGE_PERMISSOES_SYNCED, '1');
}

export function crmPermissoesForamCarregadas(): boolean {
  if (typeof window === 'undefined') return false;
  return sessionStorage.getItem(STORAGE_PERMISSOES_SYNCED) === '1';
}

export function hasCrmAcessoTotal(): boolean {
  if (typeof window === 'undefined') return true;
  if (sessionStorage.getItem(STORAGE_ACESSO_TOTAL) === '1') return true;
  return sessionStorage.getItem('is_vendedor') !== '1';
}

export function getCrmPermissoes(): CrmPermissaoCodename[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = sessionStorage.getItem(STORAGE_PERMISSOES);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((x) => typeof x === 'string') : [];
  } catch {
    return [];
  }
}

/** Verifica permissão CRM; vendedor sem permissões após sync = bloqueado. */
export function temPermissaoCrm(codename: CrmPermissaoCodename | undefined): boolean {
  if (!codename) return true;
  if (hasCrmAcessoTotal()) return true;
  if (!crmPermissoesForamCarregadas()) return true;
  const permissoes = getCrmPermissoes();
  if (permissoes.length === 0) return false;
  return permissoes.includes(codename);
}
