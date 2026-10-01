"use client";

import { Stethoscope } from "lucide-react";
import { CategoriasSelecaoGrid } from "../categorias-cadastro/CategoriasSelecaoGrid";

export type ProcedimentoCategoriaCard = {
  value: string;
  label: string;
  count: number;
  cor?: string;
};

interface Props {
  categorias: ProcedimentoCategoriaCard[];
  loading?: boolean;
  totalProcedimentos?: number;
  onSelect: (categoria: ProcedimentoCategoriaCard) => void;
  onVerTodos: () => void;
  onGerenciar: () => void;
}

export function ProcedimentosCategoriasGrid({
  categorias,
  loading,
  totalProcedimentos,
  onSelect,
  onVerTodos,
  onGerenciar,
}: Props) {
  return (
    <CategoriasSelecaoGrid
      loading={loading}
      textoItens="procedimentos"
      unidade="procedimento"
      total={totalProcedimentos}
      iconeVerTodos={Stethoscope}
      categorias={categorias.map((cat) => ({
        id: cat.value,
        label: cat.label,
        count: cat.count,
        cor: cat.cor,
      }))}
      onSelect={(id) => {
        const cat = categorias.find((item) => item.value === id);
        if (cat) onSelect(cat);
      }}
      onVerTodos={onVerTodos}
      onGerenciar={onGerenciar}
    />
  );
}
