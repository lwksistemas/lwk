import { PROCEDURE_CATEGORIA_OPTIONS } from "@/lib/clinica-beleza-categories";
import { toUpperCase } from "@/lib/format-br";
import type { ProcedimentoCategoriaItem } from "@/lib/clinica-beleza-api";
import {
  FORM_INPUT_CLASS,
  FORM_LABEL_CLASS,
  FORM_SECTION_TITLE_CLASS,
  type ProcedimentoFormState,
} from "./procedimentos-page-types";

interface ProcedimentoDadosFieldsProps {
  form: ProcedimentoFormState;
  categorias?: ProcedimentoCategoriaItem[];
  onChange: (patch: Partial<ProcedimentoFormState>) => void;
}

export function ProcedimentoDadosFields({ form, categorias = [], onChange }: ProcedimentoDadosFieldsProps) {
  const opcoes =
    categorias.length > 0
      ? categorias.map((c) => ({ value: c.slug, label: c.nome }))
      : PROCEDURE_CATEGORIA_OPTIONS.map((o) => ({ value: o.value, label: o.label }));
  return (
    <div className="space-y-4">
      <p className={FORM_SECTION_TITLE_CLASS}>Dados do procedimento</p>
      <div>
        <label className={FORM_LABEL_CLASS}>Nome do procedimento *</label>
        <input
          value={form.name}
          onChange={(e) => onChange({ name: toUpperCase(e.target.value) })}
          className={FORM_INPUT_CLASS}
          placeholder="Ex.: Limpeza de pele"
          autoFocus
        />
        {form.categoria === "protocolo" && (
          <p className="mt-1 text-xs text-gray-500">
            Este é o item da lista de Procedimentos, com o preço por convênio. Na página Protocolos, o pacote tem outro nome e aponta para este procedimento.
          </p>
        )}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className={FORM_LABEL_CLASS}>Categoria *</label>
          <select
            value={form.categoria}
            onChange={(e) => onChange({ categoria: e.target.value })}
            className={FORM_INPUT_CLASS}
          >
            <option value="">Selecione...</option>
            {form.categoria && !opcoes.some((o) => o.value === form.categoria) && (
              <option value={form.categoria}>{form.categoria}</option>
            )}
            {opcoes.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className={FORM_LABEL_CLASS}>Duração (min) *</label>
          <input
            type="number"
            min={1}
            value={form.duration}
            onChange={(e) => onChange({ duration: e.target.value })}
            className={FORM_INPUT_CLASS}
          />
        </div>
      </div>
      <div>
        <label className={FORM_LABEL_CLASS}>Descrição</label>
        <textarea
          value={form.description}
          onChange={(e) => onChange({ description: e.target.value })}
          rows={4}
          className={`${FORM_INPUT_CLASS} resize-y min-h-[96px]`}
          placeholder="Opcional"
        />
      </div>
    </div>
  );
}
