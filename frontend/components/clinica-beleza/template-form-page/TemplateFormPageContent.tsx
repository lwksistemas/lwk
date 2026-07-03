"use client";

import { FileText, Info, Loader2, Save } from "lucide-react";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { useLojaTheme } from "@/hooks/useLojaTheme";
import { useParams } from "next/navigation";
import {
  TEMPLATE_FORM_INPUT_CLASS,
  TEMPLATE_FORM_LABEL_CLASS,
  TEMPLATE_FORM_SECTION_TITLE_CLASS,
  TEMPLATE_PLACEHOLDERS,
  TEMPLATE_TIPO_OPTIONS,
} from "./template-form-page-types";
import { useTemplateFormPage } from "./useTemplateFormPage";

export function TemplateFormPageContent() {
  const slug = useParams().slug as string;
  const { theme } = useLojaTheme(slug);
  const accentColor = theme.corPrimaria || CLINICA_BELEZA_PRIMARY;
  const { isEditing, form, set, saving, loading, error, voltarLista, salvar, inserirPlaceholder } =
    useTemplateFormPage();

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
                      <p className={TEMPLATE_FORM_SECTION_TITLE_CLASS}>Dados do template</p>
                      <div>
                        <label className={TEMPLATE_FORM_LABEL_CLASS}>Nome *</label>
                        <input
                          value={form.nome}
                          onChange={(e) => set("nome", e.target.value)}
                          className={TEMPLATE_FORM_INPUT_CLASS}
                          placeholder="Ex.: Receituário padrão"
                          autoFocus
                        />
                      </div>
                      <div>
                        <label className={TEMPLATE_FORM_LABEL_CLASS}>Tipo *</label>
                        <select
                          value={form.tipo}
                          onChange={(e) => set("tipo", e.target.value)}
                          className={TEMPLATE_FORM_INPUT_CLASS}
                        >
                          {TEMPLATE_TIPO_OPTIONS.map((opt) => (
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
                          {TEMPLATE_PLACEHOLDERS.map((p) => (
                            <button
                              key={p.tag}
                              type="button"
                              onClick={() => inserirPlaceholder(p.tag)}
                              className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 text-left transition-colors"
                            >
                              <code
                                className="text-xs font-mono px-1.5 py-0.5 rounded shrink-0"
                                style={{ backgroundColor: `${accentColor}18`, color: accentColor }}
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
                      <p className={TEMPLATE_FORM_SECTION_TITLE_CLASS}>Conteúdo</p>
                      <div>
                        <label className={TEMPLATE_FORM_LABEL_CLASS}>Texto do documento *</label>
                        <textarea
                          value={form.conteudo}
                          onChange={(e) => set("conteudo", e.target.value)}
                          className={`${TEMPLATE_FORM_INPUT_CLASS} resize-y min-h-[360px] lg:min-h-[420px]`}
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
                  onClick={() => void salvar()}
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
