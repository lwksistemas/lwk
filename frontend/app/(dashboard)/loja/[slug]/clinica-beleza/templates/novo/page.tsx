"use client";

/**
 * Página dedicada para criação e edição de templates de documentos clínicos — Clínica da Beleza.
 * Layout full-page em 2 colunas (igual cadastro de procedimentos/clientes).
 */

import { useState, useEffect } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Save, FileText, Info, Loader2 } from "lucide-react";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { useLojaTheme } from "@/hooks/useLojaTheme";

const TIPO_OPTIONS = [
  { value: "receituario", label: "Receituário" },
  { value: "pedido_exame", label: "Pedido de Exame" },
  { value: "atestado", label: "Atestado" },
  { value: "documento_personalizado", label: "Documento Personalizado" },
];

const PLACEHOLDERS = [
  { tag: "{{paciente_nome}}", desc: "Nome do paciente" },
  { tag: "{{paciente_cpf}}", desc: "CPF do paciente" },
  { tag: "{{paciente_data_nascimento}}", desc: "Data de nascimento" },
  { tag: "{{profissional_nome}}", desc: "Nome do profissional" },
  { tag: "{{profissional_registro}}", desc: "Nº registro profissional" },
  { tag: "{{profissional_conselho}}", desc: "Conselho com UF e nº (ex.: COREN-SP 123456)" },
  { tag: "{{data_atual}}", desc: "Data do dia (DD/MM/AAAA)" },
  { tag: "{{consulta_procedimento}}", desc: "Procedimento da consulta" },
];

export default function NovoTemplatePage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const { theme } = useLojaTheme(slug);
  const accentColor = theme.corPrimaria || CLINICA_BELEZA_PRIMARY;

  const editId = searchParams.get("id");
  const isEditing = !!editId;

  const [form, setForm] = useState({
    nome: "",
    tipo: "receituario",
    conteudo: "",
  });
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const inputClass =
    "w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-0";
  const labelClass = "block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1";
  const sectionTitleClass =
    "text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-neutral-800 pb-2";

  useEffect(() => {
    if (!editId) return;
    const id = Number(editId);
    if (isNaN(id)) return;

    setLoading(true);
    setError("");
    ClinicaBelezaAPI.templates
      .get(id)
      .then((template) => {
        setForm({
          nome: template.nome || "",
          tipo: template.tipo || "receituario",
          conteudo: template.conteudo || "",
        });
      })
      .catch((e: { detail?: string; message?: string }) => {
        const msg = e?.detail || e?.message || "Erro ao carregar template para edição.";
        setError(typeof msg === "string" ? msg : JSON.stringify(msg));
      })
      .finally(() => setLoading(false));
  }, [editId]);

  const set = (field: string, value: string) => setForm((f) => ({ ...f, [field]: value }));

  const voltarLista = () => router.push(`/loja/${slug}/clinica-beleza/templates`);

  const salvar = async () => {
    if (!form.nome.trim()) {
      setError("Nome é obrigatório.");
      return;
    }
    if (!form.conteudo.trim()) {
      setError("Conteúdo é obrigatório.");
      return;
    }

    setSaving(true);
    setError("");

    try {
      if (isEditing) {
        await ClinicaBelezaAPI.templates.update(Number(editId), {
          nome: form.nome.trim(),
          tipo: form.tipo,
          conteudo: form.conteudo,
        });
      } else {
        await ClinicaBelezaAPI.templates.create({
          nome: form.nome.trim(),
          tipo: form.tipo,
          conteudo: form.conteudo,
        });
      }
      voltarLista();
    } catch (e: Record<string, unknown>) {
      const msg =
        (Array.isArray(e?.nome) ? e.nome[0] : null) ||
        (Array.isArray(e?.tipo) ? e.tipo[0] : null) ||
        (Array.isArray(e?.conteudo) ? e.conteudo[0] : null) ||
        (typeof e?.detail === "string" ? e.detail : null) ||
        (typeof e?.message === "string" ? e.message : null) ||
        "Erro ao salvar template.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setSaving(false);
    }
  };

  const inserirPlaceholder = (tag: string) => {
    setForm((f) => ({ ...f, conteudo: f.conteudo + tag }));
  };

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={isEditing ? "Editar template" : "Novo template"}
        subtitle={isEditing ? form.nome || undefined : "Cadastro de template de documento clínico"}
        icon={FileText}
        onBack={voltarLista}
      />
      <ClinicaBelezaPageContent className="flex flex-col flex-1 min-h-0 !p-0 !bg-[#f7f2f4] dark:!bg-gray-950">
        <div className="flex flex-col flex-1 min-h-0 w-full">
          <div className="flex-1 min-h-0 overflow-y-auto p-4 md:p-6 lg:p-8 bg-[#f7f2f4] dark:bg-gray-950">
            {loading ? (
              <div className="flex items-center justify-center py-16 text-gray-500">
                <Loader2 size={24} className="animate-spin mr-2" />
                Carregando template...
              </div>
            ) : (
              <>
                {error && (
                  <div className="mb-5 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm whitespace-pre-line">
                    {error}
                  </div>
                )}

                <ClinicaBelezaPanel className="p-5 md:p-6 lg:p-8">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10 xl:gap-14 w-full max-w-none">
                    <div className="space-y-4">
                      <p className={sectionTitleClass}>Dados do template</p>
                      <div>
                        <label className={labelClass}>Nome *</label>
                        <input
                          value={form.nome}
                          onChange={(e) => set("nome", e.target.value)}
                          className={inputClass}
                          placeholder="Ex.: Receituário padrão"
                          autoFocus
                        />
                      </div>
                      <div>
                        <label className={labelClass}>Tipo *</label>
                        <select
                          value={form.tipo}
                          onChange={(e) => set("tipo", e.target.value)}
                          className={inputClass}
                        >
                          {TIPO_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="space-y-3 pt-2">
                        <div className="flex items-center gap-2">
                          <Info size={16} className="text-gray-500 dark:text-gray-400 shrink-0" />
                          <p className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                            Placeholders disponíveis
                          </p>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          Clique para inserir no conteúdo. Serão substituídos pelos dados reais ao gerar o documento.
                        </p>
                        <div className="grid grid-cols-1 gap-2">
                          {PLACEHOLDERS.map((p) => (
                            <button
                              key={p.tag}
                              type="button"
                              onClick={() => inserirPlaceholder(p.tag)}
                              className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 text-left transition-colors"
                            >
                              <code
                                className="text-xs font-mono px-1.5 py-0.5 rounded shrink-0"
                                style={{
                                  backgroundColor: `${accentColor}18`,
                                  color: accentColor,
                                }}
                              >
                                {p.tag}
                              </code>
                              <span className="text-xs text-gray-600 dark:text-gray-400">{p.desc}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <p className={sectionTitleClass}>Conteúdo</p>
                      <div>
                        <label className={labelClass}>Texto do documento *</label>
                        <textarea
                          value={form.conteudo}
                          onChange={(e) => set("conteudo", e.target.value)}
                          className={`${inputClass} resize-y min-h-[360px] lg:min-h-[420px]`}
                          placeholder="Digite o conteúdo do template..."
                          rows={16}
                        />
                      </div>
                    </div>
                  </div>
                </ClinicaBelezaPanel>
              </>
            )}
          </div>

          {!loading && (
            <div className="shrink-0 border-t border-gray-200 dark:border-neutral-700 bg-white/80 dark:bg-neutral-800/80 px-4 md:px-6 lg:px-8 py-4">
              <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-3 w-full">
                <button
                  type="button"
                  onClick={voltarLista}
                  className="sm:min-w-[120px] py-2.5 px-5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-neutral-800"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={salvar}
                  disabled={saving}
                  className="sm:min-w-[180px] flex items-center justify-center gap-2 py-2.5 px-5 rounded-lg text-white text-sm font-medium disabled:opacity-60"
                  style={{ backgroundColor: accentColor }}
                >
                  {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
                  {saving ? "Salvando..." : isEditing ? "Salvar alterações" : "Cadastrar template"}
                </button>
              </div>
            </div>
          )}
        </div>
      </ClinicaBelezaPageContent>
    </>
  );
}
