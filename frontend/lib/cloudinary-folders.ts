/** Pastas padronizadas no Cloudinary — espelha backend/core/cloudinary_folders.py */

import { useEffect, useMemo, useState } from 'react';
import apiClient from '@/lib/api-client';
import { isBetaEnvironment } from '@/lib/api-base';

const ROOT = 'lwksistemas';

function sanitizeSegment(value: string): string {
  const raw = (value || '').trim().toLowerCase().replace(/[^a-z0-9_-]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
  return raw || 'sem-identificador';
}

export function cloudinaryAmbiente(): 'beta' | 'producao' {
  return isBetaEnvironment() ? 'beta' : 'producao';
}

function path(...parts: string[]): string {
  return [ROOT, ...parts.filter(Boolean)].join('/');
}

export function cloudinaryDocumento(cpfCnpj: string): string {
  const digits = (cpfCnpj || '').replace(/\D/g, '');
  return digits || sanitizeSegment(cpfCnpj);
}

export function cloudinarySuperadminHomepage(): string {
  return path(cloudinaryAmbiente(), 'superadmin-homepage');
}

export function cloudinarySuperadminLogin(): string {
  return path(cloudinaryAmbiente(), 'superadmin-login');
}

export function cloudinarySuporte(): string {
  return path(cloudinaryAmbiente(), 'suporte');
}

export function cloudinarySuporteLogin(): string {
  return path(cloudinaryAmbiente(), 'suporte-login');
}

/** Pasta da loja (login, logo, fundo) — use CPF/CNPJ quando disponível. */
export function cloudinaryLojaLogin(cpfCnpjOrSlug: string): string {
  return path(cloudinaryAmbiente(), cloudinaryDocumento(cpfCnpjOrSlug));
}

export function cloudinaryLojaClinicaFotos(cpfCnpjOrSlug: string): string {
  return path(cloudinaryAmbiente(), cloudinaryDocumento(cpfCnpjOrSlug), 'clinica-beleza-fotos');
}

export function cloudinaryLojaRoot(cpfCnpjOrSlug: string): string {
  return path(cloudinaryAmbiente(), cloudinaryDocumento(cpfCnpjOrSlug));
}

/** Carrega CPF/CNPJ da loja para montar a pasta correta no Cloudinary. */
export function useLojaCloudinaryDocument(slug: string): string {
  const fallback = useMemo(() => sanitizeSegment(slug), [slug]);
  const [documento, setDocumento] = useState(fallback);

  useEffect(() => {
    let cancelled = false;
    setDocumento(fallback);
    if (!slug) return;

    apiClient
      .get<{ cpf_cnpj?: string }>(`/superadmin/lojas/info_publica/?slug=${encodeURIComponent(slug)}`)
      .then((res) => {
        if (cancelled) return;
        const doc = cloudinaryDocumento(res.data?.cpf_cnpj || '');
        setDocumento(doc !== 'sem-identificador' ? doc : fallback);
      })
      .catch(() => {
        if (!cancelled) setDocumento(fallback);
      });

    return () => {
      cancelled = true;
    };
  }, [slug, fallback]);

  return documento;
}
