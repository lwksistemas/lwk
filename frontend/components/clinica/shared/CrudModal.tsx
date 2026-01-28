'use client';

import React, { useEffect } from 'react';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
  logo?: string;
}

interface CrudModalProps {
  loja: LojaInfo;
  onClose: () => void;
  title: string;
  icon?: string;
  children: React.ReactNode;
  maxWidth?: 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl';
}

const maxWidthClasses = {
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  '2xl': 'max-w-2xl',
  '3xl': 'max-w-3xl',
  '4xl': 'max-w-4xl',
};

export function CrudModal({
  loja,
  onClose,
  title,
  icon = '📋',
  children,
  maxWidth = '3xl',
}: CrudModalProps) {
  // Fechar com ESC e bloquear scroll
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEscape);
    document.body.style.overflow = 'hidden';
    
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [onClose]);

  // Fechar clicando no backdrop
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div 
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-2 sm:p-4 animate-fade-in"
      onClick={handleBackdropClick}
    >
      <div 
        className={`
          bg-white dark:bg-gray-800 
          rounded-lg sm:rounded-xl shadow-2xl p-4 sm:p-6 md:p-8 
          ${maxWidthClasses[maxWidth]} w-full 
          max-h-[95vh] sm:max-h-[90vh] overflow-y-auto
          animate-scale-in
        `}
      >
        <div className="flex items-center justify-between mb-4 sm:mb-6 gap-2">
          <h3 className="text-lg sm:text-xl md:text-2xl font-bold dark:text-white truncate" style={{ color: loja.cor_primaria }}>
            {icon} {title}
          </h3>
          <button
            onClick={onClose}
            className="w-10 h-10 sm:w-8 sm:h-8 flex items-center justify-center rounded-full flex-shrink-0
                       text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200
                       hover:bg-gray-100 dark:hover:bg-gray-700
                       transition-colors text-xl font-bold active:scale-90"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

// Componente para lista de itens dentro do modal
interface CrudListProps<T> {
  items: T[];
  loading: boolean;
  emptyMessage?: string;
  renderItem: (item: T, index: number) => React.ReactNode;
  columns?: string[];
}

export function CrudList<T>({
  items,
  loading,
  emptyMessage = 'Nenhum item encontrado.',
  renderItem,
  columns,
}: CrudListProps<T>) {
  if (loading) {
    return (
      <div className="text-center py-6 sm:py-8 text-gray-500 text-sm sm:text-base">
        Carregando...
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-6 sm:py-8 text-gray-500 text-sm sm:text-base">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto -mx-4 sm:mx-0">
      <table className="w-full min-w-[500px]">
        {columns && columns.length > 0 && (
          <thead>
            <tr className="border-b">
              {columns.map((col, idx) => (
                <th key={idx} className="text-left py-2 px-2 font-semibold text-gray-700 dark:text-gray-300 text-xs sm:text-sm whitespace-nowrap">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
        )}
        <tbody>
          {items.map((item, index) => renderItem(item, index))}
        </tbody>
      </table>
    </div>
  );
}

// Componente para botões de ação (Editar/Excluir)
interface ActionButtonsProps {
  onEdit: () => void;
  onDelete: () => void;
  editLabel?: string;
  deleteLabel?: string;
}

export function ActionButtons({
  onEdit,
  onDelete,
  editLabel = 'Editar',
  deleteLabel = 'Excluir',
}: ActionButtonsProps) {
  return (
    <div className="flex gap-1 sm:gap-2">
      <button
        onClick={onEdit}
        className="px-2 sm:px-3 py-1.5 sm:py-1 min-h-[36px] sm:min-h-[32px] bg-blue-500 text-white text-xs sm:text-sm rounded hover:bg-blue-600 active:scale-95 transition-transform"
      >
        {editLabel}
      </button>
      <button
        onClick={onDelete}
        className="px-2 sm:px-3 py-1.5 sm:py-1 min-h-[36px] sm:min-h-[32px] bg-red-500 text-white text-xs sm:text-sm rounded hover:bg-red-600 active:scale-95 transition-transform"
      >
        {deleteLabel}
      </button>
    </div>
  );
}

// Componente para formulário dentro do modal
interface CrudFormProps {
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  submitting: boolean;
  isEditing: boolean;
  children: React.ReactNode;
  submitLabel?: string;
  cancelLabel?: string;
}

export function CrudForm({
  onSubmit,
  onCancel,
  submitting,
  isEditing,
  children,
  submitLabel,
  cancelLabel = 'Cancelar',
}: CrudFormProps) {
  const defaultSubmitLabel = isEditing ? 'Salvar Alterações' : 'Cadastrar';

  return (
    <form onSubmit={onSubmit} className="space-y-4 sm:space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
        {children}
      </div>

      <div className="flex flex-col-reverse sm:flex-row gap-2 sm:gap-3 pt-3 sm:pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 py-3 sm:py-2.5 px-4 min-h-[44px] bg-gray-500 text-white rounded-md hover:bg-gray-600 font-semibold text-sm sm:text-base active:scale-[0.98] transition-transform"
        >
          {cancelLabel}
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="flex-1 py-3 sm:py-2.5 px-4 min-h-[44px] bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold text-sm sm:text-base active:scale-[0.98] transition-transform"
        >
          {submitting ? 'Salvando...' : (submitLabel || defaultSubmitLabel)}
        </button>
      </div>
    </form>
  );
}

// Componente para header com botão de adicionar
interface CrudHeaderProps {
  onAdd: () => void;
  addLabel?: string;
  loja: LojaInfo;
}

export function CrudHeader({ onAdd, addLabel = '+ Adicionar', loja }: CrudHeaderProps) {
  return (
    <div className="flex justify-end mb-3 sm:mb-4">
      <button
        onClick={onAdd}
        className="px-3 sm:px-4 py-2.5 sm:py-2 min-h-[44px] text-white rounded-md hover:opacity-90 font-semibold text-sm sm:text-base active:scale-95 transition-transform"
        style={{ backgroundColor: loja.cor_primaria }}
      >
        {addLabel}
      </button>
    </div>
  );
}

// Exportar tipo LojaInfo para uso em outros componentes
export type { LojaInfo };
