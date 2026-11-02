import { useCallback, useEffect, useState } from "react";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import type { ImportResult, NotaPendente, PreviewResult, ProdutoPreview } from "./estoque-importar-xml-types";
import type { EstoqueCategoria } from "./estoque-types";
import {
  DEFAULT_ESTOQUE_IMPORT_CATEGORIA,
  buildEstoqueImportFormData,
  extractEstoqueImportError,
  hasEstoqueImportChanges,
} from "./estoque-importar-xml-utils";

export function useEstoqueImportarXml(
  open: boolean,
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
  const [pendentes, setPendentes] = useState<NotaPendente[]>([]);
  const [notaId, setNotaId] = useState<number | null>(null);
  const [sincronizando, setSincronizando] = useState(false);

  useEffect(() => {
    setCategoria(defaultCat);
  }, [defaultCat]);

  const reset = useCallback(() => {
    setArquivo(null);
    setCategoria(defaultCat);
    setError("");
    setPreview(null);
    setResultado(null);
    setNotaId(null);
  }, [defaultCat]);

  const carregarPendentes = useCallback(async () => {
    try {
      const res = await clinicaBelezaFetch("/estoque/nfe-pendentes/");
      const data = await res.json();
      if (res.ok) setPendentes(Array.isArray(data.pendentes) ? data.pendentes : []);
    } catch {
      setPendentes([]);
    }
  }, []);

  useEffect(() => {
    if (open) void carregarPendentes();
  }, [open, carregarPendentes]);

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
          setNotaId(null);
          setPreview(data as PreviewResult);
        } else {
          setResultado(data as ImportResult);
          void carregarPendentes();
        }
      } catch {
        setError("Erro ao enviar arquivo. Tente novamente.");
      } finally {
        setLoading(false);
      }
    },
    [arquivo, categoria, opts?.categorias, preview, carregarPendentes],
  );

  const abrirPendente = useCallback(async (id: number) => {
    setLoading(true);
    setError("");
    try {
      const res = await clinicaBelezaFetch(`/estoque/nfe-pendentes/${id}/`);
      const data = await res.json();
      if (!res.ok) {
        setError(extractEstoqueImportError(data));
        return;
      }
      setNotaId(id);
      setArquivo(null);
      setPreview(data as PreviewResult);
    } catch {
      setError("Erro ao abrir a nota.");
    } finally {
      setLoading(false);
    }
  }, []);

  const confirmarPendente = useCallback(async () => {
    if (!notaId || !preview) return;
    setLoading(true);
    setError("");
    try {
      const res = await clinicaBelezaFetch(`/estoque/nfe-pendentes/${notaId}/confirmar/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          produtos: preview.produtos.map((p) => ({
            nome: p.nome,
            categoria: p.categoria,
            categoria_id: p.categoria_id ?? undefined,
          })),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(extractEstoqueImportError(data));
        return;
      }
      setResultado({ ...data, nota: preview.nota } as ImportResult);
      setPreview(null);
      void carregarPendentes();
    } catch {
      setError("Erro ao confirmar a nota.");
    } finally {
      setLoading(false);
    }
  }, [carregarPendentes, notaId, preview]);

  const ignorarPendente = useCallback(async (id: number) => {
    setError("");
    try {
      const res = await clinicaBelezaFetch(`/estoque/nfe-pendentes/${id}/ignorar/`, { method: "POST" });
      if (!res.ok) {
        const data = await res.json();
        setError(extractEstoqueImportError(data));
        return;
      }
      void carregarPendentes();
    } catch {
      setError("Erro ao ignorar a nota.");
    }
  }, [carregarPendentes]);

  const sincronizar = useCallback(async () => {
    setSincronizando(true);
    setError("");
    try {
      const res = await clinicaBelezaFetch("/estoque/nfe-pendentes/sincronizar/", { method: "POST" });
      const data = await res.json();
      if (Array.isArray(data.pendentes)) setPendentes(data.pendentes);
      if (!res.ok) {
        setError(typeof data.detail === "string" ? data.detail : extractEstoqueImportError(data));
      }
    } catch {
      setError("Erro ao consultar a SEFAZ.");
    } finally {
      setSincronizando(false);
    }
  }, []);

  return {
    arquivo,
    categoria,
    setCategoria,
    loading,
    error,
    preview,
    resultado,
    pendentes,
    notaId,
    sincronizando,
    handleClose,
    handleFileChange,
    voltarPreview,
    enviarXml,
    updateProdutoCategoria,
    abrirPendente,
    confirmarPendente,
    ignorarPendente,
    sincronizar,
  };
}
