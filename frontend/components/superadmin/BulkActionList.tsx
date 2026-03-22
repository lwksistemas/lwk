'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Search,
  X,
  CheckSquare,
  Square,
  ArrowUp,
  ArrowDown,
  Pencil,
  Trash2,
} from 'lucide-react';

interface BulkActionListProps<T extends { id?: number; ativo?: boolean }> {
  items: T[];
  searchValue: string;
  onSearchChange: (value: string) => void;
  filterValue: 'all' | 'ativo' | 'inativo';
  onFilterChange: (value: 'all' | 'ativo' | 'inativo') => void;
  selectedIds: number[];
  onToggleSelect: (id: number) => void;
  onToggleSelectAll: () => void;
  onBulkAction: (action: 'ativar' | 'desativar' | 'excluir') => void;
  onReorder: (id: number, direction: 'up' | 'down') => void;
  onEdit: (item: T) => void;
  onDelete: (id: number, name: string) => void;
  renderItem: (item: T) => React.ReactNode;
  getItemName: (item: T) => string;
  searchPlaceholder: string;
  emptyMessage: string;
  saving?: boolean;
}

export function BulkActionList<T extends { id?: number; ativo?: boolean }>({
  items,
  searchValue,
  onSearchChange,
  filterValue,
  onFilterChange,
  selectedIds,
  onToggleSelect,
  onToggleSelectAll,
  onBulkAction,
  onReorder,
  onEdit,
  onDelete,
  renderItem,
  getItemName,
  searchPlaceholder,
  emptyMessage,
  saving = false,
}: BulkActionListProps<T>) {
  const activeCount = items.filter(i => i.ativo !== false).length;
  const inactiveCount = items.filter(i => i.ativo === false).length;
  const allSelected = selectedIds.length === items.length && items.length > 0;

  return (
    <>
      {/* Busca e Filtros */}
      <div className="mb-4 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder={searchPlaceholder}
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10 pr-10"
          />
          {searchValue && (
            <button
              onClick={() => onSearchChange('')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button
            variant={filterValue === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => onFilterChange('all')}
          >
            Todos ({items.length})
          </Button>
          <Button
            variant={filterValue === 'ativo' ? 'default' : 'outline'}
            size="sm"
            onClick={() => onFilterChange('ativo')}
          >
            Ativos ({activeCount})
          </Button>
          <Button
            variant={filterValue === 'inativo' ? 'default' : 'outline'}
            size="sm"
            onClick={() => onFilterChange('inativo')}
          >
            Inativos ({inactiveCount})
          </Button>
        </div>
      </div>

      {/* Ações em Lote */}
      {selectedIds.length > 0 && (
        <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
            {selectedIds.length} {selectedIds.length === 1 ? 'item selecionado' : 'itens selecionados'}
          </span>
          <div className="flex gap-2 flex-wrap">
            <Button
              size="sm"
              variant="outline"
              onClick={() => onBulkAction('ativar')}
              disabled={saving}
            >
              Ativar
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onBulkAction('desativar')}
              disabled={saving}
            >
              Desativar
            </Button>
            <Button
              size="sm"
              variant="destructive"
              onClick={() => onBulkAction('excluir')}
              disabled={saving}
            >
              Excluir
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => items.forEach(i => i.id && selectedIds.includes(i.id) && onToggleSelect(i.id))}
            >
              Cancelar
            </Button>
          </div>
        </div>
      )}

      {/* Lista */}
      <div className="space-y-3">
        {items.length === 0 && (
          <p className="text-gray-500 italic text-center py-8">
            {emptyMessage}
          </p>
        )}

        {items.length > 0 && (
          <div className="flex items-center gap-2 p-2 bg-gray-100 dark:bg-gray-800 rounded">
            <button
              onClick={onToggleSelectAll}
              className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
            >
              {allSelected ? (
                <CheckSquare className="w-4 h-4" />
              ) : (
                <Square className="w-4 h-4" />
              )}
              Selecionar todos
            </button>
          </div>
        )}

        {items.map((item, index) => (
          <div
            key={item.id}
            className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
          >
            <input
              type="checkbox"
              checked={selectedIds.includes(item.id!)}
              onChange={() => onToggleSelect(item.id!)}
              className="w-4 h-4 rounded border-gray-300"
            />
            <div className="flex-1">
              {renderItem(item)}
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onReorder(item.id!, 'up')}
                disabled={index === 0 || saving}
                title="Mover para cima"
              >
                <ArrowUp className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onReorder(item.id!, 'down')}
                disabled={index === items.length - 1 || saving}
                title="Mover para baixo"
              >
                <ArrowDown className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onEdit(item)}
              >
                <Pencil className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="text-red-600"
                onClick={() => onDelete(item.id!, getItemName(item))}
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </div>
        ))}

        {items.length > 0 && (
          <p className="text-sm text-gray-500 text-center pt-2">
            Mostrando {items.length} itens
          </p>
        )}
      </div>
    </>
  );
}
