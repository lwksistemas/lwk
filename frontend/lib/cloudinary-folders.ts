/** Pastas padronizadas no Cloudinary — espelha backend/core/cloudinary_folders.py */

const ROOT = 'lwksistemas';

function sanitizeSegment(value: string): string {
  const raw = (value || '').trim().toLowerCase().replace(/[^a-z0-9_-]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
  return raw || 'sem-identificador';
}

export function cloudinarySuperadminHomepage(): string {
  return `${ROOT}/superadmin/homepage`;
}

export function cloudinarySuperadminLogin(): string {
  return `${ROOT}/superadmin/login`;
}

export function cloudinarySuporte(): string {
  return `${ROOT}/suporte`;
}

export function cloudinarySuporteLogin(): string {
  return `${ROOT}/suporte/login`;
}

export function cloudinaryLojaLogin(slug: string): string {
  return `${ROOT}/${sanitizeSegment(slug)}/login`;
}

export function cloudinaryLojaClinicaFotos(slug: string): string {
  return `${ROOT}/${sanitizeSegment(slug)}/clinica-beleza/fotos-paciente`;
}

export function cloudinaryLojaRoot(slug: string): string {
  return `${ROOT}/${sanitizeSegment(slug)}`;
}
