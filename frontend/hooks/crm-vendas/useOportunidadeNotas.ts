'use client';

import { useCallback, useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail, normalizeListResponse } from '@/lib/crm-utils';

export type TipoNotaNegociacao = 'resposta_cliente' | 'nota_interna';

export interface OportunidadeNota {
  id: number;
  oportunidade: number;
  tipo: TipoNotaNegociacao;
  tipo_label: string;
  texto: string;
  autor_nome: string;
  created_at: string;
}

export function useOportunidadeNotas(oportunidadeId: number) {
  const [notas, setNotas] = useState<OportunidadeNota[]>([]);
  const [loading, setLoading] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const carregar = useCallback(async () => {
    setLoading(true);
    setErro(null);
    try {
      const res = await apiClient.get(
        `/crm-vendas/oportunidade-notas/?oportunidade_id=${oportunidadeId}`,
      );
      setNotas(normalizeListResponse<OportunidadeNota>(res.data));
    } catch (err: unknown) {
      setErro(getCrmApiErrorDetail(err, 'Erro ao carregar histórico.'));
      setNotas([]);
    } finally {
      setLoading(false);
    }
  }, [oportunidadeId]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  const adicionarNota = async (tipo: TipoNotaNegociacao, texto: string) => {
    setSalvando(true);
    setErro(null);
    try {
      await apiClient.post('/crm-vendas/oportunidade-notas/', {
        oportunidade: oportunidadeId,
        tipo,
        texto: texto.trim(),
      });
      await carregar();
    } catch (err: unknown) {
      const msg = getCrmApiErrorDetail(err, 'Erro ao salvar nota.');
      setErro(msg);
      throw new Error(msg);
    } finally {
      setSalvando(false);
    }
  };

  return { notas, loading, salvando, erro, carregar, adicionarNota };
}

export function formatarDataHoraNegociacao(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}
