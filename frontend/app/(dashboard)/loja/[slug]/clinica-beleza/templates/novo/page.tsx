"use client";

/**
 * Página dedicada para criação e edição de templates de documentos clínicos — Clínica da Beleza.
 * Campos: nome, tipo (receituario, pedido_exame, atestado, documento_personalizado), conteúdo.
 * Mostra dica de placeholders disponíveis.
 * Quando recebe ?id=X, carrega template existente para edição.
 */

import { useState, useEffect } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Save, FileText, Info, Loader2 } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";

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

const inputClass =
  "w-full px-3 py-2 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100";
const labelClass =
  "block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1";

export default function NovoTemplatePage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;

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

  // Carregar template existente quando ?id=X está presente
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
      .catch((e: any) => {
        const msg =
          e?.detail || e?.message || "Erro ao carregar template para edição.";
        setError(typeof msg === "string" ? msg : JSON.stringify(msg));
      })
      .finally(() => setLoading(false));
  }, [editId]);

  const set = (field: string, value: string) =>
    setForm((f) => ({ ...f, [field]: value }));

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
      router.push(`/loja/${slug}/clinica-beleza/templates`);
    } catch (e: any) {
      const msg =
        e?.nome?.[0] ||
        e?.tipo?.[0] ||
        e?.conteudo?.[0] ||
        e?.detail ||
        e?.message ||
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
        title={isEditing ? "Editar Template" : "Novo Template"}
        icon={FileText}
        backHref={`/loja/${slug}/clinica-beleza/templates`}
      />
      <ClinicaBelezaPageContent>
        <div className="max-w-2xl mx-auto space-y-6">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <Loader2
                size={24}
                className="animate-spin text-gray-400 dark:text-gray-500"
              />
              <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
                Carregando template...
              </span>
            </div>
          )}

          {error && !loading && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
              <p className="text-sm text-red-800 dark:text-red-300 whitespace-pre-line">
                {error}
              </p>
            </div>
          )}

          {/* Dados do Template */}
          {!loading && (
          <>
          <section className="bg-white dark:bg-neutral-800 rounded-xl border dark:border-neutral-700 p-5 space-y-4">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Dados do Template
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Nome *</label>
                <input
                  value={form.nome}
                  onChange={(e) => set("nome", e.target.value)}
                  className={inputClass}
                  placeholder="Ex.: Receituário padrão"
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
            </div>

            <div>
              <label className={labelClass}>Conteúdo *</label>
              <textarea
                value={form.conteudo}
                onChange={(e) => set("conteudo", e.target.value)}
                className={`${inputClass} min-h-[200px] resize-y`}
                placeholder="Digite o conteúdo do template. Use os placeholders abaixo para inserir dados dinâmicos..."
                rows={10}
              />
            </div>
          </section>

          {/* Placeholders Disponíveis */}
          <section className="bg-white dark:bg-neutral-800 rounded-xl border dark:border-neutral-700 p-5 space-y-3">
            <div className="flex items-center gap-2">
              <Info size={16} className="text-gray-500 dark:text-gray-400" />
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                Placeholders Disponíveis
              </h3>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Clique em um placeholder para inseri-lo no conteúdo. Eles serão
              substituídos pelos dados reais ao gerar o documento.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {PLACEHOLDERS.map((p) => (
                <button
                  key={p.tag}
                  type="button"
                  onClick={() => inserirPlaceholder(p.tag)}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 text-left transition-colors"
                >
                  <code className="text-xs font-mono px-1.5 py-0.5 rounded bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300">
                    {p.tag}
                  </code>
                  <span className="text-xs text-gray-600 dark:text-gray-400">
                    {p.desc}
                  </span>
                </button>
              ))}
            </div>
          </section>

          {/* Botões */}
          <div className="flex gap-3 pb-8">
            <button
              type="button"
              onClick={() =>
                router.push(`/loja/${slug}/clinica-beleza/templates`)
              }
              className="flex-1 py-2.5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={salvar}
              disabled={saving}
              className="flex-1 py-2.5 rounded-lg text-white text-sm font-medium disabled:opacity-50 inline-flex items-center justify-center gap-2"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              <Save size={16} />
              {saving
                ? "Salvando..."
                : isEditing
                ? "Salvar Alterações"
                : "Salvar Template"}
            </button>
          </div>
          </>
          )}
        </div>
      </ClinicaBelezaPageContent>
    </>
  );
}
