import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  APP_NOME,
  CLINICA_GERAL_DARK_KEY,
  applyClinicaGeralDark,
  isClinicaGeralAppPath,
  isClinicaGeralDarkEnabled,
  persistClinicaGeralDark,
  shouldApplyClinicaGeralTheme,
} from './clinica-geral-theme';

function memoryStorage() {
  const data = new Map<string, string>();
  return {
    getItem: (key: string) => (data.has(key) ? data.get(key)! : null),
    setItem: (key: string, value: string) => {
      data.set(key, String(value));
    },
    removeItem: (key: string) => {
      data.delete(key);
    },
  };
}

describe('clinica-geral-theme', () => {
  const local = memoryStorage();
  const session = memoryStorage();
  const darkClass = { on: false };
  const style = { colorScheme: '' };

  beforeEach(() => {
    const documentElement = {
      classList: {
        toggle: (_name: string, force?: boolean) => {
          darkClass.on = Boolean(force);
        },
        contains: () => darkClass.on,
        remove: () => {
          darkClass.on = false;
        },
      },
      style,
    };
    vi.stubGlobal('localStorage', local);
    vi.stubGlobal('sessionStorage', session);
    vi.stubGlobal('document', { documentElement });
    vi.stubGlobal('window', { localStorage: local, sessionStorage: session });
  });

  afterEach(() => {
    local.removeItem(CLINICA_GERAL_DARK_KEY);
    session.removeItem('loja_tipo_clinicageral');
    session.removeItem('loja_tipo_felix');
    darkClass.on = false;
    style.colorScheme = '';
    vi.unstubAllGlobals();
  });

  it('reconhece rotas do consultório', () => {
    expect(APP_NOME).toBe('Clínica');
    expect(isClinicaGeralAppPath('/loja/clinicageral/clinica/agenda')).toBe(true);
    expect(isClinicaGeralAppPath('/loja/clinicageral/clinica-geral/agenda')).toBe(true);
    expect(isClinicaGeralAppPath('/loja/felix/crm-vendas/leads')).toBe(false);
    expect(isClinicaGeralAppPath('/loja/harmonis/clinica-beleza/consultas')).toBe(false);
  });

  it('aplica tema do consultório no login quando o tipo está em cache', () => {
    session.setItem('loja_tipo_clinicageral', 'Clínica');
    expect(shouldApplyClinicaGeralTheme('/loja/clinicageral/login')).toBe(true);
    session.setItem('loja_tipo_felix', 'CRM Vendas');
    expect(shouldApplyClinicaGeralTheme('/loja/felix/login')).toBe(false);
  });

  it('padrão é claro (ausência da chave)', () => {
    expect(isClinicaGeralDarkEnabled()).toBe(false);
  });

  it('persiste e aplica modo escuro só quando escolhido', () => {
    persistClinicaGeralDark(true);
    expect(local.getItem(CLINICA_GERAL_DARK_KEY)).toBe('true');
    expect(isClinicaGeralDarkEnabled()).toBe(true);
    expect(darkClass.on).toBe(true);
    expect(style.colorScheme).toBe('dark');

    persistClinicaGeralDark(false);
    expect(isClinicaGeralDarkEnabled()).toBe(false);
    expect(darkClass.on).toBe(false);
    expect(style.colorScheme).toBe('light');
  });

  it('applyClinicaGeralDark não grava localStorage', () => {
    applyClinicaGeralDark(true);
    expect(local.getItem(CLINICA_GERAL_DARK_KEY)).toBeNull();
  });
});
