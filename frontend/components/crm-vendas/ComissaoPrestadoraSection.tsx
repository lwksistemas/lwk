'use client';

import { useEffect, useMemo, useState } from 'react';
import { categoriasParaComissao, idsNaCategoria } from '@/lib/crm-comissao-prestadora-categorias';
import { fetchAllPaginatedResults } from '@/lib/crm-utils';

export interface ComissaoPrestadoraItem {
  produto_servico_id: number;
  valor: string;
  tipo?: 'fixo' | 'percentual';
}

export interface RegraComissaoPrestadora {
  comissao_escopo: 'todos' | 'especificos';
  comissao_tipo: 'fixo' | 'percentual';
  comissao_valor: string;
}

interface CategoriaOpcao {
  id: number;
  nome: string;
  cor: string;
  pai?: number | null;
  ordem?: number;
  caminho?: string[];
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
  prestadoraId,
  valores,
  onChange,
  regra,
  onRegraChange,
}: {
  prestadoraId?: number | null;
  valores: ComissaoPrestadoraItem[];
  onChange: (itens: ComissaoPrestadoraItem[]) => void;
  regra: RegraComissaoPrestadora;
  onRegraChange: (regra: RegraComissaoPrestadora) => void;
}) {
  const [aberto, setAberto] = useState(false);
  const [tipos, setTipos] = useState<Record<number, 'fixo' | 'percentual'>>({});
  const [categorias, setCategorias] = useState<CategoriaOpcao[]>([]);
  const [servicos, setServicos] = useState<ServicoOpcao[]>([]);
  const [categoriaId, setCategoriaId] = useState<number | 'sem' | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    if (!aberto || !prestadoraId) return;
    let cancelado = false;
    setCarregando(true);
    Promise.all([
      fetchAllPaginatedResults<CategoriaOpcao>('/crm-vendas/categorias-produtos-servicos/', { ativo: 'true' }),
      fetchAllPaginatedResults<ServicoOpcao>('/crm-vendas/produtos-servicos/', {
        ativo: 'true',
        prestadora: prestadoraId,
      }),
    ])
      .then(([cats, itens]) => {
        if (cancelado) return;
        const ativos = itens.filter((item) => item.ativo !== false);
        const raizes = categoriasParaComissao(cats, ativos);
        setCategorias(cats);
        setServicos(ativos);
        setCategoriaId((atual) => {
          if (atual === 'sem' || (typeof atual === 'number' && raizes.some((raiz) => raiz.id === atual))) {
            return atual;
          }
          return raizes[0]?.id ?? (ativos.some((item) => !item.categoria) ? 'sem' : null);
        });
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
  }, [aberto, prestadoraId]);

  const raizes = useMemo(
    () => categoriasParaComissao(categorias, servicos),
    [categorias, servicos],
  );

  const idsSelecionados = useMemo(() => {
    if (typeof categoriaId !== 'number') return new Set<number>();
    return idsNaCategoria(categorias, categoriaId);
  }, [categoriaId, categorias]);

  const daCategoria = useMemo(() => {
    if (categoriaId === 'sem') return servicos.filter((item) => !item.categoria);
    if (categoriaId == null) return [];
    return servicos
      .filter((item) => item.categoria != null && idsSelecionados.has(item.categoria))
      .sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'));
  }, [categoriaId, idsSelecionados, servicos]);

  const temSemCategoria = servicos.some((item) => !item.categoria);

  const definirValor = (produtoId: number, tipo: 'fixo' | 'percentual', valor: string) => {
    const resto = valores.filter((item) => item.produto_servico_id !== produtoId);
    if (valor.trim() === '') {
      onChange(resto);
      return;
    }
    onChange([...resto, { produto_servico_id: produtoId, tipo, valor }]);
  };

  const valorDe = (produtoId: number) =>
    valores.find((item) => item.produto_servico_id === produtoId)?.valor ?? '';

  const quantidadeNaCategoria = (id: number | 'sem') => {
    const idsCategoria = id === 'sem' ? null : idsNaCategoria(categorias, id);
    const ids = new Set(
      servicos
        .filter((item) => (id === 'sem' ? !item.categoria : item.categoria != null && idsCategoria?.has(item.categoria)))
        .map((item) => item.id),
    );
    return valores.filter((item) => ids.has(item.produto_servico_id) && item.valor.trim() !== '').length;
  };

  const trilhaDaSubpasta = (categoriaServico: number | null) => {
    if (categoriaServico == null || typeof categoriaId !== 'number') return '';
    const categoria = categorias.find((item) => item.id === categoriaServico);
    if (!categoria?.caminho || categoria.caminho.length <= 1) return '';
    return categoria.caminho.slice(1).join(' · ');
  };

  return (
    <section className="space-y-4 lg:col-span-2">
      <button
        type="button"
        onClick={() => setAberto((atual) => !atual)}
        className="w-full flex items-center justify-between text-left text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-[#0d1f3c] pb-2"
      >
        <span>Valor pago pela prestadora</span>
        <span className="text-xs font-medium text-[#0176d3]">{aberto ? 'Ocultar' : 'Configurar'}</span>
      </button>
      {aberto && (
        <>
      <p className="text-xs text-gray-500 dark:text-gray-400">
        A prestadora pode pagar uma porcentagem do preço ou um valor fixo, em todos os serviços ou só nos escolhidos.
        Exemplo: 15% em todos os serviços. O vendedor recebe o percentual do cadastro de funcionário sobre esse valor.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Aplicar em</label>
          <select
            value={regra.comissao_escopo}
            onChange={(e) => onRegraChange({
              ...regra,
              comissao_escopo: e.target.value as RegraComissaoPrestadora['comissao_escopo'],
            })}
            className={inputClass}
            aria-label="Aplicar comissão da prestadora em"
          >
            <option value="todos">Todos os produtos e serviços</option>
            <option value="especificos">Produtos e serviços escolhidos</option>
          </select>
        </div>
        {regra.comissao_escopo === 'todos' && (
          <>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Forma</label>
              <select
                value={regra.comissao_tipo}
                onChange={(e) => onRegraChange({
                  ...regra,
                  comissao_tipo: e.target.value as RegraComissaoPrestadora['comissao_tipo'],
                })}
                className={inputClass}
                aria-label="Forma da comissão da prestadora"
              >
                <option value="percentual">Porcentagem (%)</option>
                <option value="fixo">Valor fixo (R$)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                {regra.comissao_tipo === 'percentual' ? 'Porcentagem' : 'Valor fixo'}
              </label>
              <input
                type="number"
                min="0"
                max={regra.comissao_tipo === 'percentual' ? '100' : undefined}
                step="0.01"
                value={regra.comissao_valor}
                onChange={(e) => onRegraChange({ ...regra, comissao_valor: e.target.value })}
                className={inputClass}
                placeholder={regra.comissao_tipo === 'percentual' ? '15' : '0,00'}
                aria-label="Valor da comissão da prestadora"
              />
            </div>
          </>
        )}
      </div>
      {regra.comissao_escopo === 'especificos' && (
      <>
      {!prestadoraId && (
        <p className="text-sm text-gray-500">Salve a empresa e importe o catálogo para configurar os valores.</p>
      )}
      {carregando && <p className="text-sm text-gray-500">Carregando categorias...</p>}
      {erro && <p className="text-sm text-red-600">{erro}</p>}
      {prestadoraId && !carregando && !erro && servicos.length === 0 && (
        <p className="text-sm text-gray-500">Esta empresa ainda não tem serviços. Importe o PDF do catálogo neste cadastro.</p>
      )}
      {!carregando && !erro && servicos.length > 0 && (
        <>
          <div className="flex flex-wrap gap-2">
            {raizes.map((categoria) => {
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
                    <th className="py-2 px-3 font-semibold">Comissão da prestadora</th>
                  </tr>
                </thead>
                <tbody>
                  {daCategoria.map((servico) => {
                    const item = valores.find((linha) => linha.produto_servico_id === servico.id);
                    const tipo = item?.tipo || tipos[servico.id] || 'fixo';
                    return (
                    <tr key={servico.id} className="border-t border-gray-100 dark:border-[#0d1f3c]">
                      <td className="py-2 px-3 text-gray-900 dark:text-white">
                        {servico.nome}
                        {trilhaDaSubpasta(servico.categoria) ? (
                          <span className="block text-xs text-gray-500">{trilhaDaSubpasta(servico.categoria)}</span>
                        ) : null}
                        {servico.codigo ? (
                          <span className="block text-xs text-gray-500">{servico.codigo}</span>
                        ) : null}
                      </td>
                      <td className="py-2 px-3 text-gray-600 dark:text-gray-300">{moeda(servico.preco)}</td>
                      <td className="py-2 px-3">
                        <div className="flex gap-2">
                          <select
                            value={tipo}
                            onChange={(e) => {
                              const proximo = e.target.value as 'fixo' | 'percentual';
                              setTipos((atualTipos) => ({ ...atualTipos, [servico.id]: proximo }));
                              if (item?.valor) definirValor(servico.id, proximo, item.valor);
                            }}
                            className={`${inputClass} w-28`}
                            aria-label={`Forma da comissão em ${servico.nome}`}
                          >
                            <option value="percentual">%</option>
                            <option value="fixo">R$</option>
                          </select>
                          <input
                            type="number"
                            min="0"
                            max={tipo === 'percentual' ? '100' : undefined}
                            step="0.01"
                            value={valorDe(servico.id)}
                            onChange={(e) => definirValor(servico.id, tipo, e.target.value)}
                            className={inputClass}
                            placeholder="Não paga"
                            aria-label={`Valor pago pela prestadora em ${servico.nome}`}
                          />
                        </div>
                      </td>
                    </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
      </>
      )}
        </>
      )}
    </section>
  );
}
