"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertCircle, FileUp, Loader2, Plus, X } from "lucide-react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api/client";
import type { FornecedorItem } from "@/lib/clinica-beleza-api/client-ops";
import { consultaCnpj, formatCpfCnpj, resolverCepDadosCnpj } from "@/lib/consulta-cnpj";
import { ESTOQUE_INPUT_CLASS, extractEstoqueApiError } from "./estoque-types";
import { EstoqueCatalogoImportModal } from "./EstoqueCatalogoImportModal";

const EMPTY: Omit<FornecedorItem, "id" | "is_active"> & { is_active: boolean } = {
  cnpj: "",
  razao_social: "",
  nome_fantasia: "",
  inscricao_estadual: "",
  email: "",
  telefone: "",
  cep: "",
  logradouro: "",
  numero: "",
  complemento: "",
  bairro: "",
  municipio: "",
  uf: "",
  is_active: true,
};

export function EstoqueFornecedoresModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [lista, setLista] = useState<FornecedorItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ ...EMPTY });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [buscandoCnpj, setBuscandoCnpj] = useState(false);
  const [importForn, setImportForn] = useState<FornecedorItem | null>(null);

  const carregar = useCallback(async () => {
    setLoading(true);
    try {
      setLista(await ClinicaBelezaAPI.estoque.fornecedores.list({ todos: 1 }));
    } catch (err) {
      setError(extractEstoqueApiError(err, "Erro ao carregar fornecedores."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) void carregar();
  }, [open, carregar]);

  const set = (k: string, v: string | boolean) => setForm((f) => ({ ...f, [k]: v }));

  const buscarCnpj = async () => {
    const digits = form.cnpj.replace(/\D/g, "");
    if (digits.length !== 14) {
      setError("Informe um CNPJ com 14 dígitos.");
      return;
    }
    setBuscandoCnpj(true);
    setError("");
    try {
      const dados = await consultaCnpj(form.cnpj);
      if (!dados) {
        setError("CNPJ não encontrado na consulta.");
        return;
      }
      const cep = await resolverCepDadosCnpj(dados);
      setForm((f) => ({
        ...f,
        cnpj: formatCpfCnpj(digits),
        razao_social: dados.razao_social || f.razao_social,
        nome_fantasia: dados.nome_fantasia || f.nome_fantasia,
        email: dados.email || f.email,
        cep: cep || dados.cep || f.cep,
        logradouro: dados.logradouro || f.logradouro,
        numero: dados.numero || f.numero,
        complemento: dados.complemento || f.complemento,
        bairro: dados.bairro || f.bairro,
        municipio: dados.municipio || f.municipio,
        uf: dados.uf || f.uf,
      }));
    } finally {
      setBuscandoCnpj(false);
    }
  };

  const salvar = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      if (editingId) {
        await ClinicaBelezaAPI.estoque.fornecedores.update(editingId, form);
      } else {
        await ClinicaBelezaAPI.estoque.fornecedores.create(form);
      }
      setForm({ ...EMPTY });
      setEditingId(null);
      await carregar();
    } catch (err) {
      setError(extractEstoqueApiError(err, "Erro ao salvar fornecedor."));
    } finally {
      setSaving(false);
    }
  };

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
        <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col">
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-neutral-700">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Fornecedores</h2>
              <p className="text-xs text-gray-500 mt-0.5">Cadastro com CNPJ. O catálogo não altera o estoque.</p>
            </div>
            <button type="button" onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800">
              <X size={20} className="text-gray-500" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 text-sm flex gap-2">
                <AlertCircle size={16} className="shrink-0 mt-0.5" />
                {error}
              </div>
            )}
            <form onSubmit={salvar} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="sm:col-span-2 flex gap-2">
                <input
                  className={ESTOQUE_INPUT_CLASS}
                  placeholder="CNPJ"
                  value={form.cnpj}
                  onChange={(e) => set("cnpj", formatCpfCnpj(e.target.value))}
                  required
                />
                <button
                  type="button"
                  onClick={() => void buscarCnpj()}
                  disabled={buscandoCnpj}
                  className="px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-neutral-600 whitespace-nowrap"
                >
                  {buscandoCnpj ? <Loader2 size={16} className="animate-spin" /> : "Buscar CNPJ"}
                </button>
              </div>
              <input className={ESTOQUE_INPUT_CLASS} placeholder="Razão social" value={form.razao_social} onChange={(e) => set("razao_social", e.target.value)} required />
              <input className={ESTOQUE_INPUT_CLASS} placeholder="Nome fantasia" value={form.nome_fantasia} onChange={(e) => set("nome_fantasia", e.target.value)} />
              <input className={ESTOQUE_INPUT_CLASS} placeholder="E-mail" value={form.email} onChange={(e) => set("email", e.target.value)} />
              <input className={ESTOQUE_INPUT_CLASS} placeholder="Telefone / WhatsApp" value={form.telefone} onChange={(e) => set("telefone", e.target.value)} />
              <input className={ESTOQUE_INPUT_CLASS} placeholder="IE" value={form.inscricao_estadual} onChange={(e) => set("inscricao_estadual", e.target.value)} />
              <input className={ESTOQUE_INPUT_CLASS} placeholder="CEP" value={form.cep} onChange={(e) => set("cep", e.target.value)} />
              <input className={`${ESTOQUE_INPUT_CLASS} sm:col-span-2`} placeholder="Logradouro" value={form.logradouro} onChange={(e) => set("logradouro", e.target.value)} />
              <input className={ESTOQUE_INPUT_CLASS} placeholder="Número" value={form.numero} onChange={(e) => set("numero", e.target.value)} />
              <input className={ESTOQUE_INPUT_CLASS} placeholder="Complemento" value={form.complemento} onChange={(e) => set("complemento", e.target.value)} />
              <input className={ESTOQUE_INPUT_CLASS} placeholder="Bairro" value={form.bairro} onChange={(e) => set("bairro", e.target.value)} />
              <div className="flex gap-2">
                <input className={ESTOQUE_INPUT_CLASS} placeholder="Município" value={form.municipio} onChange={(e) => set("municipio", e.target.value)} />
                <input className={`${ESTOQUE_INPUT_CLASS} w-20`} placeholder="UF" value={form.uf} maxLength={2} onChange={(e) => set("uf", e.target.value.toUpperCase())} />
              </div>
              <div className="sm:col-span-2 flex justify-end gap-2">
                {editingId && (
                  <button
                    type="button"
                    onClick={() => {
                      setEditingId(null);
                      setForm({ ...EMPTY });
                    }}
                    className="px-3 py-2 text-sm rounded-lg border"
                  >
                    Novo
                  </button>
                )}
                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg text-white"
                  style={{ background: "var(--cb-primary, #8B3D52)" }}
                >
                  {saving ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
                  {editingId ? "Atualizar" : "Salvar fornecedor"}
                </button>
              </div>
            </form>

            <div className="border-t border-gray-200 dark:border-neutral-700 pt-3 space-y-2">
              {loading ? (
                <div className="flex justify-center py-6">
                  <Loader2 className="animate-spin text-gray-400" />
                </div>
              ) : lista.length === 0 ? (
                <p className="text-sm text-gray-500 py-4 text-center">Nenhum fornecedor cadastrado.</p>
              ) : (
                lista.map((f) => (
                  <div
                    key={f.id}
                    className="flex items-center justify-between gap-2 p-3 rounded-lg border border-gray-200 dark:border-neutral-700"
                  >
                    <div className="min-w-0">
                      <div className="font-medium text-sm text-gray-900 dark:text-gray-100 truncate">
                        {f.nome_fantasia || f.razao_social}
                      </div>
                      <div className="text-xs text-gray-500">{f.cnpj} · {f.email || "sem e-mail"}</div>
                    </div>
                    <div className="flex gap-1 shrink-0">
                      <button
                        type="button"
                        onClick={() => setImportForn(f)}
                        className="px-2 py-1 text-xs rounded-lg border inline-flex items-center gap-1"
                      >
                        <FileUp size={12} /> Catálogo
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setEditingId(f.id);
                          setForm({ ...f });
                        }}
                        className="px-2 py-1 text-xs rounded-lg border"
                      >
                        Editar
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
      <EstoqueCatalogoImportModal
        fornecedor={importForn}
        onClose={() => setImportForn(null)}
      />
    </>
  );
}
