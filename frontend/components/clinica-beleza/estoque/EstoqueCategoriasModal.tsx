"use client";

import { useCallback } from "react";
import { CategoriasCadastroModal } from "@/components/clinica-beleza/categorias-cadastro/CategoriasCadastroModal";
import {
  ESTOQUE_INPUT_CLASS,
  extractEstoqueApiError,
  type EstoqueCategoria,
} from "@/components/clinica-beleza/estoque/estoque-types";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";

interface Props {
  open: boolean;
  onClose: () => void;
  onChanged: () => void;
  lojaCtx?: { slug: string };
}

export function EstoqueCategoriasModal({ open, onClose, onChanged, lojaCtx }: Props) {
  const list = useCallback(async () => {
    const data = await ClinicaBelezaAPI.estoque.categorias.list(lojaCtx);
    const rows = Array.isArray(data) ? (data as EstoqueCategoria[]) : [];
    return rows.map((cat) => ({
      id: cat.id,
      nome: cat.nome,
      cor: cat.cor,
      quantidade: cat.produtos_count ?? 0,
    }));
  }, [lojaCtx]);

  return (
    <CategoriasCadastroModal
      open={open}
      onClose={onClose}
      onChanged={onChanged}
      title="Categorias do estoque"
      layout="portrait"
      placeholder="Ex.: Injetáveis"
      inputClass={ESTOQUE_INPUT_CLASS}
      unidade="produto"
      confirmExcluir={(nome) => `Excluir a categoria "${nome}"?`}
      list={list}
      create={(data) => ClinicaBelezaAPI.estoque.categorias.create(data, lojaCtx)}
      update={(id, data) => ClinicaBelezaAPI.estoque.categorias.update(id, data)}
      remove={(id) => ClinicaBelezaAPI.estoque.categorias.delete(id)}
      formatError={extractEstoqueApiError}
    />
  );
}
