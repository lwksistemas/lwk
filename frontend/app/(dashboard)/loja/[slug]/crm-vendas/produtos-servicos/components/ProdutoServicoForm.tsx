/**
 * Componente de Formulário para Produtos e Serviços.
 * 
 * Responsabilidade única: Renderizar formulário de criação/edição.
 */
import { FormData, Categoria } from '@/hooks/useProdutosServicos';

interface ProdutoServicoFormProps {
  formData: FormData;
  categorias: Categoria[];
  isEdit: boolean;
  submitting: boolean;
  onChange: (data: Partial<FormData>) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
}

export function ProdutoServicoForm({
  formData,
  categorias,
  isEdit,
  submitting,
  onChange,
  onSubmit,
  onCancel,
}: ProdutoServicoFormProps) {
  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Tipo *
        </label>
        <select
          value={formData.tipo}
          onChange={(e) => onChange({ tipo: e.target.value as 'produto' | 'servico' })}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
        >
          <option value="produto">Produto</option>
          <option value="servico">Serviço</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Código
        </label>
        <input
          type="text"
          value={formData.codigo}
          onChange={(e) => onChange({ codigo: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-500 dark:text-gray-400"
          placeholder="Gerado automaticamente (ex: P001, S001)"
          readOnly
        />
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          O código será gerado automaticamente pelo sistema
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Categoria
        </label>
        <select
          value={formData.categoria || ''}
          onChange={(e) => onChange({ categoria: e.target.value ? parseInt(e.target.value) : null })}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
        >
          <option value="">Sem categoria</option>
          {categorias.map((cat) => (
            <option key={cat.id} value={cat.id}>
              {cat.nome}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Nome *
        </label>
        <input
          type="text"
          value={formData.nome}
          onChange={(e) => onChange({ nome: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
          placeholder="Ex: Consultoria"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Descrição
        </label>
        <textarea
          value={formData.descricao}
          onChange={(e) => onChange({ descricao: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
          rows={2}
          placeholder="Descrição opcional"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Preço (R$)
        </label>
        <input
          type="number"
          min="0"
          step="0.01"
          value={formData.preco}
          onChange={(e) => onChange({ preco: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
        />
      </div>

      {isEdit && (
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="ativo"
            checked={formData.ativo}
            onChange={(e) => onChange({ ativo: e.target.checked })}
            className="rounded"
          />
          <label htmlFor="ativo" className="text-sm text-gray-700 dark:text-gray-300">
            Ativo
          </label>
        </div>
      )}

      <div className="flex gap-2 pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="flex-1 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded-lg disabled:opacity-50"
        >
          {submitting ? 'Salvando...' : 'Salvar'}
        </button>
      </div>
    </form>
  );
}
