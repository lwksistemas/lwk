'use client';

import { useEffect, useMemo, useState } from 'react';
import { Loader2, Upload, X } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail } from '@/lib/crm-utils';
import type { Categoria } from '@/hooks/useProdutosServicos';

export interface CatalogoPdfItem {
  codigo: string;
  nome: string;
  descricao: string;
  preco: string;
  recorrencia: string;
  tipo: string;
}

function moeda(valor: string) {
  const numero = Number(valor);
  if (!Number.isFinite(numero)) return valor;
  return numero.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

export function CatalogoPdfImportModal({
  categorias,
  prestadoraId,
  rascunho = false,
  onRascunho,
  onClose,
  onImported,
}: {
  categorias: Categoria[];
  prestadoraId?: number | null;
  rascunho?: boolean;
  onRascunho?: (itens: CatalogoPdfItem[], categoriaId: number | null) => void;
  onClose: () => void;
  onImported: (categoriaId: number) => void;
}) {
  const [listaCategorias, setListaCategorias] = useState(categorias);
  const [itens, setItens] = useState<CatalogoPdfItem[]>([]);
  const [prestadoras, setPrestadoras] = useState<{ id: number; nome: string }[]>([]);
  const [prestadoraEscolhida, setPrestadoraEscolhida] = useState(prestadoraId ? String(prestadoraId) : '');
  const [categoriaId, setCategoriaId] = useState('');
  const [substituir, setSubstituir] = useState(false);
  const [busca, setBusca] = useState('');
  const [erro, setErro] = useState('');
  const [avisos, setAvisos] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState('');

  const chaveCategorias = categorias.map((item) => item.id).join(',');
  useEffect(() => {
    if (chaveCategorias) {
      setListaCategorias(categorias);
      return;
    }
    let cancelado = false;
    apiClient
      .get<Categoria[] | { results: Categoria[] }>('/crm-vendas/categorias-produtos-servicos/?ativo=true&page_size=200')
      .then((res) => {
        if (cancelado) return;
        const data = res.data;
        setListaCategorias(Array.isArray(data) ? data : data.results || []);
      })
      .catch(() => {
        if (!cancelado) setListaCategorias([]);
      });
    return () => {
      cancelado = true;
    };
    // A chave estável evita buscar de novo quando o cadastro passa uma lista vazia nova a cada render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chaveCategorias]);

  useEffect(() => {
    if (prestadoraId) return;
    let cancelado = false;
    apiClient
      .get<{ id: number; nome: string }[] | { results: { id: number; nome: string }[] }>(
        '/crm-vendas/contas/?tipo=prestadora&page_size=200',
      )
      .then((res) => {
        if (cancelado) return;
        const data = res.data;
        setPrestadoras(Array.isArray(data) ? data : data.results || []);
      })
      .catch(() => {
        if (!cancelado) setPrestadoras([]);
      });
    return () => {
      cancelado = true;
    };
  }, [prestadoraId]);

  const visiveis = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    if (!termo) return itens;
    return itens.filter((item) =>
      `${item.codigo} ${item.nome} ${item.descricao}`.toLowerCase().includes(termo),
    );
  }, [busca, itens]);

  const lerPdf = async (file: File) => {
    setErro('');
    setResultado('');
    setAvisos([]);
    setLoading(true);
    try {
      const body = new FormData();
      body.append('arquivo', file);
      const { data } = await apiClient.post<{ itens: CatalogoPdfItem[]; avisos?: string[] }>(
        '/crm-vendas/produtos-servicos/importar-pdf/',
        body,
      );
      setItens(data.itens || []);
      setAvisos(data.avisos || []);
      if (!(data.itens || []).length) {
        setErro('O PDF não trouxe itens para importar.');
      }
    } catch (err) {
      setItens([]);
      setErro(getCrmApiErrorDetail(err, 'Não foi possível ler o PDF.'));
    } finally {
      setLoading(false);
    }
  };

  const confirmar = async () => {
    if (rascunho) {
      onRascunho?.(itens, categoriaId ? Number(categoriaId) : null);
      setResultado(`${itens.length} serviços ficam nesta empresa quando o cadastro for salvo.`);
      return;
    }
    if (!prestadoraEscolhida) {
      setErro('Escolha a prestadora dona deste catálogo.');
      return;
    }
    setLoading(true);
    setErro('');
    try {
      const { data } = await apiClient.post<{
        criados: number;
        atualizados: number;
        prestadora_nome: string;
      }>('/crm-vendas/produtos-servicos/importar-pdf/confirmar/', {
        prestadora_id: Number(prestadoraEscolhida),
        categoria_id: categoriaId ? Number(categoriaId) : null,
        substituir,
        itens,
      });
      setResultado(
        `${data.criados} criados e ${data.atualizados} atualizados no catálogo de ${data.prestadora_nome}. A oportunidade dessa empresa mostra só esta lista.`,
      );
      onImported(Number(categoriaId) || 0);
    } catch (err) {
      setErro(getCrmApiErrorDetail(err, 'Não foi possível salvar a lista.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-[80]" onClick={onClose} />
      <div className="fixed inset-0 z-[81] flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col">
          <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Importar PDF da prestadora</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                O catálogo fica só nesta empresa. Dentro da categoria escolhida, Medicina, Odontologia e as tabelas Blue, Green e Black viram subpastas.
              </p>
            </div>
            <button type="button" onClick={onClose} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="p-5 space-y-3 overflow-y-auto">
            {erro && (
              <p className="text-sm text-red-600 dark:text-red-300 bg-red-50 dark:bg-red-900/20 rounded-lg p-3">{erro}</p>
            )}
            {resultado && (
              <p className="text-sm text-green-700 dark:text-green-300 bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
                {resultado}
              </p>
            )}
            <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
              <Upload className="w-4 h-4" />
              <input
                type="file"
                accept="application/pdf,.pdf"
                disabled={loading || Boolean(resultado)}
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) void lerPdf(file);
                }}
              />
            </label>
            <div className="grid gap-3 sm:grid-cols-2">
              {!prestadoraId && !rascunho && (
                <label className="text-sm text-gray-700 dark:text-gray-200">
                  Prestadora
                  <select
                    value={prestadoraEscolhida}
                    onChange={(event) => setPrestadoraEscolhida(event.target.value)}
                    disabled={Boolean(resultado)}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="">Escolha a empresa</option>
                    {prestadoras.map((empresa) => (
                      <option key={empresa.id} value={empresa.id}>
                        {empresa.nome}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              <label className="text-sm text-gray-700 dark:text-gray-200">
                Categoria
                <select
                  value={categoriaId}
                  onChange={(event) => setCategoriaId(event.target.value)}
                  disabled={Boolean(resultado)}
                  className="mt-1 w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">Sem categoria</option>
                  {listaCategorias.map((categoria) => (
                    <option key={categoria.id} value={categoria.id}>
                      {categoria.caminho && categoria.caminho.length > 1
                        ? categoria.caminho.join(' / ')
                        : categoria.nome}
                    </option>
                  ))}
                </select>
              </label>
              {!rascunho && (
              <label className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-200 sm:mt-6">
                <input
                  type="checkbox"
                  checked={substituir}
                  disabled={Boolean(resultado)}
                  onChange={(event) => setSubstituir(event.target.checked)}
                  className="mt-1"
                />
                <span>
                  Substituir o catálogo desta prestadora. O que não vier no PDF sai da lista. Proposta já feita
                  continua com o item antigo.
                </span>
              </label>
              )}
            </div>
            {avisos.length > 0 && (
              <p className="text-xs text-amber-700 dark:text-amber-300">{avisos[0]}</p>
            )}
            {itens.length > 0 && (
              <>
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm text-gray-600 dark:text-gray-300">{itens.length} itens lidos</p>
                  <input
                    value={busca}
                    onChange={(event) => setBusca(event.target.value)}
                    placeholder="Filtrar código ou nome"
                    className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-auto max-h-[42vh]">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 dark:bg-gray-900 sticky top-0">
                      <tr>
                        <th className="text-left p-2">Código</th>
                        <th className="text-left p-2">Nome</th>
                        <th className="text-right p-2">Valor</th>
                        {!resultado && <th className="w-10" />}
                      </tr>
                    </thead>
                    <tbody>
                      {visiveis.map((item) => (
                        <tr key={item.codigo} className="border-t border-gray-100 dark:border-gray-700">
                          <td className="p-2 font-mono text-xs whitespace-nowrap">{item.codigo}</td>
                          <td className="p-2">
                            <div>{item.nome}</div>
                            {item.descricao && (
                              <div className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">{item.descricao}</div>
                            )}
                          </td>
                          <td className="p-2 text-right whitespace-nowrap">{moeda(item.preco)}</td>
                          {!resultado && (
                            <td className="p-1">
                              <button
                                type="button"
                                title="Tirar da lista"
                                onClick={() => setItens((atual) => atual.filter((linha) => linha.codigo !== item.codigo))}
                                className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
          <div className="p-5 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600">
              Fechar
            </button>
            <button
              type="button"
              disabled={loading || itens.length === 0 || Boolean(resultado)}
              onClick={() => void confirmar()}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-[#0176d3] text-white disabled:opacity-50"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {rascunho ? 'Usar neste cadastro' : 'Salvar no catálogo'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
