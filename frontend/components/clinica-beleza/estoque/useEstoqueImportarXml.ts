import { useCallback, useState } from "react";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import type { ImportResult, PreviewResult } from "./estoque-importar-xml-types";
import {
  DEFAULT_ESTOQUE_IMPORT_CATEGORIA,
  buildEstoqueImportFormData,
  extractEstoqueImportError,
  hasEstoqueImportChanges,
} from "./estoque-importar-xml-utils";

export function useEstoqueImportarXml(onClose: () => void, onSuccess: () => void) {
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [categoria, setCategoria] = useState(DEFAULT_ESTOQUE_IMPORT_CATEGORIA);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState<PreviewResult | null>(null);
  const [resultado, setResultado] = useState<ImportResult | null>(null);

  const reset = useCallback(() => {
    setArquivo(null);
    setCategoria(DEFAULT_ESTOQUE_IMPORT_CATEGORIA);
    setError("");
    setPreview(null);
    setResultado(null);
  }, []);

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

  const enviarXml = useCallback(
    async (confirmar: boolean) => {
      if (!arquivo) {
        setError("Selecione o arquivo XML da NF-e.");
        return;
      }
      setLoading(true);
      setError("");
      try {
        const res = await clinicaBelezaFetch("/estoque/importar-xml/", {
          method: "POST",
          body: buildEstoqueImportFormData(arquivo, categoria, confirmar),
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
    [arquivo, categoria],
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
  };
}
