/** Pastas padronizadas no Cloudinary — espelha backend/core/cloudinary_folders.py */

import { useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import { isBetaEnvironment } from '@/lib/api-base';

const ROOT = 'lwksistemas';

export function cloudinaryAmbiente(): 'beta' | 'producao' {
  return isBetaEnvironment() ? 'beta' : 'producao';
}

function path(...parts: string[]): string {
  return [ROOT, ...parts.filter(Boolean)].join('/');
}

/** CPF/CNPJ só dígitos. */
export function cloudinaryDocumento(cpfCnpj: string): string {
  const digits = (cpfCnpj || '').replace(/\D/g, '');
  return digits || '';
}

export function cloudinarySuperadminHomepage(): string {
  return path(cloudinaryAmbiente(), 'superadmin', 'homepage');
}

export function cloudinarySuperadminLogin(): string {
  return path(cloudinaryAmbiente(), 'superadmin', 'login');
}

export function cloudinarySuporte(): string {
  return path(cloudinaryAmbiente(), 'suporte');
}

export function cloudinarySuporteLogin(): string {
  return path(cloudinaryAmbiente(), 'suporte', 'login');
}

/** Login da loja — pasta com CPF/CNPJ (não atalho/slug). */
export function cloudinaryLojaLogin(cpfCnpj: string): string {
  const doc = cloudinaryDocumento(cpfCnpj);
  return path(cloudinaryAmbiente(), doc, 'login');
}

export function cloudinaryLojaClinicaFotos(cpfCnpj: string): string {
  const doc = cloudinaryDocumento(cpfCnpj);
  return path(cloudinaryAmbiente(), doc, 'clinica-beleza-fotos');
}

export function cloudinaryLojaRoot(cpfCnpj: string): string {
  const doc = cloudinaryDocumento(cpfCnpj);
  return path(cloudinaryAmbiente(), doc);
}

export interface LojaCloudinaryDocument {
  /** CPF/CNPJ só dígitos */
  documento: string;
  /** true quando o CPF/CNPJ foi carregado da API */
  ready: boolean;
}

/** Carrega CPF/CNPJ da loja — nunca usa atalho/slug como pasta. */
export function useLojaCloudinaryDocument(slug: string): LojaCloudinaryDocument {
  const [documento, setDocumento] = useState('');
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setDocumento('');
    setReady(false);
    if (!slug) return;

    apiClient
      .get<{ cpf_cnpj?: string }>(`/superadmin/lojas/info_publica/?slug=${encodeURIComponent(slug)}`)
      .then((res) => {
        if (cancelled) return;
        const doc = cloudinaryDocumento(res.data?.cpf_cnpj || '');
        if (doc) {
          setDocumento(doc);
          setReady(true);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setDocumento('');
          setReady(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [slug]);

  return { documento, ready };
}
