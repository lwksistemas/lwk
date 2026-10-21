'use client';

import { useEffect, useState } from 'react';
import { fetchAllPaginatedResults } from '@/lib/crm-utils';
import type { ComissaoCategoriaItem } from '@/lib/crm-funcionarios';

interface CategoriaOpcao {
  id: number;
  nome: string;
}

const inputClass =
  'w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-[#1e3a5f] text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0176d3]';

export function ComissaoVendedorCategorias({
  valores,
  onChange,
}: {
  valores: ComissaoCategoriaItem[];
  onChange: (itens: ComissaoCategoriaItem[]) => void;
}) {
  const [categorias, setCategorias] = useState<CategoriaOpcao[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const [tipos, setTipos] = useState<Record<number, 'fixo' | 'percentual'>>({});

  useEffect(() => {
    let cancelado = false;
    fetchAllPaginatedResults<CategoriaOpcao>('/crm-vendas/categorias-produtos-servicos/', { ativo: 'true' })
      .then((lista) => {
        if (!cancelado) setCategorias(lista);
      })
      .catch(() => {
        if (!cancelado) setErro('Não foi possível carregar as categorias.');
      })
      .finally(() => {
        if (!cancelado) setCarregando(false);
      });
    return () => {
      cancelado = true;
    };
  }, []);

  const atual = (categoriaId: number) => valores.find((item) => item.categoria_id === categoriaId);

  const definir = (categoriaId: number, tipo: 'fixo' | 'percentual', valor: string) => {
    const resto = valores.filter((item) => item.categoria_id !== categoriaId);
    if (valor.trim() === '') {
      onChange(resto);
      return;
    }
    onChange([...resto, { categoria_id: categoriaId, tipo, valor }]);
  };

  if (carregando) return <p className="text-sm text-gray-500">Carregando categorias...</p>;
  if (erro) return <p className="text-sm text-red-600">{erro}</p>;
  if (categorias.length === 0) {
    return <p className="text-sm text-gray-500">Cadastre categorias em Produtos e serviços para configurar a comissão.</p>;
  }

  return (
    <div className="divide-y divide-gray-100 dark:divide-[#0d1f3c] rounded-lg border border-gray-200 dark:border-[#0d1f3c]">
      {categorias.map((categoria) => {
        const item = atual(categoria.id);
        const tipo = item?.tipo || tipos[categoria.id] || 'percentual';
        return (
          <div key={categoria.id} className="grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_9.5rem_7.5rem] gap-2 items-center px-3 py-2">
            <p className="text-sm text-gray-900 dark:text-white truncate">{categoria.nome}</p>
            <select
              value={tipo}
              onChange={(e) => {
                const proximo = e.target.value as 'fixo' | 'percentual';
                setTipos((atualTipos) => ({ ...atualTipos, [categoria.id]: proximo }));
                if (item?.valor) definir(categoria.id, proximo, item.valor);
              }}
              className={inputClass}
              aria-label={`Tipo de comissão em ${categoria.nome}`}
            >
              <option value="fixo">Valor fixo (R$)</option>
              <option value="percentual">Porcentagem (%)</option>
            </select>
            <input
              type="number"
              min="0"
              step="0.01"
              value={item?.valor || ''}
              onChange={(e) => definir(categoria.id, tipo, e.target.value)}
              className={inputClass}
              placeholder={tipo === 'fixo' ? 'R$' : '%'}
              aria-label={`Comissão em ${categoria.nome}`}
            />
          </div>
        );
      })}
    </div>
  );
}
