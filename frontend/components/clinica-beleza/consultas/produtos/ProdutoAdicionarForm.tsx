import { AlertTriangle, Plus } from "lucide-react";
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
  return (
    <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Adicionar produto</h3>
        <button type="button" onClick={onClose} className="text-xs text-gray-500 hover:text-gray-700">
          Fechar
        </button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="sm:col-span-2">
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Produto *</label>
          {erroEstoque && (
            <p className="text-sm text-red-600 dark:text-red-400 mb-2">{erroEstoque}</p>
          )}
          <select
            value={produtoId}
            onChange={(e) => onProdutoChange(e.target.value ? Number(e.target.value) : "")}
            className={PRODUTOS_INPUT_CLASS}
            disabled={!!erroEstoque || produtos.length === 0}
          >
            <option value="">
              {erroEstoque
                ? "Estoque indisponível"
                : produtos.length === 0
                  ? "Nenhum produto cadastrado no estoque"
                  : "Selecione..."}
            </option>
            {produtosPorCategoria?.comCategoria.map(({ categoria, produtos: grupo }) => (
              <optgroup key={categoria.id} label={categoria.nome}>
                {grupo.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nome} — disp. {Number(p.quantidade_atual)} {p.unidade_medida || "un"}
                  </option>
                ))}
              </optgroup>
            ))}
            {produtosPorCategoria && produtosPorCategoria.semCategoria.length > 0 && (
              <optgroup label="Outros">
                {produtosPorCategoria.semCategoria.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nome} — disp. {Number(p.quantidade_atual)} {p.unidade_medida || "un"}
                  </option>
                ))}
              </optgroup>
            )}
            {!produtosPorCategoria && produtos.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nome} — disp. {Number(p.quantidade_atual)} {p.unidade_medida || "un"}
              </option>
            ))}
          </select>
        </div>
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
      </div>
      {erro && <p className="text-sm text-red-600 dark:text-red-400">{erro}</p>}
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
    </div>
  );
}
