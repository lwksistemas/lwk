"use client";

import { useState } from "react";
import { AlertCircle, CheckCircle2, Loader2, X } from "lucide-react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api/client";
import type { FornecedorItem, FornecedorProdutoPreview } from "@/lib/clinica-beleza-api/client-ops";
import { extractEstoqueApiError } from "./estoque-types";

function ehPdf(file: File) {
  return file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
}

export function EstoqueCatalogoImportModal({
  fornecedor,
  onClose,
}: {
  fornecedor: FornecedorItem | null;
  onClose: () => void;
}) {
  const [itens, setItens] = useState<FornecedorProdutoPreview[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState<{ criados: number; atualizados: number } | null>(null);
  const [origemPdf, setOrigemPdf] = useState(false);

  if (!fornecedor) return null;

  const lerArquivo = async (file: File) => {
    setError("");
    setResultado(null);
    setOrigemPdf(ehPdf(file));
    setLoading(true);
    try {
      const data = ehPdf(file)
        ? await ClinicaBelezaAPI.estoque.fornecedores.previewCatalogoArquivo(fornecedor.id, file)
        : await ClinicaBelezaAPI.estoque.fornecedores.previewCatalogo(fornecedor.id, await file.text());
      setItens(data.itens);
    } catch (err) {
      setItens([]);
      setError(extractEstoqueApiError(err, "Não foi possível ler o arquivo."));
    } finally {
      setLoading(false);
    }
  };

  const confirmar = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await ClinicaBelezaAPI.estoque.fornecedores.importarCatalogo(fornecedor.id, itens);
      setResultado(data);
    } catch (err) {
      setError(extractEstoqueApiError(err, "Erro ao importar catálogo."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-3 sm:p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-[96vw] max-w-6xl h-[90vh] max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-neutral-700">
          <div>
            <h2 className="text-lg font-semibold">Importar catálogo</h2>
            <p className="text-xs text-gray-500 mt-0.5">
              CSV, TXT ou PDF do fornecedor {fornecedor.nome_fantasia || fornecedor.razao_social}. Não cria produto de estoque.
            </p>
          </div>
          <button type="button" onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800">
            <X size={20} className="text-gray-500" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 text-red-600 text-sm flex gap-2">
              <AlertCircle size={16} className="shrink-0 mt-0.5" />
              {error}
            </div>
          )}
          {resultado && (
            <div className="p-3 rounded-lg bg-green-50 text-green-700 text-sm flex gap-2">
              <CheckCircle2 size={16} className="shrink-0 mt-0.5" />
              {resultado.criados} criados, {resultado.atualizados} atualizados.
            </div>
          )}
          <input
            type="file"
            accept=".csv,.txt,.pdf,text/csv,text/plain,application/pdf"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void lerArquivo(f);
            }}
            className="text-sm"
          />
          <p className="text-xs text-gray-500">
            Planilha: colunas codigo, nome, unidade, preco. PDF de tabela/catálogo: o sistema lê nome e preço em R$ —
            confira a prévia antes de confirmar.
          </p>
          {origemPdf && itens.length > 0 && !resultado && (
            <p className="text-xs text-amber-700">
              {itens.length} produtos lidos do PDF. Remova o que não for produto antes de importar.
            </p>
          )}
          {itens.length > 0 && (
            <div className="text-sm border rounded-lg overflow-auto max-h-[58vh]">
              <table className="w-full min-w-[720px]">
                <thead className="bg-gray-50 dark:bg-neutral-800 sticky top-0">
                  <tr>
                    <th className="text-left p-2 w-48">Código</th>
                    <th className="text-left p-2">Nome</th>
                    <th className="text-left p-2 w-16">Un.</th>
                    <th className="text-right p-2 w-28">Preço</th>
                    {!resultado && <th className="w-10" />}
                  </tr>
                </thead>
                <tbody>
                  {itens.map((i) => (
                    <tr key={i.codigo} className="border-t">
                      <td className="p-2 whitespace-nowrap font-mono text-xs">{i.codigo}</td>
                      <td className="p-2">{i.nome}</td>
                      <td className="p-2">{i.unidade}</td>
                      <td className="p-2 text-right whitespace-nowrap">{i.preco_ref}</td>
                      {!resultado && (
                        <td className="p-1">
                          <button
                            type="button"
                            title="Remover da prévia"
                            onClick={() => setItens((atual) => atual.filter((item) => item.codigo !== i.codigo))}
                            className="p-1 rounded hover:bg-gray-100 dark:hover:bg-neutral-800"
                          >
                            <X size={14} className="text-gray-500" />
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        <div className="px-6 py-3 border-t flex justify-end gap-2">
          <button type="button" onClick={onClose} className="px-3 py-2 text-sm rounded-lg border">
            Fechar
          </button>
          <button
            type="button"
            disabled={loading || itens.length === 0 || Boolean(resultado)}
            onClick={() => void confirmar()}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg text-white disabled:opacity-50"
            style={{ background: "var(--cb-primary, #8B3D52)" }}
          >
            {loading && <Loader2 size={16} className="animate-spin" />}
            Confirmar importação
          </button>
        </div>
      </div>
    </div>
  );
}
