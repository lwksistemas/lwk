"use client";

import { useCallback } from "react";
import { CategoriasCadastroModal } from "@/components/clinica-beleza/categorias-cadastro/CategoriasCadastroModal";
import { FORM_INPUT_CLASS } from "./procedimentos-page-types";
import { ClinicaBelezaAPI, type ProcedimentoCategoriaItem } from "@/lib/clinica-beleza-api";
import { formatApiErrorBody } from "@/lib/api-errors";

interface Props {
  open: boolean;
  onClose: () => void;
  onChanged: () => void;
  lojaCtx?: { slug: string };
}

export function ProcedimentosCategoriasModal({ open, onClose, onChanged, lojaCtx }: Props) {
  const list = useCallback(async () => {
    const data = await ClinicaBelezaAPI.procedures.categorias.list(lojaCtx);
    const rows = Array.isArray(data) ? (data as ProcedimentoCategoriaItem[]) : [];
    return rows.map((cat) => ({
      id: cat.id,
      nome: cat.nome,
      cor: cat.cor,
      quantidade: cat.procedimentos_count ?? 0,
    }));
  }, [lojaCtx]);

  const formatError = useCallback(
    (err: unknown, fallback: string) => formatApiErrorBody(err) || fallback,
    [],
  );

  return (
    <CategoriasCadastroModal
      open={open}
      onClose={onClose}
      onChanged={onChanged}
      title="Categorias de procedimentos"
      layout="landscape"
      placeholder="Ex.: Harmonização facial"
      inputClass={FORM_INPUT_CLASS}
      unidade="procedimento"
      confirmExcluir={(nome) =>
        `Excluir a categoria "${nome}"? Procedimentos nesta categoria impedem a exclusão.`
      }
      list={list}
      create={(data) => ClinicaBelezaAPI.procedures.categorias.create(data, lojaCtx)}
      update={(id, data) => ClinicaBelezaAPI.procedures.categorias.update(id, data)}
      remove={(id) => ClinicaBelezaAPI.procedures.categorias.delete(id)}
      formatError={formatError}
    />
  );
}
