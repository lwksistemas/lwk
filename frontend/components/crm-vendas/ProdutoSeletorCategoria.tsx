'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { ChevronLeft, X, Plus, FolderOpen } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { pastaTemFilhos, pastasDoNivel, type PastaCatalogo } from '@/lib/crm-catalogo-pastas';

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
  produtos?: Produto[];
  prestadoraId?: string;
  onSelecionar: (produto: Produto) => void;
  onFechar: () => void;
  itensSelecionados?: number[];
  categoriaSelecionada?: string | null;
  onCategoriaChange?: (cat: string | null) => void;
  tituloVoltar?: string;
  onVoltarRaiz?: () => void;
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

function textoBusca(valor: string) {
  return valor.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

function precoCombina(preco: string, termo: string) {
  const bruto = termo.replace(/r\$/gi, '').trim();
  if (!/\d/.test(bruto)) return false;
  const numero = parseFloat(preco);
  if (!Number.isFinite(numero)) return false;
  const exibicao = numero.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const digitosTermo = bruto.replace(/\D/g, '');
  const digitosPreco = exibicao.replace(/\D/g, '');
  return Boolean(digitosTermo) && digitosPreco.includes(digitosTermo);
}

function listarProdutos(pasta: Pasta, prefixo: string[] = []): { produto: Produto; caminho: string[] }[] {
  const atuais = pasta.itens.map((produto) => ({ produto, caminho: prefixo }));
  return pasta.filhos.reduce(
    (lista, filho) => lista.concat(listarProdutos(filho, [...prefixo, filho.nome])),
    atuais,
  );
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

function ProdutoSeletorLocal({
  produtos = [],
  onSelecionar,
  onFechar,
  itensSelecionados = [],
  tituloVoltar,
  onVoltarRaiz,
}: Props) {
  const arvore = useMemo(() => montarArvore(produtos), [produtos]);
  const [caminho, setCaminho] = useState<string[]>([]);
  const [busca, setBusca] = useState('');

  const pastaAtual = caminho.reduce<Pasta>((atual, nome) => {
    return atual.filhos.find((filho) => filho.nome === nome) || atual;
  }, arvore);
  const termo = textoBusca(busca.trim());
  const encontrados = useMemo(() => {
    if (!termo) return [];
    return listarProdutos(arvore).filter(({ produto }) => {
      const nome = textoBusca(`${produto.codigo || ''} ${produto.nome}`);
      return nome.includes(termo) || precoCombina(produto.preco, termo);
    });
  }, [arvore, termo]);
  const itensVisiveis = termo ? encontrados.map((item) => item.produto) : pastaAtual.itens;
  const caminhoPorId = useMemo(() => {
    const mapa = new Map<number, string>();
    encontrados.forEach(({ produto, caminho: trilha }) => {
      mapa.set(produto.id, trilha.join(' / '));
    });
    return mapa;
  }, [encontrados]);
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
            <span className="truncate">{caminho.length === 1 ? (tituloVoltar || 'Categorias') : caminho[caminho.length - 2]}</span>
          </button>
        ) : onVoltarRaiz ? (
          <button
            type="button"
            onClick={onVoltarRaiz}
            className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-300 hover:text-gray-900 min-w-0"
          >
            <ChevronLeft size={14} />
            <span className="truncate">{tituloVoltar || 'Categorias'}</span>
          </button>
        ) : (
          <span className="text-xs font-medium text-gray-600 dark:text-gray-300">Selecionar produto</span>
        )}
        <button type="button" onClick={onFechar} className="p-0.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600">
          <X size={14} className="text-gray-500" />
        </button>
      </div>

      <div className="px-2 pt-2">
        <input
          value={busca}
          onChange={(event) => setBusca(event.target.value)}
          placeholder="Buscar por nome ou valor"
          className="w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        />
      </div>

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
                      {p.nome}
                    </p>
                    <p className="text-[10px] text-gray-500 capitalize">
                      {caminhoPorId.get(p.id) || p.tipo}
                    </p>
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
              <p className="px-3 py-4 text-xs text-gray-500">
                {termo ? 'Nenhum serviço com esse nome ou valor.' : 'Nenhum serviço nesta pasta.'}
              </p>
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

const SEM_CATEGORIA = -1;

async function listarResumo(params: Record<string, string>, aoReceber?: (pagina: Produto[]) => void): Promise<Produto[]> {
  const itens: Produto[] = [];
  for (let page = 1; page <= 4; page += 1) {
    const res = await apiClient.get<Produto[] | { results: Produto[]; next: string | null }>(
      '/crm-vendas/produtos-servicos/',
      { params: { ...params, ativo: 'true', resumo: '1', page: String(page), page_size: '500' } },
    );
    const data = res.data;
    const pagina = Array.isArray(data) ? data : (data.results ?? []);
    itens.push(...pagina);
    aoReceber?.(pagina);
    if (Array.isArray(data) || !data.next) break;
  }
  return itens;
}

function SeletorCatalogoPrestadora({
  prestadoraId = '',
  onSelecionar,
  onFechar,
  itensSelecionados = [],
}: Props) {
  const [pastas, setPastas] = useState<PastaCatalogo[]>([]);
  const [semCategoria, setSemCategoria] = useState(0);
  const [caminho, setCaminho] = useState<number[]>([]);
  const [produtosPasta, setProdutosPasta] = useState<Produto[] | null>(null);
  const [busca, setBusca] = useState('');
  const [resultados, setResultados] = useState<Produto[] | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [carregandoItens, setCarregandoItens] = useState(false);
  const [erro, setErro] = useState('');
  const pedidoItens = useRef(0);

  useEffect(() => {
    let cancelado = false;
    setCarregando(true);
    setErro('');
    setCaminho([]);
    setProdutosPasta(null);
    setBusca('');
    setResultados(null);
    apiClient
      .get<{ pastas: PastaCatalogo[]; sem_categoria: number }>('/crm-vendas/produtos-servicos/pastas/', {
        params: { prestadora: prestadoraId, ativo: 'true' },
      })
      .then((res) => {
        if (cancelado) return;
        setPastas(res.data.pastas || []);
        setSemCategoria(res.data.sem_categoria || 0);
      })
      .catch(() => {
        if (!cancelado) setErro('Não foi possível abrir o catálogo.');
      })
      .finally(() => {
        if (!cancelado) setCarregando(false);
      });
    return () => {
      cancelado = true;
    };
  }, [prestadoraId]);

  useEffect(() => {
    const termo = busca.trim();
    if (termo.length < 2) {
      setResultados(null);
      return;
    }
    let cancelado = false;
    const timer = window.setTimeout(() => {
      apiClient
        .get<Produto[] | { results: Produto[] }>('/crm-vendas/produtos-servicos/', {
          params: { prestadora: prestadoraId, ativo: 'true', resumo: '1', busca: termo, page_size: '50' },
        })
        .then((res) => {
          if (cancelado) return;
          const data = res.data;
          setResultados(Array.isArray(data) ? data : (data.results ?? []));
        })
        .catch(() => {
          if (!cancelado) setResultados([]);
        });
    }, 250);
    return () => {
      cancelado = true;
      window.clearTimeout(timer);
    };
  }, [busca, prestadoraId]);

  const paiAtual = caminho.length ? caminho[caminho.length - 1] : null;
  const nivel = pastasDoNivel(pastas, paiAtual);
  const pastaAtual = pastas.find((pasta) => pasta.id === paiAtual);

  const carregarItens = (params: Record<string, string>) => {
    const pedido = pedidoItens.current + 1;
    pedidoItens.current = pedido;
    setCarregandoItens(true);
    setProdutosPasta([]);
    listarResumo(params, (pagina) => {
      if (pedidoItens.current !== pedido) return;
      setProdutosPasta((atual) => [...(atual || []), ...pagina]);
    })
      .catch(() => {
        if (pedidoItens.current === pedido) setProdutosPasta([]);
      })
      .finally(() => {
        if (pedidoItens.current === pedido) setCarregandoItens(false);
      });
  };

  const abrirPasta = (pasta: PastaCatalogo) => {
    setBusca('');
    setResultados(null);
    setCaminho((atual) => [...atual, pasta.id]);
    if (pastaTemFilhos(pastas, pasta.id)) {
      setProdutosPasta(null);
      return;
    }
    carregarItens({ prestadora: prestadoraId, categoria: String(pasta.id) });
  };

  const abrirSemCategoria = () => {
    setBusca('');
    setCaminho([SEM_CATEGORIA]);
    carregarItens({ prestadora: prestadoraId, sem_categoria: 'true' });
  };

  const voltar = () => {
    pedidoItens.current += 1;
    setBusca('');
    setResultados(null);
    setProdutosPasta(null);
    setCarregandoItens(false);
    setCaminho((atual) => atual.slice(0, -1));
  };

  if (produtosPasta && produtosPasta.length > 0 && !busca.trim()) {
    return (
      <ProdutoSeletorLocal
        produtos={produtosPasta}
        onSelecionar={onSelecionar}
        onFechar={onFechar}
        itensSelecionados={itensSelecionados}
        tituloVoltar={pastaAtual?.nome || 'Categorias'}
        onVoltarRaiz={voltar}
      />
    );
  }

  const titulo = caminho.length === 0
    ? 'Selecionar produto'
    : (pastaAtual?.nome || 'Sem categoria');

  return (
    <div className="border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 shadow-lg overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
        {caminho.length > 0 ? (
          <button type="button" onClick={voltar} className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-300 hover:text-gray-900 min-w-0">
            <ChevronLeft size={14} />
            <span className="truncate">{caminho.length === 1 ? 'Categorias' : pastas.find((pasta) => pasta.id === caminho[caminho.length - 2])?.nome || 'Categorias'}</span>
          </button>
        ) : (
          <span className="text-xs font-medium text-gray-600 dark:text-gray-300">{titulo}</span>
        )}
        <button type="button" onClick={onFechar} className="p-0.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600">
          <X size={14} className="text-gray-500" />
        </button>
      </div>
      <div className="px-2 pt-2">
        <input
          value={busca}
          onChange={(event) => setBusca(event.target.value)}
          placeholder="Buscar por nome ou valor"
          className="w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        />
      </div>
      <div className="max-h-80 overflow-y-auto">
        {carregando || carregandoItens ? (
          <p className="px-3 py-4 text-xs text-gray-500">Abrindo catálogo...</p>
        ) : erro ? (
          <p className="px-3 py-4 text-xs text-amber-600">{erro}</p>
        ) : resultados ? (
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {resultados.map((produto) => (
              <button
                key={produto.id}
                type="button"
                onClick={() => onSelecionar(produto)}
                className="w-full flex items-center justify-between px-3 py-2 hover:bg-blue-50 dark:hover:bg-blue-900/20 text-left"
              >
                <div className="min-w-0">
                  <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">{produto.nome}</p>
                  <p className="text-[10px] text-gray-500 truncate">{produto.categoria_nome || produto.tipo}</p>
                </div>
                <span className="text-xs font-semibold text-green-600 dark:text-green-400 shrink-0 ml-2">
                  {parseFloat(produto.preco).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                </span>
              </button>
            ))}
            {resultados.length === 0 && (
              <p className="px-3 py-4 text-xs text-gray-500">Nenhum serviço com esse nome ou valor.</p>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-1.5 p-2">
            {caminho.length === 0 && semCategoria > 0 && (
              <button type="button" onClick={abrirSemCategoria} className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-left">
                <FolderOpen size={14} className="shrink-0 text-gray-400" />
                <div className="min-w-0">
                  <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">Sem categoria</p>
                  <p className="text-[10px] text-gray-500">{semCategoria} {semCategoria === 1 ? 'item' : 'itens'}</p>
                </div>
              </button>
            )}
            {nivel.map((pasta) => (
              <button
                key={pasta.id}
                type="button"
                onClick={() => abrirPasta(pasta)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-left"
              >
                <FolderOpen size={14} className="shrink-0" style={{ color: pasta.cor || '#3B82F6' }} />
                <div className="min-w-0">
                  <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">{pasta.nome}</p>
                  <p className="text-[10px] text-gray-500">{pasta.total} {pasta.total === 1 ? 'item' : 'itens'}</p>
                </div>
              </button>
            ))}
            {nivel.length === 0 && caminho.length === 0 && semCategoria === 0 && (
              <p className="col-span-2 px-3 py-4 text-xs text-gray-500">Esta empresa ainda não tem produtos ou serviços.</p>
            )}
            {nivel.length === 0 && caminho.length > 0 && (
              <p className="col-span-2 px-3 py-4 text-xs text-gray-500">Nenhum serviço nesta pasta.</p>
            )}
          </div>
        )}
      </div>
      <div className="px-3 py-2 border-t border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700">
        <button type="button" onClick={onFechar} className="w-full py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition">
          Concluir seleção {itensSelecionados.length > 0 ? `(${itensSelecionados.length} item${itensSelecionados.length !== 1 ? 's' : ''})` : ''}
        </button>
      </div>
    </div>
  );
}

export default function ProdutoSeletorCategoria(props: Props) {
  if (props.prestadoraId) return <SeletorCatalogoPrestadora {...props} />;
  return <ProdutoSeletorLocal {...props} />;
}
