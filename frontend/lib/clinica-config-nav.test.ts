import { describe, expect, it } from 'vitest';
import { abaConfigAtiva, perfilSubmenuAtivo } from '@/lib/clinica-config-nav';

describe('clinica-config-nav', () => {
  it('marca Perfil na rota de Meu Perfil', () => {
    expect(abaConfigAtiva('/loja/clinicageral/clinica/perfil')).toBe('perfil');
    expect(perfilSubmenuAtivo('/loja/clinicageral/clinica/perfil')).toBe('meu-perfil');
  });

  it('marca o submenu de especialidades e prontuário', () => {
    expect(perfilSubmenuAtivo('/loja/clinicageral/clinica/perfil/especialidades')).toBe('especialidades');
    expect(perfilSubmenuAtivo('/loja/clinicageral/clinica/perfil/prontuario')).toBe('prontuario');
  });

  it('marca Meu consultório na agenda e na recepção', () => {
    expect(abaConfigAtiva('/loja/clinicageral/clinica/configuracoes/agenda')).toBe('consultorio');
    expect(abaConfigAtiva('/loja/clinicageral/clinica/configuracoes/recepcao')).toBe('consultorio');
  });
});
