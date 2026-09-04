import { APP_PATH } from '@/lib/clinica-geral-theme';

export function clinicaBase(slug: string) {
  return `/loja/${slug}/${APP_PATH}`;
}

export type AbaConfig = 'perfil' | 'consultorio' | 'ajustes' | 'integracoes' | 'extras';

export const PERFIL_SUBMENU = [
  { id: 'meu-perfil', label: 'Meu Perfil', suffix: 'perfil' },
  { id: 'especialidades', label: 'Especialidades', suffix: 'perfil/especialidades' },
  { id: 'prontuario', label: 'Prontuário', suffix: 'perfil/prontuario' },
] as const;

export const CONSULTORIO_MENU = [
  { label: 'Endereço', suffix: 'configuracoes/endereco' },
  { label: 'Tipos de consulta', suffix: 'configuracoes/tipos-consulta' },
  { label: 'Convênios/Empresas/Adm. de Benefícios', suffix: 'configuracoes/convenios' },
  { label: 'Agenda', suffix: 'configuracoes/agenda' },
  { label: 'Recepção/Adm', suffix: 'configuracoes/recepcao' },
] as const;

export const AJUSTES_MENU = [
  { label: 'Configurações de impressão', suffix: 'configuracoes/impressao' },
  { label: 'Encaminhamento', suffix: 'configuracoes/encaminhamento' },
  { label: 'Tabela de Acompanhamento', suffix: 'configuracoes/acompanhamento' },
] as const;

export function abaConfigAtiva(pathname: string): AbaConfig {
  if (pathname.includes('/perfil')) return 'perfil';
  if (pathname.includes('/configuracoes/whatsapp') || pathname.includes('/configuracoes/integracoes')) {
    return 'integracoes';
  }
  if (
    pathname.includes('/configuracoes/agenda') ||
    pathname.includes('/configuracoes/endereco') ||
    pathname.includes('/configuracoes/tipos-consulta') ||
    pathname.includes('/configuracoes/convenios') ||
    pathname.includes('/configuracoes/recepcao')
  ) {
    return 'consultorio';
  }
  if (
    pathname.includes('/configuracoes/impressao') ||
    pathname.includes('/configuracoes/encaminhamento') ||
    pathname.includes('/configuracoes/acompanhamento')
  ) {
    return 'ajustes';
  }
  return 'extras';
}

export function perfilSubmenuAtivo(pathname: string): string {
  if (pathname.includes('/perfil/especialidades')) return 'especialidades';
  if (pathname.includes('/perfil/prontuario')) return 'prontuario';
  return 'meu-perfil';
}
