'use client';

import { ReactNode } from 'react';

interface SkeletonProps {
  className?: string;
  children?: ReactNode;
}

// Skeleton base com animação de pulse
export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div 
      className={`animate-pulse bg-gray-200 dark:bg-gray-700 rounded ${className}`}
    />
  );
}

// Skeleton para cards de estatísticas
export function StatCardSkeleton() {
  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <Skeleton className="h-4 w-24 mb-3" />
          <Skeleton className="h-8 w-16" />
        </div>
        <Skeleton className="w-12 h-12 rounded-full" />
      </div>
    </div>
  );
}

// Skeleton para lista de agendamentos
export function AgendamentoSkeleton() {
  return (
    <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
      <div className="flex items-center space-x-4">
        <Skeleton className="w-12 h-12 rounded-full" />
        <div>
          <Skeleton className="h-5 w-32 mb-2" />
          <Skeleton className="h-4 w-24 mb-1" />
          <Skeleton className="h-3 w-20" />
        </div>
      </div>
      <div className="text-right">
        <Skeleton className="h-5 w-16 mb-2" />
        <Skeleton className="h-4 w-20 mb-1" />
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
    </div>
  );
}

// Skeleton para lista completa de agendamentos
export function AgendamentosListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <AgendamentoSkeleton key={i} />
      ))}
    </div>
  );
}

// Skeleton para cards de ação rápida
export function ActionButtonSkeleton() {
  return (
    <Skeleton className="h-24 rounded-lg" />
  );
}

// Skeleton para grid de ações rápidas
export function ActionsGridSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {Array.from({ length: 11 }).map((_, i) => (
        <ActionButtonSkeleton key={i} />
      ))}
    </div>
  );
}

// Skeleton para tabela de dados
export function TableRowSkeleton() {
  return (
    <div className="flex items-center justify-between p-4 border-b dark:border-gray-700">
      <div className="flex items-center space-x-3">
        <Skeleton className="w-10 h-10 rounded-full" />
        <div>
          <Skeleton className="h-4 w-32 mb-2" />
          <Skeleton className="h-3 w-24" />
        </div>
      </div>
      <div className="flex gap-2">
        <Skeleton className="h-8 w-16 rounded" />
        <Skeleton className="h-8 w-16 rounded" />
      </div>
    </div>
  );
}

// Skeleton para formulário
export function FormFieldSkeleton() {
  return (
    <div>
      <Skeleton className="h-4 w-20 mb-2" />
      <Skeleton className="h-10 w-full rounded" />
    </div>
  );
}

// Skeleton para modal de formulário
export function FormModalSkeleton() {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <FormFieldSkeleton key={i} />
        ))}
      </div>
      <div className="flex gap-3 pt-4">
        <Skeleton className="h-10 flex-1 rounded" />
        <Skeleton className="h-10 flex-1 rounded" />
      </div>
    </div>
  );
}

// Dashboard completo skeleton
export function DashboardSkeleton() {
  return (
    <div className="space-y-8">
      {/* Ações rápidas */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
        <Skeleton className="h-6 w-32 mb-4" />
        <ActionsGridSkeleton />
      </div>
      
      {/* Estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>
      
      {/* Próximos agendamentos */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
        <div className="flex items-center justify-between mb-4">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-9 w-20 rounded" />
        </div>
        <AgendamentosListSkeleton count={3} />
      </div>
    </div>
  );
}
