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

function isCpfCnpjDigits(digits: string): boolean {
  return digits.length === 11 || digits.length === 14;
}

/** Resolve pasta da loja: cpf_cnpj → slug numérico → id interno. */
export function resolveLojaCloudinaryDocumento(data: {
  cpf_cnpj?: string;
  slug?: string;
  id?: number;
}): { documento: string; semCpfCnpj: boolean } {
  const cpf = cloudinaryDocumento(data.cpf_cnpj || '');
  if (cpf) return { documento: cpf, semCpfCnpj: false };

  const slugDigits = cloudinaryDocumento(data.slug || '');
  if (isCpfCnpjDigits(slugDigits)) {
    return { documento: slugDigits, semCpfCnpj: false };
  }

  if (data.id) return { documento: String(data.id), semCpfCnpj: true };
  return { documento: '', semCpfCnpj: true };
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
  const doc = cloudinaryDocumento(cpfCnpj) || cpfCnpj;
  return path(cloudinaryAmbiente(), doc, 'login');
}

export function cloudinaryLojaClinicaFotos(cpfCnpj: string): string {
  const doc = cloudinaryDocumento(cpfCnpj) || cpfCnpj;
  return path(cloudinaryAmbiente(), doc, 'clinica-beleza-fotos');
}

/** Foto de perfil do paciente no cadastro. */
export function cloudinaryLojaClinicaPacientePerfil(cpfCnpj: string): string {
  const doc = cloudinaryDocumento(cpfCnpj) || cpfCnpj;
  return path(cloudinaryAmbiente(), doc, 'clinica-beleza-pacientes');
}

export function cloudinaryLojaRoot(cpfCnpj: string): string {
  const doc = cloudinaryDocumento(cpfCnpj) || cpfCnpj;
  return path(cloudinaryAmbiente(), doc);
}

export interface LojaCloudinaryDocument {
  /** CPF/CNPJ (ou id interno se CPF ausente) */
  documento: string;
  /** Pronto para upload */
  ready: boolean;
  /** Carregando dados da loja */
  loading: boolean;
  /** true se não há CPF/CNPJ cadastrado (usa id da loja) */
  semCpfCnpj: boolean;
}

/** Carrega CPF/CNPJ da loja para pasta no Cloudinary. */
export function useLojaCloudinaryDocument(slug: string): LojaCloudinaryDocument {
  const [documento, setDocumento] = useState('');
  const [ready, setReady] = useState(false);
  const [loading, setLoading] = useState(true);
  const [semCpfCnpj, setSemCpfCnpj] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setDocumento('');
    setReady(false);
    setLoading(true);
    setSemCpfCnpj(false);
    if (!slug) {
      setLoading(false);
      return;
    }

    apiClient
      .get<{ cpf_cnpj?: string; slug?: string; id?: number }>(
        `/superadmin/lojas/info_publica/?slug=${encodeURIComponent(slug)}`,
      )
      .then((res) => {
        if (cancelled) return;
        const { documento: doc, semCpfCnpj: semDoc } = resolveLojaCloudinaryDocumento(
          res.data || {},
        );
        if (doc) {
          setDocumento(doc);
          setSemCpfCnpj(semDoc);
          setReady(true);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setDocumento('');
          setReady(false);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [slug]);

  return { documento, ready, loading, semCpfCnpj };
}
