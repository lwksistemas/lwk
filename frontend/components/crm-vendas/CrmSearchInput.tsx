'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

const DEBOUNCE_MS = 300;
const MIN_QUERY_LEN = 2;

const defaultInputClass =
  'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent';

export interface CrmSearchInputProps<T> {
  selectedId: string;
  onSelectedIdChange: (id: string, item?: T) => void;
  initialLabel?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
  inputClassName?: string;
  hiddenInputName?: string;
  minQueryLen?: number;
  limit?: number;
  fetchById: (id: string) => Promise<{ label: string; displayLabel?: string }>;
  fetchResults: (query: string, limit: number) => Promise<T[]>;
  getItemId: (item: T) => string;
  formatLabel: (item: T) => string;
  listClassName?: string;
}

export default function CrmSearchInput<T>({
  selectedId,
  onSelectedIdChange,
  initialLabel = '',
  placeholder = 'Buscar...',
  required = false,
  disabled = false,
  className = '',
  inputClassName = '',
  hiddenInputName,
  minQueryLen = MIN_QUERY_LEN,
  limit = 10,
  fetchById,
  fetchResults,
  getItemId,
  formatLabel,
  listClassName = 'rounded-md',
}: CrmSearchInputProps<T>) {
  const [busca, setBusca] = useState(initialLabel || '');
  const [resultados, setResultados] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [nomeSelecionado, setNomeSelecionado] = useState(initialLabel || '');
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const limparSelecao = useCallback(() => {
    onSelectedIdChange('');
    setNomeSelecionado('');
    setBusca('');
    setResultados([]);
  }, [onSelectedIdChange]);

  const selecionar = useCallback(
    (item: T) => {
      onSelectedIdChange(getItemId(item), item);
      const label = formatLabel(item);
      setNomeSelecionado(label);
      setBusca(label);
      setResultados([]);
    },
    [formatLabel, getItemId, onSelectedIdChange],
  );

  useEffect(() => {
    if (!selectedId) {
      if (!initialLabel) {
        setNomeSelecionado('');
        setBusca('');
      }
      return;
    }
    if (initialLabel) {
      setNomeSelecionado(initialLabel);
      setBusca(initialLabel);
      return;
    }
    let cancelled = false;
    fetchById(selectedId)
      .then((res) => {
        if (cancelled) return;
        const label = res.displayLabel ?? res.label;
        setNomeSelecionado(res.label);
        setBusca(label);
      })
      .catch(() => {
        if (!cancelled) limparSelecao();
      });
    return () => {
      cancelled = true;
    };
  }, [selectedId, initialLabel, fetchById, limparSelecao]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const q = busca.trim();
    if (selectedId && nomeSelecionado && q === nomeSelecionado) {
      setResultados([]);
      return;
    }
    if (q.length < minQueryLen) {
      setResultados([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    debounceRef.current = setTimeout(async () => {
      try {
        setResultados(await fetchResults(q, limit));
      } catch {
        setResultados([]);
      } finally {
        setLoading(false);
      }
    }, DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [busca, selectedId, nomeSelecionado, minQueryLen, limit, fetchResults]);

  const mostrarLista =
    busca.trim().length >= minQueryLen && !selectedId && (loading || resultados.length > 0 || !loading);

  return (
    <div className={className}>
      {hiddenInputName && (
        <input type="hidden" name={hiddenInputName} value={selectedId} required={required} />
      )}
      <input
        type="text"
        value={busca}
        disabled={disabled}
        onChange={(e) => {
          const valor = e.target.value;
          setBusca(valor);
          if (selectedId && valor !== nomeSelecionado) {
            onSelectedIdChange('');
            setNomeSelecionado('');
          }
        }}
        className={inputClassName || defaultInputClass}
        placeholder={placeholder}
        autoComplete="off"
      />
      {loading && busca.trim().length >= minQueryLen && !selectedId && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Buscando...</p>
      )}
      {mostrarLista && resultados.length > 0 && (
        <div
          className={`w-full mt-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 max-h-40 overflow-y-auto shadow-sm ${listClassName}`}
        >
          {resultados.map((item) => (
            <button
              key={getItemId(item)}
              type="button"
              onClick={() => selecionar(item)}
              className="w-full text-left px-3 py-2 text-sm text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-600 border-b border-gray-100 dark:border-gray-600 last:border-b-0"
            >
              {formatLabel(item)}
            </button>
          ))}
        </div>
      )}
      {busca.trim().length >= minQueryLen && !selectedId && !loading && resultados.length === 0 && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Nenhum resultado encontrado.</p>
      )}
      {selectedId && nomeSelecionado && (
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
