'use client';

import Image from 'next/image';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { BulkActionList } from '@/components/superadmin/BulkActionList';
import { HeroImagemData, FilterAtivo, ItemType } from './types';

interface HeroImagensTabProps {
  items: HeroImagemData[];
  searchValue: string;
  onSearchChange: (v: string) => void;
  filterValue: FilterAtivo;
  onFilterChange: (v: FilterAtivo) => void;
  selectedIds: number[];
  onToggleSelect: (id: number) => void;
  onToggleSelectAll: () => void;
  onBulkAction: (action: 'ativar' | 'desativar' | 'excluir') => void;
  onReorder: (id: number, direction: 'up' | 'down') => void;
  onEdit: (item: HeroImagemData) => void;
  onDelete: (id: number, name: string) => void;
  onAdd: () => void;
  saving: boolean;
}

export function HeroImagensTab({
  items, searchValue, onSearchChange, filterValue, onFilterChange,
  selectedIds, onToggleSelect, onToggleSelectAll, onBulkAction,
  onReorder, onEdit, onDelete, onAdd, saving,
}: HeroImagensTabProps) {
  return (
    <Card className="overflow-x-auto">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Imagens do Hero (Carrossel)</CardTitle>
          <CardDescription>
            Imagens que alternam automaticamente no fundo da seção Hero da homepage
          </CardDescription>
        </div>
        <Button size="sm" onClick={onAdd}>
          <Plus className="w-4 h-4 mr-2" />
          Nova Imagem
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
          onEdit={onEdit}
          onDelete={onDelete}
          renderItem={(h) => (
            <>
              <p className="font-medium">{h.titulo || 'Sem título'}</p>
              {h.imagem && (
                <div className="mt-2 relative w-full aspect-video">
                  <Image
                    src={h.imagem}
                    alt={h.titulo || 'Imagem do hero'}
                    fill
                    className="object-contain rounded"
                    sizes="(max-width: 768px) 100vw, 900px"
                    unoptimized
                  />
                </div>
              )}
              <p className="text-xs text-gray-500 mt-1 truncate">{h.imagem}</p>
            </>
          )}
          getItemName={(h) => h.titulo || 'Imagem sem título'}
          searchPlaceholder="Buscar por título..."
          emptyMessage={
            searchValue || filterValue !== 'all'
              ? 'Nenhuma imagem encontrada com os filtros aplicados.'
              : 'Nenhuma imagem. Clique em Nova Imagem para adicionar.'
          }
          saving={saving}
        />
      </CardContent>
    </Card>
  );
}
