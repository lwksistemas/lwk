'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import apiClient from '@/lib/api-client';

export interface CrmOportunidadeBuscaItem {
  id: number;
  titulo: string;
  lead_nome: string;
  lead_empresa: string;
  valor: string;
  etapa: string;
}

const DEBOUNCE_MS = 300;
const MIN_QUERY_LEN = 2;

function rotuloOportunidade(item: CrmOportunidadeBuscaItem): string {
  const cliente = item.lead_empresa || item.lead_nome;
  const valor = item.valor ? ` — R$ ${parseFloat(item.valor).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}` : '';
  return cliente ? `${item.titulo} (${cliente})${valor}` : `${item.titulo}${valor}`;
}

interface BuscarOportunidadeInputProps {
  oportunidadeId: string;
  onOportunidadeChange: (id: string) => void;
  initialTitulo?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
  limit?: number;
}

export default function BuscarOportunidadeInput({
  oportunidadeId,
  onOportunidadeChange,
  initialTitulo = '',
  placeholder = 'Buscar oportunidade pelo título ou cliente...',
  required = false,
  disabled = false,
  className = '',
  limit = 10,
}: BuscarOportunidadeInputProps) {
  const [busca, setBusca] = useState(initialTitulo || '');
  const [resultados, setResultados] = useState<CrmOportunidadeBuscaItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [tituloSelecionado, setTituloSelecionado] = useState(initialTitulo || '');
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const limparSelecao = useCallback(() => {
    onOportunidadeChange('');
    setTituloSelecionado('');
    setBusca('');
    setResultados([]);
  }, [onOportunidadeChange]);

  const selecionar = useCallback(
    (item: CrmOportunidadeBuscaItem) => {
      onOportunidadeChange(String(item.id));
      setTituloSelecionado(item.titulo);
      setBusca(item.titulo);
      setResultados([]);
    },
    [onOportunidadeChange],
  );

  useEffect(() => {
    if (!oportunidadeId) {
      if (!initialTitulo) {
        setTituloSelecionado('');
        setBusca('');
      }
      return;
    }
    if (initialTitulo) {
      setTituloSelecionado(initialTitulo);
      setBusca(initialTitulo);
      return;
    }
    let cancelled = false;
    apiClient
      .get<{ titulo: string }>(`/crm-vendas/oportunidades/${oportunidadeId}/`)
      .then((res) => {
        if (cancelled) return;
        setTituloSelecionado(res.data.titulo);
        setBusca(res.data.titulo);
      })
      .catch(() => {
        if (!cancelled) limparSelecao();
      });
    return () => {
      cancelled = true;
    };
  }, [oportunidadeId, initialTitulo, limparSelecao]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const q = busca.trim();
    if (oportunidadeId && tituloSelecionado && q === tituloSelecionado) {
      setResultados([]);
      return;
    }
    if (q.length < MIN_QUERY_LEN) {
      setResultados([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await apiClient.get<{ oportunidades: CrmOportunidadeBuscaItem[] }>(
          '/crm-vendas/busca/',
          { params: { q, limit } },
        );
        setResultados(res.data.oportunidades ?? []);
      } catch {
        setResultados([]);
      } finally {
        setLoading(false);
      }
    }, DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [busca, oportunidadeId, tituloSelecionado, limit]);

  const inputClass =
    'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent';

  const mostrarLista =
    busca.trim().length >= MIN_QUERY_LEN &&
    !oportunidadeId &&
    (loading || resultados.length > 0 || !loading);

  return (
    <div className={className}>
      <input type="hidden" name="oportunidade_id" value={oportunidadeId} required={required} />
      <input
        type="text"
        value={busca}
        disabled={disabled}
        onChange={(e) => {
          const valor = e.target.value;
          setBusca(valor);
          if (oportunidadeId && valor !== tituloSelecionado) {
            onOportunidadeChange('');
            setTituloSelecionado('');
          }
        }}
        className={inputClass}
        placeholder={placeholder}
        autoComplete="off"
      />
      {loading && busca.trim().length >= MIN_QUERY_LEN && !oportunidadeId && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Buscando...</p>
      )}
      {mostrarLista && resultados.length > 0 && (
        <div className="w-full mt-1 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 max-h-40 overflow-y-auto shadow-sm">
          {resultados.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => selecionar(item)}
              className="w-full text-left px-3 py-2 text-sm text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-600 border-b border-gray-100 dark:border-gray-600 last:border-b-0"
            >
              {rotuloOportunidade(item)}
            </button>
          ))}
        </div>
      )}
      {busca.trim().length >= MIN_QUERY_LEN && !oportunidadeId && !loading && resultados.length === 0 && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Nenhuma oportunidade encontrada.</p>
      )}
      {oportunidadeId && tituloSelecionado && (
        <div className="flex items-center justify-between gap-2 mt-1">
          <p className="text-xs text-green-600 dark:text-green-400">✓ {tituloSelecionado}</p>
          {!disabled && (
            <button
              type="button"
              onClick={limparSelecao}
              className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >
              Remover
            </button>
          )}
        </div>
      )}
    </div>
  );
}
