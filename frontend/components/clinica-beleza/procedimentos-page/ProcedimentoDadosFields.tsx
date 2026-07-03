import { PROCEDURE_CATEGORIA_OPTIONS } from "@/lib/clinica-beleza-categories";
import { toUpperCase } from "@/lib/format-br";
import {
  FORM_INPUT_CLASS,
  FORM_LABEL_CLASS,
  FORM_SECTION_TITLE_CLASS,
  type ProcedimentoFormState,
} from "./procedimentos-page-types";

interface ProcedimentoDadosFieldsProps {
  form: ProcedimentoFormState;
  onChange: (patch: Partial<ProcedimentoFormState>) => void;
}

export function ProcedimentoDadosFields({ form, onChange }: ProcedimentoDadosFieldsProps) {
  return (
    <div className="space-y-4">
      <p className={FORM_SECTION_TITLE_CLASS}>Dados do procedimento</p>
      <div>
        <label className={FORM_LABEL_CLASS}>Nome *</label>
        <input
          value={form.name}
          onChange={(e) => onChange({ name: toUpperCase(e.target.value) })}
          className={FORM_INPUT_CLASS}
          placeholder="Ex.: Limpeza de pele"
          autoFocus
        />
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
            {PROCEDURE_CATEGORIA_OPTIONS.map((opt) => (
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
