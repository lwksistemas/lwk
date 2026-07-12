'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { BulkActionList } from '@/components/superadmin/BulkActionList';
import type { FilterAtivo, BulkActionType } from './types';

type BulkAction = BulkActionType;

interface ListSectionCardProps<TItem extends { id?: number; ativo?: boolean }> {
  title: string;
  description: string;
  addLabel: string;
  onAdd: () => void;

  items: TItem[];
  searchValue: string;
  onSearchChange: (v: string) => void;
  filterValue: FilterAtivo;
  onFilterChange: (v: FilterAtivo) => void;
  selectedIds: number[];
  onToggleSelect: (id: number) => void;
  onToggleSelectAll: () => void;
  onBulkAction: (action: BulkAction) => void;
  onReorder: (id: number, direction: 'up' | 'down') => void;
  onEdit: (item: TItem) => void;
  onDelete: (id: number, name: string) => void;

  renderItem: (item: TItem) => React.ReactNode;
  getItemName: (item: TItem) => string;
  searchPlaceholder: string;
  emptyMessage: string;
  saving: boolean;
}

export function ListSectionCard<TItem extends { id?: number; ativo?: boolean }>({
  title,
  description,
  addLabel,
  onAdd,
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
  saving,
}: ListSectionCardProps<TItem>) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
        <Button size="sm" onClick={onAdd}>
          <Plus className="w-4 h-4 mr-2" />
          {addLabel}
        </Button>
      </CardHeader>
      <CardContent>
        <BulkActionList
          items={items}
          searchValue={searchValue}
          onSearchChange={onSearchChange}
          filterValue={filterValue}
          onFilterChange={onFilterChange}
          selectedIds={selectedIds}
          onToggleSelect={onToggleSelect}
          onToggleSelectAll={onToggleSelectAll}
          onBulkAction={onBulkAction}
          onReorder={onReorder}
          onEdit={onEdit as any}
          onDelete={onDelete}
          renderItem={renderItem}
          getItemName={getItemName}
          searchPlaceholder={searchPlaceholder}
          emptyMessage={emptyMessage}
          saving={saving}
        />
      </CardContent>
    </Card>
  );
}

