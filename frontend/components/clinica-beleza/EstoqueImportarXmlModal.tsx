"use client";

import { useState } from "react";
import { FileUp, Loader2, X, CheckCircle2, AlertCircle } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";

interface ProdutoPreview {
  nome: string;
  unidade_medida: string;
  quantidade: string;
  preco_custo: string;
  lote: string;
  validade: string | null;
}

interface PreviewResult {
  preview: boolean;
  nota: { numero: string; fornecedor: string; data_emissao: string };
  produtos: ProdutoPreview[];
  total_produtos: number;
  aviso_destinatario?: string;
}

interface ImportResult {
  criados: number;
  atualizados: number;
  erros: { nome: string; erros: Record<string, string[]> }[];
  nota: { numero: string; fornecedor: string; data_emissao: string };
}

const CATEGORIAS = [
  { value: "injetavel", label: "Injetável" },
  { value: "soroterapia", label: "Soroterapia" },
  { value: "cosmético", label: "Cosmético" },
  { value: "medicamentos", label: "Medicamentos" },
  { value: "descartavel", label: "Descartável" },
  { value: "equipamento", label: "Equipamento" },
  { value: "outro", label: "Outro" },
];

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function EstoqueImportarXmlModal({ open, onClose, onSuccess }: Props) {
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [categoria, setCategoria] = useState("outro");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState<PreviewResult | null>(null);
  const [resultado, setResultado] = useState<ImportResult | null>(null);

  const reset = () => {
    setArquivo(null);
    setCategoria("outro");
    setError("");
    setPreview(null);
    setResultado(null);
  };

  const handleClose = () => {
    if (loading) return;
    reset();
    onClose();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setArquivo(file);
    setError("");
    setPreview(null);
    setResultado(null);
  };

  const enviarXml = async (confirmar: boolean) => {
    if (!arquivo) {
      setError("Selecione o arquivo XML da NF-e.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("arquivo", arquivo);
      formData.append("categoria", categoria);
      if (confirmar) formData.append("confirmar", "true");

      const res = await clinicaBelezaFetch("/estoque/importar-xml/", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Erro ao processar XML.");
        return;
      }

      if (data.preview) {
        setPreview(data as PreviewResult);
      } else {
        setResultado(data as ImportResult);
        if (data.criados > 0) onSuccess();
      }
    } catch {
      setError("Erro ao enviar arquivo. Tente novamente.");
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-lg max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-neutral-700 shrink-0">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Importar XML (NF-e)</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Importe produtos da nota fiscal eletrônica
            </p>
          </div>
          <button type="button" onClick={handleClose} disabled={loading} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800">
            <X size={20} className="text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm flex items-start gap-2">
              <AlertCircle size={16} className="shrink-0 mt-0.5" />
              {error}
            </div>
          )}

          {/* Resultado final */}
          {resultado && (
            <div className="p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle2 size={20} className="text-green-600" />
                <span className="font-semibold text-green-800 dark:text-green-200">
                  {resultado.criados > 0 && `${resultado.criados} novo${resultado.criados !== 1 ? "s" : ""}`}
                  {resultado.criados > 0 && resultado.atualizados > 0 && " · "}
                  {resultado.atualizados > 0 && `${resultado.atualizados} atualizado${resultado.atualizados !== 1 ? "s" : ""} (estoque somado)`}
                </span>
              </div>
              {resultado.nota.numero && (
                <p className="text-xs text-green-700 dark:text-green-300">
                  NF nº {resultado.nota.numero} — {resultado.nota.fornecedor}
                </p>
              )}
              {(resultado as unknown as {aviso_destinatario?: string}).aviso_destinatario && (
                <div className="mt-2 p-2 rounded bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 flex items-start gap-2">
                  <AlertCircle size={14} className="shrink-0 mt-0.5 text-amber-600" />
                  <p className="text-xs text-amber-800 dark:text-amber-200">
                    {(resultado as unknown as {aviso_destinatario: string}).aviso_destinatario}
                  </p>
                </div>
              )}
              {resultado.erros.length > 0 && (
                <div className="mt-2 text-xs text-red-600">
                  {resultado.erros.length} erro{resultado.erros.length !== 1 ? "s" : ""}:
                  {resultado.erros.slice(0, 3).map((e, i) => (
                    <p key={i}>• {e.nome}: {JSON.stringify(e.erros)}</p>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Preview */}
          {preview && !resultado && (
            <div>
              {preview.aviso_destinatario && (
                <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 mb-3 flex items-start gap-2">
                  <AlertCircle size={16} className="shrink-0 mt-0.5 text-amber-600" />
                  <p className="text-sm text-amber-800 dark:text-amber-200">
                    <strong>Atenção:</strong> {preview.aviso_destinatario}
                  </p>
                </div>
              )}
              <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 mb-3">
                <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
                  NF nº {preview.nota.numero || "—"} — {preview.nota.fornecedor || "Fornecedor"}
                </p>
                <p className="text-xs text-blue-600 dark:text-blue-400">
                  {preview.total_produtos} produto{preview.total_produtos !== 1 ? "s" : ""} encontrado{preview.total_produtos !== 1 ? "s" : ""}
                </p>
              </div>
              <div className="max-h-48 overflow-y-auto border border-gray-200 dark:border-neutral-700 rounded-lg divide-y divide-gray-100 dark:divide-neutral-700">
                {preview.produtos.map((p, i) => (
                  <div key={i} className="px-3 py-2 text-sm">
                    <p className="font-medium text-gray-900 dark:text-gray-100 truncate">{p.nome}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {p.quantidade} {p.unidade_medida} × R$ {parseFloat(p.preco_custo || "0").toFixed(2)}
                      {p.lote ? ` · Lote: ${p.lote}` : ""}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Upload form */}
          {!resultado && !preview && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Arquivo XML da NF-e *
                </label>
                <input
                  type="file"
                  accept=".xml"
                  onChange={handleFileChange}
                  className="w-full text-sm text-gray-600 dark:text-gray-400 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-purple-50 file:text-purple-700 dark:file:bg-purple-900/20 dark:file:text-purple-300 hover:file:bg-purple-100"
                />
                {arquivo && (
                  <p className="mt-1 text-xs text-gray-500">{arquivo.name} ({(arquivo.size / 1024).toFixed(0)} KB)</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Categoria padrão dos produtos
                </label>
                <select
                  value={categoria}
                  onChange={(e) => setCategoria(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                >
                  {CATEGORIAS.map((c) => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-neutral-700 flex justify-between gap-3 shrink-0">
          {resultado ? (
            <button
              type="button"
              onClick={handleClose}
              className="ml-auto px-4 py-2 text-sm font-medium text-white rounded-lg"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              Fechar
            </button>
          ) : preview ? (
            <>
              <button
                type="button"
                onClick={() => { setPreview(null); setArquivo(null); }}
                className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800 rounded-lg"
              >
                Voltar
              </button>
              <button
                type="button"
                onClick={() => enviarXml(true)}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white rounded-lg disabled:opacity-50"
                style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
              >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
                Confirmar importação ({preview.total_produtos})
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800 rounded-lg"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={() => enviarXml(false)}
                disabled={loading || !arquivo}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white rounded-lg disabled:opacity-50"
                style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
              >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <FileUp size={16} />}
                Visualizar produtos
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
