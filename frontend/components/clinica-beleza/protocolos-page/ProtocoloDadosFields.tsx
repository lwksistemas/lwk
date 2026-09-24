import { entityName } from "@/lib/clinica-beleza-entities";
import { resolveProcedureCategoriaSlug } from "@/lib/clinica-beleza-categories";
import { toUpperCase } from "@/lib/format-br";
import {
  FORM_INPUT_CLASS,
  FORM_LABEL_CLASS,
  FORM_SECTION_TITLE_CLASS,
  PROTOCOLO_FORM_FIELDS_LEFT,
  type ProtocoloFormState,
  type ProtocoloFormTextFieldKey,
  type ProtocoloProcedureOption,
} from "./protocolos-page-types";

interface ProtocoloDadosFieldsProps {
  form: ProtocoloFormState;
  procedures: ProtocoloProcedureOption[];
  onChange: (patch: Partial<ProtocoloFormState>) => void;
}

export function ProtocoloDadosFields({ form, procedures, onChange }: ProtocoloDadosFieldsProps) {
  const opcoes = procedures.filter(
    (pr) =>
      resolveProcedureCategoriaSlug(pr.categoria) === "protocolo" || String(pr.id) === form.procedure,
  );
  const temCategoria = procedures.some(
    (pr) => resolveProcedureCategoriaSlug(pr.categoria) === "protocolo",
  );

  return (
    <div className="space-y-4">
      <p className={FORM_SECTION_TITLE_CLASS}>Dados do protocolo</p>
      <div>
        <label className={FORM_LABEL_CLASS}>Nome *</label>
        <input
          value={form.nome}
          onChange={(e) => onChange({ nome: toUpperCase(e.target.value) })}
          className={FORM_INPUT_CLASS}
          placeholder="Ex.: Protocolo limpeza de pele"
          autoFocus
        />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className={FORM_LABEL_CLASS}>Procedimento *</label>
          <select
            value={form.procedure}
            onChange={(e) => onChange({ procedure: e.target.value })}
            className={FORM_INPUT_CLASS}
          >
            <option value="">Selecione...</option>
            {opcoes.map((pr) => (
              <option key={pr.id} value={pr.id}>
                {entityName(pr)}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-gray-500">
            {temCategoria
              ? "O valor por convênio fica neste procedimento, na página Procedimentos."
              : "Cadastre antes o procedimento na categoria Protocolo, em Procedimentos, e defina o valor por convênio lá."}
          </p>
        </div>
        <div>
          <label className={FORM_LABEL_CLASS}>Tempo estimado (min) *</label>
          <input
            type="number"
            min={1}
            value={form.tempo_estimado}
            onChange={(e) => onChange({ tempo_estimado: e.target.value })}
            className={FORM_INPUT_CLASS}
          />
        </div>
      </div>
      {PROTOCOLO_FORM_FIELDS_LEFT.map(([key, label]) => (
        <div key={key}>
          <label className={FORM_LABEL_CLASS}>{label}</label>
          <textarea
            value={form[key as ProtocoloFormTextFieldKey]}
            onChange={(e) => onChange({ [key]: e.target.value } as Partial<ProtocoloFormState>)}
            rows={4}
            className={`${FORM_INPUT_CLASS} resize-y min-h-[96px]`}
            placeholder="Opcional"
          />
        </div>
      ))}
    </div>
  );
}
