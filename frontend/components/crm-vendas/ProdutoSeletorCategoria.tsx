'use client';

import { useState } from 'react';
import { ChevronLeft, X, Plus } from 'lucide-react';

interface Produto {
  id: number;
  nome: string;
  tipo: string;
  preco: string;
  codigo?: string;
  categoria_nome?: string;
  categoria_cor?: string;
}

interface Props {
  produtos: Produto[];
  onSelecionar: (produto: Produto) => void;
  onFechar: () => void;
}

export default function ProdutoSeletorCategoria({ produtos, onSelecionar, onFechar }: Props) {
  const [categoriaSelecionada, setCategoriaSelecionada] = useState<string | null>(null);

  // Agrupar por categoria
  const grupos = produtos.reduce<Record<string, Produto[]>>((acc, p) => {
    const cat = p.categoria_nome || 'Sem Categoria';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(p);
    return acc;
  }, {});

  const categorias = Object.keys(grupos).sort((a, b) => {
    if (a === 'Sem Categoria') return 1;
    if (b === 'Sem Categoria') return -1;
    return a.localeCompare(b);
  });

  // Cor da categoria (pega do primeiro produto)
  const corCategoria = (cat: string) => {
    const p = grupos[cat]?.[0];
    return p?.categoria_cor || '#3B82F6';
  };

  const produtosDaCategoria = categoriaSelecionada ? grupos[categoriaSelecionada] || [] : [];

  return (
    <div className="border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 shadow-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
        {categoriaSelecionada ? (
          <button
            type="button"
            onClick={() => setCategoriaSelecionada(null)}
            className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-300 hover:text-gray-900"
          >
            <ChevronLeft size={14} /> Categorias
          </button>
        ) : (
          <span className="text-xs font-medium text-gray-600 dark:text-gray-300">Selecionar produto</span>
        )}
        <button type="button" onClick={onFechar} className="p-0.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600">
          <X size={14} className="text-gray-500" />
        </button>
      </div>

      <div className="max-h-56 overflow-y-auto">
        {!categoriaSelecionada ? (
          // Grade de categorias
          <div className="grid grid-cols-2 gap-1.5 p-2">
            {categorias.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setCategoriaSelecionada(cat)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-left transition"
              >
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: corCategoria(cat) }}
                />
                <div className="min-w-0">
                  <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">{cat}</p>
                  <p className="text-[10px] text-gray-500">{grupos[cat].length} item{grupos[cat].length !== 1 ? 's' : ''}</p>
                </div>
              </button>
            ))}
          </div>
        ) : (
          // Lista de produtos da categoria
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {produtosDaCategoria.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => { onSelecionar(p); onFechar(); }}
                className="w-full flex items-center justify-between px-3 py-2 hover:bg-blue-50 dark:hover:bg-blue-900/20 text-left transition"
              >
                <div className="min-w-0">
                  <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
                    {p.codigo ? <span className="text-gray-400 mr-1">[{p.codigo}]</span> : null}
                    {p.nome}
                  </p>
                  <p className="text-[10px] text-gray-500 capitalize">{p.tipo}</p>
                </div>
                <span className="text-xs font-semibold text-green-600 dark:text-green-400 shrink-0 ml-2">
                  {parseFloat(p.preco).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
