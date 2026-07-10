import { useCallback, useEffect, useState } from "react";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import type { ImportResult, PreviewResult, ProdutoPreview } from "./estoque-importar-xml-types";
import type { EstoqueCategoria } from "./estoque-types";
import {
  DEFAULT_ESTOQUE_IMPORT_CATEGORIA,
  buildEstoqueImportFormData,
  extractEstoqueImportError,
  hasEstoqueImportChanges,
} from "./estoque-importar-xml-utils";

export function useEstoqueImportarXml(
  onClose: () => void,
  onSuccess: () => void,
  opts?: { categorias?: EstoqueCategoria[]; defaultCategoriaSlug?: string },
) {
  const defaultCat = opts?.defaultCategoriaSlug || DEFAULT_ESTOQUE_IMPORT_CATEGORIA;
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [categoria, setCategoria] = useState(defaultCat);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState<PreviewResult | null>(null);
  const [resultado, setResultado] = useState<ImportResult | null>(null);

  useEffect(() => {
    setCategoria(defaultCat);
  }, [defaultCat]);

  const reset = useCallback(() => {
    setArquivo(null);
    setCategoria(defaultCat);
    setError("");
    setPreview(null);
    setResultado(null);
  }, [defaultCat]);

  const handleClose = useCallback(() => {
    if (loading) return;
    if (resultado && hasEstoqueImportChanges(resultado)) {
      onSuccess();
    }
    reset();
    onClose();
  }, [loading, onClose, onSuccess, reset, resultado]);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setArquivo(file);
    setError("");
    setPreview(null);
    setResultado(null);
  }, []);

  const voltarPreview = useCallback(() => {
    setPreview(null);
    setArquivo(null);
  }, []);

  const updateProdutoCategoria = useCallback(
    (index: number, slug: string, categoriaId?: number | null) => {
      setPreview((prev) => {
        if (!prev) return prev;
        const produtos = prev.produtos.map((p, i) =>
          i === index
            ? { ...p, categoria: slug, categoria_id: categoriaId ?? p.categoria_id, categoria_motivo: "manual" }
            : p,
        );
        return { ...prev, produtos };
      });
    },
    [],
  );

  const enviarXml = useCallback(
    async (confirmar: boolean) => {
      if (!arquivo) {
        setError("Selecione o arquivo XML da NF-e.");
        return;
      }
      setLoading(true);
      setError("");
      try {
        const catId = opts?.categorias?.find((c) => c.slug === categoria)?.id ?? null;
        const res = await clinicaBelezaFetch("/estoque/importar-xml/", {
          method: "POST",
          body: buildEstoqueImportFormData(arquivo, categoria, confirmar, {
            categoriaId: catId,
            produtos: confirmar && preview ? preview.produtos : undefined,
          }),
        });

        const data = await res.json();
        if (!res.ok) {
          setError(extractEstoqueImportError(data));
          return;
        }

        if (data.preview) {
          setPreview(data as PreviewResult);
        } else {
          setResultado(data as ImportResult);
        }
      } catch {
        setError("Erro ao enviar arquivo. Tente novamente.");
      } finally {
        setLoading(false);
      }
    },
    [arquivo, categoria, opts?.categorias, preview],
  );

  return {
    arquivo,
    categoria,
    setCategoria,
    loading,
    error,
    preview,
    resultado,
    handleClose,
    handleFileChange,
    voltarPreview,
    enviarXml,
    updateProdutoCategoria,
  };
}
