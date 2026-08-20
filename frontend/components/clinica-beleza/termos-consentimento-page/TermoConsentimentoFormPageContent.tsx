"use client";

import { Loader2, Plus, Save, ScrollText, Trash2 } from "lucide-react";
import { useParams } from "next/navigation";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { useLojaTheme } from "@/hooks/useLojaTheme";
import { FORM_INPUT_CLASS, FORM_LABEL_CLASS } from "@/components/clinica-beleza/procedimentos-page/procedimentos-page-types";
import { TERMO_SECAO_TIPO_OPTIONS, TERMO_TIPO_OPTIONS } from "./termos-consentimento-utils";
import { useTermoConsentimentoForm } from "./useTermoConsentimentoForm";

export function TermoConsentimentoFormPageContent() {
  const slug = useParams().slug as string;
  const { theme } = useLojaTheme(slug);
  const accentColor = theme.corPrimaria || CLINICA_BELEZA_PRIMARY;
  const page = useTermoConsentimentoForm();

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={page.isEditing ? "Editar termo" : "Novo termo"}
        subtitle={page.form.tipo === "interativo" ? "TCLE Interativo" : "Termo simples"}
        icon={ScrollText}
        onBack={page.voltarLista}
      />
      <ClinicaBelezaPageContent>
        {page.loading ? (
          <div className="flex items-center justify-center py-16 text-gray-500">
            <Loader2 size={24} className="animate-spin mr-2" />
            Carregando…
          </div>
        ) : (
          <ClinicaBelezaPanel className="p-5 md:p-6 space-y-5">
            {page.error && (
              <div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm">{page.error}</div>
            )}
            <div>
              <label className={FORM_LABEL_CLASS}>Nome *</label>
              <input
                value={page.form.nome}
                onChange={(e) => page.set("nome", e.target.value)}
                className={FORM_INPUT_CLASS}
                placeholder="Ex.: TCLE Interativo — Microagulhamento"
              />
            </div>
            <div>
              <label className={FORM_LABEL_CLASS}>Procedimento *</label>
              <select
                value={page.form.procedimentoId ?? ""}
                onChange={(e) => page.set("procedimentoId", e.target.value ? Number(e.target.value) : null)}
                className={FORM_INPUT_CLASS}
              >
                <option value="">Selecione o procedimento</option>
                {page.procedimentosDisponiveis.map((p) => (
                  <option key={p.id} value={p.id}>{p.nome}</option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Cada procedimento usa um único termo. Cadastre o procedimento antes, se ainda não existir.
              </p>
            </div>
            <div>
              <label className={FORM_LABEL_CLASS}>Tipo *</label>
              <select
                value={page.form.tipo}
                onChange={(e) => page.set("tipo", e.target.value as "simples" | "interativo")}
                className={FORM_INPUT_CLASS}
              >
                {TERMO_TIPO_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            {page.form.tipo === "simples" ? (
              <div>
                <label className={FORM_LABEL_CLASS}>Texto do termo</label>
                <p className="text-xs text-gray-500 mb-2">
                  Variáveis: {"{paciente_nome}"}, {"{paciente_cpf}"}, {"{profissional_nome}"},{" "}
                  {"{profissional_conselho}"}, {"{clinica_nome}"}, {"{procedimentos}"}, {"{data}"}
                </p>
                <textarea
                  value={page.form.conteudo}
                  onChange={(e) => page.set("conteudo", e.target.value)}
                  rows={14}
                  className={`${FORM_INPUT_CLASS} font-mono text-xs min-h-[220px]`}
                />
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className={FORM_LABEL_CLASS}>Introdução (opcional)</label>
                  <p className="text-xs text-gray-500 mb-1">
                    Não coloque dados de paciente, profissional nem logomarca — o sistema preenche no envio.
                  </p>
                  <textarea
                    value={page.form.introducao}
                    onChange={(e) => page.set("introducao", e.target.value)}
                    rows={4}
                    className={FORM_INPUT_CLASS}
                  />
                </div>
                {page.form.secoes.map((secao, idx) => (
                  <div key={secao.id} className="rounded-lg border border-gray-200 dark:border-neutral-700 p-3 space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-xs font-semibold text-gray-700 dark:text-gray-300">Seção {idx + 1}</p>
                      <button type="button" onClick={() => page.removeSecao(idx)} className="text-gray-400 hover:text-red-600">
                        <Trash2 size={14} />
                      </button>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      <input
                        value={secao.codigo}
                        onChange={(e) => page.patchSecao(idx, { codigo: e.target.value })}
                        className={FORM_INPUT_CLASS}
                        placeholder="I, II…"
                      />
                      <input
                        value={secao.titulo}
                        onChange={(e) => page.patchSecao(idx, { titulo: e.target.value })}
                        className={`${FORM_INPUT_CLASS} sm:col-span-2`}
                        placeholder="Título da seção"
                      />
                    </div>
                    <select
                      value={secao.tipo}
                      onChange={(e) => page.patchSecao(idx, { tipo: e.target.value as typeof secao.tipo })}
                      className={FORM_INPUT_CLASS}
                    >
                      {TERMO_SECAO_TIPO_OPTIONS.map((o) => (
                        <option key={o.value} value={o.value}>{o.label}</option>
                      ))}
                    </select>
                    <textarea
                      value={secao.texto}
                      onChange={(e) => page.patchSecao(idx, { texto: e.target.value })}
                      rows={5}
                      className={FORM_INPUT_CLASS}
                      placeholder="Texto que o paciente lê nesta seção"
                    />
                  </div>
                ))}
                <button
                  type="button"
                  onClick={page.addSecao}
                  className="inline-flex items-center gap-1.5 text-sm font-medium"
                  style={{ color: accentColor }}
                >
                  <Plus size={16} /> Adicionar seção
                </button>
              </div>
            )}

            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => void page.salvar()}
                disabled={page.saving}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-white text-sm font-medium disabled:opacity-60"
                style={{ backgroundColor: accentColor }}
              >
                {page.saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                Salvar
              </button>
            </div>
          </ClinicaBelezaPanel>
        )}
      </ClinicaBelezaPageContent>
    </>
  );
}
