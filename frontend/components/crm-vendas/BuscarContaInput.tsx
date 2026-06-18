'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import apiClient from '@/lib/api-client';

export interface CrmContaBuscaItem {
  id: number;
  nome: string;
  segmento?: string;
  cnpj?: string;
}

const DEBOUNCE_MS = 300;
const MIN_QUERY_LEN = 2;

function rotuloConta(conta: CrmContaBuscaItem): string {
  const extras: string[] = [];
  if (conta.cnpj) extras.push(conta.cnpj);
  if (conta.segmento) extras.push(conta.segmento);
  return extras.length ? `${conta.nome} — ${extras.join(' · ')}` : conta.nome;
}

interface BuscarContaInputProps {
  contaId: string;
  onContaChange: (id: string) => void;
  /** Nome exibido ao editar (ex.: conta_nome do contato). */
  initialNome?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
  limit?: number;
}

export default function BuscarContaInput({
  contaId,
  onContaChange,
  initialNome = '',
  placeholder = 'Buscar conta pelo nome, CNPJ ou e-mail...',
  required = false,
  disabled = false,
  className = '',
  limit = 10,
}: BuscarContaInputProps) {
  const [busca, setBusca] = useState(initialNome || '');
  const [resultados, setResultados] = useState<CrmContaBuscaItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [nomeSelecionado, setNomeSelecionado] = useState(initialNome || '');
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const limparSelecao = useCallback(() => {
    onContaChange('');
    setNomeSelecionado('');
    setBusca('');
    setResultados([]);
  }, [onContaChange]);

  const selecionar = useCallback(
    (conta: CrmContaBuscaItem) => {
      onContaChange(String(conta.id));
      setNomeSelecionado(conta.nome);
      setBusca(conta.nome);
      setResultados([]);
    },
    [onContaChange],
  );

  // Carregar rótulo quando só temos o id (edição ou ?conta_id=)
  useEffect(() => {
    if (!contaId) {
      if (!initialNome) {
        setNomeSelecionado('');
        setBusca('');
      }
      return;
    }
    if (initialNome) {
      setNomeSelecionado(initialNome);
      setBusca(initialNome);
      return;
    }
    let cancelled = false;
    apiClient
      .get<CrmContaBuscaItem>(`/crm-vendas/contas/${contaId}/`)
      .then((res) => {
        if (cancelled) return;
        setNomeSelecionado(res.data.nome);
        setBusca(res.data.nome);
      })
      .catch(() => {
        if (!cancelled) limparSelecao();
      });
    return () => {
      cancelled = true;
    };
  }, [contaId, initialNome, limparSelecao]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const q = busca.trim();
    if (contaId && nomeSelecionado && q === nomeSelecionado) {
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
        const res = await apiClient.get<{ contas: CrmContaBuscaItem[] }>('/crm-vendas/busca/', {
          params: { q, limit },
        });
        setResultados(res.data.contas ?? []);
      } catch {
        setResultados([]);
      } finally {
        setLoading(false);
      }
    }, DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [busca, contaId, nomeSelecionado, limit]);

  const inputClass =
    'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent';

  const mostrarLista =
    busca.trim().length >= MIN_QUERY_LEN &&
    !contaId &&
    (loading || resultados.length > 0 || !loading);

  return (
    <div className={className}>
      <input type="hidden" name="conta_id" value={contaId} required={required} />
      <input
        type="text"
        value={busca}
        disabled={disabled}
        onChange={(e) => {
          const valor = e.target.value;
          setBusca(valor);
          if (contaId && valor !== nomeSelecionado) {
            onContaChange('');
            setNomeSelecionado('');
          }
        }}
        className={inputClass}
        placeholder={placeholder}
        autoComplete="off"
      />
      {loading && busca.trim().length >= MIN_QUERY_LEN && !contaId && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Buscando...</p>
      )}
      {mostrarLista && resultados.length > 0 && (
        <div className="w-full mt-1 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 max-h-40 overflow-y-auto shadow-sm">
          {resultados.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => selecionar(c)}
              className="w-full text-left px-3 py-2 text-sm text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-600 border-b border-gray-100 dark:border-gray-600 last:border-b-0"
            >
              {rotuloConta(c)}
            </button>
          ))}
        </div>
      )}
      {busca.trim().length >= MIN_QUERY_LEN && !contaId && !loading && resultados.length === 0 && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Nenhuma conta encontrada.</p>
      )}
      {contaId && nomeSelecionado && (
        <div className="flex items-center justify-between gap-2 mt-1">
          <p className="text-xs text-green-600 dark:text-green-400">✓ {nomeSelecionado}</p>
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
