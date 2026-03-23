/**
 * Componente de Tabela para Produtos e Serviços.
 * 
 * Responsabilidade única: Renderizar tabela de produtos/serviços.
 */
import { Eye, Edit2, Trash2, Package, Tag } from 'lucide-react';
import { ProdutoServico } from '@/hooks/useProdutosServicos';

interface ProdutoServicoTableProps {
  itens: ProdutoServico[];
  onView: (item: ProdutoServico) => void;
  onEdit: (item: ProdutoServico) => void;
  onDelete: (item: ProdutoServico) => void;
}

export function ProdutoServicoTable({
  itens,
  onView,
  onEdit,
  onDelete,
}: ProdutoServicoTableProps) {
  const formatPreco = (v: string) => {
    const n = parseFloat(v);
    return isNaN(n) ? 'R$ 0,00' : n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  };

  return (
    <div className="bg-white dark:bg-[#16325c] rounded-lg shadow border border-gray-200 dark:border-[#0d1f3c] overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[500px]">
          <thead>
            <tr className="border-b border-gray-200 dark:border-[#0d1f3c] bg-gray-50 dark:bg-[#0d1f3c]/50">
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                Código
              </th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                Categoria
              </th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                Nome
              </th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                Tipo
              </th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                Preço
              </th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                Status
              </th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                Ações
              </th>
            </tr>
          </thead>
          <tbody>
            {itens.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-gray-500 dark:text-gray-400">
                  <Package size={48} className="mx-auto mb-3 opacity-30" />
                  <p className="font-medium">Nenhum produto ou serviço cadastrado</p>
                  <p className="text-sm mt-1">Clique em &quot;Novo&quot; para cadastrar</p>
                </td>
              </tr>
            ) : (
              itens.map((item) => (
                <tr
                  key={item.id}
                  className="border-b border-gray-100 dark:border-[#0d1f3c] hover:bg-gray-50 dark:hover:bg-[#0d1f3c]/30 transition-colors"
                >
                  <td className="py-3 px-4 text-gray-700 dark:text-gray-300 font-mono text-sm">
                    {item.codigo || '-'}
                  </td>
                  <td className="py-3 px-4">
                    {item.categoria_nome ? (
                      <span
                        className="inline-block px-2 py-0.5 rounded text-xs font-medium text-white"
                        style={{ backgroundColor: item.categoria_cor || '#6B7280' }}
                      >
                        {item.categoria_nome}
                      </span>
                    ) : (
                      <span className="text-gray-400 text-xs">Sem categoria</span>
                    )}
                  </td>
                  <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">
                    {item.nome}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${
                        item.tipo === 'produto'
                          ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200'
                          : 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                      }`}
                    >
                      <Tag size={12} />
                      {item.tipo === 'produto' ? 'Produto' : 'Serviço'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-700 dark:text-gray-300">
                    {formatPreco(item.preco)}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs ${
                        item.ativo
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                      }`}
                    >
                      {item.ativo ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        type="button"
                        onClick={() => onView(item)}
                        className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300"
                        title="Visualizar"
                      >
                        <Eye size={16} />
                      </button>
                      <button
                        type="button"
                        onClick={() => onEdit(item)}
                        className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300"
                        title="Editar"
                      >
                        <Edit2 size={16} />
                      </button>
                      <button
                        type="button"
                        onClick={() => onDelete(item)}
                        className="p-1.5 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400"
                        title="Excluir"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
