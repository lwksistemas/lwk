import { describe, expect, it } from 'vitest';
import {
  buildLojaManifest,
  getPWAContext,
  isInstallPWALojaPath,
  lojaManifestUrl,
  themeColorForLojaManifest,
} from '@/lib/pwa-loja';

describe('PWA da loja', () => {
  it('oferece instalar na agenda da Clínica', () => {
    expect(isInstallPWALojaPath('/loja/clinicageral/clinica/agenda')).toBe(true);
    expect(getPWAContext('/loja/clinicageral/clinica/agenda')).toEqual({
      allow: true,
      type: 'loja',
    });
  });

  it('não oferece no dashboard genérico nem na troca de senha', () => {
    expect(isInstallPWALojaPath('/loja/dashboard')).toBe(false);
    expect(isInstallPWALojaPath('/loja/trocar-senha')).toBe(false);
  });

  it('gera manifesto fora de /api, com ícones PNG da Clínica', () => {
    expect(lojaManifestUrl('clinicageral')).toBe('/pwa/manifest/loja?slug=clinicageral');
    const manifest = buildLojaManifest('clinicageral', {
      nome: 'Clínica Beta',
      tipo_loja_nome: 'Clínica',
      cor_primaria: '#10B981',
    });
    expect(manifest.start_url).toBe('/loja/clinicageral/login');
    expect(manifest.theme_color).toBe('#2F2E5B');
    expect(manifest.icons.some((i) => i.src === '/icons/clinica-192.png' && i.purpose === 'any')).toBe(true);
    expect(manifest.icons.some((i) => i.purpose === 'any maskable')).toBe(false);
  });

  it('usa a cor da loja quando não é o verde legado da estética', () => {
    expect(
      themeColorForLojaManifest({ tipo_loja_nome: 'Clínica', cor_primaria: '#112233' }),
    ).toBe('#112233');
  });
});
