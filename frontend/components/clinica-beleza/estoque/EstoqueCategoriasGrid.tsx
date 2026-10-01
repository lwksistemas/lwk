"use client";

import { Package } from "lucide-react";
import { CategoriasSelecaoGrid } from "../categorias-cadastro/CategoriasSelecaoGrid";
import type { EstoqueCategoria } from "./estoque-types";

interface Props {
  categorias: EstoqueCategoria[];
  loading?: boolean;
  onSelect: (categoria: EstoqueCategoria) => void;
  onVerTodos: () => void;
  onGerenciar: () => void;
  totalProdutos?: number;
}

export function EstoqueCategoriasGrid({
  categorias,
  loading,
  onSelect,
  onVerTodos,
  onGerenciar,
  totalProdutos,
}: Props) {
  return (
    <CategoriasSelecaoGrid
      loading={loading}
      textoItens="produtos"
      unidade="produto"
      total={totalProdutos}
      iconeVerTodos={Package}
      categorias={categorias.map((cat) => ({
        id: String(cat.id),
        label: cat.nome,
        count: cat.produtos_count ?? 0,
        cor: cat.cor,
      }))}
      onSelect={(id) => {
        const cat = categorias.find((item) => String(item.id) === id);
        if (cat) onSelect(cat);
      }}
      onVerTodos={onVerTodos}
      onGerenciar={onGerenciar}
    />
  );
}
