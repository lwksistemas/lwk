import { useMemo, useState } from "react";
import { AlertTriangle, ArrowLeft, FolderOpen, Package, Plus } from "lucide-react";
import type { CategoriaEstoque, ProdutoEstoque } from "./produtos-types";
import { PRODUTOS_INPUT_CLASS } from "./produtos-types";

export function ProdutoAdicionarForm({
  produtos,
  produtosPorCategoria,
  produtoId,
  quantidade,
  lote,
  validade,
  erro,
  erroEstoque,
  avisoFormulario,
  saving,
  onProdutoChange,
  onQuantidadeChange,
  onLoteChange,
  onValidadeChange,
  onClose,
  onAdicionar,
}: {
  produtos: ProdutoEstoque[];
  produtosPorCategoria?: {
    comCategoria: { categoria: CategoriaEstoque; produtos: ProdutoEstoque[] }[];
    semCategoria: ProdutoEstoque[];
  };
  produtoId: number | "";
  quantidade: string;
  lote: string;
  validade: string;
  erro: string;
  erroEstoque: string;
  avisoFormulario: string;
  saving: boolean;
  onProdutoChange: (id: number | "") => void;
  onQuantidadeChange: (v: string) => void;
  onLoteChange: (v: string) => void;
  onValidadeChange: (v: string) => void;
  onClose: () => void;
  onAdicionar: () => void;
}) {
  const [categoriaSelecionada, setCategoriaSelecionada] = useState<CategoriaEstoque | null>(null);

  const produtoSelecionado = useMemo(
    () => produtos.find((p) => p.id === produtoId),
    [produtos, produtoId],
  );

  const categorias = produtosPorCategoria?.comCategoria ?? [];
  const semCategoria = produtosPorCategoria?.semCategoria ?? [];

  const handleEscolherCategoria = (cat: CategoriaEstoque | null) => {
    setCategoriaSelecionada(cat);
    onProdutoChange("");
  };

  const handleVoltarCategorias = () => {
    setCategoriaSelecionada(null);
    onProdutoChange("");
  };

  const handleSelecionarProduto = (id: number) => {
    onProdutoChange(id);
  };

  const produtosParaExibir = categoriaSelecionada
    ? categoriaSelecionada.id === -1
      ? semCategoria
      : categorias.find((c) => c.categoria.id === categoriaSelecionada.id)?.produtos ?? []
    : [];

  const renderizarGridCategorias = () => (
    <div className="space-y-4">
      <p className="text-xs text-gray-500 dark:text-gray-400">Escolha uma categoria para ver os produtos:</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {categorias.map(({ categoria, produtos: grupo }) => (
          <button
            key={categoria.id}
            type="button"
            onClick={() => handleEscolherCategoria(categoria)}
            className="text-left rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 shadow-sm hover:shadow-md hover:border-[#8B3D52]/50 transition-all group"
          >
            <div className="flex items-start gap-3">
              <span
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-white shadow-inner"
                style={{ backgroundColor: categoria.cor || "#8B3D52" }}
              >
                <FolderOpen className="w-5 h-5 opacity-90" aria-hidden />
              </span>
              <div className="min-w-0 flex-1">
                <h3 className="font-semibold text-gray-900 dark:text-white group-hover:text-[#8B3D52] transition-colors truncate">
                  {categoria.nome}
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  <Package className="inline w-3.5 h-3.5 mr-1 -mt-0.5" aria-hidden />
                  {grupo.length} {grupo.length === 1 ? "produto" : "produtos"}
                </p>
              </div>
            </div>
          </button>
        ))}

        {semCategoria.length > 0 && (
          <button
            type="button"
            onClick={() => handleEscolherCategoria({ id: -1, nome: "Outros", slug: "outros" })}
            className="text-left rounded-xl border border-amber-200 dark:border-amber-900/50 bg-amber-50/80 dark:bg-amber-950/20 p-4 shadow-sm hover:shadow-md transition-all"
          >
            <div className="flex items-start gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-amber-200 dark:bg-amber-900/40 text-amber-900 dark:text-amber-100">
                <Package className="w-5 h-5" aria-hidden />
              </span>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">Outros</h3>
                <p className="text-xs text-amber-800 dark:text-amber-200/80 mt-1">
                  {semCategoria.length} {semCategoria.length === 1 ? "produto" : "produtos"}
                </p>
              </div>
            </div>
          </button>
        )}
      </div>

      {categorias.length === 0 && semCategoria.length === 0 && (
        <div className="rounded-xl border border-dashed border-gray-300 dark:border-gray-600 p-8 text-center text-gray-500 dark:text-gray-400">
          <FolderOpen className="w-10 h-10 mx-auto mb-2 opacity-40" />
          <p className="font-medium text-sm">Nenhuma categoria cadastrada</p>
          <p className="text-xs mt-1">Cadastre categorias no estoque para organizar os produtos.</p>
        </div>
      )}
    </div>
  );

  const renderizarProdutosDaCategoria = () => (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={handleVoltarCategorias}
          className="inline-flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
        >
          <ArrowLeft size={14} />
          Voltar para categorias
        </button>
      </div>

      <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
        {categoriaSelecionada?.nome}
      </h4>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-64 overflow-y-auto pr-1">
        {produtosParaExibir.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => handleSelecionarProduto(p.id)}
            className={`text-left rounded-lg border p-3 transition-all ${
              produtoId === p.id
                ? "border-[#8B3D52] bg-[#8B3D52]/5 dark:bg-[#8B3D52]/20 ring-1 ring-[#8B3D52]"
                : "border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/60 hover:border-[#8B3D52]/50"
            }`}
          >
            <p className="font-medium text-sm text-gray-900 dark:text-gray-100">{p.nome}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              disp. {Number(p.quantidade_atual)} {p.unidade_medida || "un"}
            </p>
          </button>
        ))}
      </div>
    </div>
  );

  const renderizarFormularioQuantidade = () => {
    if (!produtoSelecionado) return null;
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-gray-100 dark:border-neutral-700/50">
        <div>
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
            Quantidade usada *
          </label>
          <input
            type="number"
            min="0.01"
            step="0.01"
            value={quantidade}
            onChange={(e) => onQuantidadeChange(e.target.value)}
            className={PRODUTOS_INPUT_CLASS}
          />
          {avisoFormulario && (
            <p className="mt-1.5 text-xs text-amber-700 dark:text-amber-300 flex items-start gap-1">
              <AlertTriangle size={14} className="shrink-0 mt-0.5" />
              {avisoFormulario} A finalização será bloqueada até regularizar o estoque.
            </p>
          )}
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Nº do lote</label>
          <input
            type="text"
            value={lote}
            onChange={(e) => onLoteChange(e.target.value)}
            className={PRODUTOS_INPUT_CLASS}
            placeholder="Lote do produto"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Validade</label>
          <input
            type="date"
            value={validade}
            onChange={(e) => onValidadeChange(e.target.value)}
            className={PRODUTOS_INPUT_CLASS}
          />
        </div>
        <div className="flex items-end">
          <p className="text-xs text-gray-500 dark:text-gray-400 pb-2">
            Produto: <strong className="text-gray-700 dark:text-gray-300">{produtoSelecionado.nome}</strong>
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Adicionar produto</h3>
        <button type="button" onClick={onClose} className="text-xs text-gray-500 hover:text-gray-700">
          Fechar
        </button>
      </div>

      {erroEstoque && (
        <p className="text-sm text-red-600 dark:text-red-400">{erroEstoque}</p>
      )}

      {!categoriaSelecionada && renderizarGridCategorias()}
      {categoriaSelecionada && !produtoId && renderizarProdutosDaCategoria()}
      {categoriaSelecionada && produtoId && (
        <>
          {renderizarProdutosDaCategoria()}
          {renderizarFormularioQuantidade()}
        </>
      )}

      {erro && <p className="text-sm text-red-600 dark:text-red-400">{erro}</p>}

      {produtoId && (
        <button
          type="button"
          onClick={onAdicionar}
          disabled={saving}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-white text-sm font-medium disabled:opacity-50"
          style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
        >
          <Plus size={16} />
          {saving ? "Salvando..." : "Adicionar"}
        </button>
      )}
    </div>
  );
}
