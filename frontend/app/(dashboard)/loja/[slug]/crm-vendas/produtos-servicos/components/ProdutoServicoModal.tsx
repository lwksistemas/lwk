/**
 * Componente de Modal para Produtos e Serviços.
 * 
 * Responsabilidade única: Renderizar modal com diferentes modos.
 */
import { X } from 'lucide-react';
import { ProdutoServico, FormData, Categoria } from '@/hooks/useProdutosServicos';
import { ProdutoServicoForm } from './ProdutoServicoForm';

type ModalType = 'create' | 'edit' | 'view' | 'delete' | null;

interface ProdutoServicoModalProps {
  modalType: ModalType;
  selected: ProdutoServico | null;
  formData: FormData;
  categorias: Categoria[];
  submitting: boolean;
  onClose: () => void;
  onFormChange: (data: Partial<FormData>) => void;
  onSubmit: (e: React.FormEvent) => void;
  onDelete: () => void;
}

export function ProdutoServicoModal({
  modalType,
  selected,
  formData,
  categorias,
  submitting,
  onClose,
  onFormChange,
  onSubmit,
  onDelete,
}: ProdutoServicoModalProps) {
  if (!modalType) return null;

  const formatPreco = (v: string) => {
    const n = parseFloat(v);
    return isNaN(n) ? 'R$ 0,00' : n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  };

  const getTitle = () => {
    switch (modalType) {
      case 'create':
        return 'Novo Produto/Serviço';
      case 'edit':
        return 'Editar';
      case 'view':
        return 'Detalhes';
      case 'delete':
        return 'Excluir';
      default:
        return '';
    }
  };

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-[80]" onClick={onClose} />
      <div className="fixed inset-0 z-[81] flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {getTitle()}
            </h2>
            <button
              type="button"
              onClick={onClose}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <X size={20} />
            </button>
          </div>

          <div className="p-6">
            {(modalType === 'create' || modalType === 'edit') && (
              <ProdutoServicoForm
                formData={formData}
                categorias={categorias}
                isEdit={modalType === 'edit'}
                submitting={submitting}
                onChange={onFormChange}
                onSubmit={onSubmit}
                onCancel={onClose}
              />
            )}

            {modalType === 'view' && selected && (
              <div className="space-y-3">
                <p>
                  <span className="font-medium">Tipo:</span>{' '}
                  {selected.tipo === 'produto' ? 'Produto' : 'Serviço'}
                </p>
                {selected.codigo && (
                  <p>
                    <span className="font-medium">Código:</span> {selected.codigo}
                  </p>
                )}
                {selected.categoria_nome && (
                  <p>
                    <span className="font-medium">Categoria:</span>{' '}
                    <span
                      className="inline-block px-2 py-0.5 rounded text-xs font-medium text-white ml-1"
                      style={{ backgroundColor: selected.categoria_cor || '#6B7280' }}
                    >
                      {selected.categoria_nome}
                    </span>
                  </p>
                )}
                <p>
                  <span className="font-medium">Nome:</span> {selected.nome}
                </p>
                <p>
                  <span className="font-medium">Preço:</span> {formatPreco(selected.preco)}
                </p>
                <p>
                  <span className="font-medium">Status:</span>{' '}
                  {selected.ativo ? 'Ativo' : 'Inativo'}
                </p>
                {selected.descricao && (
                  <p>
                    <span className="font-medium">Descrição:</span> {selected.descricao}
                  </p>
                )}
                <button
                  type="button"
                  onClick={onClose}
                  className="w-full mt-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg"
                >
                  Fechar
                </button>
              </div>
            )}

            {modalType === 'delete' && selected && (
              <div className="space-y-4">
                <p className="text-gray-600 dark:text-gray-400">
                  Deseja excluir &quot;{selected.nome}&quot;? Esta ação não pode ser desfeita.
                </p>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={onClose}
                    className="flex-1 px-4 py-2 border rounded-lg"
                  >
                    Cancelar
                  </button>
                  <button
                    type="button"
                    onClick={onDelete}
                    disabled={submitting}
                    className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-50"
                  >
                    {submitting ? 'Excluindo...' : 'Excluir'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
