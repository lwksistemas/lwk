'use client';

import { useMemo, useState } from 'react';
import { ChevronLeft, X, Plus, FolderOpen } from 'lucide-react';

interface Produto {
  id: number;
  nome: string;
  tipo: string;
  preco: string;
  codigo?: string;
  categoria_nome?: string;
  categoria_cor?: string;
  categoria_caminho?: string[];
}

interface Props {
  produtos: Produto[];
  onSelecionar: (produto: Produto) => void;
  onFechar: () => void;
  itensSelecionados?: number[];
  categoriaSelecionada?: string | null;
  onCategoriaChange?: (cat: string | null) => void;
}

interface Pasta {
  nome: string;
  cor: string;
  itens: Produto[];
  filhos: Pasta[];
}

const CORES: Record<string, string> = {
  MEDICINA: '#0F766E',
  ODONTOLOGIA: '#0369A1',
  'DEMAIS CATEGORIAS': '#6B7280',
  'TABELA BLUE': '#2563EB',
  'TABELA GREEN': '#15803D',
  'TABELA BLACK': '#111827',
  'TABELA ESSENCIAL': '#7C3AED',
};

function corDaPasta(nome: string, fallback?: string) {
  return CORES[nome] || fallback || '#3B82F6';
}

function contar(pasta: Pasta): number {
  return pasta.itens.length + pasta.filhos.reduce((total, filho) => total + contar(filho), 0);
}

function caminhoDoProduto(produto: Produto): string[] {
  if (produto.categoria_caminho && produto.categoria_caminho.length > 1) {
    return produto.categoria_caminho;
  }
  const base = produto.categoria_caminho?.length
    ? produto.categoria_caminho
    : [produto.categoria_nome || 'Sem Categoria'];
  const codigo = (produto.codigo || '').toUpperCase();
  const partes = /^(BLU|GRN|BLKR|BLK|ESS)\d*-(MED|ODO|DEM)-/.exec(codigo);
  if (!partes) return base;
  const tabela = {
    BLU: 'TABELA BLUE',
    GRN: 'TABELA GREEN',
    BLK: 'TABELA BLACK',
    BLKR: 'TABELA BLACK',
    ESS: 'TABELA ESSENCIAL',
  }[partes[1]];
  const area = { MED: 'MEDICINA', ODO: 'ODONTOLOGIA', DEM: 'DEMAIS CATEGORIAS' }[partes[2]];
  if (!tabela || !area) return base;
  return [...base, area, tabela];
}

function montarArvore(produtos: Produto[]): Pasta {
  const raiz: Pasta = { nome: '', cor: '#3B82F6', itens: [], filhos: [] };
  for (const produto of produtos) {
    const caminho = caminhoDoProduto(produto);
    let pasta = raiz;
    caminho.forEach((nome, indice) => {
      let filho = pasta.filhos.find((item) => item.nome === nome);
      if (!filho) {
        filho = { nome, cor: corDaPasta(nome, produto.categoria_cor), itens: [], filhos: [] };
        pasta.filhos.push(filho);
      }
      pasta = filho;
      if (indice === caminho.length - 1) pasta.itens.push(produto);
    });
  }
  const ordenar = (pasta: Pasta) => {
    pasta.filhos.sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'));
    pasta.filhos.forEach(ordenar);
  };
  ordenar(raiz);
  return raiz;
}

export default function ProdutoSeletorCategoria({
  produtos,
  onSelecionar,
  onFechar,
  itensSelecionados = [],
}: Props) {
  const arvore = useMemo(() => montarArvore(produtos), [produtos]);
  const [caminho, setCaminho] = useState<string[]>([]);
  const [busca, setBusca] = useState('');

  const pastaAtual = caminho.reduce<Pasta>((atual, nome) => {
    return atual.filhos.find((filho) => filho.nome === nome) || atual;
  }, arvore);
  const termo = busca.trim().toLowerCase();
  const itensVisiveis = termo
    ? pastaAtual.itens.filter((item) => `${item.codigo || ''} ${item.nome}`.toLowerCase().includes(termo))
    : pastaAtual.itens;
  const mostrandoPastas = pastaAtual.filhos.length > 0 && !termo;

  const abrir = (nome: string) => {
    setBusca('');
    setCaminho((atual) => [...atual, nome]);
  };

  const voltar = () => {
    setBusca('');
    setCaminho((atual) => atual.slice(0, -1));
  };

  return (
    <div className="border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 shadow-lg overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
        {caminho.length > 0 ? (
          <button
            type="button"
            onClick={voltar}
            className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-300 hover:text-gray-900 min-w-0"
          >
            <ChevronLeft size={14} />
            <span className="truncate">{caminho.length === 1 ? 'Categorias' : caminho[caminho.length - 2]}</span>
          </button>
        ) : (
          <span className="text-xs font-medium text-gray-600 dark:text-gray-300">Selecionar produto</span>
        )}
        <button type="button" onClick={onFechar} className="p-0.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600">
          <X size={14} className="text-gray-500" />
        </button>
      </div>

      {pastaAtual.itens.length > 8 && (
        <div className="px-2 pt-2">
          <input
            value={busca}
            onChange={(event) => setBusca(event.target.value)}
            placeholder="Buscar nesta pasta"
            className="w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
      )}

      <div className="max-h-80 overflow-y-auto">
        {mostrandoPastas ? (
          <div className="grid grid-cols-2 gap-1.5 p-2">
            {pastaAtual.filhos.map((filho) => {
              const total = contar(filho);
              return (
                <button
                  key={filho.nome}
                  type="button"
                  onClick={() => abrir(filho.nome)}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-left transition"
                >
                  <FolderOpen size={14} className="shrink-0" style={{ color: filho.cor }} />
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">{filho.nome}</p>
                    <p className="text-[10px] text-gray-500">{total} item{total !== 1 ? 's' : ''}</p>
                  </div>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {itensVisiveis.map((p) => {
              const qtdAdicionada = itensSelecionados.filter((id) => id === p.id).length;
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => onSelecionar(p)}
                  className="w-full flex items-center justify-between px-3 py-2 hover:bg-blue-50 dark:hover:bg-blue-900/20 text-left transition"
                >
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
                      {p.codigo ? <span className="text-gray-400 mr-1">[{p.codigo}]</span> : null}
                      {p.nome}
                    </p>
                    <p className="text-[10px] text-gray-500 capitalize">{p.tipo}</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-2">
                    {qtdAdicionada > 0 && (
                      <span className="text-[10px] font-bold bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 rounded-full px-1.5 py-0.5">
                        ×{qtdAdicionada}
                      </span>
                    )}
                    <span className="text-xs font-semibold text-green-600 dark:text-green-400">
                      {parseFloat(p.preco).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                    </span>
                    <Plus size={13} className="text-blue-500" />
                  </div>
                </button>
              );
            })}
            {itensVisiveis.length === 0 && (
              <p className="px-3 py-4 text-xs text-gray-500">Nenhum serviço nesta pasta.</p>
            )}
          </div>
        )}
      </div>

      <div className="px-3 py-2 border-t border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700">
        <button
          type="button"
          onClick={onFechar}
          className="w-full py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition"
        >
          Concluir seleção {itensSelecionados.length > 0 ? `(${itensSelecionados.length} item${itensSelecionados.length !== 1 ? 's' : ''})` : ''}
        </button>
      </div>
    </div>
  );
}
