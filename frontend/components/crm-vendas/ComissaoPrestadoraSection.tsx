'use client';

import { useEffect, useMemo, useState } from 'react';
import { fetchAllPaginatedResults } from '@/lib/crm-utils';

export interface ComissaoPrestadoraItem {
  produto_servico_id: number;
  valor: string;
}

interface CategoriaOpcao {
  id: number;
  nome: string;
  cor: string;
}

interface ServicoOpcao {
  id: number;
  nome: string;
  codigo: string;
  preco: string;
  categoria: number | null;
  ativo: boolean;
}

const inputClass =
  'w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-[#1e3a5f] text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0176d3]';

function moeda(valor: string) {
  const numero = parseFloat(valor);
  if (Number.isNaN(numero)) return '—';
  return numero.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

export function ComissaoPrestadoraSection({
  valores,
  onChange,
}: {
  valores: ComissaoPrestadoraItem[];
  onChange: (itens: ComissaoPrestadoraItem[]) => void;
}) {
  const [categorias, setCategorias] = useState<CategoriaOpcao[]>([]);
  const [servicos, setServicos] = useState<ServicoOpcao[]>([]);
  const [categoriaId, setCategoriaId] = useState<number | 'sem' | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;
    setCarregando(true);
    Promise.all([
      fetchAllPaginatedResults<CategoriaOpcao>('/crm-vendas/categorias-produtos-servicos/', { ativo: 'true' }),
      fetchAllPaginatedResults<ServicoOpcao>('/crm-vendas/produtos-servicos/', { ativo: 'true' }),
    ])
      .then(([cats, itens]) => {
        if (cancelado) return;
        setCategorias(cats);
        setServicos(itens.filter((item) => item.ativo !== false));
        setCategoriaId((atual) => atual ?? (cats[0]?.id ?? (itens.some((item) => !item.categoria) ? 'sem' : null)));
      })
      .catch(() => {
        if (!cancelado) setErro('Não foi possível carregar as categorias e os serviços.');
      })
      .finally(() => {
        if (!cancelado) setCarregando(false);
      });
    return () => {
      cancelado = true;
    };
  }, []);

  const daCategoria = useMemo(() => {
    if (categoriaId === 'sem') return servicos.filter((item) => !item.categoria);
    if (categoriaId == null) return [];
    return servicos.filter((item) => item.categoria === categoriaId);
  }, [categoriaId, servicos]);

  const temSemCategoria = servicos.some((item) => !item.categoria);

  const definirValor = (produtoId: number, valor: string) => {
    const resto = valores.filter((item) => item.produto_servico_id !== produtoId);
    if (valor.trim() === '') {
      onChange(resto);
      return;
    }
    onChange([...resto, { produto_servico_id: produtoId, valor }]);
  };

  const valorDe = (produtoId: number) =>
    valores.find((item) => item.produto_servico_id === produtoId)?.valor ?? '';

  const quantidadeNaCategoria = (id: number | 'sem') => {
    const ids = new Set(
      servicos
        .filter((item) => (id === 'sem' ? !item.categoria : item.categoria === id))
        .map((item) => item.id),
    );
    return valores.filter((item) => ids.has(item.produto_servico_id) && item.valor.trim() !== '').length;
  };

  return (
    <section className="space-y-4 lg:col-span-2">
      <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-[#0d1f3c] pb-2">
        Valor pago pela prestadora
      </h3>
      <p className="text-xs text-gray-500 dark:text-gray-400">
        Escolha a categoria e informe o valor que esta prestadora paga em cada serviço.
        Deixe em branco o serviço que ela não paga. O vendedor recebe o percentual do cadastro de funcionário sobre esse valor.
      </p>
      {carregando && <p className="text-sm text-gray-500">Carregando categorias...</p>}
      {erro && <p className="text-sm text-red-600">{erro}</p>}
      {!carregando && !erro && categorias.length === 0 && !temSemCategoria && (
        <p className="text-sm text-gray-500">Cadastre categorias e serviços em Produtos e serviços para configurar o valor.</p>
      )}
      {!carregando && !erro && (categorias.length > 0 || temSemCategoria) && (
        <>
          <div className="flex flex-wrap gap-2">
            {categorias.map((categoria) => {
              const ativa = categoriaId === categoria.id;
              const qtd = quantidadeNaCategoria(categoria.id);
              return (
                <button
                  key={categoria.id}
                  type="button"
                  onClick={() => setCategoriaId(categoria.id)}
                  className={`px-3 py-1.5 rounded-full text-sm border ${
                    ativa
                      ? 'bg-[#0176d3] text-white border-[#0176d3]'
                      : 'bg-white dark:bg-[#1e3a5f] text-gray-700 dark:text-gray-200 border-gray-200 dark:border-neutral-600'
                  }`}
                >
                  {categoria.nome}
                  {qtd > 0 ? ` (${qtd})` : ''}
                </button>
              );
            })}
            {temSemCategoria && (
              <button
                type="button"
                onClick={() => setCategoriaId('sem')}
                className={`px-3 py-1.5 rounded-full text-sm border ${
                  categoriaId === 'sem'
                    ? 'bg-[#0176d3] text-white border-[#0176d3]'
                    : 'bg-white dark:bg-[#1e3a5f] text-gray-700 dark:text-gray-200 border-gray-200 dark:border-neutral-600'
                }`}
              >
                Sem categoria
                {quantidadeNaCategoria('sem') > 0 ? ` (${quantidadeNaCategoria('sem')})` : ''}
              </button>
            )}
          </div>
          {daCategoria.length === 0 ? (
            <p className="text-sm text-gray-500">Nenhum serviço cadastrado nesta categoria.</p>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-[#0d1f3c]">
              <table className="w-full min-w-[520px] text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-[#0d1f3c]/50 text-left text-xs uppercase text-gray-600 dark:text-gray-300">
                    <th className="py-2 px-3 font-semibold">Serviço</th>
                    <th className="py-2 px-3 font-semibold">Preço</th>
                    <th className="py-2 px-3 font-semibold">Valor pago pela prestadora (R$)</th>
                  </tr>
                </thead>
                <tbody>
                  {daCategoria.map((servico) => (
                    <tr key={servico.id} className="border-t border-gray-100 dark:border-[#0d1f3c]">
                      <td className="py-2 px-3 text-gray-900 dark:text-white">
                        {servico.nome}
                        {servico.codigo ? (
                          <span className="block text-xs text-gray-500">{servico.codigo}</span>
                        ) : null}
                      </td>
                      <td className="py-2 px-3 text-gray-600 dark:text-gray-300">{moeda(servico.preco)}</td>
                      <td className="py-2 px-3">
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={valorDe(servico.id)}
                          onChange={(e) => definirValor(servico.id, e.target.value)}
                          className={inputClass}
                          placeholder="Não paga"
                          aria-label={`Valor pago pela prestadora em ${servico.nome}`}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </section>
  );
}
